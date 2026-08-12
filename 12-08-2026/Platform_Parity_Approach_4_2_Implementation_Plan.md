# Platform Parity 4.2 Implementation Plan

## Executive Summary

This document proposes the final architecture for the Platform Parity enhancement initiative.

The objective is to enrich deterministic SCM platform parity assessments with real-world repository usage data from Discovery Reports while preserving auditability, explainability, repeatability, and enterprise-grade governance.

The chosen architecture is:

**Approach 4.2 – Deterministic Evidence Engine + Deterministic Parity Engine + LangChain-Orchestrated Bedrock Reporting**

### Core Principle

Migration facts are always determined by deterministic logic.

LLMs and LangChain are used exclusively for:
- Narrative generation
- Report formatting
- Executive summaries
- Human-readable migration recommendations

LLMs must never determine:
- Platform support status
- Gap classifications
- Risk levels
- Workarounds
- Capability mappings
- Migration decisions

---

# Business Problem

Current parity reports answer:

- Does GitLab support Feature X?
- Does GitHub support Feature X?
- Is this a blocker?

Current reports do not answer:

- How many repositories actually use Feature X?
- How many teams are affected?
- Which blockers are most urgent?
- Which features are unused and therefore low priority?

Discovery CSV data provides these missing business signals.

Example:

Current Output:

- Service Desk → HARD_BLOCKER

Enhanced Output:

- Service Desk → HARD_BLOCKER
- 219 of 243 repositories impacted
- 90.1% usage
- HIGH urgency

This significantly improves migration planning quality.

---

# Target Architecture

```text
Discovery CSV
      ↓
Step 0 - Parse Discovery
      ↓
Evidence Extraction
      ↓
Usage Signals
      ↓
Step 1 - Init
      ↓
Step 2 - Load KB
      ↓
Step 3 - Deterministic Compare
      ↓
Migration Facts
      ↓
Step 4 - LangChain + Claude
      ↓
Narrative Report
      ↓
Step 5 - Export
```

---

# Architectural Responsibilities

## Deterministic Layer

Responsible for:

- Platform detection
- CSV parsing
- Capability discovery
- Evidence aggregation
- Capability parity
- Gap classification
- Risk calculation
- Usage analysis

Outputs authoritative migration facts.

## LangChain Layer

Responsible for:

- Prompt orchestration
- Structured report generation
- Executive summaries
- Human-readable explanations
- Markdown formatting

Outputs narrative only.

---

# Implementation Roadmap

## Phase 1 - Discovery Evidence Framework

### New File

```text
capability_kb/discovery_mapping.yaml
```

### Purpose

Move all CSV-to-capability mappings into configuration.

Benefits:

- No hardcoded mappings in Python
- Easy maintenance
- Easier onboarding of additional discovery formats
- Better auditability

### Example Structure

```yaml
review.draft_pr:
  columns:
    - mr_draft_count
  detection_rule: any_positive
  confidence: HIGH
  value_type: numeric
```

---

## Phase 2 - Discovery Parsing Engine

### New Script

```text
scripts/platform_parity_parse_discovery.py
```

### Inputs

```text
CSV_PATH
EXECUTION_ID
```

### Responsibilities

#### 1. CSV Validation

Validate:

- File exists
- File readable
- Headers present
- Records present

#### 2. Platform Detection

Deterministic score-based detection.

Evidence sources:

- URL fingerprints
- SSH fingerprints
- Platform-specific columns

Output:

```json
{
  "source_platform": "gitlab",
  "platform_confidence": "HIGH"
}
```

#### 3. Evidence Extraction

Convert raw observations into capability evidence.

Example:

```text
mr_draft_count > 0
```

becomes:

```text
review.draft_pr detected
```

#### 4. Usage Aggregation

Calculate:

- repo_count
- percentage
- urgency
- total_value
- examples

#### 5. Evidence Summary

Maintain audit trail:

```text
CSV Column
    ↓
Evidence Rule
    ↓
Capability
```

---

## Phase 3 - Enhanced Usage Signal Model

### Target Structure

```json
{
  "repo_count": 219,
  "percentage": 90.1,
  "urgency": "HIGH",
  "confidence": "HIGH",
  "total_value": 0,
  "examples": ["repo1", "repo2"],
  "evidence": {
    "columns": ["service_desk_enabled"],
    "detection_rule": "boolean_true",
    "value_type": "boolean"
  }
}
```

### Urgency Rules

```text
>50%   HIGH
>10%   MEDIUM
<=10%  LOW
```

---

## Phase 4 - Workflow Initialization Updates

### Modify

```text
platform_parity_init.py
```

### Change

Remove direct SOURCE_PLATFORM input.

Consume:

```text
{{steps.platform_parity_parse_discovery.source_platform}}
```

Target platform remains user-supplied.

---

## Phase 5 - Comparison Engine Enhancements

### Modify

```text
platform_parity_compare.py
```

### Current Responsibility

Determine:

- HARD_BLOCKER
- PARTIAL_SUPPORT
- BEHAVIORAL_DIFF
- SEAMLESS

### Enhancement

Attach usage detail to every comparison result.

Example:

```json
{
  "capability_id": "service_desk",
  "classification": "HARD_BLOCKER",
  "repo_count": 219,
  "repo_percentage": 90.1,
  "urgency": "HIGH",
  "confidence": "HIGH"
}
```

### Risk Enhancements

Current:

```text
Hard blocker exists
→ Critical
```

Enhanced:

```text
Hard blocker
+
90% adoption
→ Critical
```

---

## Phase 6 - LangChain Reporting Layer

### Modify

```text
platform_parity_generate_report.py
```

### LangChain Components

#### ChatBedrock

```python
from langchain_aws import ChatBedrock
```

#### PromptTemplate

Build structured prompts.

#### RunnableSequence

```text
Prompt
 ↓
Claude
 ↓
Output Parser
```

#### PydanticOutputParser

Ensure report structure consistency.

---

## LangChain Rules

LangChain must not:

- Reclassify gaps
- Infer workarounds
- Change risk ratings
- Invent capabilities

LangChain receives facts.

LangChain returns explanations.

---

## Report Sections

1. Executive Summary
2. Hard Blockers
3. Behavioral Differences
4. Seamless Migrations
5. Coverage Report

Additional emphasis:

- Repository impact
- Percentage adoption
- Urgency
- Migration recommendations

---

## Phase 7 - CLI Entry Point

### New File

```text
platform_parity_run.py
```

### Responsibilities

1. Accept CSV path
2. Execute detection
3. Display evidence
4. Ask target platform
5. Start workflow

Example:

```text
Detected Platform: GitLab
Confidence: HIGH
Repositories: 243

Enter Target Platform:
```

---

## Phase 8 - Workflow Definition

### Add Step 0

```text
platform_parity_parse_discovery
```

Updated Flow:

```text
Parse Discovery
 ↓
Init
 ↓
Load KB
 ↓
Compare
 ↓
Generate Report
 ↓
Export
```

---

## Phase 9 - Test Framework Enhancements

### Update

```text
test_bedrock_e2e.py
```

### Required Support

```text
--csv-path
--skip-bedrock
```

### Validation Areas

- Platform detection
- Capability detection
- Usage aggregation
- Evidence tracing
- Comparison enrichment
- Report generation

---

# Success Criteria

The implementation is considered complete when:

- Discovery CSV is parsed successfully.
- Source platform is detected deterministically.
- Capability usage statistics are generated.
- Evidence is fully traceable.
- Usage metadata is attached to parity findings.
- Existing deterministic parity logic remains unchanged.
- LangChain generates narrative-only reports.
- Reports include repository impact and urgency.
- CI mode works without Bedrock.
- Temporal workflow remains deterministic.

---

# Copilot Implementation Prompt

## Objective

Implement Approach 4.2 for the platform_parity module.

### Mandatory Design Principles

1. Deterministic systems own all migration facts.
2. LangChain is used for orchestration and narrative generation only.
3. Claude must never generate or modify migration facts.
4. Existing parity logic must remain authoritative.
5. Discovery evidence must be traceable from CSV column to final report.
6. Follow all script-writing rules defined in guide_to_write_scripts.md.

### Scope

Create a discovery-driven evidence layer that enriches parity results with repository usage metrics.

### Required Deliverables

Create:

- scripts/platform_parity_parse_discovery.py
- metadata/platform_parity_parse_discovery.txt
- capability_kb/discovery_mapping.yaml
- platform_parity_run.py

Modify:

- platform_parity_init.py
- platform_parity_compare.py
- platform_parity_generate_report.py
- platform_parity_workflow.json
- test_bedrock_e2e.py

### Parse Discovery Requirements

Inputs:

- CSV_PATH
- EXECUTION_ID

Outputs:

- source_platform
- platform_confidence
- platform_evidence
- total_repos
- usage_signals
- column_stats
- csv_columns
- evidence_summary

Implement:

- deterministic platform detection
- CSV validation
- evidence extraction
- capability aggregation
- confidence scoring
- urgency scoring

### Usage Signal Contract

Every usage signal must contain:

- repo_count
- percentage
- urgency
- confidence
- total_value
- examples
- evidence

### Comparison Enhancements

Attach usage metadata to all gap objects.

Maintain current classification logic unchanged.

### LangChain Requirements

Use:

- ChatBedrock
- PromptTemplate
- RunnableSequence
- PydanticOutputParser

Do not use:

- Agents
- Memory
- ReAct
- Tool Calling
- Autonomous Reasoning

### Reporting Rules

Supply deterministic parity facts to Claude.

Add explicit prompt instructions:

- Do not invent capabilities.
- Do not alter classifications.
- Do not modify risk.
- Do not introduce unsupported workarounds.
- Explain supplied facts only.

### Workflow Updates

Insert:

platform_parity_parse_discovery

before:

platform_parity_init

### Testing Requirements

Verify:

- platform detection
- evidence extraction
- usage aggregation
- compare enrichment
- report generation
- skip-bedrock operation

### Final Goal

Produce migration reports that answer:

- What gaps exist?
- How many repositories are affected?
- How urgent are the gaps?
- What evidence supports the conclusion?

while preserving deterministic parity decisions and using LangChain exclusively for narrative generation.
