# SCM Migration Parity Check Agent
## Stakeholder Presentation — Implementation Framework

**Version:** 1.0  
**Date:** 2026-08-03  
**Scope:** GitLab → GitHub (extensible to Azure DevOps, Bitbucket, Perforce)

---

## 1. Problem Statement

When an enterprise migrates from one Source Code Management (SCM) platform to another, three failure modes cause the most damage:

| Failure Mode | Description | Business Impact |
|---|---|---|
| **Unknown hard blockers** | A critical feature has no equivalent on the target | Migration stalls mid-execution, requiring emergency re-architecture |
| **Silent behavioral differences** | A feature exists on both platforms but behaves differently | Data corruption, broken workflows, post-go-live incidents |
| **Scope underestimation** | Team discovers gaps after sprint planning | Budget overruns, deadline slippage |

**This system answers one question before the migration begins:**
> *"If we migrate from Platform A to Platform B today, which features migrate cleanly, which are lost, and which will behave differently — and what is the exact remediation path for each?"*

---

## 2. Solution Architecture

### Design Philosophy

The system uses a **three-layer architecture** with a strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PARITY CHECK AGENT                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 1 — FACTS (YAML Knowledge Base)                              │
│  ─────────────────────────────────────                              │
│  Curated, versioned, human-reviewable capability declarations.      │
│  No inference. No hallucination. Approved by platform SMEs.         │
│                                                                     │
│  Layer 2 — LOGIC (Python Comparison Engine)                         │
│  ─────────────────────────────────────────                          │
│  Deterministic structural diff of Layer 1 data.                     │
│  Same inputs always produce identical gap analysis.                 │
│  Auditable, unit-testable, no LLM involved.                         │
│                                                                     │
│  Layer 3 — NARRATIVE (AWS Bedrock / Claude)                         │
│  ─────────────────────────────────────────                          │
│  LLM receives the pre-computed structured gaps and synthesizes      │
│  human-readable explanations, workaround guidance, and              │
│  executive summaries. LLM does NOT decide what the facts are.       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
CLI Input (source, target)
        │
        ▼
CapabilityLoader ──────────► capability_kb/
  loads YAML                  ├── platforms/gitlab.yaml
                              ├── platforms/github.yaml
                              ├── capability_taxonomy.yaml
                              └── known_gaps.yaml
        │
        ▼
ComparisonEngine
  deterministic diff
        │
        ├── Hard Blockers (source has it, target does not)
        ├── Behavioral Differences (both have it, works differently)
        ├── Partial Support (target has workaround)
        └── Seamless (full parity)
        │
        ▼
BedrockClient
  structured JSON gaps → LLM prompt → human-readable report
        │
        ▼
ParityReport (Markdown + JSON)
```

### Key Architectural Decision: Why KB-First, Not LLM-First

| Concern | KB + LLM Synthesis (This System) | LLM-Only (Live Doc Fetch) |
|---|---|---|
| **Accuracy** | KB is ground truth. LLM cannot contradict it. | LLM interprets raw HTML. Can hallucinate. |
| **False negatives** | Near-zero for documented capabilities | Possible — LLM may miss a blocker |
| **Auditability** | YAML changes go through review/approval | LLM reasoning is opaque |
| **Cost per report** | 1 LLM call, ~2K tokens | 4+ LLM calls, 10K–40K tokens each |
| **Reliability** | No external HTTP dependency | Fragile to doc site restructure |
| **Determinism** | Identical inputs = identical outputs | Non-deterministic |

False negatives (missed blockers) are catastrophic in enterprise migrations. The KB-first design eliminates that risk within KB coverage.

---

## 3. Knowledge Base Design

### Structure

```
capability_kb/
├── capability_taxonomy.yaml      ← Master list of all canonical capability IDs
├── known_gaps.yaml               ← Pre-documented pair-specific migration risks
└── platforms/
    ├── gitlab.yaml               ← GitLab support declarations + behavior
    ├── github.yaml               ← GitHub support declarations + behavior
    ├── azure_devops.yaml         ← (planned)
    └── bitbucket.yaml            ← (planned)
```

### Capability Taxonomy

The taxonomy is the single source of truth for what capabilities exist. Every platform YAML must map to a canonical taxonomy ID. This prevents drift between platform descriptions.

Current taxonomy covers **8 categories** and **54 individual capabilities**:

| Category | Capability IDs | Examples |
|---|---|---|
| `repository` | 10 | `repo.mirroring`, `repo.dependency_proxy`, `repo.lfs` |
| `code_review` | 12 | `review.approval_rules`, `review.merge_trains`, `review.draft_pr` |
| `labels` | 6 | `labels.case_sensitivity`, `labels.scoped`, `labels.group_level` |
| `snippets` | 6 | `snippets.project_scope`, `snippets.visibility`, `snippets.multi_file` |
| `cicd` | 10 | `cicd.pipelines`, `cicd.runners`, `cicd.environments` |
| `security` | 5 | `security.secret_detection`, `security.sast`, `security.dast` |
| `project_management` | 4 | `pm.confidential_issues`, `pm.milestones` |
| `integrations` | 1 | `integrations.webhooks` |

### Platform YAML Schema

Each capability entry in a platform file follows this schema:

```yaml
# Supported, no behavioral differences
repo.lfs:
  supported: true
  notes: "Git LFS with configurable storage limits"

# Supported with behavioral constraints
review.multiple_assignees:
  supported: true
  notes: "Up to 10 assignees per PR"
  max_assignees: 10          # ← behavioral attribute

# Not supported — with workaround documented
repo.mirroring:
  supported: false
  notes: "No native mirroring support"
  workaround: "Use GitHub Actions or external tools for mirroring"
  migration_impact: "HIGH - Manual workflow change required"
```

### Known Gaps File

The `known_gaps.yaml` enriches the structural comparison with qualitative, expert-curated guidance that the YAML diff alone cannot express. Each gap record includes:

- `severity` (HIGH / MEDIUM / LOW)
- `title` and `description` (plain language)
- `impact` (business consequences, not just technical)
- `workarounds[]` with effort rating per option (LOW / MEDIUM / HIGH)
- `data_migration` notes (what happens to existing data)

This is the layer where SME knowledge lives and where the LLM draws its workaround guidance from. The LLM does not invent workarounds — it expands on what is already in this file.

### KB Coverage and Confidence Model

Not every capability can be verified with equal certainty. The KB roadmap introduces an explicit confidence tier per entry:

| Tier | Label | Criteria | Handling |
|---|---|---|---|
| 1 | `HIGH` | Official docs + tested in production | Full trust |
| 2 | `MEDIUM` | Official docs, not independently tested | Proceed with disclaimer |
| 3 | `LOW` | Community sources / indirect evidence | Flag for manual verification |
| 4 | `UNKNOWN` | Not in KB | Report as "Not Covered" — do not omit |

Entries not in the KB are surfaced explicitly in the report rather than silently ignored. This "known unknowns" transparency is a design requirement, not a limitation.

---

## 4. Implementation Methodology

### Guiding Principles

1. **Deterministic comparison first, LLM synthesis second.** The LLM's job is explanation, not discovery.
2. **No silent omissions.** A capability outside KB coverage appears in a "Not Covered" section, not dropped.
3. **Separation of facts from narrative.** YAML is the source of truth. Prompt templates are in `prompts/bedrock_prompts.yaml`, not hardcoded.
4. **Platform-agnostic design.** Adding a third platform means adding one YAML file and extending `known_gaps.yaml`. No code changes.
5. **Structured output alongside narrative.** Every report has a machine-readable JSON representation alongside the Markdown, enabling downstream tooling.

### Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Orchestrator | Python 3.12 | Single-file deployability, no framework lock-in |
| LLM | AWS Bedrock (Claude 3 Sonnet) | Enterprise-grade, no data leaves the AWS boundary, IAM-controlled access |
| KB Format | YAML | Human-readable, diff-friendly, PR-reviewable |
| CLI | `argparse` / `click` | No web server required for initial deployment |
| Output | Markdown + JSON | Markdown for stakeholders; JSON for CI/CD pipeline integration |
| Testing | `pytest` | Unit tests for comparison logic; integration tests for end-to-end |
| Dependencies | `boto3`, `PyYAML`, `rich`, `click` | Minimal surface area |

### Output Report Anatomy

A generated parity report contains five mandatory sections:

```
1. Executive Summary
   ├── Total capabilities analyzed
   ├── Count: Hard Blockers / Behavioral Differences / Seamless
   ├── Overall Risk Rating (LOW / MEDIUM / HIGH / CRITICAL)
   └── Top 3 Concerns

2. 🔴 Hard Blockers
   └── Per gap: title, impact, workaround options with effort, data migration path

3. 🟡 Behavioral Differences
   └── Per gap: source behavior vs. target behavior, concrete example, impact

4. 🟢 Seamless Migrations
   └── List of capabilities that migrate without change

5. Coverage Report (Confidence Transparency)
   ├── Fully Covered (HIGH confidence)
   ├── Partially Covered (MEDIUM confidence — verify recommended)
   └── Not Covered (UNKNOWN — manual verification required)
```

---

## 5. Implementation Phases

### Phase 1 — Core Engine (Current State)
**Duration:** Completed  
**Goal:** Prove the KB + deterministic comparison + LLM synthesis architecture works end to end.

| Deliverable | Status |
|---|---|
| `parity_agent.py` — full orchestrator with CLI | ✅ Complete |
| `capability_taxonomy.yaml` — 54-capability master catalog | ✅ Complete |
| `platforms/gitlab.yaml` + `platforms/github.yaml` | ✅ Complete |
| `known_gaps.yaml` — GitLab→GitHub gap library | ✅ Complete |
| `prompts/bedrock_prompts.yaml` — prompt templates | ✅ Complete |
| Sample output (GitLab→GitHub) | ✅ Complete |
| Architecture comparison document | ✅ Complete |

**What the current system can do:**  
Run `python parity_agent.py gitlab github` and receive a full parity report with hard blockers, behavioral differences, and workaround guidance.

---

### Phase 2 — KB Expansion and Confidence Scoring
**Duration:** 2–3 weeks  
**Goal:** Expand coverage, add confidence tiers, make gaps transparent.

| Task | Owner | Effort |
|---|---|---|
| Add `confidence` + `last_verified` + `source` fields to all KB entries | KB Team | Medium |
| Expand `known_gaps.yaml` with CI/CD pipeline gaps | DevOps SME | Medium |
| Add `security` category gaps (SAST/DAST/Secret Detection) | Security SME | Medium |
| Add `azure_devops.yaml` and `bitbucket.yaml` platform files | Platform Team | High |
| Update comparison engine to emit confidence in gap objects | Engineering | Low |
| Update report template to include "Coverage Report" section | Engineering | Low |

**Deliverables:**
- KB with confidence tiers on all 54 capabilities
- At least 2 additional platform files
- Updated report with explicit "Not Covered" section

---

### Phase 3 — Robustness, Caching, and CI Integration
**Duration:** 2–3 weeks  
**Goal:** Make the system production-ready for use within CI/CD pipelines and pre-migration checklists.

| Task | Owner | Effort |
|---|---|---|
| Add `--output-json` flag for structured JSON export | Engineering | Low |
| Add `--scope` filter (run parity check on a subset of categories) | Engineering | Low |
| Implement LLM response caching (hash of gap JSON → cached report) | Engineering | Medium |
| Add `pytest` suite for ComparisonEngine unit tests | Engineering | Medium |
| Add integration test with mocked Bedrock response | Engineering | Low |
| Create GitHub Actions workflow to run parity check on KB changes | DevOps | Medium |
| Write KB update runbook (how to add/update a capability entry) | KB Team | Low |

**Deliverables:**
- JSON output mode for pipeline integration
- Full test suite (unit + integration)
- CI workflow that runs parity check on every KB pull request
- KB maintenance runbook

---

### Phase 4 — API Introspection Fallback and LLM Knowledge Fallback
**Duration:** 3–4 weeks  
**Goal:** Cover gaps that the static KB cannot — using live API data and explicit LLM inference where necessary, both with clear confidence labeling.

| Task | Owner | Effort |
|---|---|---|
| Implement `KBValidator` to cross-check KB values against live API endpoints | Engineering | High |
| Add API introspection for schema/field discovery on both platforms | Engineering | High |
| Add LLM fallback path for capabilities with `UNKNOWN` confidence | Engineering | Medium |
| Mark all LLM-inferred findings as `LLM_INFERRED` with `LOW` confidence | Engineering | Low |
| Build feedback loop form — users submit discovered gaps post-migration | Product | Medium |
| Automated weekly KB validation job (compares KB vs. scraped docs) | DevOps | High |

**Deliverables:**
- Hybrid inference: KB → API Introspection → LLM Fallback (with confidence labels at each tier)
- Live API introspection module
- Automated KB drift detection
- User feedback portal for gap submission

---

### Phase 5 — Self-Service Web Interface (Optional)
**Duration:** 3–4 weeks  
**Goal:** Make the tool accessible to non-technical stakeholders without CLI access.

| Task | Effort |
|---|---|
| FastAPI backend wrapping `ParityCheckAgent.analyze()` | Medium |
| Simple React/Next.js front end with platform dropdowns and report viewer | High |
| PDF export of parity report | Low |
| User authentication (SSO/OAuth) | Medium |
| Report history and comparison ("how did risks change since last KB update?") | High |

---

## 6. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| KB becomes stale as platforms evolve | High | High | Phase 4 automated validation; `last_verified` field on every entry |
| LLM expands on a gap with incorrect detail | Medium | High | LLM receives structured facts; system prompt forbids inventing capabilities |
| Bedrock API outage blocks report generation | Low | Medium | LLM call is the last step; structured JSON output is independent |
| New platform feature not in taxonomy | Medium | Medium | "Not Covered" section surfaces gaps explicitly; KB update runbook |
| Over-reliance on report without manual validation | Medium | High | Report includes explicit "Verify Recommended" items; coverage section is mandatory |

---

## 7. Success Metrics

| Metric | Target |
|---|---|
| KB coverage — capabilities with HIGH confidence | ≥ 90% by Phase 3 |
| False negative rate (blocker missed by system, found post-migration) | 0 for HIGH/CRITICAL severity items |
| Report generation time | < 30 seconds end-to-end |
| LLM token cost per report | < $0.10 per run |
| KB update cycle time (platform change detected → KB updated) | ≤ 5 business days |

---

## 8. Implementation Prompt

The following prompt is designed to be given directly to an AI coding assistant to drive the full Phase 2–3 implementation from the current Phase 1 codebase.

---

```
=======================================================================
IMPLEMENTATION PROMPT — SCM PARITY CHECK AGENT (PHASE 2 & 3)
=======================================================================

You are implementing Phase 2 and Phase 3 of the SCM Parity Check Agent.
The Phase 1 codebase is already complete. Read every file before writing
any code.

READ THIS ENTIRE PROMPT BEFORE WRITING ANY CODE.

=======================================================================
CONTEXT: WHAT ALREADY EXISTS
=======================================================================

The existing system is in parity_agent.py and has these working classes:
  - CapabilityLoader     loads YAML KB files
  - ComparisonEngine     deterministic diff producing CapabilityGap list
  - BedrockClient        sends gap JSON to AWS Bedrock Claude, returns Markdown
  - ParityCheckAgent     orchestrator combining the three above
  - main()               argparse CLI entry point

The KB lives in:
  capability_kb/
    capability_taxonomy.yaml    (54 capabilities across 8 categories)
    known_gaps.yaml             (gitlab_to_github gap records)
    platforms/
      gitlab.yaml
      github.yaml

Prompts live in:
  prompts/bedrock_prompts.yaml

Do NOT rewrite the existing classes. Extend them.

=======================================================================
PHASE 2: KB EXPANSION AND CONFIDENCE SCORING
=======================================================================

TASK 2.1 — ADD CONFIDENCE FIELDS TO ALL KB ENTRIES

In capability_kb/platforms/gitlab.yaml and github.yaml, add these
three fields to every capability entry:

  confidence: HIGH | MEDIUM | LOW
  last_verified: "YYYY-MM-DD"
  verification_source: "string describing where this was verified"

Rules:
  - Use HIGH when the value comes from official platform documentation
    and has been tested or is unambiguous.
  - Use MEDIUM when from official docs but untested or
    potentially version-specific.
  - Use LOW when sourced from community posts, indirect evidence,
    or over 12 months old.
  - ALL existing entries in gitlab.yaml and github.yaml must be updated.
    Do not leave any entry without confidence fields.

TASK 2.2 — UPDATE CapabilityGap DATACLASS

In parity_agent.py, add these fields to the CapabilityGap dataclass:

  confidence: str = "HIGH"    # Inherits from lower of source/target entry
  last_verified: str = ""
  verification_source: str = ""

In ComparisonEngine.compare(), when creating a CapabilityGap, set its
confidence to the LOWER of the source and target entry's confidence.
Confidence ordering: HIGH > MEDIUM > LOW > UNKNOWN.

TASK 2.3 — ADD "NOT COVERED" SECTION TO REPORTS

In BedrockClient.generate_parity_report(), after the existing prompt
sections, add a mandatory sixth section to the prompt template:

  ### 6. 📋 Coverage Report

  For each capability in the gap analysis JSON where confidence is LOW
  or where the field is absent:
  - List capability ID and name
  - State last verified date
  - State verification source
  - Recommend manual verification before relying on this finding

  Also list any capability category from the taxonomy that has ZERO
  entries in both platform files (completely uncovered category).

TASK 2.4 — EXPAND known_gaps.yaml WITH CI/CD GAPS

Add a new section to known_gaps.yaml under gitlab_to_github.
Add gap records for at minimum these CI/CD capability IDs:

  cicd.pipelines         (GitLab .gitlab-ci.yml vs GitHub Actions .yml)
  cicd.runners           (GitLab Runners vs GitHub-hosted + self-hosted)
  cicd.environments      (GitLab Environments vs GitHub Environments)
  cicd.artifacts         (retention policies differ)

Each gap record must follow the exact schema already used in the file
for hard_blockers and behavioral_differences. Do not invent a new schema.

=======================================================================
PHASE 3: ROBUSTNESS, OUTPUT MODES, AND TESTING
=======================================================================

TASK 3.1 — JSON OUTPUT MODE

In main() and ParityCheckAgent.analyze(), add support for structured
JSON output.

Add CLI argument:
  --output-format  choices: ["markdown", "json", "both"]  default: "markdown"

When json or both is selected, serialize ParityReport to a JSON file.
The JSON must include every field of ParityReport including the
hard_blockers, behavioral_differences, partial_support, and seamless
lists — each CapabilityGap serialized as a dict.

Use a new method on ParityReport:
  def to_dict(self) -> dict

Do not use a third-party serialization library. Use Python dataclasses
and manual dict construction.

TASK 3.2 — SCOPE FILTER

Add CLI argument:
  --scope  nargs="+"  choices matching all category names in the taxonomy
           e.g. --scope repository code_review

When provided, ComparisonEngine.compare() should only compare capabilities
whose ID starts with one of the provided category prefixes.
If not provided, compare all categories (current behavior, unchanged).

TASK 3.3 — LLM RESPONSE CACHING

Add a simple file-based cache to BedrockClient.

Cache key: SHA-256 hash of the serialized gap_analysis dict (sorted keys,
deterministic JSON).

Cache directory: .parity_cache/ in the working directory.
Cache file name: {hash}.md (for markdown) or {hash}.json (for JSON).
Cache TTL: 7 days. Entries older than 7 days are ignored and regenerated.

Add CLI argument:
  --no-cache    bypass cache for this run

Log a message at INFO level when a cache hit is used:
  "Cache hit for gap analysis {hash[:8]}... (saved Bedrock call)"

TASK 3.4 — TEST SUITE

Create a tests/ directory with the following files:

tests/__init__.py   (empty)

tests/test_comparison_engine.py
  - Test that a capability present in source but absent in target
    produces a CapabilityGap with gap_type == HARD_BLOCKER.
  - Test that a capability with different behavior values in source
    and target produces gap_type == BEHAVIORAL_DIFFERENCE.
  - Test that a capability present with identical behavior in both
    results in it appearing in the seamless list.
  - Test the --scope filter: only capabilities in the specified
    category prefix are returned.
  - All tests use in-memory YAML dicts — do NOT load actual files.

tests/test_kb_loader.py
  - Test that CapabilityLoader raises ValueError for unknown platform.
  - Test that all entries in gitlab.yaml and github.yaml have
    a "confidence" field after Phase 2 is complete.
  - Test that capability IDs in platform files match IDs in the taxonomy.

tests/test_output_format.py
  - Test that ParityReport.to_dict() produces a dict with the required
    top-level keys: source_platform, target_platform, hard_blockers,
    behavioral_differences, partial_support, seamless, overall_risk.
  - Test that JSON output mode writes a valid JSON file to the
    specified output path.

Use pytest. No mocking of Bedrock — test only the deterministic
Python layers. Bedrock integration is covered by manual smoke tests.

=======================================================================
TASK 3.5 — KB UPDATE RUNBOOK (create as kb-update-runbook.md)
=======================================================================

Create kb-update-runbook.md in the project root with the following
sections:

1. When to Update the KB
   - A platform releases a new feature
   - An existing feature's behavior changes
   - A migration reveals an undocumented gap
   - A last_verified date is more than 6 months old

2. How to Add a New Capability
   Step-by-step instructions for:
   a. Adding the capability ID to capability_taxonomy.yaml
   b. Adding the entry to each relevant platform YAML
   c. Adding a known_gaps.yaml entry if a gap exists
   d. Running the test suite to verify KB integrity

3. How to Update an Existing Entry
   - Updating the value
   - Updating confidence and last_verified
   - Adding or modifying workarounds

4. How to Add a New Platform
   - Create platforms/{platform_id}.yaml following the schema
   - Add gap records to known_gaps.yaml
   - Run tests

5. Review and Approval Process
   - All KB changes go through a pull request
   - Reviewer must be an SME for the affected platform
   - CI runs parity check on change to validate no regressions

=======================================================================
CODING STANDARDS
=======================================================================

- Python 3.12 type hints on all new functions and methods.
- No new external dependencies beyond what is in requirements.txt.
  If a new dependency is absolutely required, add it to requirements.txt
  and justify the addition in a comment.
- All new code follows the existing naming conventions in parity_agent.py.
- Do not reformat or reorganize existing code.
- All new CLI arguments must be documented in --help text.
- Log at DEBUG for internal operations, INFO for user-visible steps.
- Never print directly — use logging or rich console.

=======================================================================
DELIVERY ORDER
=======================================================================

Implement in this exact order. Do not skip ahead.

1. TASK 2.1 — confidence fields in YAML files
2. TASK 2.2 — CapabilityGap dataclass update
3. TASK 2.3 — Coverage Report section in prompt
4. TASK 2.4 — CI/CD gaps in known_gaps.yaml
5. TASK 3.1 — JSON output mode + to_dict()
6. TASK 3.2 — scope filter
7. TASK 3.3 — LLM response caching
8. TASK 3.4 — test suite
9. TASK 3.5 — KB update runbook

After each task, verify that python -m py_compile parity_agent.py
passes before moving to the next task.

After TASK 3.4, run pytest tests/ and confirm all tests pass
before marking Phase 3 complete.

=======================================================================
END OF IMPLEMENTATION PROMPT
=======================================================================
```

---

## 9. Appendix — Current vs. Target State Summary

| Dimension | Phase 1 (Current) | Phase 3 (Target) |
|---|---|---|
| Platforms supported | GitLab, GitHub | + Azure DevOps, Bitbucket |
| Capabilities covered | 54 (GitLab→GitHub) | 54+ with confidence tiers |
| Output formats | Markdown only | Markdown + JSON |
| Scope filtering | Full scan only | Per-category subset |
| LLM call cost | ~$0.03 per report | ~$0.03 (cached: $0.00) |
| Test coverage | 0% | >80% on comparison logic |
| CI/CD gap coverage | Minimal | Full |
| False negative transparency | None | Explicit "Not Covered" section |
| KB maintenance process | Ad hoc | Documented runbook + CI gate |
