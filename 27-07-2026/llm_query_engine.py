# llm_query_engine.py

"""
LLM QUERY ENGINE (Google Gemini)

Free-form English -> Cypher -> Neo4j

Uses:
    Google Gemini API (FREE)
    ReadOnlyNeo4j

Safety:
    READ ONLY
"""

import os
import re

from google import genai

from neo4j_readonly import ReadOnlyNeo4j


# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

MODEL_NAME = "gemini-3.6-flash"

# Write keywords that should NEVER appear in generated Cypher
FORBIDDEN_PATTERNS = [
    r"\bCREATE\b",
    r"\bMERGE\b",
    r"\bDELETE\b",
    r"\bDETACH\b",
    r"\bSET\b",
    r"\bREMOVE\b",
    r"\bDROP\b",
    r"\bLOAD\s+CSV\b",
    r"\bFOREACH\b",
]


# ═══════════════════════════════════════════════════════════
# SCHEMA CONTEXT (Customized for UST PACE database)
# ═══════════════════════════════════════════════════════════

SCHEMA_INFO = """
NEO4J GRAPH SCHEMA (UST PACE Platform)
========================================

Two data models coexist in this graph:
- Code Analysis Model (Lumen)
- CI/CD Pipeline Model (GraphNode-based)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CODE ANALYSIS NODE TYPES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Repository:
  properties: id, name, language, repository_id
  count: 493

File:
  properties: id, path, language, repository_id
  count: 130,405

Class:
  properties: id, name, qualified_name, kind, repository_id

Method:
  properties: id, name, qualified_name, kind, repository_id

Symbol (generic base for code entities):
  properties: id, name, qualified_name, kind, repository_id
  kind can be: property, method, class, interface, enum, constructor
  count: 1,822,645

API:
  properties: id, path, method, repository_id

Service:
  properties: id, name, kind, repository_id

Function:
  properties: id, name, qualified_name, content, description,
              startLine, endLine, parameterCount, returnType,
              visibility, isExported, kind, repository_id

Interface, Constructor, Enum, Package:
  Similar to Class

External:
  properties: ext_id, kind, target

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CI/CD PIPELINE NODE TYPES (GraphNode)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All these have TWO labels: :GraphNode and specific subtype
Query pattern: MATCH (n:GraphNode {node_type: 'PIPELINE'})

Common properties for ALL GraphNode types:
  - node_id (unique)
  - node_type (matches subtype)
  - name
  - path (source file path)
  - artifact_type ('jenkinsfile', 'gitlab_ci', 'bamboo_yaml', 'harness_ci')
  - job_id
  - pipeline_id
  - product_name
  - text (human-readable description)
  - vector (for semantic search)

Subtypes (node_type values):
  PIPELINE     STAGE        JOB          STEP
  TOOL         RISK         SECURITY     ENVIRONMENT
  NOTIFICATION CREDENTIAL   FACT         AGENT
  PARAMETER    TRIGGER      IMPORT       SHARED_LIB
  ARTIFACT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GITHUB COPILOT DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GitHubRepo:
  properties: repository_id, name, full_name, org_id,
              language, visibility, private, archived,
              default_branch, description, html_url,
              created_at, updated_at
  count: 6

GitHubMember:
  properties: github_user_id, login, org_id,
              ide_type, last_activity_editor,
              last_activity_at, days_since_active,
              is_inactive, seat_created_at,
              created_at, updated_at
  count: 13

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEY RELATIONSHIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CODE MODEL:
  (Symbol|Class|Method|Function) -[:DEFINED_IN]-> (File)
  (File) -[:DEFINES]-> (Symbol)
  (Symbol) -[:CHILD_OF]-> (Class|Symbol)
  (Class) -[:HAS_METHOD]-> (Method)
  (Class) -[:HAS_PROPERTY]-> (Symbol)
  (API) -[:EXPOSED_BY]-> (Service)
  (API) -[:HANDLED_BY]-> (Method)
  (Method|Class) -[:INTERACTS_WITH]-> (External)
  (Method) -[:CALLS]-> (Method)
  (Symbol) -[:USES]-> (Symbol)
  (File) -[:HAS_IMPORT]-> (Symbol)
  (Symbol) -[:USES_LIBRARY]-> (Package)

PIPELINE MODEL:
  (PIPELINE) -[:HAS_STAGE]-> (STAGE)
  (STAGE) -[:HAS_JOB]-> (JOB)
  (JOB) -[:HAS_STEP]-> (STEP)
  (PIPELINE) -[:USES_TOOL]-> (TOOL)
  (PIPELINE) -[:HAS_RISK]-> (RISK)
  (PIPELINE) -[:TARGETS_ENV]-> (ENVIRONMENT)
  (PIPELINE) -[:NOTIFIES_VIA]-> (NOTIFICATION)
  (PIPELINE) -[:HAS_SECURITY_SCAN]-> (SECURITY)
  (PIPELINE) -[:RUNS_ON]-> (AGENT)
  (PIPELINE) -[:HAS_CREDENTIAL]-> (CREDENTIAL)
  (PIPELINE) -[:HAS_FACT]-> (FACT)
  (PIPELINE) -[:HAS_TRIGGER]-> (TRIGGER)
  (JOB) -[:HAS_PARAMETER]-> (PARAMETER)

GITHUB:
  (GitHubRepo) -[:HAS_MEMBER]-> (GitHubMember)
"""


# ═══════════════════════════════════════════════════════════
# VALIDATION & SANITIZATION
# ═══════════════════════════════════════════════════════════

def validate_cypher(cypher: str):
    """Reject any Cypher with write operations."""

    upper = cypher.upper()

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, upper, re.IGNORECASE):
            raise PermissionError(
                f"Unsafe Cypher generated. "
                f"Contains forbidden pattern: {pattern}"
            )

    return True


def sanitize_cypher(cypher: str):
    """Clean up LLM response — remove markdown, whitespace."""

    cypher = cypher.strip()

    # Remove markdown code fences if present
    cypher = re.sub(r"^```(?:cypher|sql)?\s*", "", cypher)
    cypher = re.sub(r"\s*```$", "", cypher)

    # Remove leading/trailing whitespace
    cypher = cypher.strip()

    # Validate
    validate_cypher(cypher)

    return cypher


# ═══════════════════════════════════════════════════════════
# GEMINI CLIENT
# ═══════════════════════════════════════════════════════════

_client_cache = None

def get_gemini_client():
    global _client_cache

    if _client_cache is not None:
        return _client_cache

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set."
        )

    _client_cache = genai.Client(api_key=api_key)

    return _client_cache



# ═══════════════════════════════════════════════════════════
# CYPHER GENERATION
# ═══════════════════════════════════════════════════════════

def generate_cypher(question: str) -> str:
    """
    Use Gemini to convert English question to Cypher query.
    """

    client = get_gemini_client()

    prompt = f"""You are an expert Neo4j Cypher query generator.

TASK: Generate a READ-ONLY Cypher query for the user's question.

═══════════════════════════════════════════
DATABASE SCHEMA:
═══════════════════════════════════════════
{SCHEMA_INFO}

═══════════════════════════════════════════
USER QUESTION:
═══════════════════════════════════════════
{question}

═══════════════════════════════════════════
STRICT RULES:
═══════════════════════════════════════════

1. Generate ONLY READ operations:
   - Use: MATCH, OPTIONAL MATCH, WITH, WHERE, RETURN, ORDER BY, LIMIT
   - NEVER use: CREATE, MERGE, DELETE, DETACH, SET, REMOVE, DROP

2. Use ONLY the labels and properties shown in schema above.

3. For pipeline queries, use pattern:
   MATCH (n:GraphNode {{node_type: 'PIPELINE'}})
   NOT: MATCH (n:PIPELINE) — this won't work

4. For counts, use: RETURN count(n) AS count

5. Always add LIMIT (max 30) for list queries unless it's an aggregate.

6. For text/name matching, use case-insensitive:
   WHERE toLower(n.name) CONTAINS toLower('searchterm')

7. Return ONLY the Cypher query. No explanations, no markdown, no comments.

═══════════════════════════════════════════
CYPHER QUERY:
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        cypher = response.text

    except Exception as e:
        raise RuntimeError(
            f"""
    Gemini API Error

    {e}

    Possible causes:
    • Invalid GEMINI_API_KEY
    • Model unavailable
    • Internet connectivity issue
    • API quota exceeded
    """
        )

    return sanitize_cypher(cypher)


# ═══════════════════════════════════════════════════════════
# RESULT FORMATTING
# ═══════════════════════════════════════════════════════════

def format_results(data):
    """Format query results for display."""

    if not data:
        return "No results found."

    # Count format
    if len(data) == 1 and "count" in data[0]:
        return f"📊 Count = {data[0]['count']:,}"

    # Table format
    lines = [f"\n📋 Found {len(data)} result(s):\n"]

    for index, row in enumerate(data[:25], start=1):

        values = []

        for key, value in row.items():

            value_str = str(value)

            if len(value_str) > 120:
                value_str = value_str[:120] + "..."

            values.append(f"{key}: {value_str}")

        lines.append(f"  {index:>3}. " + " | ".join(values))

    if len(data) > 25:
        lines.append(f"\n  ... and {len(data) - 25} more results")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# MAIN EXECUTION FLOW
# ═══════════════════════════════════════════════════════════

def execute_question(db, question):
    """Full pipeline: question -> cypher -> results -> formatted answer."""

    print("\n🤔 Generating Cypher with Gemini...")
    cypher = generate_cypher(question)

    print("\n💡 Generated Cypher:")
    print("─" * 70)
    print(cypher)
    print("─" * 70)

    print("\n⚡ Executing query...")
    data = db.query(cypher)

    print("\n📊 Answer:")
    print("─" * 70)
    print(format_results(data))
    print("─" * 70)


# ═══════════════════════════════════════════════════════════
# INTERACTIVE MODE
# ═══════════════════════════════════════════════════════════

def interactive_mode():

    print("=" * 70)
    print("  GitLift LLM Query Engine (Google Gemini)")
    print("  Free-form English → Cypher → Neo4j")
    print("  READ-ONLY MODE")
    print("=" * 70)

    # Verify API key exists
    try:
        get_gemini_client()
        print("[OK] Gemini API connected")
    except EnvironmentError as e:
        print(str(e))
        return

    # Connect to Neo4j
    db = ReadOnlyNeo4j(
        uri="bolt+s://neo4j-bolt.ustpace.com:7687",
        username="neo4j",
        password="password123",
    )

    print("\n💬 Type your questions in English")
    print("   Type 'exit', 'quit', or 'q' to stop\n")

    try:
        while True:

            try:
                question = input("🔍 Ask: ").strip()

            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 Goodbye!")
                break

            if not question:
                continue

            if question.lower() in ("exit", "quit", "q", "bye"):
                print("\n👋 Goodbye!")
                break

            try:
                execute_question(db, question)

            except PermissionError as e:
                print(f"\n🚫 Safety Block:\n{e}")

            except Exception as e:
                print(f"\n❌ Error:\n{e}")

    finally:
        db.close()


if __name__ == "__main__":
    interactive_mode()