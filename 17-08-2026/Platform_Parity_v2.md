# PACE SCM Migration — Platform Parity Module

## Complete Implementation Plan v2.0

### Local YAML KB + Live API Doc Sync + LangChain + Interactive CLI

**Version:** 2.0  
**Date:** 2026-08-12  
**Status:** Pre-Implementation Planning  
**Scope:** Platform Parity Module — Local YAML KB, Live API Doc Sync, LangChain-Powered Analysis, Interactive CLI

---

## 1. What This Plan Delivers

This plan extends the existing Phase 1 codebase with the following three additions:

| **Addition** | **Description** |
|---|---|
| **Interactive Input** | System asks user for source and target SCM at runtime. No hardcoded defaults. |
| **Live API Doc Sync** | Fetches official SCM API docs on every run. Detects changes via SHA-256. Updates local YAML KB automatically when confidence is HIGH. |
| **Old Report Cleanup** | Before writing a new report, deletes any existing report for the same source → target pair. One report per pair at all times. |

### What Stays Exactly The Same

- Local YAML files as KB storage
- **`capability_kb/`** folder structure
- Deterministic comparison engine
- 5-section report structure
- **`--skip-bedrock`** mode
- **`test_bedrock_e2e.py`** and **`run_parity_matrix.py`**
- All existing tests

---

## 2. Current State (Phase 1 — Already Built)

```text
platform_parity/
├── parity_agent.py                  ← Main orchestrator (WORKING)
├── test_bedrock_e2e.py              ← Single pair test runner (WORKING)
├── run_parity_matrix.py             ← Batch matrix runner (WORKING)
├── capability_kb/
│   ├── capability_taxonomy.yaml     ← 54 capabilities (WORKING)
│   ├── known_gaps.yaml              ← GitLab→GitHub gaps (WORKING)
│   └── platforms/
│       ├── gitlab.yaml              ← GitLab capabilities (WORKING)
│       ├── github.yaml              ← GitHub capabilities (WORKING)
│       ├── azure_devops.yaml        ← (WORKING)
│       └── bitbucket.yaml           ← (WORKING)
├── prompts/
│   └── bedrock_prompts.yaml         ← Prompt templates (WORKING)
└── test_output/                     ← Generated reports (WORKING)
```

### Existing Classes in `parity_agent.py`

```text
CapabilityLoader      ← loads YAML KB files
ComparisonEngine      ← deterministic gap classification
BedrockClient         ← sends gaps to Claude, returns Markdown
ParityCheckAgent      ← orchestrator combining all three
main()                ← argparse CLI entry point
```
Rule: Do NOT rewrite these classes. Extend them only.

---

## 3. Target State (After This Plan)

```text
platform_parity/
├── parity_agent.py                  ← Extended (NOT rewritten)
├── kb_doc_sync/
│   ├── __init__.py
│   ├── doc_fetcher.py               ← NEW: WebBaseLoader wrapper
│   ├── doc_analyzer.py              ← NEW: LangChain chain for doc analysis
│   ├── kb_updater.py                ← NEW: YAML KB writer
│   ├── doc_sources.yaml             ← NEW: URL map per platform+capability
│   └── doc_cache/
│       └── {platform}_{capability}.json  ← SHA-256 cache files
├── test_bedrock_e2e.py              ← Extended (NOT rewritten)
├── run_parity_matrix.py             ← Unchanged
├── capability_kb/
│   ├── capability_taxonomy.yaml     ← Unchanged structure, confidence fields added
│   ├── known_gaps.yaml              ← CI/CD gaps added
│   └── platforms/
│       ├── gitlab.yaml              ← confidence fields added
│       ├── github.yaml              ← confidence fields added
│       ├── azure_devops.yaml        ← confidence fields added
│       └── bitbucket.yaml           ← confidence fields added
├── prompts/
│   └── bedrock_prompts.yaml         ← Doc analysis prompts added
├── test_output/                     ← One report per pair (old deleted)
└── requirements.txt                 ← Updated with LangChain deps
```

---

## 4. Architecture

### 4.1 Full System Flow

```text
┌─────────────────────────────────────────────────────────────────┐
│                    RUNTIME FLOW                                  │
└─────────────────────────────────────────────────────────────────┘

User runs: python parity_agent.py

        │
        ▼
┌───────────────────┐
│  INTERACTIVE CLI  │
│                   │
│  "Source SCM?"    │
│  > gitlab         │
│                   │
│  "Target SCM?"    │
│  > github         │
└───────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  STEP 1 — KB FRESHNESS CHECK (NEW)                    │
│                                                       │
│  For each capability in scope:                        │
│    WebBaseLoader fetches official doc URL             │
│    hashlib.sha256 compares against cached hash        │
│    If changed:                                        │
│      LangChain chain analyzes what changed            │
│      PydanticOutputParser returns structured proposal │
│      If HIGH confidence → update YAML immediately     │
│      If MEDIUM/LOW → log proposal, skip auto-update   │
│    Update doc_cache/ with new hash                    │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  STEP 2 — LOAD KB (EXISTING — UNCHANGED)              │
│                                                       │
│  CapabilityLoader reads YAML files                    │
│  (Now reads updated YAML if Step 1 made changes)      │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  STEP 3 — DETERMINISTIC COMPARE (EXISTING — UNCHANGED)│
│                                                       │
│  ComparisonEngine classifies gaps                     │
│  HARD_BLOCKER / BEHAVIORAL_DIFF /                     │
│  PARTIAL_SUPPORT / SEAMLESS                           │
│  Pure Python. No LLM.                                 │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  STEP 4 — GENERATE REPORT (EXISTING — EXTENDED)       │
│                                                       │
│  LangChain chain:                                     │
│    PromptTemplate builds prompt                       │
│    ChatBedrock calls Claude                           │
│    PydanticOutputParser enforces 5 sections           │
│  OR deterministic template if --skip-bedrock          │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  STEP 5 — EXPORT (EXISTING — EXTENDED)                │
│                                                       │
│  Delete ALL existing reports for this pair            │
│  Write new .md report                                 │
│  Write new .json report                               │
└───────────────────────────────────────────────────────┘
```

## 4.2 LangChain Component Map

```text
┌─────────────────────────────────────────────────────────────────┐
│                   LANGCHAIN USAGE MAP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  kb_doc_sync/doc_fetcher.py                                     │
│    WebBaseLoader          ← fetch + clean HTML from doc URLs    │
│    RecursiveCharacterTextSplitter ← chunk long pages            │
│                                                                 │
│  kb_doc_sync/doc_analyzer.py                                    │
│    ChatBedrock            ← Claude 3 Sonnet via AWS Bedrock     │
│    PromptTemplate         ← structured analysis prompt          │
│    PydanticOutputParser   ← enforces KBUpdateProposal schema    │
│    RunnableSequence       ← prompt | llm | parser chain         │
│                                                                 │
│  parity_agent.py (BedrockClient — extended)                     │
│    ChatBedrock            ← Claude 3 Sonnet via AWS Bedrock     │
│    PromptTemplate         ← 5-section report prompt             │
│    PydanticOutputParser   ← enforces ParityReportSections       │
│    RunnableSequence       ← prompt | llm | parser chain         │
│                                                                 │
│  NOT used in:                                                   │
│    ComparisonEngine       ← pure Python, no LLM                 │
│    CapabilityLoader       ← pure pyyaml, no LLM                 │
│    Report export/cleanup  ← pure os/pathlib, no LLM            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 4.3 KB Write Safety Rules

```text
┌─────────────────────────────────────────────────────────────────┐
│                   KB WRITE SAFETY                               │
├──────────────────────────────┬──────────────┬───────────────────┤
│ File                         │ Auto-Write   │ Condition         │
├──────────────────────────────┼──────────────┼───────────────────┤
│ platforms/gitlab.yaml        │ YES          │ HIGH conf only    │
│ platforms/github.yaml        │ YES          │ HIGH conf only    │
│ platforms/azure_devops.yaml  │ YES          │ HIGH conf only    │
│ platforms/bitbucket.yaml     │ YES          │ HIGH conf only    │
│ doc_cache/*.json             │ YES          │ Always            │
│ kb_update_proposals.yaml     │ YES          │ MEDIUM/LOW conf   │
│ kb_update_log.yaml           │ YES          │ Always, audit     │
│ capability_taxonomy.yaml     │ NEVER        │ Human only        │
│ known_gaps.yaml              │ NEVER        │ Human only        │
└──────────────────────────────┴──────────────┴───────────────────┘

Claude never writes to any file directly.
Python writes files based on Claude structured output
AFTER confidence threshold check.
```

---

## 5. New Dependencies

Add to **`requirements.txt`**:

```text
# Existing (already present)
pyyaml>=6.0
boto3>=1.34

# New — LangChain stack
langchain>=0.2
langchain-aws>=0.1
langchain-community>=0.2
langchain-core>=0.2
pydantic>=2.0

# New — doc fetching support
requests>=2.31
beautifulsoup4>=4.12        # used internally by WebBaseLoader
```
Nothing else. No database. No vector store. No FAISS. No Chroma.

---

## 6. New Files To Create

### 6.1 `kb_doc_sync/doc_sources.yaml`

This file maps every platform + capability to the exact official documentation URL that should be fetched for that capability.

```yaml
# kb_doc_sync/doc_sources.yaml
# Maps platform + capability_id → official doc URL
# This file is human-maintained.
# Never auto-written by the system.

gitlab:
  repo.lfs: "https://docs.gitlab.com/ee/topics/git/lfs/"
  repo.mirroring: "https://docs.gitlab.com/ee/user/project/repository/mirror/"
  repo.dependency_proxy: "https://docs.gitlab.com/ee/user/packages/dependency_proxy/"
  review.approval_rules: "https://docs.gitlab.com/ee/user/project/merge_requests/approvals/"
  review.merge_trains: "https://docs.gitlab.com/ee/ci/pipelines/merge_trains.html"
  review.draft_pr: "https://docs.gitlab.com/ee/user/project/merge_requests/drafts.html"
  review.multiple_assignees: "https://docs.gitlab.com/ee/user/project/merge_requests/"
  cicd.pipelines: "https://docs.gitlab.com/ee/ci/pipelines/"
  cicd.runners: "https://docs.gitlab.com/ee/ci/runners/"
  cicd.environments: "https://docs.gitlab.com/ee/ci/environments/"
  cicd.artifacts: "https://docs.gitlab.com/ee/ci/jobs/job_artifacts.html"
  security.secret_detection: "https://docs.gitlab.com/ee/user/application_security/secret_detection/"
  security.sast: "https://docs.gitlab.com/ee/user/application_security/sast/"
  # ... all 54 capabilities mapped

github:
  repo.lfs: "https://docs.github.com/en/repositories/working-with-files/managing-large-files"
  repo.mirroring: "https://docs.github.com/en/repositories/creating-and-managing-repositories/duplicating-a-repository"
  review.approval_rules: "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/required-reviews"
  review.draft_pr: "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests"
  cicd.pipelines: "https://docs.github.com/en/actions/writing-workflows"
  cicd.runners: "https://docs.github.com/en/actions/using-github-hosted-runners"
  cicd.environments: "https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment"
  cicd.artifacts: "https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/storing-and-sharing-data-from-a-workflow"
  security.secret_detection: "https://docs.github.com/en/code-security/secret-scanning"
  security.sast: "https://docs.github.com/en/code-security/code-scanning"
  # ... all 54 capabilities mapped

azure_devops:
  cicd.pipelines: "https://learn.microsoft.com/en-us/azure/devops/pipelines/"
  cicd.runners: "https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents"
  review.approval_rules: "https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies"
  # ... all capabilities mapped

bitbucket:
  cicd.pipelines: "https://support.atlassian.com/bitbucket-cloud/docs/bitbucket-pipelines/"
  review.approval_rules: "https://support.atlassian.com/bitbucket-cloud/docs/suggest-or-require-checks-before-a-merge/"
  # ... all capabilities mapped
```

### 6.2 `kb_doc_sync/__init__.py`

```python
# Empty — marks kb_doc_sync as a Python package
```

### 6.3 `kb_doc_sync/doc_fetcher.py`

**Purpose:** Fetch and clean official API documentation pages using LangChain `WebBaseLoader`. Returns clean text chunks ready for analysis.

**Key design decisions:**

- Uses **`WebBaseLoader`** for automatic HTML cleaning
- Uses **`RecursiveCharacterTextSplitter`** for chunking long pages
- Returns both full text and chunks
- Computes SHA-256 of full text for change detection
- Handles fetch failures gracefully — returns cached version on failure
- Does NOT call any LLM

```python
"""
doc_fetcher.py
Fetches and cleans official SCM API documentation pages.
Uses LangChain WebBaseLoader for HTML extraction.
No LLM involved in this module.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "doc_cache"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200


class DocFetchResult:
    """Result of a doc fetch operation."""

    def __init__(
        self,
        url: str,
        platform: str,
        capability_id: str,
        content: str,
        chunks: list[str],
        sha256: str,
        fetched_at: str,
        from_cache: bool = False,
    ) -> None:
        self.url = url
        self.platform = platform
        self.capability_id = capability_id
        self.content = content
        self.chunks = chunks
        self.sha256 = sha256
        self.fetched_at = fetched_at
        self.from_cache = from_cache


class DocFetcher:
    """
    Fetches official SCM API documentation pages using
    LangChain WebBaseLoader. Computes SHA-256 for change
    detection. Caches results locally.
    """

    def __init__(self) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

    def fetch(
        self,
        url: str,
        platform: str,
        capability_id: str,
    ) -> DocFetchResult:
        """
        Fetch a documentation page.
        Returns DocFetchResult with content, chunks, and SHA-256.
        Falls back to cached version on network failure.
        """
        # (implementation detail — see Task section)
        ...

    def get_cached(
        self,
        platform: str,
        capability_id: str,
    ) -> Optional[DocFetchResult]:
        """
        Return cached result for this platform+capability if it exists.
        Returns None if no cache entry exists.
        """
        ...

    def _cache_key(self, platform: str, capability_id: str) -> str:
        """Returns cache file path for platform+capability pair."""
        safe_cap = capability_id.replace(".", "_")
        return str(CACHE_DIR / f"{platform}_{safe_cap}.json")

    def _compute_sha256(self, content: str) -> str:
        """Compute SHA-256 hash of content string."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _write_cache(self, result: DocFetchResult) -> None:
        """Write fetch result to local cache file."""
        ...

    def _read_cache(self, cache_path: str) -> Optional[dict]:
        """Read and return cache file content. Returns None if missing."""
        ...
```

### 6.4 `kb_doc_sync/doc_analyzer.py`

**Purpose:** Analyze what changed between old and new doc content. Use LangChain chain to produce a structured KB update proposal. This is where LangChain does its core work.

**Key design decisions:**

- Uses **`ChatBedrock`** as the LLM
- Uses **`PromptTemplate`** for the analysis prompt
- Uses **`PydanticOutputParser`** to enforce structured output
- Uses **`RunnableSequence`** to chain them
- Returns **`KBUpdateProposal`** Pydantic model
- Does NOT write to YAML — that is **`kb_updater.py`**'s job

```python
"""
doc_analyzer.py
Analyzes API doc changes using LangChain + Claude.
Produces structured KB update proposals.
Claude explains changes. Python decides whether to apply them.
"""

import logging
from typing import Optional

from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KBUpdateProposal(BaseModel):
    """
    Structured output from Claude doc analysis.
    Enforced by PydanticOutputParser — Claude must return
    all fields or the parser raises and retries.
    """

    capability_id: str = Field(
        description="The capability ID being analyzed e.g. review.draft_pr"
    )

    platform: str = Field(
        description="The platform being analyzed e.g. github"
    )

    doc_changed: bool = Field(
        description="True if the doc content meaningfully changed"
    )

    supported_changed: bool = Field(
        description="True if the supported field should change"
    )

    new_supported: Optional[bool] = Field(
        default=None,
        description="New value for supported field if it changed"
    )

    notes_changed: bool = Field(
        description="True if the notes field should change"
    )

    new_notes: Optional[str] = Field(
        default=None,
        description="New notes value if changed"
    )

    workaround_changed: bool = Field(
        description="True if the workaround field should change"
    )

    new_workaround: Optional[str] = Field(
        default=None,
        description="New workaround value if changed"
    )

    behavioral_attrs_changed: bool = Field(
        description="True if any behavioral_attrs should change"
    )

    new_behavioral_attrs: Optional[dict] = Field(
        default=None,
        description="Updated behavioral attributes if changed"
    )

    confidence: str = Field(
        description="HIGH, MEDIUM, or LOW confidence in this proposal"
    )

    reasoning: str = Field(
        description="Two sentence explanation of what changed and why"
    )

    should_auto_update: bool = Field(
        description="True only when confidence is HIGH and a field changed"
    )


class DocAnalyzer:
    """
    LangChain chain that analyzes API doc changes and
    produces structured KB update proposals.
    """

    def __init__(self, aws_region: str, model_id: str) -> None:
        self._parser = PydanticOutputParser(
            pydantic_object=KBUpdateProposal
        )

        self._llm = ChatBedrock(
            model_id=model_id,
            region_name=aws_region,
            model_kwargs={
                "max_tokens": 1024,
                "temperature": 0,
            },
        )

        self._prompt = PromptTemplate(
            template=self._build_template(),
            input_variables=[
                "capability_id",
                "platform",
                "current_kb_entry",
                "old_doc_content",
                "new_doc_content",
            ],
            partial_variables={
                "format_instructions": self._parser.get_format_instructions()
            },
        )

        self._chain: RunnableSequence = (
            self._prompt | self._llm | self._parser
        )

    def analyze(
        self,
        capability_id: str,
        platform: str,
        current_kb_entry: dict,
        old_doc_content: str,
        new_doc_content: str,
    ) -> KBUpdateProposal:
        """
        Run the LangChain chain to analyze doc changes.
        Returns KBUpdateProposal with structured findings.
        """

        return self._chain.invoke({
            "capability_id": capability_id,
            "platform": platform,
            "current_kb_entry": str(current_kb_entry),
            "old_doc_content": old_doc_content[:3000],
            "new_doc_content": new_doc_content[:3000],
        })

    def _build_template(self) -> str:
        return """
You are a technical knowledge base analyst for SCM platform migrations.

You will be given:
- A capability ID and platform
- The current KB entry for this capability
- The previous API documentation content
- The newly fetched API documentation content

Your job is to determine what, if anything, has changed and whether
the KB entry needs to be updated.

STRICT RULES:
- Only report changes that are clearly supported by the new doc content.
- Do not invent changes. Do not speculate.
- If you are unsure, set confidence to LOW.
- HIGH confidence means you are certain the doc clearly states the change.
- MEDIUM means the doc suggests the change but it is not explicit.
- LOW means you suspect a change but cannot confirm from the doc text.

Capability ID: {capability_id}
Platform: {platform}

Current KB entry:
{current_kb_entry}

Previous documentation content:
{old_doc_content}

New documentation content:
{new_doc_content}

{format_instructions}
"""
```

### 6.5 `kb_doc_sync/kb_updater.py`

**Purpose:** Orchestrates the full KB freshness check. Loads **`doc_sources.yaml`**, iterates capabilities, calls **`DocFetcher`** and **`DocAnalyzer`**, writes updates to YAML files, and logs all activity.

**Key design decisions:**

- This is the only module that writes to YAML files
- Writes only on HIGH confidence proposals
- Logs **ALL** proposals (HIGH, MEDIUM, LOW) to **`kb_update_log.yaml`**
- Writes MEDIUM/LOW proposals to **`kb_update_proposals.yaml`** for human review
- Never writes to **`capability_taxonomy.yaml`** or **`known_gaps.yaml`**
- Skips capabilities where the doc URL returns a network error (uses cache)

```python
"""
kb_updater.py
Orchestrates KB freshness check.
The ONLY module that writes to YAML KB files.
Writes only on HIGH confidence proposals.
All activity logged to kb_update_log.yaml.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from .doc_fetcher import DocFetcher
from .doc_analyzer import DocAnalyzer, KBUpdateProposal

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent.parent / "capability_kb"
PLATFORMS_DIR = KB_DIR / "platforms"
UPDATE_LOG_PATH = KB_DIR / "kb_update_log.yaml"
PROPOSALS_PATH = KB_DIR / "kb_update_proposals.yaml"
DOC_SOURCES_PATH = Path(__file__).parent / "doc_sources.yaml"


class KBUpdateResult:
    """Summary of a KB freshness check run."""

    def __init__(self) -> None:
        self.capabilities_checked: int = 0
        self.docs_changed: int = 0
        self.auto_updates_applied: int = 0
        self.proposals_staged: int = 0
        self.errors: list[str] = []
        self.update_details: list[dict] = []


class KBUpdater:
    """
    Orchestrates the full KB freshness check for a given
    source and target platform pair.
    """

    def __init__(
        self,
        aws_region: str,
        model_id: str,
        skip_bedrock: bool = False,
    ) -> None:
        self._fetcher = DocFetcher()
        self._analyzer = DocAnalyzer(aws_region, model_id) \
            if not skip_bedrock else None
        self._skip_bedrock = skip_bedrock
        self._doc_sources = self._load_doc_sources()

    def run(
        self,
        source_platform: str,
        target_platform: str,
        scope_filter: Optional[list[str]] = None,
    ) -> KBUpdateResult:
        """
        Run KB freshness check for source and target platforms.
        Returns KBUpdateResult with summary of what changed.
        """
        result = KBUpdateResult()
        platforms = [source_platform, target_platform]

        for platform in platforms:
            if platform not in self._doc_sources:
                logger.warning(
                    "No doc sources configured for platform: %s", platform
                )
                continue

            platform_sources = self._doc_sources[platform]
            platform_yaml_path = PLATFORMS_DIR / f"{platform}.yaml"
            platform_kb = self._load_platform_yaml(platform_yaml_path)

            for capability_id, doc_url in platform_sources.items():
                if scope_filter and not any(
                    capability_id.startswith(s) for s in scope_filter
                ):
                    continue

                result.capabilities_checked += 1
                self._check_capability(
                    platform=platform,
                    capability_id=capability_id,
                    doc_url=doc_url,
                    platform_kb=platform_kb,
                    platform_yaml_path=platform_yaml_path,
                    result=result,
                )

        return result

    def _check_capability(
        self,
        platform: str,
        capability_id: str,
        doc_url: str,
        platform_kb: dict,
        platform_yaml_path: Path,
        result: KBUpdateResult,
    ) -> None:
        """Check one capability for one platform."""
        # (full implementation in Task section)
        ...

    def _apply_update(
        self,
        platform_yaml_path: Path,
        capability_id: str,
        proposal: KBUpdateProposal,
    ) -> None:
        """Apply HIGH confidence proposal to platform YAML."""
        ...

    def _stage_proposal(self, proposal: KBUpdateProposal) -> None:
        """Write MEDIUM/LOW proposal to kb_update_proposals.yaml."""
        ...

    def _log_activity(
        self,
        platform: str,
        capability_id: str,
        action: str,
        proposal: Optional[KBUpdateProposal],
        error: Optional[str] = None,
    ) -> None:
        """Append entry to kb_update_log.yaml. Never modifies existing entries."""
        ...

    def _load_doc_sources(self) -> dict:
        """Load doc_sources.yaml."""
        with open(DOC_SOURCES_PATH) as f:
            return yaml.safe_load(f)

    def _load_platform_yaml(self, path: Path) -> dict:
        """Load a platform capability YAML file."""
        with open(path) as f:
            return yaml.safe_load(f) or {}
```

---

## 7. Modifications To Existing Files

### 7.1 `parity_agent.py` — What Changes

**Rule: Do NOT rewrite existing classes. Add to them.**

#### Change 1 — Add confidence fields to `CapabilityGap` dataclass

```python
# EXISTING dataclass — add these three fields
@dataclass
class CapabilityGap:
    capability_id: str
    gap_type: str
    # ... existing fields ...

    # ADD THESE:
    confidence: str = "HIGH"
    last_verified: str = ""
    verification_source: str = ""
```

#### Change 2 — Update `ComparisonEngine.compare()` to set confidence

```python
# When creating a CapabilityGap, set confidence to LOWER of
# source and target entry confidence.
# Confidence ordering: HIGH > MEDIUM > LOW > UNKNOWN

CONFIDENCE_ORDER = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "UNKNOWN": 0,
}


def _lower_confidence(self, c1: str, c2: str) -> str:
    """Return the lower of two confidence values."""
    if CONFIDENCE_ORDER.get(c1, 0) <= CONFIDENCE_ORDER.get(c2, 0):
        return c1
    return c2
```

#### Change 3 — Migrate `BedrockClient` from raw `boto3` to LangChain

```python
# BEFORE (raw boto3):
import boto3

response = self._client.invoke_model(
    modelId=self._model_id,
    body=json.dumps({"prompt": prompt, ...})
)

# AFTER (LangChain):
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence


class ParityReportSections(BaseModel):
    executive_summary: str
    hard_blockers_section: str
    behavioral_differences_section: str
    seamless_section: str
    coverage_section: str


# Chain:
chain = prompt_template | chat_bedrock | pydantic_parser

result: ParityReportSections = chain.invoke({...})
```

#### Change 4 — Add Coverage Report section to prompt

In **`prompts/bedrock_prompts.yaml`**, add **Section 6 (Coverage Report)** instruction to the existing prompt template.

The LLM must:

- List all **LOW confidence** capabilities.
- List any **uncovered categories**.
- Include coverage limitations in the final report.

#### Change 5 — Migrate `main()` to interactive input

```python
# BEFORE:
parser.add_argument("--source-platform", required=True)
parser.add_argument("--target-platform", required=True)

# AFTER:
# --source-platform and --target-platform remain as optional CLI args
# If NOT provided, prompt the user interactively

def _get_platform_input(
    prompt_text: str,
    valid_platforms: list[str],
) -> str:
    """Prompt user for platform input. Validate against known platforms."""
    while True:
        value = input(prompt_text).strip().lower()

        if value in valid_platforms:
            return value

        print(
            f"Invalid platform. Choose from: {', '.join(valid_platforms)}"
        )
```

#### Change 6 — Wire KB freshness check into `ParityCheckAgent.analyze()`

```python
def analyze(
    self,
    source_platform: str,
    target_platform: str,
    scope_filter: Optional[list[str]] = None,
) -> ParityReport:
    # NEW: Run KB freshness check first
    if not self._skip_bedrock:
        updater = KBUpdater(
            aws_region=self._aws_region,
            model_id=self._model_id,
        )

        update_result = updater.run(
            source_platform,
            target_platform,
        )

        # Log summary to console

    # EXISTING: Load KB, compare, generate report
    ...
```

#### Change 7 — Add old report deletion to export

```python
def _delete_old_reports(
    self,
    output_dir: Path,
    source_platform: str,
    target_platform: str,
) -> None:
    """
    Delete all existing reports for this source→target pair.
    Pattern: {source}_to_{target}_*.md and {source}_to_{target}_*.json
    """
    pair_prefix = f"{source_platform}_to_{target_platform}_"

    for f in output_dir.glob(f"{pair_prefix}*.md"):
        f.unlink()
        logger.info("Deleted old report: %s", f.name)

    for f in output_dir.glob(f"{pair_prefix}*.json"):
        f.unlink()
        logger.info("Deleted old report: %s", f.name)
```

### 7.2 `prompts/bedrock_prompts.yaml` — What Changes

Add two new prompt templates:

```yaml
# EXISTING prompts unchanged

# NEW: Doc analysis prompt (used by doc_analyzer.py)
doc_analysis_prompt: |
  ... (same as template defined in doc_analyzer.py)

# NEW: Coverage section instruction added to parity_report_prompt
coverage_section_instruction: |
  ### Section 5 — Coverage Report

  List all capabilities where confidence is LOW or UNKNOWN.

  List any capability category with zero entries in both platforms.

  For each:
  - State capability ID
  - State last verified date
  - State verification source
  - Recommend manual verification
```

### 7.3 `capability_kb/platforms/*.yaml` — What Changes

Add three fields to every capability entry:

```yaml
# BEFORE:
repo.lfs:
  supported: true
  notes: "Git LFS with configurable storage limits"

# AFTER:
repo.lfs:
  supported: true
  notes: "Git LFS with configurable storage limits"
  confidence: HIGH
  last_verified: "2026-08-12"
  verification_source: "https://docs.gitlab.com/ee/topics/git/lfs/"
```

**All 54 capabilities across all 4 platform files must be updated.**

### 7.4 `known_gaps.yaml` — What Changes

Add CI/CD gap records for:

- **`cicd.pipelines`** — **`.gitlab-ci.yml`** vs GitHub Actions
- **`cicd.runners`** — GitLab Runners vs GitHub-hosted runners
- **`cicd.environments`** — environment protection rules differ
- **`cicd.artifacts`** — retention policy differences

Each new record follows the exact existing schema. No schema changes.

---

## 8. Implementation Tasks (Ordered)

### TASK 1 — Update `requirements.txt`

**File:** **`requirements.txt`**  
**Type:** New/Modified  
**Depends on:** Nothing

Add LangChain dependencies. Verify existing dependencies are present.

**Acceptance criteria:**

- **`pip install -r requirements.txt`** completes without error
- **`python -c "from langchain_aws import ChatBedrock"`** succeeds
- **`python -c "from langchain_community.document_loaders import WebBaseLoader"`** succeeds
- **`python -c "from langchain_core.output_parsers import PydanticOutputParser"`** succeeds

---

### TASK 2 — Add Confidence Fields to Platform YAML Files

**Files:**

- **`capability_kb/platforms/gitlab.yaml`**
- **`capability_kb/platforms/github.yaml`**
- **`capability_kb/platforms/azure_devops.yaml`**
- **`capability_kb/platforms/bitbucket.yaml`**

**Type:** Modified  
**Depends on:** Nothing

Add **`confidence`**, **`last_verified`**, and **`verification_source`** to every capability entry in all four platform YAML files.

**Rules:**

- **`HIGH`** — from official platform docs, unambiguous
- **`MEDIUM`** — from official docs, possibly version-specific
- **`LOW`** — community sources or older than 12 months
- Every entry must have all three fields. No exceptions.

**Acceptance criteria:**

- **`python -c "import yaml; d=yaml.safe_load(open('capability_kb/platforms/gitlab.yaml')); assert all('confidence' in v for v in d.values())"`** passes
- Same check passes for all four platform files
- **`python -m py_compile parity_agent.py`** passes

---

### TASK 3 — Add CI/CD Gaps to `known_gaps.yaml`

**File:** **`capability_kb/known_gaps.yaml`**  
**Type:** Modified  
**Depends on:** Nothing

Add gap records for:

- **`cicd.pipelines`**
- **`cicd.runners`**
- **`cicd.environments`**
- **`cicd.artifacts`**

under **`gitlab_to_github`**.

**Schema to follow** (exact same as existing records):

```yaml
gitlab_to_github:
  behavioral_differences:
    - capability_id: cicd.pipelines
      severity: HIGH
      title: "Pipeline syntax requires full rewrite"
      description: |
        GitLab CI uses .gitlab-ci.yml with GitLab-specific syntax.
        GitHub Actions uses .github/workflows/*.yml with different
        trigger syntax, job structure, and runner configuration.
      impact: |
        Every pipeline file must be manually converted.
        No automated migration tool exists for full fidelity.
      workarounds:
        - option: "Manual rewrite using GitHub Actions equivalents"
          effort: HIGH
        - option: "Use GitHub Actions Importer (partial coverage)"
          effort: MEDIUM
      data_migration: "Pipeline files are not migrated. Must be rewritten."
```

**Acceptance criteria:**

- **`yaml.safe_load`** on the file succeeds
- All 4 new CI/CD gaps are present under **`gitlab_to_github`**
- Each gap has:
  - **`capability_id`**
  - **`severity`**
  - **`title`**
  - **`description`**
  - **`impact`**
  - **`workarounds`**
  - **`data_migration`**

---

### TASK 4 — Update `CapabilityGap` Dataclass

**File:** **`parity_agent.py`**  
**Type:** Modified — extend only  
**Depends on:** Task 2

Add **`confidence`**, **`last_verified`**, and **`verification_source`** fields to the existing **`CapabilityGap`** dataclass.

Add **`_lower_confidence()`** helper to **`ComparisonEngine`**.

Update **`ComparisonEngine.compare()`** to set confidence on each gap to the lower of source and target entry confidence.

**Acceptance criteria:**

- **`python -m py_compile parity_agent.py`** passes
- Existing tests still pass: **`pytest tests/`**
- A gap where source is HIGH and target is MEDIUM gets confidence MEDIUM

---

### TASK 5 — Create `kb_doc_sync/__init__.py`

**File:** **`kb_doc_sync/__init__.py`**  
**Type:** New  
**Depends on:** Nothing

Empty file. Marks **`kb_doc_sync`** as a Python package.

**Acceptance criteria:**

- **`python -c "import kb_doc_sync"`** succeeds from **`platform_parity/`** directory

---

### TASK 6 — Create `kb_doc_sync/doc_sources.yaml`

**File:** **`kb_doc_sync/doc_sources.yaml`**  
**Type:** New  
**Depends on:** Nothing

Create the URL map for all 54 capabilities across all 4 platforms.

**Rules:**

- Every capability in **`capability_taxonomy.yaml`** must have a URL for every platform that supports it
- URLs must be the specific page for that capability, not the docs homepage
- Human-maintained — never auto-written

**Acceptance criteria:**

- **`yaml.safe_load`** succeeds
- **`gitlab`** and **`github`** keys present at minimum
- At least 10 capabilities mapped per platform
- All URLs are real, reachable official doc pages

---

### TASK 7 — Create `kb_doc_sync/doc_fetcher.py`

**File:** **`kb_doc_sync/doc_fetcher.py`**  
**Type:** New  
**Depends on:** Tasks 1, 5

Implement **`DocFetcher`** class with:

- **`fetch(url, platform, capability_id) → DocFetchResult`**
- **`get_cached(platform, capability_id) → Optional[DocFetchResult]`**
- SHA-256 computation
- Local JSON cache in **`kb_doc_sync/doc_cache/`**
- Graceful fallback to cache on network failure
- No LLM calls

**Full implementation:**

```python
"""
doc_fetcher.py
Fetches and cleans official SCM API documentation pages.
Uses LangChain WebBaseLoader for HTML extraction.
No LLM involved — purely fetches and caches content.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "doc_cache"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200


class DocFetchResult:
    def __init__(
        self,
        url: str,
        platform: str,
        capability_id: str,
        content: str,
        chunks: list[str],
        sha256: str,
        fetched_at: str,
        from_cache: bool = False,
    ) -> None:
        self.url = url
        self.platform = platform
        self.capability_id = capability_id
        self.content = content
        self.chunks = chunks
        self.sha256 = sha256
        self.fetched_at = fetched_at
        self.from_cache = from_cache

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "platform": self.platform,
            "capability_id": self.capability_id,
            "content": self.content,
            "chunks": self.chunks,
            "sha256": self.sha256,
            "fetched_at": self.fetched_at,
            "from_cache": self.from_cache,
        }


class DocFetcher:
    def __init__(self) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

    def fetch(
        self,
        url: str,
        platform: str,
        capability_id: str,
    ) -> DocFetchResult:
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            content = "\n\n".join(d.page_content for d in docs)

            chunks = [
                c.page_content
                for c in self._splitter.create_documents([content])
            ]

            sha256 = self._compute_sha256(content)
            fetched_at = datetime.now(timezone.utc).isoformat()

            result = DocFetchResult(
                url=url,
                platform=platform,
                capability_id=capability_id,
                content=content,
                chunks=chunks,
                sha256=sha256,
                fetched_at=fetched_at,
                from_cache=False,
            )

            self._write_cache(result)

            logger.info(
                "Fetched doc for %s/%s (sha256: %s...)",
                platform,
                capability_id,
                sha256[:8],
            )

            return result

        except Exception as exc:
            logger.warning(
                "Failed to fetch %s for %s/%s: %s — using cache",
                url,
                platform,
                capability_id,
                exc,
            )

            cached = self.get_cached(
                platform,
                capability_id,
            )

            if cached:
                cached.from_cache = True
                return cached

            raise RuntimeError(
                f"No cache available for {platform}/{capability_id} "
                f"and live fetch failed: {exc}"
            ) from exc

    def get_cached(
        self,
        platform: str,
        capability_id: str,
    ) -> Optional[DocFetchResult]:
        cache_path = self._cache_key(
            platform,
            capability_id,
        )

        data = self._read_cache(cache_path)

        if data is None:
            return None

        return DocFetchResult(**data)

    def _cache_key(
        self,
        platform: str,
        capability_id: str,
    ) -> str:
        safe_cap = capability_id.replace(".", "_")
        return str(
            CACHE_DIR / f"{platform}_{safe_cap}.json"
        )

    def _compute_sha256(
        self,
        content: str,
    ) -> str:
        return hashlib.sha256(
            content.encode()
        ).hexdigest()

    def _write_cache(
        self,
        result: DocFetchResult,
    ) -> None:
        with open(
            self._cache_key(
                result.platform,
                result.capability_id,
            ),
            "w",
        ) as f:
            json.dump(
                result.to_dict(),
                f,
                indent=2,
            )

    def _read_cache(
        self,
        cache_path: str,
    ) -> Optional[dict]:
        try:
            with open(cache_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return None
```

**Acceptance criteria:**

- **`python -m py_compile kb_doc_sync/doc_fetcher.py`** passes
- **`DocFetcher().fetch(url, "github", "repo.lfs")`** returns a **`DocFetchResult`**
- Second call to the same URL returns from cache
- Network failure returns the cached result if cache exists
- **`doc_cache/`** directory is created automatically

---

### TASK 8 — Create `kb_doc_sync/doc_analyzer.py`

**File:** **`kb_doc_sync/doc_analyzer.py`**  
**Type:** New  
**Depends on:** Tasks 1, 5, 7

Implement **`DocAnalyzer`** class with the full LangChain chain:

```text
PromptTemplate | ChatBedrock | PydanticOutputParser
```

Returns **`KBUpdateProposal`** Pydantic model.

**Full implementation:**

```python
"""
doc_analyzer.py
LangChain chain that analyzes API doc changes.
Returns structured KBUpdateProposal.
Claude explains. Python decides whether to apply.
"""

import logging
from typing import Optional

from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
You are a technical knowledge base analyst for SCM platform migrations.
You analyze API documentation changes and propose KB updates.
RULES:
- Only report changes clearly supported by the new doc content.
- Do not invent changes. Do not speculate beyond what the doc says.
- HIGH confidence: doc explicitly and clearly states the change.
- MEDIUM confidence: doc implies the change but is not explicit.
- LOW confidence: you suspect a change but cannot confirm from doc text.
- Set should_auto_update = true ONLY when confidence is HIGH
  AND at least one field actually changed.
"""

ANALYSIS_TEMPLATE = """{system_instruction}

Capability ID: {capability_id}
Platform: {platform}

Current KB entry:
{current_kb_entry}

Previous documentation content (truncated):
{old_doc_content}

New documentation content (truncated):
{new_doc_content}

{format_instructions}
"""


class KBUpdateProposal(BaseModel):
    capability_id: str = Field(
        description="Capability ID e.g. review.draft_pr"
    )

    platform: str = Field(
        description="Platform e.g. github"
    )

    doc_changed: bool = Field(
        description="True if doc content meaningfully changed"
    )

    supported_changed: bool = Field(
        description="True if supported field should change"
    )

    new_supported: Optional[bool] = Field(
        default=None,
        description="New value for supported if it changed"
    )

    notes_changed: bool = Field(
        description="True if notes field should change"
    )

    new_notes: Optional[str] = Field(
        default=None,
        description="New notes value if changed"
    )

    workaround_changed: bool = Field(
        description="True if workaround field should change"
    )

    new_workaround: Optional[str] = Field(
        default=None,
        description="New workaround value if changed"
    )

    behavioral_attrs_changed: bool = Field(
        description="True if any behavioral_attrs should change"
    )

    new_behavioral_attrs: Optional[dict] = Field(
        default=None,
        description="Updated behavioral attributes if changed"
    )

    confidence: str = Field(
        description="HIGH, MEDIUM, or LOW"
    )

    reasoning: str = Field(
        description="Two sentence explanation of what changed and why"
    )

    should_auto_update: bool = Field(
        description="True only when confidence HIGH and a field changed"
    )


class DocAnalyzer:
    def __init__(self, aws_region: str, model_id: str) -> None:
        self._parser = PydanticOutputParser(
            pydantic_object=KBUpdateProposal
        )

        self._llm = ChatBedrock(
            model_id=model_id,
            region_name=aws_region,
            model_kwargs={
                "max_tokens": 1024,
                "temperature": 0,
            },
        )

        self._prompt = PromptTemplate(
            template=ANALYSIS_TEMPLATE,
            input_variables=[
                "system_instruction",
                "capability_id",
                "platform",
                "current_kb_entry",
                "old_doc_content",
                "new_doc_content",
            ],
            partial_variables={
                "format_instructions": (
                    self._parser.get_format_instructions()
                )
            },
        )

        self._chain = self._prompt | self._llm | self._parser

    def analyze(
        self,
        capability_id: str,
        platform: str,
        current_kb_entry: dict,
        old_doc_content: str,
        new_doc_content: str,
    ) -> KBUpdateProposal:
        logger.info(
            "Analyzing doc change for %s/%s",
            platform,
            capability_id,
        )

        return self._chain.invoke({
            "system_instruction": SYSTEM_INSTRUCTION,
            "capability_id": capability_id,
            "platform": platform,
            "current_kb_entry": str(current_kb_entry),
            "old_doc_content": old_doc_content[:3000],
            "new_doc_content": new_doc_content[:3000],
        })
```

**Acceptance criteria:**

- **`python -m py_compile kb_doc_sync/doc_analyzer.py`** passes
- **`KBUpdateProposal`** can be instantiated with all required fields
- **`DocAnalyzer`** can be instantiated (AWS credentials not required for class init)
- With valid AWS credentials, **`analyze()`** returns a **`KBUpdateProposal`**

---

### TASK 9 — Create `kb_doc_sync/kb_updater.py`

**File:** **`kb_doc_sync/kb_updater.py`**  
**Type:** New  
**Depends on:** Tasks 5, 6, 7, 8

Implement the full **`KBUpdater`** class.

**Full logic for `_check_capability()`:**

```python
def _check_capability(
    self,
    platform: str,
    capability_id: str,
    doc_url: str,
    platform_kb: dict,
    platform_yaml_path: Path,
    result: KBUpdateResult,
) -> None:
    """Check one capability for one platform."""
    try:
        # 1. Fetch live doc
        live_result = self._fetcher.fetch(
            doc_url,
            platform,
            capability_id,
        )

        # 2. Get cached (previous) version
        cached = self._fetcher.get_cached(
            platform,
            capability_id,
        )

        # 3. If no previous cache existed, this is first fetch
        #    Write cache (already done in fetch) and log.
        #    No update needed.
        if cached is None or cached.sha256 == live_result.sha256:
            logger.info(
                "%s/%s — doc unchanged (sha256 match)",
                platform,
                capability_id,
            )

            self._log_activity(
                platform,
                capability_id,
                "DOC_UNCHANGED",
                None,
            )
            return

        # 4. Doc changed — analyze if Bedrock is available
        result.docs_changed += 1

        if self._skip_bedrock or self._analyzer is None:
            logger.info(
                "%s/%s — doc changed but skip-bedrock set. "
                "Skipping analysis.",
                platform,
                capability_id,
            )

            self._log_activity(
                platform,
                capability_id,
                "DOC_CHANGED_SKIPPED",
                None,
            )
            return

        # 5. Get current KB entry
        current_kb_entry = platform_kb.get(
            capability_id,
            {},
        )

        # 6. Run LangChain analysis chain
        proposal = self._analyzer.analyze(
            capability_id=capability_id,
            platform=platform,
            current_kb_entry=current_kb_entry,
            old_doc_content=cached.content,
            new_doc_content=live_result.content,
        )

        # 7. Apply or stage based on confidence
        if proposal.should_auto_update:
            self._apply_update(
                platform_yaml_path,
                capability_id,
                proposal,
            )

            result.auto_updates_applied += 1

            self._log_activity(
                platform,
                capability_id,
                "AUTO_UPDATED",
                proposal,
            )
        else:
            self._stage_proposal(proposal)
            result.proposals_staged += 1

            self._log_activity(
                platform,
                capability_id,
                "STAGED_FOR_REVIEW",
                proposal,
            )

        result.update_details.append({
            "platform": platform,
            "capability_id": capability_id,
            "confidence": proposal.confidence,
            "should_auto_update": proposal.should_auto_update,
            "reasoning": proposal.reasoning,
        })

    except Exception as exc:
        error_msg = f"{platform}/{capability_id}: {exc}"

        result.errors.append(error_msg)

        logger.error(
            "Error checking capability %s: %s",
            capability_id,
            exc,
        )

        self._log_activity(
            platform,
            capability_id,
            "ERROR",
            None,
            str(exc),
        )
```

**Full logic for `_apply_update()`:**

```python
def _apply_update(
    self,
    platform_yaml_path: Path,
    capability_id: str,
    proposal: KBUpdateProposal,
) -> None:
    """Apply HIGH confidence update to platform YAML."""
    with open(platform_yaml_path) as f:
        data = yaml.safe_load(f) or {}

    entry = data.get(capability_id, {})

    if proposal.supported_changed and proposal.new_supported is not None:
        entry["supported"] = proposal.new_supported

    if proposal.notes_changed and proposal.new_notes is not None:
        entry["notes"] = proposal.new_notes

    if proposal.workaround_changed and proposal.new_workaround is not None:
        entry["workaround"] = proposal.new_workaround

    if (
        proposal.behavioral_attrs_changed
        and proposal.new_behavioral_attrs is not None
    ):
        entry.setdefault("behavioral_attrs", {}).update(
            proposal.new_behavioral_attrs
        )

    # Update metadata fields
    entry["confidence"] = proposal.confidence
    entry["last_verified"] = (
        datetime.now(timezone.utc).date().isoformat()
    )
    entry["verification_source"] = (
        f"Auto-updated from live API doc — {proposal.reasoning}"
    )

    data[capability_id] = entry

    with open(platform_yaml_path, "w") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
        )

    logger.info(
        "Applied HIGH confidence update to %s: %s",
        platform_yaml_path.name,
        capability_id,
    )
```

**Acceptance criteria:**

- **`python -m py_compile kb_doc_sync/kb_updater.py`** passes
- **`KBUpdater.run("gitlab", "github")`** executes without error
- HIGH confidence proposals update the YAML file
- MEDIUM/LOW proposals are written to **`kb_update_proposals.yaml`**
- All activity is logged to **`kb_update_log.yaml`**
- **`capability_taxonomy.yaml`** and **`known_gaps.yaml`** are never touched
- Network failure on one URL does not crash the entire run

---

### TASK 10 — Migrate `BedrockClient` to LangChain in `parity_agent.py`

**File:** **`parity_agent.py`**  
**Type:** Modified — extend only  
**Depends on:** Tasks 1, 4

Replace raw **`boto3.invoke_model`** calls in **`BedrockClient`** with a LangChain chain.

**New Pydantic model for report sections:**

```python
from pydantic import BaseModel, Field


class ParityReportSections(BaseModel):
    executive_summary: str = Field(
        description=(
            "Section 1 — executive summary with risk rating "
            "and top concerns"
        )
    )

    hard_blockers_section: str = Field(
        description=(
            "Section 2 — hard blockers with workaround options"
        )
    )

    behavioral_differences_section: str = Field(
        description=(
            "Section 3 — behavioral differences with concrete examples"
        )
    )

    seamless_section: str = Field(
        description=(
            "Section 4 — capabilities that migrate without change"
        )
    )

    coverage_section: str = Field(
        description=(
            "Section 5 — coverage report with LOW confidence items"
        )
    )
```

### New Chain Construction

```python
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence


class BedrockClient:
    def __init__(
        self,
        aws_region: str,
        model_id: str,
        inference_profile_id: Optional[str] = None,
        max_tokens: int = 4096,
        connect_timeout: int = 20,
        read_timeout: int = 300,
        max_attempts: int = 3,
    ) -> None:
        self._parser = PydanticOutputParser(
            pydantic_object=ParityReportSections
        )

        self._llm = ChatBedrock(
            model_id=inference_profile_id or model_id,
            region_name=aws_region,
            model_kwargs={
                "max_tokens": max_tokens,
                "temperature": 0,
            },
        )

        self._prompt = PromptTemplate(
            template=self._load_prompt_template(),
            input_variables=[
                "gap_analysis_json",
                "source",
                "target",
            ],
            partial_variables={
                "format_instructions": (
                    self._parser.get_format_instructions()
                )
            },
        )

        self._chain: RunnableSequence = (
            self._prompt | self._llm | self._parser
        )

    def generate_parity_report(
        self,
        gap_analysis: dict,
        source_platform: str,
        target_platform: str,
    ) -> str:
        """Generate report. Returns assembled Markdown string."""
        import json

        sections: ParityReportSections = self._chain.invoke({
            "gap_analysis_json": json.dumps(
                gap_analysis,
                indent=2,
            ),
            "source": source_platform,
            "target": target_platform,
        })

        return self._assemble_markdown(
            sections,
            source_platform,
            target_platform,
        )

    def _assemble_markdown(
        self,
        sections: ParityReportSections,
        source: str,
        target: str,
    ) -> str:
        return f"""# Platform Parity Report: {source} → {target}

## 1. Executive Summary
{sections.executive_summary}

## 2. 🔴 Hard Blockers
{sections.hard_blockers_section}

## 3. 🟡 Behavioral Differences
{sections.behavioral_differences_section}

## 4. 🟢 Seamless Migrations
{sections.seamless_section}

## 5. 📋 Coverage Report
{sections.coverage_section}
"""
```

Acceptance criteria:

python -m py_compile parity_agent.py passes
Existing tests still pass: pytest tests/
--skip-bedrock mode still works (no LangChain call made)
Report still has all 5 sections in correct order
Section headers match validation patterns in test_bedrock_e2e.py
TASK 11 — Add Interactive Input to main()
File: parity_agent.py
Type: Modified
Depends on: Task 10

Modify main() to prompt the user interactively when --source-platform or --target-platform are not provided.

Python

VALID_PLATFORMS = ["gitlab", "github", "azure_devops", "bitbucket"]

def _prompt_for_platform(prompt_text: str) -> str:
    """Prompt user for a platform. Validate input. Retry on invalid."""
    while True:
        value = input(prompt_text).strip().lower()
        if value in VALID_PLATFORMS:
            return value
        print(
            f"  Invalid platform '{value}'. "
            f"Choose from: {', '.join(VALID_PLATFORMS)}"
        )

def main() -> None:
    parser = argparse.ArgumentParser(...)

    # Keep existing args — make optional
    parser.add_argument(
        "--source-platform",
        choices=VALID_PLATFORMS,
        default=None,
        help="Source SCM platform. If not provided, will prompt interactively.",
    )
    parser.add_argument(
        "--target-platform",
        choices=VALID_PLATFORMS,
        default=None,
        help="Target SCM platform. If not provided, will prompt interactively.",
    )
    # ... all other existing args unchanged ...

    args = parser.parse_args()

    # Interactive fallback
    if args.source_platform is None:
        print("\nPlatform Parity Check")
        print("─" * 40)
        args.source_platform = _prompt_for_platform(
            f"Source SCM platform ({'/'.join(VALID_PLATFORMS)}): "
        )

    if args.target_platform is None:
        args.target_platform = _prompt_for_platform(
            f"Target SCM platform ({'/'.join(VALID_PLATFORMS)}): "
        )

    if args.source_platform == args.target_platform:
        print("Error: Source and target platforms must be different.")
        raise SystemExit(1)

    # ... rest of main unchanged ...
```

**Acceptance criteria:**

- **`python parity_agent.py`** (no args) prompts for source then target
- **`python parity_agent.py --source-platform gitlab --target-platform github`** still works (no prompt)
- Invalid platform name causes re-prompt, not crash
- Same source and target raises clear error
- **`python -m py_compile parity_agent.py`** passes

---

### TASK 12 — Wire KB Freshness Check into `ParityCheckAgent`

**File:** **`parity_agent.py`**  
**Type:** Modified  
**Depends on:** Tasks 9, 10, 11

Wire **`KBUpdater`** into **`ParityCheckAgent.analyze()`**.

```python
from kb_doc_sync.kb_updater import KBUpdater, KBUpdateResult


class ParityCheckAgent:
    def analyze(
        self,
        source_platform: str,
        target_platform: str,
        scope_filter: Optional[list[str]] = None,
    ) -> "ParityReport":

        # STEP 1 — KB Freshness Check (NEW)
        if not self._skip_bedrock:
            print("\nChecking KB freshness...")

            updater = KBUpdater(
                aws_region=self._aws_region,
                model_id=self._model_id,
                skip_bedrock=self._skip_bedrock,
            )

            update_result = updater.run(
                source_platform=source_platform,
                target_platform=target_platform,
                scope_filter=scope_filter,
            )

            self._print_update_summary(update_result)

        else:
            print(
                "\nSkipping KB freshness check "
                "(--skip-bedrock mode)"
            )

        # STEP 2 — Load KB (EXISTING — unchanged)
        # Now reads potentially-updated YAML files
        kb_data = self._loader.load(
            source_platform,
            target_platform,
        )

        # STEP 3 — Compare (EXISTING — unchanged)
        gaps = self._engine.compare(
            kb_data,
            source_platform,
            target_platform,
        )

        # STEP 4 — Generate Report (EXISTING — now uses LangChain)
        report = self._bedrock.generate_parity_report(
            gaps,
            source_platform,
            target_platform,
        )

        return report

    def _print_update_summary(
        self,
        result: KBUpdateResult,
    ) -> None:
        print(
            f"  Capabilities checked : "
            f"{result.capabilities_checked}"
        )

        print(
            f"  Docs changed         : "
            f"{result.docs_changed}"
        )

        print(
            f"  Auto-updates applied : "
            f"{result.auto_updates_applied}"
        )

        print(
            f"  Staged for review    : "
            f"{result.proposals_staged}"
        )

        if result.errors:
            print(
                f"  Errors               : "
                f"{len(result.errors)}"
            )

            for e in result.errors:
                print(f"    - {e}")
```

**Acceptance criteria:**

- **`python -m py_compile parity_agent.py`** passes
- KB freshness check runs before comparison on every non-skip-bedrock run
- **`--skip-bedrock`** skips KB freshness check entirely
- If KB updater raises an error, it is caught and logged — run continues
- Update summary is printed to the console after the freshness check

---

### TASK 13 — Add Old Report Deletion to Export

**File:** **`parity_agent.py`**  
**Type:** Modified  
**Depends on:** Task 12

Add **`_delete_old_reports()`** and call it before writing new reports.

```python
def _delete_old_reports(
    self,
    output_dir: Path,
    source_platform: str,
    target_platform: str,
) -> None:
    """
    Delete all existing .md and .json reports for this pair.
    Pattern: {source}_to_{target}_*.md / *.json
    """
    pair_prefix = f"{source_platform}_to_{target_platform}_"
    deleted = []

    for ext in ("*.md", "*.json"):
        for f in output_dir.glob(f"{pair_prefix}{ext}"):
            f.unlink()
            deleted.append(f.name)

    if deleted:
        for name in deleted:
            logger.info(
                "Deleted old report: %s",
                name,
            )

        print(
            f"  Deleted {len(deleted)} old report(s) "
            f"for this pair."
        )
    else:
        print(
            "  No previous reports found for this pair."
        )


# Call this in the report export section of ParityCheckAgent
# BEFORE writing new files:

self._delete_old_reports(
    output_dir,
    source_platform,
    target_platform,
)

# THEN write new .md and .json files as before
```

**Acceptance criteria:**

- Running the same pair twice — second run deletes first run's output
- Running different pairs — outputs do not affect each other
- Deletion logged at INFO level
- Console message shown to user
- **`python -m py_compile parity_agent.py`** passes

---

### TASK 14 — Update Test Suite

**Files:**
- **`tests/test_comparison_engine.py`**
- **`tests/test_kb_loader.py`**
- **`tests/test_output_format.py`**

**Type:** Modified  
**Depends on:** Tasks 2, 4, 10, 13

**Add to `test_kb_loader.py`:**

```python
def test_all_platform_yaml_entries_have_confidence_fields():
    """After Task 2, all entries must have confidence, last_verified,
    verification_source fields."""
    platforms = [
        "gitlab",
        "github",
        "azure_devops",
        "bitbucket",
    ]

    for platform in platforms:
        path = Path(
            f"capability_kb/platforms/{platform}.yaml"
        )

        data = yaml.safe_load(
            path.read_text()
        )

        for cap_id, entry in data.items():
            assert "confidence" in entry, (
                f"{platform}.yaml: "
                f"{cap_id} missing confidence"
            )

            assert "last_verified" in entry, (
                f"{platform}.yaml: "
                f"{cap_id} missing last_verified"
            )

            assert "verification_source" in entry, (
                f"{platform}.yaml: "
                f"{cap_id} missing verification_source"
            )

            assert entry["confidence"] in (
                "HIGH",
                "MEDIUM",
                "LOW",
            ), (
                f"{platform}.yaml: "
                f"{cap_id} invalid confidence value"
            )
```

**Add to `tests/test_doc_sync.py` (new file):**

```python
"""
test_doc_sync.py
Tests for KB doc sync module.
Does NOT make real network calls or Bedrock calls.
Uses in-memory fixtures only.
"""

import json
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from kb_doc_sync.doc_fetcher import (
    DocFetcher,
    DocFetchResult,
)

from kb_doc_sync.doc_analyzer import (
    KBUpdateProposal,
)


def test_doc_fetch_result_to_dict():
    result = DocFetchResult(
        url="https://example.com",
        platform="github",
        capability_id="repo.lfs",
        content="some content",
        chunks=["some content"],
        sha256="abc123",
        fetched_at="2026-08-12T00:00:00+00:00",
        from_cache=False,
    )

    d = result.to_dict()

    assert d["platform"] == "github"
    assert d["capability_id"] == "repo.lfs"
    assert d["sha256"] == "abc123"


def test_doc_fetcher_cache_roundtrip(tmp_path):
    """Test that writing and reading cache works."""
    with patch(
        "kb_doc_sync.doc_fetcher.CACHE_DIR",
        tmp_path,
    ):
        fetcher = DocFetcher()

        result = DocFetchResult(
            url="https://example.com",
            platform="github",
            capability_id="repo.lfs",
            content="some content",
            chunks=["some content"],
            sha256="abc123",
            fetched_at="2026-08-12T00:00:00+00:00",
            from_cache=False,
        )

        fetcher._write_cache(result)

        cached = fetcher.get_cached(
            "github",
            "repo.lfs",
        )

        assert cached is not None
        assert cached.sha256 == "abc123"


def test_kb_update_proposal_validation():
    """KBUpdateProposal must enforce all required fields."""
    proposal = KBUpdateProposal(
        capability_id="repo.lfs",
        platform="github",
        doc_changed=True,
        supported_changed=False,
        new_supported=None,
        notes_changed=True,
        new_notes="Updated notes from doc",
        workaround_changed=False,
        new_workaround=None,
        behavioral_attrs_changed=False,
        new_behavioral_attrs=None,
        confidence="HIGH",
        reasoning=(
            "The doc now explicitly states LFS is supported."
        ),
        should_auto_update=True,
    )

    assert proposal.confidence == "HIGH"
    assert proposal.should_auto_update is True


def test_kb_updater_never_writes_taxonomy(tmp_path):
    """KB Updater must never write to capability_taxonomy.yaml."""
    taxonomy_path = (
        tmp_path / "capability_taxonomy.yaml"
    )

    taxonomy_path.write_text(
        "repo.lfs:\n"
        "  category: repository\n"
    )

    original_mtime = taxonomy_path.stat().st_mtime

    # Even if we trigger a full run (mocked), taxonomy must not change.
    # Implementation: verify the file is never opened for writing.
    import time

    time.sleep(0.01)

    assert taxonomy_path.stat().st_mtime == original_mtime
```

**Acceptance criteria:**

- **`pytest tests/`** passes with all existing and new tests
- No test makes real network calls
- No test calls Bedrock
- All new tests use mocks or in-memory fixtures

---

### TASK 15 — Update `test_bedrock_e2e.py`

**File:** **`test_bedrock_e2e.py`**  
**Type:** Modified — extend only  
**Depends on:** All previous tasks

Add optional **`--skip-kb-sync`** flag to bypass the KB freshness check for fast testing runs.

```python
parser.add_argument(
    "--skip-kb-sync",
    action="store_true",
    default=False,
    help="Skip KB freshness check (faster, no doc fetching)",
)
```

All existing arguments unchanged. All existing behavior unchanged.

**Acceptance criteria:**

- **`python test_bedrock_e2e.py --source-platform gitlab --target-platform github --skip-bedrock`** passes
- **`python test_bedrock_e2e.py --source-platform gitlab --target-platform github --skip-bedrock --skip-kb-sync`** passes
- **`python -m py_compile test_bedrock_e2e.py`** passes

---

## 9. Delivery Order

```text
TASK 1  — requirements.txt
TASK 2  — confidence fields in all platform YAML files
TASK 3  — CI/CD gaps in known_gaps.yaml
TASK 4  — CapabilityGap dataclass + confidence inheritance
TASK 5  — kb_doc_sync/__init__.py
TASK 6  — kb_doc_sync/doc_sources.yaml
TASK 7  — kb_doc_sync/doc_fetcher.py
TASK 8  — kb_doc_sync/doc_analyzer.py
TASK 9  — kb_doc_sync/kb_updater.py
TASK 10 — Migrate BedrockClient to LangChain in parity_agent.py
TASK 11 — Add interactive input to main()
TASK 12 — Wire KB freshness check into ParityCheckAgent
TASK 13 — Add old report deletion to export
TASK 14 — Update test suite
TASK 15 — Update test_bedrock_e2e.py
```

### Validation After Each Task

After every task, run:

```bash
python -m py_compile <modified_file>
```

After Task 14:

```bash
pytest tests/ -v
```

After Task 15 — full end-to-end validation:

```bash
# Deterministic — no AWS needed
python parity_agent.py --source-platform gitlab --target-platform github --skip-bedrock

# Interactive — no args
python parity_agent.py

# Full Bedrock run with KB sync
python parity_agent.py --source-platform gitlab --target-platform github
```

## 10. File Change Register

### New Files

| **File** | **Purpose** |
| --- | --- |
| **`kb_doc_sync/__init__.py`** | Package marker |
| **`kb_doc_sync/doc_sources.yaml`** | URL map per platform + capability |
| **`kb_doc_sync/doc_fetcher.py`** | WebBaseLoader wrapper, SHA-256 cache |
| **`kb_doc_sync/doc_analyzer.py`** | LangChain chain, `KBUpdateProposal` |
| **`kb_doc_sync/kb_updater.py`** | Orchestrates freshness check, writes YAML |
| **`kb_doc_sync/doc_cache/`** | Auto-created directory for SHA-256 cache |
| **`capability_kb/kb_update_log.yaml`** | Append-only audit log |
| **`capability_kb/kb_update_proposals.yaml`** | MEDIUM/LOW proposals for human review |
| **`tests/test_doc_sync.py`** | Tests for `kb_doc_sync` module |

### Modified Files

| **File** | **Change** |
| --- | --- |
| **`requirements.txt`** | LangChain dependencies added |
| **`capability_kb/platforms/gitlab.yaml`** | Confidence fields added to all entries |
| **`capability_kb/platforms/github.yaml`** | Confidence fields added to all entries |
| **`capability_kb/platforms/azure_devops.yaml`** | Confidence fields added to all entries |
| **`capability_kb/platforms/bitbucket.yaml`** | Confidence fields added to all entries |
| **`capability_kb/known_gaps.yaml`** | CI/CD gaps added |
| **`prompts/bedrock_prompts.yaml`** | Doc analysis prompt added, coverage section added |
| **`parity_agent.py`** | LangChain chain, interactive input, KB sync wired, old report deletion |
| **`tests/test_kb_loader.py`** | Confidence field validation added |
| **`test_bedrock_e2e.py`** | `--skip-kb-sync` flag added |

### Unchanged Files

| **File** | **Reason** |
| --- | --- |
| **`run_parity_matrix.py`** | No changes needed |
| **`capability_kb/capability_taxonomy.yaml`** | Never auto-written |
| **`tests/__init__.py`** | Unchanged |
| **`tests/test_comparison_engine.py`** | Existing tests still pass |
| **`tests/test_output_format.py`** | Existing tests still pass |

---

## 11. Runtime Behavior (End-to-End)

```text
$ python parity_agent.py

Platform Parity Check
────────────────────────────────────────
Source SCM platform (gitlab/github/azure_devops/bitbucket): gitlab
Target SCM platform (gitlab/github/azure_devops/bitbucket): github

Checking KB freshness...
  review.draft_pr        — doc unchanged
  service_desk_enabled   — doc changed → AUTO-UPDATED (HIGH confidence)
  review.approval_rules  — doc changed → staged for review (MEDIUM confidence)
  cicd.pipelines         — doc unchanged
  ...
  Capabilities checked : 54
  Docs changed         : 3
  Auto-updates applied : 1
  Staged for review    : 2

Loading knowledge base...
Running comparison: gitlab → github
  Hard Blockers       : 8
  Behavioral Diffs    : 12
  Partial Support     : 4
  Seamless            : 30
  Overall Risk        : HIGH

Generating report...
  Deleted 1 old report(s) for this pair.
  Report written: test_output/gitlab_to_github_a3f9c1.md
  Report written: test_output/gitlab_to_github_a3f9c1.json

Done.
```

---

## 12. Governing Principle

```text
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  DETERMINISTIC ENGINE  →  DECIDES all migration facts           │
│  KB UPDATER + DOC SYNC →  KEEPS knowledge current              │
│  CLAUDE via LANGCHAIN  →  EXPLAINS facts as narrative only      │
│                                                                 │
│  Claude never creates a blocker.                                │
│  Claude never removes a blocker.                                │
│  Claude never changes a risk level.                             │
│  Claude never writes to any file directly.                      │
│  Every KB update traces back to a source doc URL.               │
│  KB writes only allowed for HIGH confidence proposals.          │
│  MEDIUM and LOW go to human review only.                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# IMPLEMENTATION PROMPT

## Platform Parity Module v2.0 — Complete Implementation

```text
=======================================================================
IMPLEMENTATION PROMPT — PLATFORM PARITY MODULE v2.0
Local YAML KB + Live API Doc Sync + LangChain + Interactive CLI
=======================================================================

READ THIS ENTIRE PROMPT BEFORE WRITING A SINGLE LINE OF CODE.
DO NOT SKIP ANY SECTION.
DO NOT REORDER TASKS.
DO NOT COMBINE TASKS.

=======================================================================
SECTION 1 — WHO YOU ARE AND WHAT YOU ARE DOING
=======================================================================

You are implementing v2.0 of the Platform Parity Module for the
PACE SCM Migration project.

The Phase 1 codebase is already complete and working. Your job is
to EXTEND it — not rewrite it.

You are adding three things to an existing working system:
  1. Interactive user input — ask for source and target SCM at runtime
  2. Live API doc sync — fetch official docs, detect changes,
     update local YAML KB when confidence is HIGH
  3. Old report cleanup — delete previous report for same pair
     before writing new one

You are NOT:
  - Rewriting existing classes
  - Adding a database
  - Adding Temporal workflow
  - Changing the 5-section report structure
  - Changing the deterministic comparison logic
  - Touching capability_taxonomy.yaml or known_gaps.yaml structure

=======================================================================
SECTION 2 — EXISTING CODEBASE (READ BEFORE TOUCHING ANYTHING)
=======================================================================

The existing system lives in platform_parity/ and has:

FILES THAT EXIST AND WORK:
  parity_agent.py              Main orchestrator with these classes:
                                 CapabilityLoader
                                 ComparisonEngine
                                 BedrockClient
                                 ParityCheckAgent
                                 main()
  test_bedrock_e2e.py          Single pair test runner
  run_parity_matrix.py         Batch matrix runner
  capability_kb/
    capability_taxonomy.yaml   54 capabilities across 8 categories
    known_gaps.yaml            Gap records per migration path
    platforms/
      gitlab.yaml              GitLab capability declarations
      github.yaml              GitHub capability declarations
      azure_devops.yaml        Azure DevOps capability declarations
      bitbucket.yaml           Bitbucket capability declarations
  prompts/
    bedrock_prompts.yaml       Prompt templates for Bedrock
  tests/
    __init__.py
    test_comparison_engine.py
    test_kb_loader.py
    test_output_format.py
  test_output/                 Generated reports land here

RULES FOR EXISTING FILES:
  - Read every existing file before writing any code
  - Do NOT rewrite existing classes
  - Do NOT reformat existing code
  - Do NOT rename existing methods or arguments
  - EXTEND only — add new methods, add new fields, add new classes
  - All existing tests must still pass after every task
  - python -m py_compile parity_agent.py must pass after every task

=======================================================================
SECTION 3 — WHAT YOU WILL BUILD
=======================================================================

NEW FILES TO CREATE:
  requirements.txt                      (update if exists, create if not)
  kb_doc_sync/__init__.py               empty package marker
  kb_doc_sync/doc_sources.yaml          URL map per platform+capability
  kb_doc_sync/doc_fetcher.py            WebBaseLoader wrapper + SHA-256 cache
  kb_doc_sync/doc_analyzer.py           LangChain chain + KBUpdateProposal
  kb_doc_sync/kb_updater.py             Orchestrates freshness check
  kb_doc_sync/doc_cache/               Auto-created at runtime
  capability_kb/kb_update_log.yaml      Auto-created at runtime
  capability_kb/kb_update_proposals.yaml Auto-created at runtime
  tests/test_doc_sync.py               Tests for kb_doc_sync module

FILES TO MODIFY (EXTEND ONLY):
  capability_kb/platforms/gitlab.yaml       add confidence fields
  capability_kb/platforms/github.yaml       add confidence fields
  capability_kb/platforms/azure_devops.yaml add confidence fields
  capability_kb/platforms/bitbucket.yaml    add confidence fields
  capability_kb/known_gaps.yaml             add CI/CD gaps
  prompts/bedrock_prompts.yaml              add doc analysis prompt
  parity_agent.py                           extend classes, wire new modules
  tests/test_kb_loader.py                   add confidence field tests
  test_bedrock_e2e.py                       add --skip-kb-sync flag

FILES TO NEVER TOUCH:
  run_parity_matrix.py
  capability_kb/capability_taxonomy.yaml
  tests/__init__.py
  tests/test_comparison_engine.py
  tests/test_output_format.py

=======================================================================
SECTION 4 — CODING STANDARDS (NON-NEGOTIABLE)
=======================================================================

1. Python 3.12 type hints on every new function and method.

2. No new external dependencies beyond what is listed in Section 5.
   Every dependency must be in requirements.txt.

3. Never use print() for internal operations.
   Use logging.getLogger(__name__) in every module.
   Use print() ONLY for user-facing console messages in main().

4. Never sys.exit() inside classes.
   Raise RuntimeError with a descriptive message.
   Only main() may call sys.exit().

5. No shell=True in any subprocess call.
   (There are no subprocess calls in this project — keep it that way.)

6. No hardcoded secrets, credentials, or API keys anywhere.

7. Every new module must have a module-level docstring explaining
   its purpose and what it does NOT do.

8. All new CLI arguments must have complete --help text.

9. Log at DEBUG for internal operations.
   Log at INFO for user-visible steps.
   Log at WARNING for recoverable issues.
   Log at ERROR for failures that are caught and handled.

10. After every single task:
    python -m py_compile <file_you_just_wrote>
    Fix any syntax error before moving to the next task.

=======================================================================
SECTION 5 — DEPENDENCIES
=======================================================================

requirements.txt must contain exactly these. No more, no less.

  # Existing
  pyyaml>=6.0
  boto3>=1.34

  # LangChain stack (NEW)
  langchain>=0.2
  langchain-aws>=0.1
  langchain-community>=0.2
  langchain-core>=0.2
  pydantic>=2.0

  # Supporting (NEW)
  requests>=2.31
  beautifulsoup4>=4.12

  # Testing
  pytest>=8.0

Do NOT add:
  pandas
  faiss-cpu
  chromadb
  langchain-postgres
  psycopg2
  pgvector
  openpyxl
  pypdf
  unstructured

=======================================================================
SECTION 6 — ARCHITECTURE RULES (NEVER VIOLATE)
=======================================================================

RULE 1 — DETERMINISTIC ENGINE DECIDES FACTS
  ComparisonEngine classifies gaps.
  Claude never creates a blocker.
  Claude never removes a blocker.
  Claude never changes a risk level.
  Claude's job is: explain only.

RULE 2 — CLAUDE NEVER WRITES FILES
  Python writes files.
  Claude returns structured output via PydanticOutputParser.
  Python reads the structured output and decides what to write.

RULE 3 — KB WRITE SAFETY
  AUTO-WRITE ALLOWED:
    platforms/gitlab.yaml         HIGH confidence proposals only
    platforms/github.yaml         HIGH confidence proposals only
    platforms/azure_devops.yaml   HIGH confidence proposals only
    platforms/bitbucket.yaml      HIGH confidence proposals only
    kb_doc_sync/doc_cache/        Always — on every fetch
    capability_kb/kb_update_log.yaml   Always — audit trail
    capability_kb/kb_update_proposals.yaml  MEDIUM/LOW staging only

  NEVER AUTO-WRITE:
    capability_kb/capability_taxonomy.yaml   Human approval only
    capability_kb/known_gaps.yaml            Human approval only

RULE 4 — LANGCHAIN IS USED FOR:
  WebBaseLoader     doc fetching + HTML cleaning
  RecursiveCharacterTextSplitter   chunking long pages
  ChatBedrock       LLM calls (replaces raw boto3.invoke_model)
  PromptTemplate    structured prompt management
  PydanticOutputParser   structured output enforcement
  RunnableSequence  chaining prompt | llm | parser

RULE 5 — LANGCHAIN IS NOT USED FOR:
  Reading YAML files       use pyyaml
  Writing YAML files       use pyyaml
  SHA-256 comparison       use hashlib
  Gap classification       pure Python
  File deletion            use pathlib
  User input               use input()

RULE 6 — NETWORK FAILURE HANDLING
  If a doc URL cannot be fetched:
    Use the cached version if it exists.
    Log a WARNING.
    Continue to the next capability.
    Never crash the entire run because one URL failed.

RULE 7 — ONE REPORT PER PAIR
  Before writing any new report file:
    Delete ALL existing files matching:
      test_output/{source}_to_{target}_*.md
      test_output/{source}_to_{target}_*.json
    Log each deletion.
    Print count of deleted files to console.

=======================================================================
SECTION 7 — PYDANTIC OUTPUT MODELS
=======================================================================

These two Pydantic models enforce structured output from Claude.
Implement them exactly as specified.

--- Model 1: KBUpdateProposal (in kb_doc_sync/doc_analyzer.py) ---

class KBUpdateProposal(BaseModel):
    capability_id: str
      # The capability ID e.g. "review.draft_pr"

    platform: str
      # The platform e.g. "github"

    doc_changed: bool
      # True if the doc content meaningfully changed

    supported_changed: bool
      # True if the supported field should change

    new_supported: Optional[bool]
      # New value for supported if supported_changed is True
      # None if supported_changed is False

    notes_changed: bool
      # True if the notes field should change

    new_notes: Optional[str]
      # New notes value if notes_changed is True
      # None if notes_changed is False

    workaround_changed: bool
      # True if the workaround field should change

    new_workaround: Optional[str]
      # New workaround value if workaround_changed is True
      # None if workaround_changed is False

    behavioral_attrs_changed: bool
      # True if any behavioral_attrs should change

    new_behavioral_attrs: Optional[dict]
      # Updated behavioral attributes dict if changed
      # None if behavioral_attrs_changed is False

    confidence: str
      # Exactly one of: "HIGH", "MEDIUM", "LOW"

    reasoning: str
      # Exactly two sentences explaining what changed and why

    should_auto_update: bool
      # True ONLY when confidence == "HIGH" AND at least one
      # field actually changed (supported, notes, workaround,
      # or behavioral_attrs)

--- Model 2: ParityReportSections (in parity_agent.py) ---

class ParityReportSections(BaseModel):
    executive_summary: str
      # Full text for Section 1
      # Must include: total capabilities, counts per category,
      # overall risk rating, top 3 concerns

    hard_blockers_section: str
      # Full text for Section 2
      # Per gap: title, impact, workaround options with effort,
      # data migration path

    behavioral_differences_section: str
      # Full text for Section 3
      # Per gap: source behavior vs target behavior,
      # concrete example, impact

    seamless_section: str
      # Full text for Section 4
      # List of capabilities that migrate without change

    coverage_section: str
      # Full text for Section 5
      # List all LOW/UNKNOWN confidence capabilities
      # List any category with zero coverage
      # Recommend manual verification per item

=======================================================================
SECTION 8 — LANGCHAIN CHAIN SPECIFICATIONS
=======================================================================

--- Chain 1: Doc Analysis Chain (in doc_analyzer.py) ---

Components:
  PromptTemplate      with input_variables:
                        system_instruction
                        capability_id
                        platform
                        current_kb_entry
                        old_doc_content
                        new_doc_content
                      with partial_variables:
                        format_instructions (from parser)

  ChatBedrock         model_id from constructor argument
                      temperature: 0
                      max_tokens: 1024

  PydanticOutputParser  pydantic_object: KBUpdateProposal

Chain assembly:
  self._chain = self._prompt | self._llm | self._parser

Invocation:
  proposal = self._chain.invoke({
      "system_instruction": SYSTEM_INSTRUCTION,
      "capability_id": capability_id,
      "platform": platform,
      "current_kb_entry": str(current_kb_entry),
      "old_doc_content": old_doc_content[:3000],
      "new_doc_content": new_doc_content[:3000],
  })

Content truncation:
  old_doc_content is truncated to first 3000 characters
  new_doc_content is truncated to first 3000 characters
  This prevents context window overflow

--- Chain 2: Report Generation Chain (in parity_agent.py) ---

Components:
  PromptTemplate      with input_variables:
                        gap_analysis_json
                        source
                        target
                      with partial_variables:
                        format_instructions (from parser)

  ChatBedrock         model_id from constructor argument
                      inference_profile_id overrides model_id if set
                      temperature: 0
                      max_tokens: 4096

  PydanticOutputParser  pydantic_object: ParityReportSections

Chain assembly:
  self._chain = self._prompt | self._llm | self._parser

Invocation:
  sections = self._chain.invoke({
      "gap_analysis_json": json.dumps(gap_analysis, indent=2),
      "source": source_platform,
      "target": target_platform,
  })

After invocation:
  Assemble the 5 sections into a Markdown string
  with exact headers:
    ## 1. Executive Summary
    ## 2. 🔴 Hard Blockers
    ## 3. 🟡 Behavioral Differences
    ## 4. 🟢 Seamless Migrations
    ## 5. 📋 Coverage Report

  These headers are validated by test_bedrock_e2e.py
  Do NOT change them.

=======================================================================
SECTION 9 — SYSTEM INSTRUCTION FOR DOC ANALYSIS
=======================================================================

Use this exact system instruction string in DocAnalyzer:

SYSTEM_INSTRUCTION = """
You are a technical knowledge base analyst for SCM platform migrations.
You analyze API documentation changes and propose Knowledge Base updates.

STRICT RULES YOU MUST FOLLOW:
- Only report changes that are clearly and explicitly supported by
  the new documentation content.
- Do not invent changes. Do not speculate beyond what the doc says.
- Do not assume a feature changed unless the doc text clearly says so.
- HIGH confidence: the new doc explicitly and unambiguously states
  the change.
- MEDIUM confidence: the new doc implies the change but is not explicit.
- LOW confidence: you suspect a change but cannot confirm from the
  doc text alone.
- Set should_auto_update = true ONLY when ALL of these are true:
    a. confidence is HIGH
    b. at least one of supported, notes, workaround, or
       behavioral_attrs actually needs to change
- If the doc content is identical or you cannot determine what changed,
  set doc_changed = false and should_auto_update = false.
"""

=======================================================================
SECTION 10 — SYSTEM INSTRUCTION FOR REPORT GENERATION
=======================================================================

Use this exact system instruction in the report generation prompt
in parity_agent.py (add to the existing prompt template in
prompts/bedrock_prompts.yaml):

SYSTEM_INSTRUCTION = """
You are a technical writer for enterprise SCM migration reports.
The structured gap analysis you receive is the authoritative source
of truth. You explain it. You do not modify it.

STRICT RULES YOU MUST FOLLOW:
- Do not invent capabilities not present in the gap analysis.
- Do not add blockers that are not in the hard_blockers list.
- Do not remove blockers from the hard_blockers list.
- Do not change any risk level or classification.
- Do not introduce workarounds not present in the gap analysis.
- Do not add caveats like "this may vary" unless the gap analysis
  explicitly flags low confidence.
- Every section must be present. Empty sections are not allowed.
- Write in plain professional English. No bullet soup. No filler.
"""

=======================================================================
SECTION 11 — INTERACTIVE INPUT SPECIFICATION
=======================================================================

When --source-platform or --target-platform are NOT provided as
CLI arguments, prompt the user interactively.

VALID_PLATFORMS = ["gitlab", "github", "azure_devops", "bitbucket"]

Prompt format:
  "\nPlatform Parity Check"
  "─" * 40
  "Source SCM platform (gitlab/github/azure_devops/bitbucket): "
  "Target SCM platform (gitlab/github/azure_devops/bitbucket): "

On invalid input:
  Print: "  Invalid platform '{value}'. Choose from: gitlab, github,
          azure_devops, bitbucket"
  Re-prompt. Do not crash.

On same source and target:
  Print: "Error: Source and target platforms must be different."
  Exit with code 1.

When --source-platform and --target-platform ARE provided:
  Skip interactive prompts entirely.
  Validate against VALID_PLATFORMS.
  This preserves backward compatibility with existing scripts.

=======================================================================
SECTION 12 — DOC SOURCES YAML SPECIFICATION
=======================================================================

File: kb_doc_sync/doc_sources.yaml

Structure:
  {platform}:
    {capability_id}: "{official_doc_url}"

Rules:
  - Every platform must have a top-level key
  - Every capability in capability_taxonomy.yaml must have at least
    one URL entry in at least one platform
  - URLs must point to specific capability pages, not homepages
  - This file is human-maintained — never auto-written by the system
  - gitlab and github must be complete (all 54 capabilities)
  - azure_devops and bitbucket must have at minimum these capabilities:
      cicd.pipelines
      cicd.runners
      cicd.environments
      review.approval_rules
      repo.lfs
      security.secret_detection

Minimum required entries for gitlab:
  repo.lfs
  repo.mirroring
  repo.dependency_proxy
  review.approval_rules
  review.merge_trains
  review.draft_pr
  review.multiple_assignees
  cicd.pipelines
  cicd.runners
  cicd.environments
  cicd.artifacts
  security.secret_detection
  security.sast
  security.dast
  pm.confidential_issues
  pm.milestones
  integrations.webhooks
  labels.case_sensitivity
  labels.scoped
  labels.group_level
  snippets.project_scope
  snippets.visibility
  snippets.multi_file

(and all remaining capabilities from capability_taxonomy.yaml)

=======================================================================
SECTION 13 — DOC CACHE SPECIFICATION
=======================================================================

Cache directory: kb_doc_sync/doc_cache/
Cache file name: {platform}_{capability_id_with_dots_replaced_by_underscores}.json

Example:
  github_repo_lfs.json
  gitlab_review_approval_rules.json

Cache file format (JSON):
  {
    "url": "https://...",
    "platform": "github",
    "capability_id": "repo.lfs",
    "content": "full cleaned text content",
    "chunks": ["chunk1", "chunk2", ...],
    "sha256": "abc123...",
    "fetched_at": "2026-08-12T00:00:00+00:00",
    "from_cache": false
  }

Cache behavior:
  - Written on every successful live fetch
  - Read on fallback when live fetch fails
  - Used for SHA-256 comparison (old hash vs new hash)
  - Never manually edited
  - Not committed to version control (add to .gitignore)

=======================================================================
SECTION 14 — KB UPDATE LOG SPECIFICATION
=======================================================================

File: capability_kb/kb_update_log.yaml
Created automatically on first run if it does not exist.
APPEND ONLY — never modify or delete existing entries.

Entry format:
  - timestamp: "2026-08-12T10:30:00+00:00"
    platform: "github"
    capability_id: "repo.lfs"
    action: "AUTO_UPDATED"        # or DOC_UNCHANGED, STAGED_FOR_REVIEW,
                                  # DOC_CHANGED_SKIPPED, ERROR
    confidence: "HIGH"            # null if no proposal
    reasoning: "..."              # null if no proposal or error
    source_doc_url: "https://..."
    error: null                   # populated only for ERROR action

Action values:
  DOC_UNCHANGED        Hash matched — no update needed
  AUTO_UPDATED         HIGH confidence — YAML updated
  STAGED_FOR_REVIEW    MEDIUM or LOW — written to proposals
  DOC_CHANGED_SKIPPED  Doc changed but skip-bedrock is set
  ERROR                Exception occurred — check error field

=======================================================================
SECTION 15 — KB UPDATE PROPOSALS SPECIFICATION
=======================================================================

File: capability_kb/kb_update_proposals.yaml
Created automatically if it does not exist.
Written by kb_updater.py for MEDIUM and LOW confidence proposals.
Read and actioned by humans only — never auto-read by the system.

Entry format:
  - timestamp: "2026-08-12T10:30:00+00:00"
    platform: "github"
    capability_id: "repo.lfs"
    confidence: "MEDIUM"
    reasoning: "..."
    source_doc_url: "https://..."
    proposed_changes:
      notes_changed: true
      new_notes: "..."
      supported_changed: false
      new_supported: null
      workaround_changed: false
      new_workaround: null
      behavioral_attrs_changed: false
      new_behavioral_attrs: null
    status: "pending"

=======================================================================
SECTION 16 — CONFIDENCE FIELDS IN PLATFORM YAML FILES
=======================================================================

Every capability entry in every platform YAML file must have
exactly these three additional fields after Task 2:

  confidence: HIGH          # HIGH, MEDIUM, or LOW
  last_verified: "YYYY-MM-DD"
  verification_source: "URL or description of where verified"

Confidence assignment rules:
  HIGH   — from official platform docs, unambiguous, recently verified
  MEDIUM — from official docs but potentially version-specific
           or not independently tested
  LOW    — community sources, indirect evidence, or
           not verified within the last 12 months

Every single entry in all four platform files must have all three
fields. No entry may be missing any of these fields.

=======================================================================
SECTION 17 — CI/CD GAPS TO ADD TO known_gaps.yaml
=======================================================================

Add these four gap records under gitlab_to_github in known_gaps.yaml.
Follow the EXACT schema already used in the file.
Do NOT invent a new schema.

Gap 1:
  capability_id: cicd.pipelines
  gap_type: BEHAVIORAL_DIFF
  severity: HIGH
  title: "CI pipeline syntax requires full rewrite"
  description: |
    GitLab CI uses .gitlab-ci.yml with GitLab-specific syntax including
    stages, before_script, after_script, and GitLab-specific keywords.
    GitHub Actions uses .github/workflows/*.yml with different trigger
    syntax, job structure, needs dependencies, and runner configuration.
    No automated tool provides full-fidelity conversion.
  impact: |
    Every pipeline file must be manually converted or rewritten.
    Teams must learn GitHub Actions syntax from scratch.
    Existing GitLab CI optimizations may not have direct equivalents.
  workarounds:
    - option: "Manual rewrite using GitHub Actions equivalents"
      effort: HIGH
    - option: "GitHub Actions Importer (partial coverage only)"
      effort: MEDIUM
  data_migration: |
    Pipeline YAML files are not migrated automatically.
    They must be rewritten. Historical pipeline run data is not preserved.

Gap 2:
  capability_id: cicd.runners
  gap_type: BEHAVIORAL_DIFF
  severity: MEDIUM
  title: "Runner configuration and tagging model differs"
  description: |
    GitLab Runners use tags for routing jobs to specific runners.
    GitHub Actions uses runs-on labels for GitHub-hosted runners
    and self-hosted runner groups with label-based routing.
    GitLab executor types (docker, shell, kubernetes) map differently
    to GitHub Actions runner environments.
  impact: |
    Runner registration process must be redone.
    Job routing configuration must be rewritten.
    Self-hosted runner setup requires new tooling.
  workarounds:
    - option: "Map GitLab runner tags to GitHub runner labels manually"
      effort: MEDIUM
    - option: "Use GitHub-hosted runners where GitLab used shared runners"
      effort: LOW
  data_migration: |
    Runner registration is not migrated. Must be re-registered
    on GitHub Actions infrastructure.

Gap 3:
  capability_id: cicd.environments
  gap_type: BEHAVIORAL_DIFF
  severity: MEDIUM
  title: "Environment protection rules and deployment tracking differ"
  description: |
    GitLab Environments track deployments with full history, rollback,
    and stop actions. GitHub Environments support protection rules
    and required reviewers but have a simpler deployment tracking model.
    GitLab environment-scoped variables have no direct GitHub equivalent.
  impact: |
    Environment-scoped CI/CD variables must be migrated manually.
    Deployment history is not preserved.
    Rollback workflows must be reimplemented.
  workarounds:
    - option: "Recreate environment protection rules in GitHub manually"
      effort: MEDIUM
    - option: "Use GitHub Actions environment secrets for scoped vars"
      effort: MEDIUM
  data_migration: |
    Deployment history is not migrated. Environment configuration
    must be manually recreated. Scoped variables must be
    individually moved to GitHub environment secrets.

Gap 4:
  capability_id: cicd.artifacts
  gap_type: BEHAVIORAL_DIFF
  severity: LOW
  title: "Artifact retention policies and storage differ"
  description: |
    GitLab artifact retention is configured per job with expire_in.
    GitHub Actions artifact retention is configured at the repository
    or organization level (default 90 days) with no per-job override
    in the same way. GitLab artifact browsing UI differs from
    GitHub's artifact download model.
  impact: |
    Teams relying on long-term artifact storage must adjust retention
    settings at the repository level on GitHub.
    Artifact download workflows must be updated.
  workarounds:
    - option: "Configure repository-level retention in GitHub settings"
      effort: LOW
    - option: "Use external artifact storage (S3, etc.) for long-term"
      effort: HIGH
  data_migration: |
    Existing artifacts are not migrated. Only new pipeline runs
    produce GitHub Actions artifacts.

=======================================================================
SECTION 18 — TASK LIST (IMPLEMENT IN THIS EXACT ORDER)
=======================================================================

DO NOT SKIP AHEAD.
DO NOT COMBINE TASKS.
After each task: python -m py_compile <file>
After Task 14: pytest tests/ -v

---

TASK 1 — UPDATE requirements.txt
─────────────────────────────────
File: requirements.txt
Action: Create or update

Content must be exactly:
  # Existing
  pyyaml>=6.0
  boto3>=1.34

  # LangChain stack
  langchain>=0.2
  langchain-aws>=0.1
  langchain-community>=0.2
  langchain-core>=0.2
  pydantic>=2.0

  # Supporting
  requests>=2.31
  beautifulsoup4>=4.12

  # Testing
  pytest>=8.0

Acceptance criteria:
  pip install -r requirements.txt completes without error
  python -c "from langchain_aws import ChatBedrock" succeeds
  python -c "from langchain_community.document_loaders import WebBaseLoader" succeeds
  python -c "from langchain_core.output_parsers import PydanticOutputParser" succeeds
  python -c "from pydantic import BaseModel, Field" succeeds

---

TASK 2 — ADD CONFIDENCE FIELDS TO ALL PLATFORM YAML FILES
───────────────────────────────────────────────────────────
Files:
  capability_kb/platforms/gitlab.yaml
  capability_kb/platforms/github.yaml
  capability_kb/platforms/azure_devops.yaml
  capability_kb/platforms/bitbucket.yaml
Action: Extend each file — add three fields to every entry

Add to EVERY capability entry in ALL FOUR files:
  confidence: HIGH          (or MEDIUM or LOW per the rules in Section 16)
  last_verified: "2026-08-12"
  verification_source: "URL where this was verified"

Rules:
  Use HIGH for entries from official platform documentation that are
  unambiguous and clearly documented.
  Use MEDIUM for entries that are documented but may be version-specific.
  Use LOW for anything sourced from community resources or older than
  12 months.
  Every single entry must have all three fields. Zero exceptions.

Acceptance criteria:
  python -c "
  import yaml
  from pathlib import Path
  platforms = ['gitlab', 'github', 'azure_devops', 'bitbucket']
  for p in platforms:
      data = yaml.safe_load(
          Path(f'capability_kb/platforms/{p}.yaml').read_text()
      )
      for cap_id, entry in data.items():
          assert 'confidence' in entry, f'{p}: {cap_id} missing confidence'
          assert 'last_verified' in entry, f'{p}: {cap_id} missing last_verified'
          assert 'verification_source' in entry, f'{p}: {cap_id} missing verification_source'
          assert entry['confidence'] in ('HIGH','MEDIUM','LOW'), \
              f'{p}: {cap_id} invalid confidence'
  print('ALL CONFIDENCE FIELDS VALID')
  "
  python -m py_compile parity_agent.py passes

---

TASK 3 — ADD CI/CD GAPS TO known_gaps.yaml
────────────────────────────────────────────
File: capability_kb/known_gaps.yaml
Action: Add four gap records under gitlab_to_github

Add the four gap records specified in Section 17 exactly.
Follow the existing schema in the file exactly.
Do NOT change any existing records.
Do NOT change the file structure.

Acceptance criteria:
  python -c "
  import yaml
  from pathlib import Path
  data = yaml.safe_load(
      Path('capability_kb/known_gaps.yaml').read_text()
  )
  gaps = data.get('gitlab_to_github', {})
  all_ids = []
  for section in gaps.values():
      if isinstance(section, list):
          all_ids.extend(g.get('capability_id','') for g in section)
  required = ['cicd.pipelines','cicd.runners','cicd.environments','cicd.artifacts']
  for r in required:
      assert r in all_ids, f'Missing gap: {r}'
  print('ALL CI/CD GAPS PRESENT')
  "
  yaml.safe_load on the file succeeds without error

---

TASK 4 — EXTEND CapabilityGap DATACLASS IN parity_agent.py
────────────────────────────────────────────────────────────
File: parity_agent.py
Action: Extend the CapabilityGap dataclass — DO NOT rewrite it

Add these three fields to the existing CapabilityGap dataclass
with these exact defaults:
  confidence: str = "HIGH"
  last_verified: str = ""
  verification_source: str = ""

Add this constant above or near ComparisonEngine:
  CONFIDENCE_ORDER: dict[str, int] = {
      "HIGH": 3,
      "MEDIUM": 2,
      "LOW": 1,
      "UNKNOWN": 0,
  }

Add this method to ComparisonEngine:
  def _lower_confidence(self, c1: str, c2: str) -> str:
      """Return the lower of two confidence values."""
      if CONFIDENCE_ORDER.get(c1, 0) <= CONFIDENCE_ORDER.get(c2, 0):
          return c1
      return c2

In ComparisonEngine.compare(), when creating any CapabilityGap,
set confidence to the lower of source entry confidence and
target entry confidence using _lower_confidence().
Set last_verified from whichever platform has the older date.
Set verification_source from the lower-confidence platform entry.

Acceptance criteria:
  python -m py_compile parity_agent.py passes
  pytest tests/ passes (all existing tests still pass)
  A gap where source confidence=HIGH and target confidence=MEDIUM
  results in gap.confidence == "MEDIUM"

---

TASK 5 — CREATE kb_doc_sync/__init__.py
─────────────────────────────────────────
File: kb_doc_sync/__init__.py
Action: Create

Content: empty file (just a newline)

Acceptance criteria:
  python -c "import kb_doc_sync" succeeds from platform_parity/ directory

---

TASK 6 — CREATE kb_doc_sync/doc_sources.yaml
──────────────────────────────────────────────
File: kb_doc_sync/doc_sources.yaml
Action: Create

Create the URL mapping file with all platforms and capabilities
as specified in Section 12.

Minimum entries required:
  gitlab: all capabilities from capability_taxonomy.yaml
  github: all capabilities from capability_taxonomy.yaml
  azure_devops: minimum 6 capabilities listed in Section 12
  bitbucket: minimum 6 capabilities listed in Section 12

Every URL must be a real, specific official documentation page.
Do not use homepage URLs.

Acceptance criteria:
  python -c "
  import yaml
  from pathlib import Path
  data = yaml.safe_load(
      Path('kb_doc_sync/doc_sources.yaml').read_text()
  )
  assert 'gitlab' in data
  assert 'github' in data
  assert 'azure_devops' in data
  assert 'bitbucket' in data
  assert len(data['gitlab']) >= 22
  assert len(data['github']) >= 22
  assert len(data['azure_devops']) >= 6
  assert len(data['bitbucket']) >= 6
  print('DOC SOURCES VALID')
  "

---

TASK 7 — CREATE kb_doc_sync/doc_fetcher.py
────────────────────────────────────────────
File: kb_doc_sync/doc_fetcher.py
Action: Create

Implement exactly as specified. Full implementation:

"""
doc_fetcher.py

Fetches and cleans official SCM API documentation pages using
LangChain WebBaseLoader.

This module does NOT call any LLM.
This module does NOT write to any YAML KB file.
This module ONLY fetches web content, cleans it, caches it,
and returns it for analysis.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "doc_cache"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200


class DocFetchResult:
    """
    Result of a single documentation page fetch.
    Holds content, chunks, SHA-256, and metadata.
    """

    def __init__(
        self,
        url: str,
        platform: str,
        capability_id: str,
        content: str,
        chunks: list[str],
        sha256: str,
        fetched_at: str,
        from_cache: bool = False,
    ) -> None:
        self.url = url
        self.platform = platform
        self.capability_id = capability_id
        self.content = content
        self.chunks = chunks
        self.sha256 = sha256
        self.fetched_at = fetched_at
        self.from_cache = from_cache

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "platform": self.platform,
            "capability_id": self.capability_id,
            "content": self.content,
            "chunks": self.chunks,
            "sha256": self.sha256,
            "fetched_at": self.fetched_at,
            "from_cache": self.from_cache,
        }


class DocFetcher:
    """
    Fetches official SCM API documentation pages using
    LangChain WebBaseLoader. Computes SHA-256 for change
    detection. Caches results locally in doc_cache/.

    On network failure: falls back to cached version.
    If no cache exists and fetch fails: raises RuntimeError.
    """

    def __init__(self) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

    def fetch(
        self,
        url: str,
        platform: str,
        capability_id: str,
    ) -> DocFetchResult:
        """
        Fetch a documentation page.
        Writes result to cache.
        Falls back to cache on network failure.
        Raises RuntimeError if fetch fails and no cache exists.
        """
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            content = "\n\n".join(d.page_content for d in docs)
            chunks = [
                c.page_content
                for c in self._splitter.create_documents([content])
            ]
            sha256 = self._compute_sha256(content)
            fetched_at = datetime.now(timezone.utc).isoformat()
            result = DocFetchResult(
                url=url,
                platform=platform,
                capability_id=capability_id,
                content=content,
                chunks=chunks,
                sha256=sha256,
                fetched_at=fetched_at,
                from_cache=False,
            )
            self._write_cache(result)
            logger.info(
                "Fetched doc for %s/%s (sha256: %s...)",
                platform, capability_id, sha256[:8],
            )
            return result

        except Exception as exc:
            logger.warning(
                "Failed to fetch %s for %s/%s: %s — trying cache",
                url, platform, capability_id, exc,
            )
            cached = self.get_cached(platform, capability_id)
            if cached is not None:
                cached.from_cache = True
                logger.info(
                    "Using cached doc for %s/%s",
                    platform, capability_id,
                )
                return cached
            raise RuntimeError(
                f"Cannot fetch doc for {platform}/{capability_id} "
                f"from {url} and no cache exists. Error: {exc}"
            ) from exc

    def get_cached(
        self,
        platform: str,
        capability_id: str,
    ) -> Optional[DocFetchResult]:
        """
        Return cached DocFetchResult if it exists.
        Returns None if no cache entry found.
        """
        cache_path = self._cache_key(platform, capability_id)
        data = self._read_cache(cache_path)
        if data is None:
            return None
        return DocFetchResult(
            url=data["url"],
            platform=data["platform"],
            capability_id=data["capability_id"],
            content=data["content"],
            chunks=data["chunks"],
            sha256=data["sha256"],
            fetched_at=data["fetched_at"],
            from_cache=True,
        )

    def _cache_key(self, platform: str, capability_id: str) -> str:
        safe_cap = capability_id.replace(".", "_")
        return str(CACHE_DIR / f"{platform}_{safe_cap}.json")

    def _compute_sha256(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def _write_cache(self, result: DocFetchResult) -> None:
        path = self._cache_key(result.platform, result.capability_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    def _read_cache(self, cache_path: str) -> Optional[dict]:
        try:
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

Acceptance criteria:
  python -m py_compile kb_doc_sync/doc_fetcher.py passes
  python -c "from kb_doc_sync.doc_fetcher import DocFetcher, DocFetchResult"
    succeeds
  DocFetchResult(url='u',platform='p',capability_id='c',content='x',
    chunks=[],sha256='h',fetched_at='t').to_dict() returns a dict
  DocFetcher() creates CACHE_DIR automatically

---

TASK 8 — CREATE kb_doc_sync/doc_analyzer.py
─────────────────────────────────────────────
File: kb_doc_sync/doc_analyzer.py
Action: Create

Implement exactly as specified in Sections 7, 8, 9.

Module docstring:
  """
  doc_analyzer.py

  LangChain chain that analyzes API documentation changes
  and returns structured KB update proposals.

  This module does NOT write to any file.
  This module does NOT read YAML files.
  This module ONLY calls Claude via LangChain and returns
  a KBUpdateProposal Pydantic model.

  Claude explains what changed. Python decides what to do with it.
  """

Implement:
  SYSTEM_INSTRUCTION constant (exact text from Section 9)
  ANALYSIS_TEMPLATE constant (prompt template string)
  KBUpdateProposal Pydantic model (exact fields from Section 7)
  DocAnalyzer class with:
    __init__(self, aws_region: str, model_id: str) -> None
    analyze(self, capability_id, platform, current_kb_entry,
            old_doc_content, new_doc_content) -> KBUpdateProposal

Chain must be assembled as:
  self._chain = self._prompt | self._llm | self._parser

Content passed to LLM must be truncated:
  old_doc_content[:3000]
  new_doc_content[:3000]

Acceptance criteria:
  python -m py_compile kb_doc_sync/doc_analyzer.py passes
  python -c "from kb_doc_sync.doc_analyzer import DocAnalyzer,
    KBUpdateProposal" succeeds
  KBUpdateProposal can be instantiated with all required fields
  DocAnalyzer can be instantiated (no AWS call at init time)
  The chain attribute self._chain is a RunnableSequence

---

TASK 9 — CREATE kb_doc_sync/kb_updater.py
───────────────────────────────────────────
File: kb_doc_sync/kb_updater.py
Action: Create

Module docstring:
  """
  kb_updater.py

  Orchestrates the KB freshness check for a source+target platform pair.

  This is the ONLY module that writes to YAML KB files.
  It writes to platform YAML files on HIGH confidence proposals only.
  It never writes to capability_taxonomy.yaml or known_gaps.yaml.
  All activity is logged to capability_kb/kb_update_log.yaml.
  MEDIUM and LOW proposals are staged to
  capability_kb/kb_update_proposals.yaml for human review.
  """

Implement:
  KB_DIR, PLATFORMS_DIR, UPDATE_LOG_PATH, PROPOSALS_PATH,
  DOC_SOURCES_PATH constants

  KBUpdateResult dataclass or class with fields:
    capabilities_checked: int = 0
    docs_changed: int = 0
    auto_updates_applied: int = 0
    proposals_staged: int = 0
    errors: list[str] = field(default_factory=list)
    update_details: list[dict] = field(default_factory=list)

  KBUpdater class with:
    __init__(self, aws_region, model_id, skip_bedrock=False)
    run(self, source_platform, target_platform,
        scope_filter=None) -> KBUpdateResult
    _check_capability(self, platform, capability_id, doc_url,
                      platform_kb, platform_yaml_path, result)
    _apply_update(self, platform_yaml_path, capability_id, proposal)
    _stage_proposal(self, proposal)
    _log_activity(self, platform, capability_id, action,
                  proposal, error=None)
    _load_doc_sources(self) -> dict
    _load_platform_yaml(self, path) -> dict

_check_capability logic (exact order):
  1. Fetch live doc using DocFetcher.fetch()
  2. Get previous cached version using DocFetcher.get_cached()
     NOTE: get_cached() returns the PREVIOUS cached version.
     After fetch(), the cache has already been updated.
     So read the cache BEFORE calling fetch() to get the old version.
     Correct order:
       old_cached = self._fetcher.get_cached(platform, capability_id)
       live_result = self._fetcher.fetch(url, platform, capability_id)
  3. If old_cached is None: first fetch. Log DOC_UNCHANGED. Return.
  4. If old_cached.sha256 == live_result.sha256:
       Log DOC_UNCHANGED. Return.
  5. Hash differs: increment result.docs_changed
  6. If skip_bedrock: Log DOC_CHANGED_SKIPPED. Return.
  7. Run DocAnalyzer.analyze() with old and new content
  8. If proposal.should_auto_update:
       Call _apply_update()
       Increment result.auto_updates_applied
       Log AUTO_UPDATED
     Else:
       Call _stage_proposal()
       Increment result.proposals_staged
       Log STAGED_FOR_REVIEW
  9. Append to result.update_details
  Wrap entire method in try/except:
    On exception: append to result.errors, log ERROR, continue

_apply_update logic:
  Load the platform YAML file
  Get the entry for capability_id (create empty dict if missing)
  Apply only the fields where the corresponding _changed flag is True:
    If proposal.supported_changed and new_supported is not None:
      entry["supported"] = proposal.new_supported
    If proposal.notes_changed and new_notes is not None:
      entry["notes"] = proposal.new_notes
    If proposal.workaround_changed and new_workaround is not None:
      entry["workaround"] = proposal.new_workaround
    If proposal.behavioral_attrs_changed and new_behavioral_attrs:
      entry.setdefault("behavioral_attrs", {}).update(
          proposal.new_behavioral_attrs
      )
  Always update metadata fields:
    entry["confidence"] = proposal.confidence
    entry["last_verified"] = today's date as "YYYY-MM-DD"
    entry["verification_source"] = f"Auto-updated: {proposal.reasoning}"
  Write the updated dict back to the YAML file

_log_activity logic:
  Load existing log if it exists (or start with empty list)
  Append new entry with all fields from Section 14
  Write back to UPDATE_LOG_PATH
  This is append-only — never modify existing entries

_stage_proposal logic:
  Load existing proposals if file exists (or start with empty list)
  Append new proposal entry with all fields from Section 15
  Write back to PROPOSALS_PATH

Acceptance criteria:
  python -m py_compile kb_doc_sync/kb_updater.py passes
  python -c "from kb_doc_sync.kb_updater import KBUpdater,
    KBUpdateResult" succeeds
  KBUpdater instantiation succeeds (no network call at init)
  run() with skip_bedrock=True completes without AWS credentials
  On network failure for one capability: run() continues,
    error recorded in result.errors, not raised
  capability_taxonomy.yaml is never opened for writing
  known_gaps.yaml is never opened for writing

---

TASK 10 — MIGRATE BedrockClient TO LANGCHAIN IN parity_agent.py
─────────────────────────────────────────────────────────────────
File: parity_agent.py
Action: Extend — do NOT rewrite the class

Add these imports to parity_agent.py:
  from langchain_aws import ChatBedrock
  from langchain.prompts import PromptTemplate
  from langchain_core.output_parsers import PydanticOutputParser
  from langchain_core.runnables import RunnableSequence
  from pydantic import BaseModel, Field

Add ParityReportSections Pydantic model (exact fields from Section 7)
above or near BedrockClient.

Modify BedrockClient.__init__() to build the LangChain chain:
  self._parser = PydanticOutputParser(
      pydantic_object=ParityReportSections
  )
  self._llm = ChatBedrock(
      model_id=inference_profile_id or model_id,
      region_name=aws_region,
      model_kwargs={"max_tokens": max_tokens, "temperature": 0},
  )
  self._prompt = PromptTemplate(
      template=<load from prompts/bedrock_prompts.yaml>,
      input_variables=["gap_analysis_json", "source", "target"],
      partial_variables={
          "format_instructions": self._parser.get_format_instructions()
      },
  )
  self._chain = self._prompt | self._llm | self._parser

Modify BedrockClient.generate_parity_report() to:
  Use self._chain.invoke({...}) instead of boto3.invoke_model()
  Receive a ParityReportSections object back
  Assemble it into a Markdown string using _assemble_markdown()
  Return the assembled Markdown string

Add _assemble_markdown() method:
  Assembles the 5 sections into a Markdown string with these
  EXACT headers (required by test_bedrock_e2e.py validation):
    ## 1. Executive Summary
    ## 2. 🔴 Hard Blockers
    ## 3. 🟡 Behavioral Differences
    ## 4. 🟢 Seamless Migrations
    ## 5. 📋 Coverage Report

For --skip-bedrock mode:
  BedrockClient must NOT call ChatBedrock or self._chain
  Use the existing deterministic template path (keep it working)
  The chain is built in __init__ but ONLY called when not skip_bedrock

Update prompts/bedrock_prompts.yaml:
  Add the system instruction from Section 10 to the report prompt
  Add format_instructions placeholder: {format_instructions}
  Add source: {source} and target: {target} placeholders

Acceptance criteria:
  python -m py_compile parity_agent.py passes
  pytest tests/ passes (all existing tests still pass)
  --skip-bedrock mode still works without AWS credentials
  Report still has all 5 sections in correct order
  Section headers exactly match the patterns checked by test_bedrock_e2e.py

---

TASK 11 — ADD INTERACTIVE INPUT TO main() IN parity_agent.py
──────────────────────────────────────────────────────────────
File: parity_agent.py
Action: Extend main() — do NOT rewrite it

Add this constant near the top of the file or near main():
  VALID_PLATFORMS: list[str] = [
      "gitlab", "github", "azure_devops", "bitbucket"
  ]

Add this standalone function (not a method):
  def _prompt_for_platform(prompt_text: str) -> str:
      """
      Prompt user for a platform name.
      Validates against VALID_PLATFORMS.
      Re-prompts on invalid input.
      Never raises on bad input — always re-prompts.
      """
      while True:
          value = input(prompt_text).strip().lower()
          if value in VALID_PLATFORMS:
              return value
          print(
              f"  Invalid: '{value}'. "
              f"Choose from: {', '.join(VALID_PLATFORMS)}"
          )

Modify main() — keep all existing arguments, make source and
target optional:
  Change --source-platform to: required=False, default=None
  Change --target-platform to: required=False, default=None

After args = parser.parse_args(), add:
  if args.source_platform is None:
      print("\nPlatform Parity Check")
      print("─" * 40)
      args.source_platform = _prompt_for_platform(
          "Source SCM platform "
          "(gitlab/github/azure_devops/bitbucket): "
      )

  if args.target_platform is None:
      args.target_platform = _prompt_for_platform(
          "Target SCM platform "
          "(gitlab/github/azure_devops/bitbucket): "
      )

  if args.source_platform == args.target_platform:
      print("Error: Source and target platforms must be different.")
      raise SystemExit(1)

Acceptance criteria:
  python -m py_compile parity_agent.py passes
  python parity_agent.py (no args) prompts for source then target
  python parity_agent.py --source-platform gitlab
    --target-platform github skips prompts entirely
  Invalid platform name causes re-prompt, does not crash
  Same platform for source and target: error message + exit 1
  pytest tests/ still passes

---

TASK 12 — WIRE KB FRESHNESS CHECK INTO ParityCheckAgent
─────────────────────────────────────────────────────────
File: parity_agent.py
Action: Extend ParityCheckAgent.analyze() — do NOT rewrite it

Add this import at top of parity_agent.py:
  from kb_doc_sync.kb_updater import KBUpdater, KBUpdateResult

Add _print_update_summary() method to ParityCheckAgent:
  def _print_update_summary(self, result: KBUpdateResult) -> None:
      print(f"  Capabilities checked : {result.capabilities_checked}")
      print(f"  Docs changed         : {result.docs_changed}")
      print(f"  Auto-updates applied : {result.auto_updates_applied}")
      print(f"  Staged for review    : {result.proposals_staged}")
      if result.errors:
          print(f"  Errors               : {len(result.errors)}")
          for err in result.errors:
              print(f"    - {err}")

At the START of ParityCheckAgent.analyze(), before loading KB,
add:
  if not self._skip_bedrock:
      print("\nChecking KB freshness...")
      try:
          updater = KBUpdater(
              aws_region=self._aws_region,
              model_id=self._model_id,
              skip_bedrock=False,
          )
          update_result = updater.run(
              source_platform=source_platform,
              target_platform=target_platform,
              scope_filter=scope_filter,
          )
          self._print_update_summary(update_result)
      except Exception as exc:
          logger.error("KB freshness check failed: %s", exc)
          print(f"  WARNING: KB freshness check failed: {exc}")
          print("  Continuing with existing KB data.")
  else:
      print("\nSkipping KB freshness check (--skip-bedrock)")

IMPORTANT: The KB freshness check runs BEFORE CapabilityLoader.
This ensures that if KB Updater wrote new data to a YAML file,
CapabilityLoader reads the updated version.

Acceptance criteria:
  python -m py_compile parity_agent.py passes
  KB freshness check runs before KB load on full Bedrock runs
  --skip-bedrock skips the freshness check entirely
  If KBUpdater raises an exception: warning printed, run continues
  pytest tests/ still passes

---

TASK 13 — ADD OLD REPORT DELETION
───────────────────────────────────
File: parity_agent.py
Action: Add method and call it before writing reports

Add this method to ParityCheckAgent (or to the report export
section — wherever reports are currently written):

  def _delete_old_reports(
      self,
      output_dir: Path,
      source_platform: str,
      target_platform: str,
  ) -> None:
      """
      Delete all existing .md and .json reports for this
      source→target pair before writing the new report.
      Pattern: {source}_to_{target}_*.md and *.json
      """
      pair_prefix = f"{source_platform}_to_{target_platform}_"
      deleted: list[str] = []

      for ext in ("*.md", "*.json"):
          for f in output_dir.glob(f"{pair_prefix}{ext}"):
              f.unlink()
              deleted.append(f.name)
              logger.info("Deleted old report: %s", f.name)

      if deleted:
          print(f"  Deleted {len(deleted)} old report(s) for this pair.")
      else:
          print("  No previous reports found for this pair.")

Call _delete_old_reports() BEFORE writing any new .md or .json file.

Verify call order:
  1. _delete_old_reports()    ← first
  2. Write new .md file       ← second
  3. Write new .json file     ← third

Acceptance criteria:
  python -m py_compile parity_agent.py passes
  Running same pair twice: second run deletes first run outputs
  Running gitlab→github then github→gitlab: each pair independent
  gitlab→github reports do not delete github→gitlab reports
  Deletion count printed to console
  pytest tests/ still passes

---

TASK 14 — UPDATE TEST SUITE
─────────────────────────────
Files:
  tests/test_kb_loader.py      extend
  tests/test_doc_sync.py       create new

DO NOT modify:
  tests/test_comparison_engine.py
  tests/test_output_format.py

ADD to tests/test_kb_loader.py:

def test_all_platform_yaml_entries_have_confidence_fields():
    """Every entry in every platform YAML must have confidence,
    last_verified, and verification_source after Task 2."""
    import yaml
    from pathlib import Path
    platforms = ["gitlab", "github", "azure_devops", "bitbucket"]
    for platform in platforms:
        path = Path(f"capability_kb/platforms/{platform}.yaml")
        data = yaml.safe_load(path.read_text())
        for cap_id, entry in data.items():
            assert "confidence" in entry, \
                f"{platform}.yaml: {cap_id} missing 'confidence'"
            assert "last_verified" in entry, \
                f"{platform}.yaml: {cap_id} missing 'last_verified'"
            assert "verification_source" in entry, \
                f"{platform}.yaml: {cap_id} missing 'verification_source'"
            assert entry["confidence"] in ("HIGH", "MEDIUM", "LOW"), \
                f"{platform}.yaml: {cap_id} invalid confidence value"

def test_confidence_field_values_are_valid():
    """Confidence values must be exactly HIGH, MEDIUM, or LOW."""
    import yaml
    from pathlib import Path
    valid = {"HIGH", "MEDIUM", "LOW"}
    platforms = ["gitlab", "github", "azure_devops", "bitbucket"]
    for platform in platforms:
        data = yaml.safe_load(
            Path(f"capability_kb/platforms/{platform}.yaml").read_text()
        )
        for cap_id, entry in data.items():
            assert entry.get("confidence") in valid, \
                f"{platform}.yaml: {cap_id} has invalid confidence"

CREATE tests/test_doc_sync.py:

"""
test_doc_sync.py

Tests for the kb_doc_sync module.
No real network calls. No real Bedrock calls.
All tests use in-memory fixtures or mocks.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from kb_doc_sync.doc_fetcher import DocFetcher, DocFetchResult
from kb_doc_sync.doc_analyzer import KBUpdateProposal


class TestDocFetchResult:
    def test_to_dict_returns_all_fields(self):
        result = DocFetchResult(
            url="https://example.com",
            platform="github",
            capability_id="repo.lfs",
            content="some content",
            chunks=["some content"],
            sha256="abc123",
            fetched_at="2026-08-12T00:00:00+00:00",
            from_cache=False,
        )
        d = result.to_dict()
        assert d["platform"] == "github"
        assert d["capability_id"] == "repo.lfs"
        assert d["sha256"] == "abc123"
        assert d["from_cache"] is False
        assert "content" in d
        assert "chunks" in d
        assert "fetched_at" in d

    def test_from_cache_flag(self):
        result = DocFetchResult(
            url="https://example.com",
            platform="github",
            capability_id="repo.lfs",
            content="x",
            chunks=[],
            sha256="h",
            fetched_at="t",
            from_cache=True,
        )
        assert result.from_cache is True


class TestDocFetcherCache:
    def test_cache_roundtrip(self, tmp_path):
        """Write to cache then read back — content must match."""
        with patch("kb_doc_sync.doc_fetcher.CACHE_DIR", tmp_path):
            fetcher = DocFetcher()
            result = DocFetchResult(
                url="https://example.com",
                platform="github",
                capability_id="repo.lfs",
                content="some content",
                chunks=["some content"],
                sha256="abc123",
                fetched_at="2026-08-12T00:00:00+00:00",
                from_cache=False,
            )
            fetcher._write_cache(result)
            cached = fetcher.get_cached("github", "repo.lfs")
            assert cached is not None
            assert cached.sha256 == "abc123"
            assert cached.content == "some content"
            assert cached.from_cache is True

    def test_get_cached_returns_none_when_missing(self, tmp_path):
        """Returns None when no cache file exists."""
        with patch("kb_doc_sync.doc_fetcher.CACHE_DIR", tmp_path):
            fetcher = DocFetcher()
            result = fetcher.get_cached("github", "repo.lfs")
            assert result is None

    def test_sha256_computation(self, tmp_path):
        """SHA-256 of same content always returns same hash."""
        with patch("kb_doc_sync.doc_fetcher.CACHE_DIR", tmp_path):
            fetcher = DocFetcher()
            h1 = fetcher._compute_sha256("hello world")
            h2 = fetcher._compute_sha256("hello world")
            assert h1 == h2
            assert len(h1) == 64

    def test_sha256_different_content(self, tmp_path):
        """Different content produces different SHA-256."""
        with patch("kb_doc_sync.doc_fetcher.CACHE_DIR", tmp_path):
            fetcher = DocFetcher()
            h1 = fetcher._compute_sha256("content A")
            h2 = fetcher._compute_sha256("content B")
            assert h1 != h2

    def test_cache_dir_created_automatically(self, tmp_path):
        """CACHE_DIR is created if it does not exist."""
        new_cache = tmp_path / "new_cache_dir"
        assert not new_cache.exists()
        with patch("kb_doc_sync.doc_fetcher.CACHE_DIR", new_cache):
            DocFetcher()
        assert new_cache.exists()


class TestKBUpdateProposal:
    def test_valid_proposal_instantiation(self):
        """KBUpdateProposal with all fields instantiates correctly."""
        proposal = KBUpdateProposal(
            capability_id="repo.lfs",
            platform="github",
            doc_changed=True,
            supported_changed=False,
            new_supported=None,
            notes_changed=True,
            new_notes="Updated notes",
            workaround_changed=False,
            new_workaround=None,
            behavioral_attrs_changed=False,
            new_behavioral_attrs=None,
            confidence="HIGH",
            reasoning="The doc changed. LFS is now explicitly confirmed.",
            should_auto_update=True,
        )
        assert proposal.confidence == "HIGH"
        assert proposal.should_auto_update is True
        assert proposal.notes_changed is True
        assert proposal.new_notes == "Updated notes"

    def test_no_change_proposal(self):
        """A proposal with no changes sets should_auto_update False."""
        proposal = KBUpdateProposal(
            capability_id="repo.lfs",
            platform="github",
            doc_changed=False,
            supported_changed=False,
            new_supported=None,
            notes_changed=False,
            new_notes=None,
            workaround_changed=False,
            new_workaround=None,
            behavioral_attrs_changed=False,
            new_behavioral_attrs=None,
            confidence="HIGH",
            reasoning="No change detected. Content is identical.",
            should_auto_update=False,
        )
        assert proposal.should_auto_update is False
        assert proposal.doc_changed is False

    def test_medium_confidence_should_not_auto_update(self):
        """MEDIUM confidence proposals should have should_auto_update=False."""
        proposal = KBUpdateProposal(
            capability_id="repo.lfs",
            platform="github",
            doc_changed=True,
            supported_changed=True,
            new_supported=False,
            notes_changed=False,
            new_notes=None,
            workaround_changed=False,
            new_workaround=None,
            behavioral_attrs_changed=False,
            new_behavioral_attrs=None,
            confidence="MEDIUM",
            reasoning="Doc implies change. Not fully explicit.",
            should_auto_update=False,
        )
        assert proposal.confidence == "MEDIUM"
        assert proposal.should_auto_update is False


class TestKBWriteSafety:
    def test_taxonomy_never_written(self, tmp_path):
        """
        capability_taxonomy.yaml must never be opened for writing
        during a KB updater run.
        """
        taxonomy_path = tmp_path / "capability_taxonomy.yaml"
        taxonomy_path.write_text("repo.lfs:\n  category: repository\n")
        import time
        original_mtime = taxonomy_path.stat().st_mtime
        time.sleep(0.05)
        # File must not have been modified
        assert taxonomy_path.stat().st_mtime == original_mtime

    def test_known_gaps_never_written(self, tmp_path):
        """
        known_gaps.yaml must never be opened for writing
        during a KB updater run.
        """
        gaps_path = tmp_path / "known_gaps.yaml"
        gaps_path.write_text("gitlab_to_github:\n  hard_blockers: []\n")
        import time
        original_mtime = gaps_path.stat().st_mtime
        time.sleep(0.05)
        assert gaps_path.stat().st_mtime == original_mtime


Acceptance criteria:
  pytest tests/ -v passes with ALL tests (existing + new)
  No test makes real network calls
  No test calls AWS Bedrock
  All assertions use descriptive messages

---

TASK 15 — UPDATE test_bedrock_e2e.py
──────────────────────────────────────
File: test_bedrock_e2e.py
Action: Extend — add one argument, do not change anything else

Add this argument to the argparse setup:
  parser.add_argument(
      "--skip-kb-sync",
      action="store_true",
      default=False,
      help=(
          "Skip KB freshness check. "
          "Faster for testing. "
          "Does not fetch live API docs."
      ),
  )

When --skip-kb-sync is set, pass skip_bedrock=True to KBUpdater
OR set an environment variable / flag that causes ParityCheckAgent
to skip the freshness check for this run.

All existing arguments remain exactly as they are.
All existing behavior remains exactly as it is.

Acceptance criteria:
  python -m py_compile test_bedrock_e2e.py passes
  python test_bedrock_e2e.py --source-platform gitlab
    --target-platform github --skip-bedrock passes
  python test_bedrock_e2e.py --source-platform gitlab
    --target-platform github --skip-bedrock --skip-kb-sync passes
  Both commands produce valid output files in test_output/

=======================================================================
SECTION 19 — FINAL VALIDATION CHECKLIST
=======================================================================

After all 15 tasks are complete, run these in order:

STEP 1 — Syntax check all new and modified files:
  python -m py_compile parity_agent.py
  python -m py_compile kb_doc_sync/doc_fetcher.py
  python -m py_compile kb_doc_sync/doc_analyzer.py
  python -m py_compile kb_doc_sync/kb_updater.py
  python -m py_compile test_bedrock_e2e.py

STEP 2 — Full test suite:
  pytest tests/ -v
  Expected: all tests pass, zero failures

STEP 3 — Deterministic single pair (no AWS needed):
  python parity_agent.py \
    --source-platform gitlab \
    --target-platform github \
    --skip-bedrock
  Expected:
    No prompts (args provided)
    "Skipping KB freshness check (--skip-bedrock)"
    Report written to test_output/
    Console shows: All 5 required sections present - PASS

STEP 4 — Interactive mode (no AWS needed):
  python parity_agent.py --skip-bedrock
  Expected:
    Prompts for source platform
    Prompts for target platform
    Invalid input causes re-prompt
    Report generated after valid inputs

STEP 5 — Old report cleanup validation:
  Run the same pair twice:
    python parity_agent.py \
      --source-platform gitlab \
      --target-platform github \
      --skip-bedrock
    python parity_agent.py \
      --source-platform gitlab \
      --target-platform github \
      --skip-bedrock
  Expected second run:
    "Deleted 2 old report(s) for this pair."
    Only 2 files in test_output/ (1 .md + 1 .json)

STEP 6 — Cross-pair isolation:
  Run gitlab→github then github→gitlab:
    python parity_agent.py \
      --source-platform gitlab \
      --target-platform github \
      --skip-bedrock
    python parity_agent.py \
      --source-platform github \
      --target-platform gitlab \
      --skip-bedrock
  Expected:
    4 files in test_output/ (2 per pair)
    gitlab→github reports NOT deleted by github→gitlab run

STEP 7 — Full Bedrock run (AWS credentials required):
  python parity_agent.py \
    --source-platform gitlab \
    --target-platform github
  Expected:
    "Checking KB freshness..."
    Update summary printed
    Report generated with all 5 sections
    KB update log written

STEP 8 — Matrix runner still works:
  python run_parity_matrix.py
  Expected: completes without error

=======================================================================
SECTION 20 — WHAT DONE LOOKS LIKE
=======================================================================

The implementation is complete when:

  ✅ pytest tests/ -v passes with zero failures
  ✅ python parity_agent.py (no args) prompts interactively
  ✅ --source-platform and --target-platform args still work
  ✅ --skip-bedrock mode works without AWS credentials
  ✅ Running same pair twice deletes first pair's reports
  ✅ Running different pairs does not cross-delete
  ✅ All platform YAML files have confidence fields on every entry
  ✅ Four CI/CD gaps present in known_gaps.yaml
  ✅ doc_fetcher.py uses WebBaseLoader (not requests directly)
  ✅ doc_analyzer.py uses LangChain chain (not raw boto3)
  ✅ BedrockClient uses LangChain chain (not raw boto3)
  ✅ PydanticOutputParser used for both KB proposals and report sections
  ✅ capability_taxonomy.yaml never written by automation
  ✅ known_gaps.yaml never written by automation
  ✅ platform YAML files updated only on HIGH confidence proposals
  ✅ MEDIUM/LOW proposals written to kb_update_proposals.yaml
  ✅ All activity logged to kb_update_log.yaml
  ✅ run_parity_matrix.py still works unchanged
  ✅ All 5 report sections present with correct headers
  ✅ No hardcoded secrets anywhere

=======================================================================
END OF IMPLEMENTATION PROMPT
=======================================================================
```
