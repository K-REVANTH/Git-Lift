# PACE SCM Migration — Platform Parity Module
## Discovery-Enriched Parity Engine: Implementation Plan

**Version:** 2.0
**Date:** 2026-08-12
**Status:** Pre-Implementation Planning
**Scope:** Platform Parity Module — Self-Evolving Discovery-Enriched Architecture
**Author:** Platform Migration Engineering Team

---

## 1. Problem Statement

The current platform parity system compares two SCM platforms using a static Knowledge Base and produces reports like:

> *"Service Desk: HARD\_BLOCKER — GitLab supports it, GitHub does not."*

This is technically correct but **operationally useless** for a migration team. It does not answer the questions that actually drive migration planning:

| Unanswered Question | Why It Matters |
|---|---|
| How many repositories actually use this feature? | 1 repo vs 219 repos requires completely different remediation budgets |
| Which blockers demand immediate action? | Teams cannot plan sprints without urgency ordering |
| Where did that count come from? | Auditors and approvers need traceable evidence |
| What happens when a new discovery CSV arrives with unknown columns? | Static systems silently miss new signals |

**This implementation plan describes a system that answers all four questions** by combining a
deterministic evidence engine, a self-evolving Knowledge Base, and a LangChain-orchestrated
LLM narrator.

The system will transform reports from:
Service Desk → HARD_BLOCKER

Into:
Service Desk → HARD_BLOCKER
219 of 243 repositories affected (90.1%)
Urgency: HIGH
Evidence: service_desk_enabled = true (243 rows scanned)
This will break immediately post-migration.
Plan replacement before go-live.

---

## 2. Core Architectural Principle

Before any diagram or code, one rule governs every design decision in this system:


```text
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│ DETERMINISTIC ENGINE → DECIDES all migration facts              │
│ KB UPDATER → EXPANDS knowledge over time                        │
│ CLAUDE via LANGCHAIN → EXPLAINS facts as narrative              │
│                                                                 │
│ Claude never creates a blocker.                                 │
│ Claude never removes a blocker.                                 │
│ Claude never changes a risk level.                              │
│ Claude never writes directly to any KB file.                    │
│ Every number in the report traces back to a CSV column.         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

This separation is non-negotiable. It is what makes the system auditable, reproducible,
and safe for enterprise migration decisions.

---

## 3. Three-Layer Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│ PARITY CHECK SYSTEM v2.0                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Layer 1 — EVIDENCE (Discovery CSV + Knowledge Base)                 │
│ ────────────────────────────────────────────────                    │
│ Real repository usage data extracted from discovery CSV.            │
│ Curated, versioned, human-reviewable capability declarations.       │
│ No inference. No hallucination. Ground truth only.                  │
│                                                                     │
│ Layer 2 — LOGIC (Deterministic Comparison Engine)                   │
│ ─────────────────────────────────────────────────                   │
│ Structural diff of KB data enriched with usage signals.             │
│ Same inputs always produce identical gap analysis.                  │
│ Auditable, unit-testable. No LLM involved at this layer.            │
│                                                                     │
│ Layer 3 — NARRATIVE (LangChain + AWS Bedrock Claude)                │
│ ────────────────────────────────────────────────────                │
│ LLM receives pre-computed structured facts and generates            │
│ human-readable narrative. LLM explains facts. Never decides them.   │
│ LangChain enforces structured output via PydanticOutputParser.      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
---

## 4. Full System Architecture

### 4.1 High-Level Data Flow

```mermaid
flowchart TD
    CSV[Discovery CSV\n243 repositories] --> STEP0

    subgraph STEP0["Step 0 — Parse Discovery"]
        PD1[Detect Source Platform\nScore-based deterministic]
        PD2[Load discovery_mapping.yaml]
        PD3[Extract Evidence per Column]
        PD4[Aggregate Usage Signals]
        PD5[Flag Unmapped Columns]
        PD1 --> PD2 --> PD3 --> PD4 --> PD5
    end

    STEP0 --> US[Usage Signals\nrepo_count · percentage\nurgency · evidence]
    STEP0 --> UC[Unmapped Columns\nnew / unknown]

    UC --> STEP05

    subgraph STEP05["Step 0.5 — KB Updater"]
        KB1{Unmapped\ncolumns?}
        KB2[Claude classifies\nunknown column]
        KB3{Confidence\nHIGH?}
        KB4[Auto-write to\ndiscovery_mapping.yaml]
        KB5[Stage in\nkb_update_proposals.yaml]
        KB6[Log to\nkb_update_log.yaml]
        KB1 -->|Yes| KB2
        KB1 -->|No| KB6
        KB2 --> KB3
        KB3 -->|Yes| KB4
        KB3 -->|No| KB5
        KB4 --> KB6
        KB5 --> KB6
    end

    US --> STEP1
    STEP05 --> STEP1

    subgraph STEP1["Step 1 — Init"]
        I1[Validate platforms]
        I2[SOURCE from Step 0\nTARGET from user]
        I1 --> I2
    end

    subgraph STEP2["Step 2 — Load KB"]
        L1[capability_taxonomy.yaml]
        L2[platforms/source.yaml]
        L3[platforms/target.yaml]
        L4[known_gaps.yaml]
        L1 & L2 & L3 & L4 --> L5[KB Loaded]
    end

    subgraph STEP3["Step 3 — Compare"]
        C1[Deterministic Gap Classification]
        C2[Attach Usage Signals to Gaps]
        C3[Calculate Risk with Usage Weighting]
        C1 --> C2 --> C3
    end

    subgraph STEP4["Step 4 — Generate Report"]
        G1[Build Structured Fact Payload]
        G2[LangChain PromptTemplate]
        G3[ChatBedrock — Claude]
        G4[PydanticOutputParser\n5-section enforcement]
        G1 --> G2 --> G3 --> G4
    end

    subgraph STEP5["Step 5 — Export"]
        E1[Write .md report]
        E2[Write .json report]
        E1 & E2 --> E3[EFS / tmp]
    end

    STEP1 --> STEP2 --> STEP3 --> STEP4 --> STEP5
```

### 4.2 KB Self-Evolution Flow

```mermaid
flowchart TD
    A[New Discovery CSV Arrives] --> B[Step 0: Parse Discovery]
    B --> C{All columns in\ndiscovery_mapping.yaml?}

    C -->|Yes| D[Proceed to normal pipeline\nno KB update needed]

    C -->|No| E[Step 0.5: KB Updater triggered]

    E --> F[LangChain + Claude\nclassifies each unknown column]

    F --> G{Confidence\nlevel?}

    G -->|HIGH| H[Auto-write to\ndiscovery_mapping.yaml]
    G -->|MEDIUM| I[Stage in\nkb_update_proposals.yaml]
    G -->|LOW| J[Flag for manual review\nwith Claude reasoning]

    H --> K[Log entry in kb_update_log.yaml]
    I --> K
    J --> K

    K --> L[KB Grows\nwith each new CSV]

    L --> M[Next CSV processes\nmore columns automatically]

    M --> A
```

### 4.3 Usage Signal Evidence Chain

```mermaid
flowchart LR
    A["Raw CSV Row\nmr_draft_count = 7"] --> B

    subgraph B["Evidence Extraction"]
        B1[Column: mr_draft_count]
        B2[Rule: value > 0]
        B3[Maps to: review.draft_pr]
        B1 --> B2 --> B3
    end

    B --> C

    subgraph C["Usage Aggregation\n243 repos scanned"]
        C1[repo_count: 131]
        C2[percentage: 53.9%]
        C3[urgency: HIGH]
        C4[examples: repo-alpha, repo-beta]
    end

    C --> D

    subgraph D["Gap Enrichment"]
        D1[classification: HARD_BLOCKER]
        D2[repo_count: 131]
        D3[urgency: HIGH]
        D4[evidence.columns: mr_draft_count]
        D5[evidence.rule: value > 0]
    end

    D --> E["Report Section\nDraft PRs: HARD_BLOCKER\n131/243 repos 53.9% — Urgency HIGH\nEvidence: mr_draft_count > 0"]
```

### 4.4 Report Generation — LangChain Pipeline

```mermaid
flowchart TD
    A[Deterministic Facts\nfrom Step 3] --> B

    subgraph B["Fact Payload Builder"]
        B1[Hard Blockers + usage counts]
        B2[Behavioral Diffs + usage counts]
        B3[Risk level + justification]
        B4[Usage signals summary]
    end

    B --> C[LangChain PromptTemplate\nInjects facts into template]

    C --> D[ChatBedrock\nClaude 3 Sonnet]

    D --> E[PydanticOutputParser]

    E --> F{All 5 sections\npresent?}

    F -->|Yes| G[ParityReport object\nvalidated]
    F -->|No| H[LangChain retry\nmax 2 attempts]

    H --> D

    G --> I[Markdown Report]
    G --> J[JSON Report]

    subgraph SK["Skip-Bedrock Mode — CI / Deterministic"]
        SK1[Deterministic template\nfills sections 2 and 3]
        SK2[No AWS required]
        SK3[No LangChain call]
    end

    A -->|"--skip-bedrock flag"| SK
    SK --> I
    SK --> J
```


### 4.5 KB Write Safety Model

```mermaid
flowchart TD
    A[Claude proposes KB update] --> B{Confidence?}

    B -->|HIGH| C[Auto-write to\ndiscovery_mapping.yaml]
    B -->|MEDIUM| D[Stage in\nkb_update_proposals.yaml]
    B -->|LOW| E[Flag for manual review]

    C --> F[Log in kb_update_log.yaml]
    D --> F
    E --> F

    G["NEVER auto-write to:"] --> H[capability_taxonomy.yaml]
    G --> I[known_gaps.yaml]
    G --> J["platforms/*.yaml"]

    K[Human approval required\nfor all three above]
```

## 5. Knowledge Base Design

### 5.1 File Structure

```text
capability_kb/
├── capability_taxonomy.yaml      ← 54 canonical capability IDs — source of truth
├── known_gaps.yaml               ← Curated per-path migration gap records
├── discovery_mapping.yaml        ← NEW: CSV column → capability mapping config
├── kb_update_proposals.yaml      ← NEW: Human review staging area
├── kb_update_log.yaml            ← NEW: Full audit log of every auto-update
└── platforms/
    ├── gitlab.yaml               ← Per-capability support data
    ├── github.yaml               ← Per-capability support data
    ├── azure_devops.yaml         ← Per-capability support data
    └── bitbucket.yaml            ← Per-capability support data
```

### 5.2 New File: discovery\_mapping.yaml

This is the master translation table between discovery CSV columns and capability IDs.
It is **configuration — not code**. Adding support for a new platform's CSV columns
requires only a YAML change, not a code change.

```yaml
# discovery_mapping.yaml
# Maps CSV columns from any SCM discovery report to canonical capability IDs.
# This file grows automatically as new discovery CSVs are processed.

repo.lfs:
  columns:
    - lfs_enabled
    - total_lfs_files
    - lfs_objects_size_bytes
  detection_rule: any_positive
  confidence: HIGH
  value_type: numeric
  platforms: [gitlab]
  last_updated: "2026-08-12"

review.draft_pr:
  columns:
    - mr_draft_count           # GitLab column name
    - draft_pull_requests      # GitHub column name (added later)
  detection_rule: any_positive
  confidence: HIGH
  value_type: numeric
  platforms: [gitlab, github]
  last_updated: "2026-08-12"

review.approval_rules:
  columns:
    - total_approval_rules
    - approval_rules_names
    - approval_rules_min_approvals
  detection_rule: any_positive
  confidence: HIGH
  value_type: numeric
  platforms: [gitlab]
  last_updated: "2026-08-12"
```

### 5.3 Usage Signal Schema

Every capability in the pipeline output carries this structure after Step 0 runs:
```json
{
  "review.draft_pr": {
    "repo_count": 131,
    "percentage": 53.9,
    "urgency": "HIGH",
    "confidence": "HIGH",
    "total_value": 847,
    "examples": ["repo-alpha", "repo-beta", "repo-gamma"],
    "evidence": {
      "columns": ["mr_draft_count"],
      "detection_rule": "value > 0",
      "value_type": "numeric"
    }
  }
}
```
The `evidence` block is the audit trail. Every number in the final report is traceable back to a specific column and detection rule.

### 5.4 KB Write Safety Rules

| **File** | **Auto-write Allowed** | **Condition** |
| --- | --- | --- |
| **`discovery_mapping.yaml`** | ✅ Yes | Confidence HIGH only |
| **`kb_update_log.yaml`** | ✅ Yes | Always — audit trail |
| **`kb_update_proposals.yaml`** | ✅ Yes | Staging only — not live KB |
| **`capability_taxonomy.yaml`** | ❌ Never | Human approval required |
| **`known_gaps.yaml`** | ❌ Never | Human approval required |
| **`platforms/*.yaml`** | ❌ Never | Human approval required |

---

## 6. Component Specifications

### 6.1 Step 0 — platform\_parity\_parse\_discovery.py

| **Property** | **Detail** |
| --- | --- |
| Type | New script |
| LLM involved | No |
| LangChain involved | No |
| Dependencies | **`csv`**, **`json`**, **`yaml`**, **`pathlib`**, **`sys`**, **`re`** — stdlib only |
| Input placeholders | **`CSV_PATH`**, **`EXECUTION_ID`** |

Platform detection uses a score-based model — not string matching alone:
```text
GitLab URL found in http_url / ssh_url     → +100 points
GitLab-specific column found               → +20 points each
GitHub-specific column found               → -20 points each
Azure DevOps-specific column found         → -20 points each

Score ≥ 100  → HIGH confidence
Score 60–99  → MEDIUM confidence
Score < 60   → RuntimeError (ambiguous — do not guess)
```

Urgency thresholds:
```text
repo_percentage > 50%  →  HIGH
repo_percentage > 10%  →  MEDIUM
repo_percentage ≤ 10%  →  LOW
```

Output keys:

| **Key** | **Type** | **Description** |
| --- | --- | --- |
| **`source_platform`** | string | Detected platform: **`gitlab`** / **`github`** / **`azure_devops`** / **`bitbucket`** |
| **`platform_confidence`** | string | **`HIGH`** / **`MEDIUM`** / **`LOW`** |
| **`platform_evidence`** | object | **`url_matches`** count, platform-specific columns found |
| **`total_repos`** | int | Row count from CSV |
| **`usage_signals`** | object | capability_id → enriched signal object |
| **`unmapped_columns`** | list | Column names not found in **`discovery_mapping.yaml`** |
| **`column_stats`** | object | Raw per-column aggregate stats |
| **`csv_columns`** | list | All column names found in the CSV |


### 6.2 Step 0.5 — platform\_parity\_kb\_updater.py
| **Property** | **Detail** |
| --- | --- |
| Type | New script |
| LLM involved | Yes — column classification only |
| LangChain involved | Yes — PromptTemplate + ChatBedrock + PydanticOutputParser |
| Triggers | Only when **`unmapped_columns`** is non-empty |
| Input placeholders | **`KB_BASE_PATH`**, **`AUTO_UPDATE_THRESHOLD`**, **`EXECUTION_ID`** |

LangChain components used:
```python
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class KBUpdateProposal(BaseModel):
    column_name: str
    maps_to_capability: str      # existing ID or "NEW"
    proposed_capability_id: str  # only if maps_to == "NEW"
    detection_rule: str          # e.g. "value > 0" / "boolean_true"
    confidence: str              # HIGH / MEDIUM / LOW
    reasoning: str               # Claude's explanation for audit log
```

**What Claude is asked here — and nothing more:**

```text
Given:
  - Unknown CSV column name: "workflow_runs"
  - Sample values from 10 repos: [0, 0, 5, 12, 0, 3, 0, 8, 0, 1]
  - Source platform detected: github
  - Full capability taxonomy: [54 capability IDs provided]

Answer:
  1. Which existing capability does this column most likely measure?
  2. What is the correct detection rule?
  3. How confident are you? (HIGH / MEDIUM / LOW)
  4. If no existing capability fits, propose a new capability ID.
  5. Explain your reasoning in one sentence.
```

Write behaviour by confidence level:
| **Confidence** | **Action** |
| --- | --- |
| HIGH | Auto-write to **`discovery_mapping.yaml`** + log to **`kb_update_log.yaml`** |
| MEDIUM | Write to **`kb_update_proposals.yaml`** only + log |
| LOW | Write to **`kb_update_proposals.yaml`** only + log |
| Any | Always log to **`kb_update_log.yaml`** |


### 6.3 Step 3 — platform_parity_compare.py (Enhanced)

The gap classification logic is completely unchanged. Usage signals are attached
after classification.

Gap object before enhancement:

```json
{
  "capability_id": "service_desk",
  "classification": "HARD_BLOCKER"
}
Gap object after enhancement:
```

```json
{
  "capability_id": "service_desk",
  "classification": "HARD_BLOCKER",
  "repo_count": 219,
  "repo_percentage": 90.1,
  "urgency": "HIGH",
  "confidence": "HIGH",
  "examples": ["repo-1", "repo-2", "repo-3"],
  "evidence": {
    "columns": ["service_desk_enabled"],
    "detection_rule": "boolean_true",
    "value_type": "boolean"
  }
}
```

Usage-aware risk weighting:
| **Condition** | **Risk Level** |
| --- | --- |
| Hard blocker + usage ≥ 50% | CRITICAL |
| Hard blocker + usage 10–49% | HIGH |
| Hard blocker + usage < 10% | HIGH (serious, lower priority) |
| Behavioral diff + usage ≥ 50% | HIGH |
| Behavioral diff + usage < 50% | MEDIUM |
| Partial support only | MEDIUM |
| All seamless | LOW |


### 6.4 Step 4 — platform\_parity\_generate_report.py (LangChain)

LangChain chain structure:

```python
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence

chain = PromptTemplate(...) | ChatBedrock(...) | PydanticOutputParser(...)
```

System instruction injected into every prompt:
```text
The supplied facts are authoritative.
Do not invent capabilities.
Do not alter classifications.
Do not introduce workarounds not present in the input.
Do not change risk levels.
Your responsibility is explanation only.
Reference repository counts and urgency in every section you write.
```

Pydantic model enforcing 5-section structure:
```python
class ParityReport(BaseModel):
    executive_summary: str
    hard_blockers_section: str
    behavioral_differences_section: str
    seamless_section: str
    coverage_section: str
```

If Claude omits any section, the PydanticOutputParser raises and LangChain retries automatically up to the configured maximum attempts.

Skip-bedrock mode is fully preserved. When --skip-bedrock is set, the LangChain call is bypassed entirely and deterministic templates fill the report sections.
No AWS credentials required.

---

## 7. Complete File Change Register

New Files

| **File** | **Purpose** |
| --- | --- |
| **`capability_kb/discovery_mapping.yaml`** | CSV column → capability mapping config |
| **`capability_kb/kb_update_proposals.yaml`** | Human review staging area for MEDIUM/LOW proposals |
| **`capability_kb/kb_update_log.yaml`** | Full audit log of every auto-update |
| **`scripts/platform_parity_parse_discovery.py`** | Step 0 — CSV parser and usage aggregator |
| **`scripts/platform_parity_kb_updater.py`** | Step 0.5 — KB self-evolution engine |
| **`metadata/platform_parity_parse_discovery.txt`** | Script descriptor |
| **`metadata/platform_parity_kb_updater.txt`** | Script descriptor |
| **`platform_parity_run.py`** | CLI entry point for local runs |

### Modified Files

| **File** | **Change** |
| --- | --- |
| **`scripts/platform_parity_init.py`** | **`SOURCE_PLATFORM`** now reads from Step 0 — no longer a user input |
| **`scripts/platform_parity_compare.py`** | Attaches usage signals to gap objects; usage-aware risk weighting |
| **`scripts/platform_parity_generate_report.py`** | Raw boto3 replaced with LangChain PromptTemplate + ChatBedrock + PydanticOutputParser |
| **`workflow/platform_parity_workflow.json`** | Steps 0 and 0.5 added before existing steps |
| **`test_bedrock_e2e.py`** | Optional **`--csv`** argument; wires to parse_discovery before pipeline |

### Unchanged Files

| **File** | **Reason Unchanged** |
| --- | --- |
| **`scripts/platform_parity_load_kb.py`** | Loads updated KB — no logic change needed |
| **`scripts/platform_parity_export.py`** | Fully compatible with enriched gap objects |
| **`capability_kb/capability_taxonomy.yaml`** | Grows only via human approval |
| **`capability_kb/known_gaps.yaml`** | Grows only via human approval |
| **`capability_kb/platforms/*.yaml`** | Updated only via human approval |

---

## 8. Updated Workflow Definition

```json
{
  "name": "platform_parity_check",
  "steps": [
    {
      "name": "platform_parity_parse_discovery",
      "values": {
        "CSV_PATH": ""
      }
    },
    {
      "name": "platform_parity_kb_updater",
      "values": {
        "KB_BASE_PATH": "",
        "AUTO_UPDATE_THRESHOLD": "HIGH"
      }
    },
    {
      "name": "platform_parity_init",
      "values": {
        "TARGET_PLATFORM": "",
        "OUTPUT_FORMAT": "markdown",
        "SCOPE_FILTER": "[]",
        "AWS_REGION": "",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
        "KB_BASE_PATH": "",
        "NO_CACHE": false,
        "PROJECT_ID": ""
      }
    },
    { "name": "platform_parity_load_kb" },
    { "name": "platform_parity_compare" },
    {
      "name": "platform_parity_generate_report",
      "activity_options": {
        "start_to_close_seconds": 120,
        "heartbeat_seconds": 30,
        "retry_policy": {
          "maximum_attempts": 2,
          "non_retryable_error_types": ["ScriptNotFoundError"]
        }
      }
    },
    { "name": "platform_parity_export" }
  ]
}
```

> ***Key change: `SOURCE_PLATFORM` is removed from `platform_parity_init` values.***
> ***It now flows automatically from `{{steps.platform_parity_parse_discovery.source_platform}}`.***

---
