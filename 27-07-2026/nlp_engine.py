# nlp_engine.py

"""
Schema-aware NLP Query Engine for GitLift Neo4j.

READ-ONLY
Only executes Cypher through ReadOnlyNeo4j.
"""

import re
from neo4j_readonly import ReadOnlyNeo4j


TEMPLATES = [

    #
    # General
    #
    {
        "id": "COUNT_NODES",
        "description": "Count total nodes",
        "patterns": [
            r"how many nodes",
            r"total nodes",
        ],
        "cypher": """
            MATCH (n)
            RETURN count(n) AS count
        """,
        "format": "count"
    },

    {
        "id": "COUNT_RELS",
        "description": "Count relationships",
        "patterns": [
            r"how many relationships",
            r"total relationships",
        ],
        "cypher": """
            MATCH ()-[r]->()
            RETURN count(r) AS count
        """,
        "format": "count"
    },

    #
    # Repositories
    #
    {
        "id": "COUNT_REPOS",
        "description": "Count repositories",
        "patterns": [
            r"how many repos",
            r"how many repositories",
        ],
        "cypher": """
            MATCH (r:Repository)
            RETURN count(r) AS count
        """,
        "format": "count"
    },

    {
        "id": "SHOW_REPOS",
        "description": "List repositories",
        "patterns": [
            r"show repositories",
            r"list repositories",
            r"show repos",
            r"list repos",
        ],
        "cypher": """
            MATCH (r:Repository)
            RETURN
                r.name AS repository,
                r.language AS language
            LIMIT 20
        """,
        "format": "table"
    },

    #
    # APIs
    #
    {
        "id": "COUNT_APIS",
        "description": "Count APIs",
        "patterns": [
            r"how many apis",
            r"count apis",
        ],
        "cypher": """
            MATCH (a:API)
            RETURN count(a) AS count
        """,
        "format": "count"
    },

    {
        "id": "SHOW_APIS",
        "description": "List APIs",
        "patterns": [
            r"show apis",
            r"list apis",
            r"show api",
        ],
        "cypher": """
            MATCH (a:API)
            RETURN
                a.path AS path,
                a.method AS method
            LIMIT 20
        """,
        "format": "table"
    },

    #
    # Services
    #
    {
        "id": "SHOW_SERVICES",
        "description": "List Services",
        "patterns": [
            r"show services",
            r"list services",
        ],
        "cypher": """
            MATCH (s:Service)
            RETURN s.name AS service
            LIMIT 20
        """,
        "format": "table"
    },

    #
    # Pipelines
    #
    {
        "id": "COUNT_PIPELINES",
        "description": "Count pipelines",
        "patterns": [
            r"how many pipelines",
            r"count pipelines",
        ],
        "cypher": """
            MATCH (p:GraphNode:PIPELINE)
            RETURN count(p) AS count
        """,
        "format": "count"
    },

    {
        "id": "SHOW_PIPELINES",
        "description": "List pipelines",
        "patterns": [
            r"show pipelines",
            r"list pipelines",
        ],
        "cypher": """
            MATCH (p:GraphNode:PIPELINE)
            RETURN
                p.name AS pipeline,
                p.pipeline_id AS pipeline_id
            LIMIT 20
        """,
        "format": "table"
    },

    #
    # Methods
    #
    {
        "id": "COUNT_METHODS",
        "description": "Count methods",
        "patterns": [
            r"how many methods",
            r"count methods",
        ],
        "cypher": """
            MATCH (m:Method)
            RETURN count(m) AS count
        """,
        "format": "count"
    },

    #
    # Classes
    #
    {
        "id": "COUNT_CLASSES",
        "description": "Count classes",
        "patterns": [
            r"how many classes",
            r"count classes",
        ],
        "cypher": """
            MATCH (c:Class)
            RETURN count(c) AS count
        """,
        "format": "count"
    },

    #
    # GitHub Repositories
    #
    {
        "id": "SHOW_GITHUB_REPOS",
        "description": "List GitHub repositories",
        "patterns": [
            r"show github repos",
            r"show github repositories",
            r"list github repos",
        ],
        "cypher": """
            MATCH (g:GitHubRepo)
            RETURN
                g.name AS repo,
                g.language AS language,
                g.visibility AS visibility
            LIMIT 20
        """,
        "format": "table"
    },

    #
    # GitHub Members
    #
    {
        "id": "SHOW_GITHUB_MEMBERS",
        "description": "List GitHub members",
        "patterns": [
            r"show github members",
            r"list github members",
        ],
        "cypher": """
            MATCH (g:GitHubMember)
            RETURN
                g.login AS login,
                g.ide_type AS ide
            LIMIT 20
        """,
        "format": "table"
    },

    #
    # Labels
    #
    {
        "id": "LABELS",
        "description": "List labels",
        "patterns": [
            r"list labels",
            r"list node types",
            r"show labels",
        ],
        "cypher": """
            CALL db.labels()
            YIELD label
            RETURN label
        """,
        "format": "table"
    },

    #
    # Relationship Types
    #
    {
        "id": "REL_TYPES",
        "description": "List relationship types",
        "patterns": [
            r"relationship types",
            r"list relationships",
            r"show relationship types",
        ],
        "cypher": """
            MATCH ()-[r]->()
            RETURN
                type(r) AS relationship,
                count(*) AS count
            ORDER BY count DESC
        """,
        "format": "table"
    },
]


class NLPEngine:

    def __init__(self, db):
        self.db = db

    def ask(self, question: str):

        question = question.strip().lower()

        for template in TEMPLATES:

            for pattern in template["patterns"]:

                if re.search(pattern, question):

                    try:

                        data = self.db.query(
                            template["cypher"]
                        )

                        return {
                            "matched": True,
                            "description": template["description"],
                            "cypher": template["cypher"],
                            "answer": self._format(
                                template["format"],
                                data
                            ),
                            "data": data
                        }

                    except Exception as e:

                        return {
                            "matched": True,
                            "answer": f"Query failed: {e}"
                        }

        return {
            "matched": False,
            "answer": self.help_text()
        }

    def _format(self, format_type, data):

        if not data:
            return "No results found."

        if format_type == "count":
            return f"Count = {data[0]['count']:,}"

        lines = []

        for i, row in enumerate(data[:20], start=1):

            values = []

            for k, v in row.items():

                value = str(v)

                if len(value) > 80:
                    value = value[:80] + "..."

                values.append(f"{k}: {value}")

            lines.append(
                f"{i}. " + " | ".join(values)
            )

        return "\n".join(lines)

    def help_text(self):

        return """
Examples:

how many nodes
how many repositories
show repositories

how many apis
show apis

show services

how many pipelines
show pipelines

how many methods
how many classes

show github repos
show github members

list node types
show relationship types

how many relationships
"""


def interactive_mode():

    print("=" * 70)
    print("GitLift NLP Query Engine (READ ONLY)")
    print("Type 'exit' to quit")
    print("=" * 70)

    db = ReadOnlyNeo4j(
        uri="bolt+s://neo4j-bolt.ustpace.com:7687",
        username="neo4j",
        password="password123"
    )

    engine = NLPEngine(db)

    while True:

        try:
            question = input("\nAsk: ").strip()

        except (KeyboardInterrupt, EOFError):
            break

        if question.lower() in (
            "exit",
            "quit",
            "q"
        ):
            break

        if not question:
            continue

        result = engine.ask(question)

        print()
        print(result["answer"])

        if result.get("cypher"):
            print("\nCypher:")
            print(result["cypher"])

    db.close()


if __name__ == "__main__":
    interactive_mode()