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
