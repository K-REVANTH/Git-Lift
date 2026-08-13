\=======================================================================
PACE SCM MIGRATION SCRIPTS — PLATFORM PARITY MODULE
FULL CONTEXT DOCUMENT — 2026-08-12
\=======================================================================

PURPOSE OF THIS DOCUMENT
─────────────────────────
This document captures complete project context, architecture, what has 
been built, and the next planned implementation so any AI assistant or
developer can continue work without missing information.

\=======================================================================
SECTION 1 — REPOSITORY OVERVIEW
\=======================================================================

Repository: pace-scm-migration-scripts
Working folder for THIS project: platform\_parity/
(Do NOT touch other sibling folders: ghec\_to\_ghec/, perfroce\_to\_github/)

Each top-level folder is a separate project. All changes must stay
inside platform\_parity/ only.

\=======================================================================
SECTION 2 — SCRIPT WRITING RULES (applies to every .py file written)
\=======================================================================

These are non-negotiable rules from guide\_to\_write\_scripts.md:

1\. Placeholders are BARE: write VAR = {{VAR}}, NEVER VAR = "{{VAR}}"
   The renderer calls repr() on the value — quoting breaks it.

2\. ONE stdout print only: the LAST statement must be
   print(json.dumps({...}))
   ALL other output goes to sys.stderr only.

3\. No host-app imports: scripts run as standalone subprocesses.
   You CANNOT import scm\_migration\_tool.\*

4\. No shell=True in subprocess: always use list form
   subprocess.run(["cmd", "arg"], check=True)

5\. No .. in paths. No hardcoded secrets.

6\. Raise exceptions on error: NEVER sys.exit(1). Use raise RuntimeError()

7\. Use ApiRequestBuilder for HTTP calls:
   from activities.script\_executor.http\_client import ApiRequestBuilder

8\. Use db\_session for DB:
   from activities.commons.db.db\_session import db\_session

9\. One script, one responsibility (\~150 lines of logic max).

10\. All shared inputs declared ONCE in init.py (the first script).
    Downstream scripts read via {{steps.init.\<key>}} — never re-declare.

11\. {{EXECUTION\_ID}} is auto-injected — never pass it in values.

12\. Source vars prefixed SOURCE\_, target vars prefixed TARGET\_.

13\. Placeholder chaining:
    {{previous.KEY}}              — from immediately prior script
    {{steps.SCRIPT\_NAME.KEY}}     — from a specific named script

\=======================================================================
SECTION 3 — PLATFORM PARITY MODULE — WHAT IT DOES
\=======================================================================

The platform\_parity/ folder is a SCM Platform Parity Reporting system.

It compares two SCM platforms (source → target) and generates a parity
report that identifies:
  \- HARD\_BLOCKER: source has capability, target doesn't, no workaround
  \- PARTIAL\_SUPPORT: source has it, target doesn't, but workaround exists
  \- BEHAVIORAL\_DIFF: both support it, behavior/limits differ
  \- SEAMLESS: no differences

Supported platforms: gitlab, github, azure\_devops, bitbucket

Two report modes:
  \- Deterministic: purely from KB YAML files, no LLM, used for CI/validation
  \- Bedrock mode: deterministic compare + AWS Bedrock Claude LLM narrative

\=======================================================================
SECTION 4 — FOLDER STRUCTURE (platform\_parity/)
\=======================================================================

platform\_parity/
├── README.md                    — user guide and quick-start
├── test\_bedrock\_e2e.py          — local single-pair test runner
├── run\_parity\_matrix.py         — local batch test runner (all pairs)
├── aws-ca-bundle.pem            — corporate TLS CA bundle (optional)
├── capability\_kb/
│   ├── capability\_taxonomy.yaml — 54 canonical capability IDs (THE source of truth)
│   ├── known\_gaps.yaml          — curated human-reviewed gap records per migration path
│   └── platforms/
│       ├── gitlab.yaml          — GitLab per-capability support data
│       ├── github.yaml          — GitHub per-capability support data
│       ├── azure\_devops.yaml    — Azure DevOps per-capability support data
│       └── bitbucket.yaml       — Bitbucket per-capability support data
├── prompts/
│   └── bedrock\_prompts.yaml     — system\_prompt + parity\_report\_prompt for Claude
├── scripts/                     — Temporal workflow scripts (the 5-step pipeline)
│   ├── platform\_parity\_init.py
│   ├── platform\_parity\_load\_kb.py
│   ├── platform\_parity\_compare.py
│   ├── platform\_parity\_generate\_report.py
│   └── platform\_parity\_export.py
├── metadata/                    — plain-text descriptions of each script
│   ├── platform\_parity\_init.txt
│   ├── platform\_parity\_load\_kb.txt
│   ├── platform\_parity\_compare.txt
│   ├── platform\_parity\_generate\_report.txt
│   └── platform\_parity\_export.txt
├── workflow/
│   └── platform\_parity\_workflow\.json   — Temporal workflow definition
└── test\_output/                 — generated .md and .json report artifacts
    ├── gitlab\_to\_github\_\*.md/.json
    ├── github\_to\_gitlab\_\*.md/.json
    ├── azure\_devops\_to\_github\_\*.md/.json
    ├── azure\_devops\_to\_gitlab\_\*.md/.json
    ├── azure\_devops\_to\_bitbucket\_\*.md/.json
    ├── bitbucket\_to\_github\_\*.md/.json
    └── bitbucket\_to\_gitlab\_\*.md/.json

\=======================================================================
SECTION 5 — THE 5-STEP TEMPORAL WORKFLOW PIPELINE (EXISTING, COMPLETE)
\=======================================================================

Step 1: platform\_parity\_init.py
  \- Placeholders: SOURCE\_PLATFORM, TARGET\_PLATFORM, OUTPUT\_FORMAT,
    SCOPE\_FILTER, AWS\_REGION, BEDROCK\_MODEL\_ID, KB\_BASE\_PATH,
    NO\_CACHE, EXECUTION\_ID, PROJECT\_ID
  \- Validates all inputs (allowed platforms, format options, KB path exists)
  \- Outputs: source\_platform, target\_platform, output\_format, scope\_filter,
    aws\_region, bedrock\_model\_id, kb\_base\_path, no\_cache, execution\_id,
    project\_id, job\_id
  \- ALL downstream scripts read from {{steps.platform\_parity\_init.\<key>}}

Step 2: platform\_parity\_load\_kb.py
  \- Reads from {{steps.platform\_parity\_init.\*}}
  \- Loads: capability\_taxonomy.yaml, platforms/{source}.yaml,
    platforms/{target}.yaml, known\_gaps.yaml
  \- Applies SCOPE\_FILTER if set
  \- Validates all capability IDs exist in taxonomy
  \- Outputs: taxonomy, source\_capabilities, target\_capabilities,
    known\_gaps, capabilities\_loaded

Step 3: platform\_parity\_compare.py
  \- Reads from platform\_parity\_init + platform\_parity\_load\_kb
  \- Pure deterministic diff — NO LLM involved
  \- Gap classification rules (in priority order):
    1\. If capability in known\_gaps.yaml for this migration path → HARD\_BLOCKER
    2\. Source supported, target not, workaround in target YAML → PARTIAL\_SUPPORT
    3\. Source supported, target not, no workaround → HARD\_BLOCKER
    4\. Both supported, behavioral attr differs OR in known\_gaps.behavioral\_differences → BEHAVIORAL\_DIFF
    5\. Otherwise → SEAMLESS
  \- Behavioral attrs compared: max\_assignees, case\_sensitive, retention\_days,
    default\_retention\_days, max\_retention\_days, named\_rules,
    supports\_group\_milestones, tier\_required, strategies, runner\_scopes,
    separator, scope
  \- Risk calculation: CRITICAL if hard\_blockers exist, HIGH if >3 behavioral\_diffs,
    MEDIUM if 1-3 behavioral\_diffs or partial\_support, LOW otherwise
  \- Outputs: hard\_blockers, behavioral\_diffs, partial\_support, seamless,
    not\_covered, overall\_risk, gap\_count
  \- NOTE: not\_covered is always [] — the logic to populate it exists in
    test\_bedrock\_e2e.py but is not yet in the Temporal script

Step 4: platform\_parity\_generate\_report.py
  \- Reads from platform\_parity\_init + platform\_parity\_compare
  \- Computes SHA-256 cache key from gap payload
  \- Cache location: /tmp/.parity\_cache/{hash}.md (7-day TTL)
  \- If NO\_CACHE=false and cache valid → returns cached Markdown
  \- Else → calls AWS Bedrock Claude with system\_prompt + parity\_report\_prompt
  \- Validates 5 required sections present in response:
      \## 1. Executive Summary
      \## 2. 🔴 Hard Blockers
      \## 3. 🟡 Behavioral Differences
      \## 4. 🟢 Seamless Migrations
      \## 5. 📋 Coverage Report
  \- Outputs: report\_markdown, report\_hash, cache\_hit, bedrock\_model\_id, token\_count
  \- NOTE: this script uses simpler boto3 without botocore Config tuning;
    the local test runner (test\_bedrock\_e2e.py) has better retry/timeout config

Step 5: platform\_parity\_export.py
  \- Reads from platform\_parity\_init + platform\_parity\_compare + platform\_parity\_generate\_report
  \- Writes files to /mnt/efs (fallback to /tmp if not writable)
  \- File name: {EXECUTION\_ID}\_parity\_report.{md,json}
  \- JSON omits report\_markdown key; Markdown is the full report
  \- Outputs: json\_path, markdown\_path, overall\_risk, gap\_count,
    source\_platform, target\_platform

\=======================================================================
SECTION 6 — WORKFLOW DEFINITION (workflow/platform\_parity\_workflow\.json)
\=======================================================================

{
  "name": "platform\_parity\_check",
  "steps": [
    {
      "name": "platform\_parity\_init",
      "values": {
        "SOURCE\_PLATFORM": "",
        "TARGET\_PLATFORM": "",
        "OUTPUT\_FORMAT": "markdown",
        "SCOPE\_FILTER": "[]",
        "AWS\_REGION": "",
        "BEDROCK\_MODEL\_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
        "KB\_BASE\_PATH": "",
        "NO\_CACHE": false,
        "PROJECT\_ID": ""
      }
    },
    { "name": "platform\_parity\_load\_kb" },
    { "name": "platform\_parity\_compare" },
    {
      "name": "platform\_parity\_generate\_report",
      "activity\_options": {
        "start\_to\_close\_seconds": 120,
        "heartbeat\_seconds": 30,
        "retry\_policy": {
          "maximum\_attempts": 2,
          "non\_retryable\_error\_types": ["ScriptNotFoundError"]
        }
      }
    },
    { "name": "platform\_parity\_export" }
  ]
}

\=======================================================================
SECTION 7 — KNOWLEDGE BASE DETAILS
\=======================================================================

capability\_taxonomy.yaml — 54 capability IDs across 10 categories:
  repository: repo.lfs, repo.mirroring, repo.dependency\_proxy,
    repo.wikis, repo.protected\_branches, repo.branch\_rules,
    repo.fork\_restrictions, repo.archived\_state, repo.transfer,
    repo.visibility\_control, repo.packages, repo.container\_registry,
    repo.releases, repo.signed\_commits, repo.submodule\_support

  code\_review: review\.approval\_rules, review\.merge\_trains,
    review\.draft\_pr, review\.required\_reviewers, review\.multiple\_assignees,
    review\.review\_threads, review\.suggested\_changes, review\.auto\_merge,
    review\.merge\_strategies, review\.branch\_protection\_bypass,
    review\.code\_owners, review\.pr\_templates, review\.status\_checks,
    review\.review\_apps, review\.merge\_queue

  labels: labels.case\_sensitivity, labels.scoped, labels.group\_level,
    labels.color, labels.description, labels.default\_labels

  snippets: snippets.project\_scope, snippets.personal\_scope,
    snippets.visibility, snippets.multi\_file, snippets.versioning,
    snippets.embed

  cicd: cicd.pipelines, cicd.runners, cicd.environments, cicd.artifacts,
    cicd.schedules, cicd.pipeline\_triggers, cicd.protected\_variables,
    cicd.deployment\_approvals, cicd.reusable\_components, cicd.matrix\_builds,
    cicd.oidc\_workload\_identity

  security: security.secret\_detection, security.sast, security.dast,
    security.dependency\_scanning, security.audit\_log,
    security.container\_scanning, security.license\_scanning,
    security.compliance\_frameworks, security.custom\_secret\_patterns

  project\_management: pm.confidential\_issues, pm.milestones,
    pm.issue\_templates, pm.time\_tracking, pm.boards, pm.epics, pm.roadmaps

  integrations: integrations.webhooks

  access\_control: access.sso, access.ip\_allowlist, access.deploy\_keys,
    access.fine\_grained\_tokens, access.team\_hierarchy, access.scim\_provisioning

  packages: packages.npm, packages.maven, packages.pypi, packages.nuget,
    packages.generic

Each platform YAML (e.g. gitlab.yaml, github.yaml) has this structure per capability:
  repo.lfs:
    supported: true
    notes: "description of how the platform supports this"
    confidence: HIGH | MEDIUM | LOW | UNKNOWN
    last\_verified: "2026-08-04"
    verification\_source: "official documentation"
    workaround: "optional — if supported=false, what to use instead"
    migration\_impact: "optional — impact description"
    [behavioral attrs]: max\_assignees, strategies, retention\_days, etc.

known\_gaps.yaml structure:
  gitlab\_to\_github:
    hard\_blockers:
      \- capability\_id: repo.mirroring
        severity: HIGH
        title: "..."
        description: "..."
        impact: "..."
        workarounds:
          \- option: "..."
            effort: MEDIUM
            description: "..."
        data\_migration: "..."
    behavioral\_differences:
      \- capability\_id: review\.approval\_rules
        source\_behavior: "..."
        target\_behavior: "..."
        impact: "..."

Known migration paths in known\_gaps.yaml:
  gitlab\_to\_github, github\_to\_gitlab,
  azure\_devops\_to\_github, azure\_devops\_to\_gitlab, azure\_devops\_to\_bitbucket,
  bitbucket\_to\_github, bitbucket\_to\_gitlab

bedrock\_prompts.yaml:
  system\_prompt: instructs Claude to write narrative from pre-computed facts only,
    not invent gaps or contradict provided data
  parity\_report\_prompt: instructs Claude to produce EXACTLY 5 sections in order,
    with specific content requirements for section 5 (Coverage Report)

\=======================================================================
SECTION 8 — LOCAL TEST RUNNERS (not Temporal scripts)
\=======================================================================

test\_bedrock\_e2e.py:
  \- Single-pair report run (local test, not deployed)
  \- Runs all 5 pipeline stages inline
  \- --skip-bedrock flag for deterministic mode (no AWS needed)
  \- Has better botocore Config (connect\_timeout, read\_timeout, retries)
    than the Temporal script version
  \- Reads AWS credentials from environment variables (never hardcoded)
  \- Writes output to test\_output/ as {source}\_to\_{target}\_{hash12}.md/.json
  \- Has \_normalize\_report\_format() that stitches missing sections if LLM misses any
  \- Has \_render\_hard\_blockers\_section() and \_render\_behavioral\_differences\_section()
    which override whatever the LLM produced for sections 2 and 3 with deterministic
    structured output (ensures consistent format)

run\_parity\_matrix.py:
  \- Batch run across all pairs in known\_gaps.yaml
  \- --with-bedrock flag, --pairs for selective pairs
  \- Calls test\_bedrock\_e2e.configure\_runtime() + run\_e2e() per pair
  \- Prints summary table: pair, risk, gaps, tokens

\=======================================================================
SECTION 9 — THE DISCOVERY REPORT CSV (user-uploaded input)
\=======================================================================

File: discovery\_report\_July\_23\_2026\_at\_3-05\_PM.csv
Location: user Downloads folder (not committed to repo)
Dimensions: 178 columns, 243 rows (243 repositories)

SOURCE PLATFORM: GitLab (confirmed by multiple signals)
  \- http\_url: [https://gitlab.com/](https://gitlab.com/)...
  \- ssh\_url: git\@gitlab.com:...
  \- GitLab-specific columns present: auto\_devops\_enabled, namespace\_kind,
    service\_desk\_enabled, mr\_draft\_count, squash\_option, snippets\_access,
    merge\_requests\_access (terminology "merge\_requests" not "pull\_requests")

KEY USAGE SIGNALS from the 243 repos:
  repos\_with\_lfs:            33  / 243  (14%)
  repos\_with\_wikis:         158  / 243  (65%)
  repos\_with\_pipelines:     107  / 243  (44%)
  repos\_with\_milestones:    156  / 243  (64%)
  repos\_with\_releases:      119  / 243  (49%)
  repos\_with\_webhooks:      142  / 243  (58%)
  repos\_with\_draft\_mrs:     131  / 243  (54%)
  repos\_with\_service\_desk:  219  / 243  (90%)  ← HIGH URGENCY HARD BLOCKER
  repos\_with\_environments:    7  / 243   (3%)
  repos\_with\_submodules:      7  / 243   (3%)
  repos\_with\_approval\_rules:  0  / 243   (0%)
  repos\_with\_packages:        0  / 243   (0%)
  repos\_with\_containers:      0  / 243   (0%)
  repos\_with\_deploy\_keys:     0  / 243   (0%)
  merge\_methods used: merge (240), ff (2), rebase\_merge (1)

FULL COLUMN → CAPABILITY MAPPING
(Maps discovery CSV columns to taxonomy capability IDs):

  lfs\_objects\_size\_bytes, lfs\_enabled, total\_lfs\_files
    → repo.lfs

  total\_wikis, wiki\_size\_bytes
    → repo.wikis

  total\_protected\_branches, protected\_branch\_names,
  total\_protected\_branches\_with\_force\_push,
  total\_protected\_branches\_with\_code\_owner\_approval,
  protected\_branch\_names
    → repo.protected\_branches, repo.branch\_rules

  total\_approval\_rules, approval\_rules\_names, approval\_rules\_min\_approvals
    → review\.approval\_rules

  approval\_rules\_code\_owner\_required
    → review\.required\_reviewers

  mr\_draft\_count
    → review\.draft\_pr

  merge\_method, squash\_option
    → review\.merge\_strategies

  remove\_source\_branch\_after\_merge,
  only\_merge\_if\_pipeline\_succeeds,
  only\_merge\_if\_all\_discussions\_resolved
    → review\.approval\_rules (merge gate signals)

  total\_pipelines, total\_pipeline\_jobs
    → cicd.pipelines

  total\_pipeline\_schedules
    → cicd.schedules

  total\_ci\_variables
    → cicd.protected\_variables

  total\_environments, total\_deployments
    → cicd.environments

  auto\_devops\_enabled
    → GitLab-source-only feature (no target equivalent on GitHub/ADO/Bitbucket)

  shared\_runners\_enabled, build\_timeout
    → cicd.runners

  ci\_config\_path
    → cicd.pipelines (custom config signal)

  total\_packages, packages\_size\_bytes, packages\_enabled
    → repo.packages

  total\_registry\_repositories, container\_registry\_size\_bytes,
  container\_registry\_enabled
    → repo.container\_registry

  service\_desk\_enabled
    → (GitLab-specific) — flags as source-only feature

  total\_milestones, milestones\_active\_count
    → pm.milestones

  issues\_confidential\_count
    → pm.confidential\_issues

  total\_labels
    → labels.color (proxy for label usage signal)

  total\_releases
    → repo.releases

  total\_tags
    → repo.releases (tags as release artifacts)

  total\_webhooks, total\_project\_integrations
    → integrations.webhooks

  total\_submodules
    → repo.submodule\_support

  total\_deploy\_keys, deploy\_keys\_read\_only\_count, deploy\_keys\_read\_write\_count
    → access.deploy\_keys

  compliance\_frameworks
    → security.compliance\_frameworks

  visibility (public/internal/private)
    → repo.visibility\_control

  snippets\_enabled, snippets\_size\_bytes
    → snippets.project\_scope, snippets.multi\_file

  total\_wikis, wiki\_titles, wiki\_formats
    → repo.wikis

  web\_based\_commit\_signing
    → repo.signed\_commits

  member\_count, owners\_count, maintainers\_count, developers\_count
    → access.team\_hierarchy

  total\_approval\_rules > 0 with approval\_rules\_code\_owner\_required
    → review\.code\_owners

PLATFORM DETECTION LOGIC (for new parse\_discovery script):
  \- URL fingerprint: http\_url or ssh\_url contains "gitlab" → gitlab
    contains "github" → github; contains "dev.azure" or "visualstudio" → azure\_devops
    contains "bitbucket" → bitbucket
  \- Column fingerprint (if URL unavailable):
    Presence of columns: auto\_devops\_enabled, namespace\_kind,
    service\_desk\_enabled, mr\_draft\_count, squash\_option → GitLab
    Presence of: workflow\_runs, actions, check\_runs → GitHub
    Presence of: build\_definition\_id, tfvc → Azure DevOps
    Presence of: pipeline\_uuid, clone\_ssh\_url → Bitbucket

\=======================================================================
SECTION 10 — WHAT NEEDS TO BE BUILT (THE FEATURE REQUEST)
\=======================================================================

THE GOAL:
User uploads a discovery report CSV → system auto-detects source platform
→ asks user for target platform → runs platform parity using KB + usage
signals from CSV + LLM → produces enriched report showing WHICH capabilities
are actually in use and HOW MANY repos will be affected.

CURRENT GAP:
Right now, the pipeline only reads from static YAML KB files.
It says "GitLab has service\_desk\_enabled" but does NOT say
"219 of 243 repos (90%) have it active — this is a critical migration blocker."
The discovery report fills this gap.

\=======================================================================
SECTION 11 — THREE IMPLEMENTATION APPROACHES
\=======================================================================

────────────────────────────────────────────────────────────────
APPROACH 1 — CSV Enrichment Layer (Minimal change, fits existing arch)
────────────────────────────────────────────────────────────────

Add ONE new pre-processing script before the existing pipeline:

  [NEW] platform\_parity\_parse\_discovery.py   ← parses CSV
            ↓
  platform\_parity\_init.py         (unchanged)
            ↓
  platform\_parity\_load\_kb.py      (unchanged)
            ↓
  platform\_parity\_compare.py      (minor: receives usage\_signals, adds urgency)
            ↓
  platform\_parity\_generate\_report.py  (receives usage\_signals in prompt)
            ↓
  platform\_parity\_export.py       (unchanged)

New script platform\_parity\_parse\_discovery.py:
  Placeholders: {{CSV\_PATH}}, {{EXECUTION\_ID}}
  Logic:
    1\. Read CSV with csv.DictReader
    2\. Detect source platform from URL pattern + column fingerprint
    3\. For each capability ID in the column mapping, aggregate:
       repo\_count (how many repos have non-zero value for that column),
       percentage, total value (e.g., total LFS bytes), example repo names
    4\. Compute urgency: >50% → HIGH, 10–50% → MEDIUM, <10% → LOW
  Output keys: source\_platform, total\_repos, usage\_signals, column\_stats

platform\_parity\_compare.py enhancements:
  \- Receives usage\_signals as additional input
  \- Attaches to each gap object: repo\_count, repo\_percentage, urgency
  \- Gaps with HIGH urgency get priority ordering in the output list

Report impact example:
  BEFORE: "Service Desk: HARD\_BLOCKER (source supported, no target equivalent)"
  AFTER:  "Service Desk: HARD\_BLOCKER — 219 of 243 repos (90%) have this enabled.
           Urgency: HIGH. This will break immediately post-migration."

PROS: Minimal change, no new dependencies, fits Temporal script pattern
CONS: Static column mapping, won't handle unknown platforms intelligently

────────────────────────────────────────────────────────────────
APPROACH 2 — Full LangChain Agent Pipeline
────────────────────────────────────────────────────────────────

Replace the generate\_report script with a LangChain chain:

  [NEW] platform\_parity\_parse\_discovery.py   (same as Approach 1)
            ↓
  [NEW] platform\_parity\_langchain\_analyze.py  (replaces steps 1–4)
            ↓
  platform\_parity\_export.py       (unchanged)

LangChain components:
  \- LangChain DocumentLoader for KB YAML files
  \- FAISS (or Chroma) vector store from KB docs
  \- RetrievalQA chain per capability: "What is GitHub's equivalent of GitLab X?"
  \- PandasDataFrameAgent for intelligent CSV column interpretation
  \- ChatBedrock LLM (from langchain\_aws)
  \- StructuredOutputParser to enforce 5-section report contract
  \- LangChain Memory for context across chain steps

New dependencies: langchain, langchain-aws, langchain-community,
                  faiss-cpu (or chromadb), pandas

PROS: Most intelligent, can reason about ambiguous columns,
      handle new platforms, pull documentation, explain WHY
CONS: Heavier deps, slower, non-deterministic, harder to debug,
      doesn't fit Temporal script pattern cleanly

────────────────────────────────────────────────────────────────
APPROACH 3 — HYBRID (RECOMMENDED ✅)
CSV-driven pre-processing + LangChain-enhanced report generation
────────────────────────────────────────────────────────────────

Adds a new Step 0 and enhances generate\_report, everything else unchanged:

  [STEP 0 - NEW] platform\_parity\_parse\_discovery.py
                 CSV → source\_platform (auto-detected)
                     → usage\_signals {cap\_id: {count, pct, urgency}}
                     → raw\_column\_stats
                     → total\_repos
                 ↓
  [STEP 1] platform\_parity\_init.py
           Receives: TARGET\_PLATFORM (user input), all existing inputs
           SOURCE\_PLATFORM now comes from parse\_discovery output
                 ↓
  [STEP 2] platform\_parity\_load\_kb.py  (unchanged)
                 ↓
  [STEP 3] platform\_parity\_compare.py
           Enhancement: receives usage\_signals, attaches repo\_count +
           repo\_percentage + urgency to each gap object
                 ↓
  [STEP 4 - ENHANCED] platform\_parity\_generate\_report.py
           LangChain chain instead of raw boto3:
             ├─ KB RAG retriever (FAISS from YAML KB docs)
             ├─ Usage context injector (from parse\_discovery signals)
             └─ ChatBedrock (Bedrock Claude) for narrative generation
                 ↓
  [STEP 5] platform\_parity\_export.py  (unchanged)

New CLI entry point: platform\_parity\_run.py
  1\. Accept CSV path as argument
  2\. Call parse\_discovery logic → auto-detect source platform
  3\. Print: "Detected source platform: GitLab. Is this correct? [Y/n]"
  4\. Prompt: "Enter target platform (github / azure\_devops / bitbucket):"
  5\. Kick off the pipeline with these inputs

New dependencies: langchain, langchain-aws, langchain-community,
                  faiss-cpu, pandas

PROS: Best of both worlds — deterministic foundation with LLM narrative;
      usage signals make reports actionable; fits Temporal workflow pattern;
      Step 0 is independently testable; LangChain blast radius is contained
      to generate\_report only

RECOMMENDED IMPLEMENTATION ORDER:
  1\. Build platform\_parity\_parse\_discovery.py first
     (pure Python, pandas, no LLM — testable immediately)
  2\. Enhance platform\_parity\_compare.py to consume usage\_signals
  3\. Replace boto3 call in generate\_report with LangChain ChatBedrock chain
  4\. Add platform\_parity\_run.py as the new CLI entry point
  5\. Update workflow/platform\_parity\_workflow\.json to add Step 0

\=======================================================================
SECTION 12 — platform\_parity\_parse\_discovery.py DESIGN (Step 0)
\=======================================================================

Script purpose:
  Parse a discovery CSV report, auto-detect the source SCM platform,
  aggregate per-capability usage signals across all repos, and output
  structured data for the downstream parity pipeline.

Placeholders:
  {{CSV\_PATH}}     — absolute path to the discovery CSV file
  {{EXECUTION\_ID}} — auto-injected

Output keys:
  source\_platform   — detected platform: "gitlab" | "github" | "azure\_devops" | "bitbucket"
  total\_repos       — int: number of rows in CSV
  usage\_signals     — dict: {capability\_id: {repo\_count, percentage, urgency, total\_value, examples}}
  column\_stats      — dict: raw per-column aggregate stats
  csv\_columns       — list: all column names found in the CSV

Platform detection logic (ordered, first match wins):
  1\. URL fingerprint from http\_url or ssh\_url column:
     "gitlab" in url → gitlab
     "github" in url → github
     "dev.azure" or "visualstudio" in url → azure\_devops
     "bitbucket" in url → bitbucket
  2\. Column fingerprint (GitLab-specific cols present):
     {auto\_devops\_enabled, namespace\_kind, service\_desk\_enabled, mr\_draft\_count}
     → gitlab
  3\. Column fingerprint (GitHub-specific):
     {workflow\_runs, check\_runs} → github
  4\. Column fingerprint (Azure DevOps-specific):
     {build\_definition\_id, tfvc\_path} → azure\_devops
  5\. If none match → raise RuntimeError with list of detected columns

Urgency thresholds:
  repo\_percentage > 50% → "HIGH"
  repo\_percentage > 10% → "MEDIUM"
  else               → "LOW"

Numeric column aggregation (for size/count columns):
  repo\_count = number of rows where column value > 0
  total\_value = sum across all rows
  examples = first 3 repo names where value > 0

Boolean column aggregation:
  repo\_count = number of rows where value is "True" or "true" or "1"

\=======================================================================
SECTION 13 — WORKFLOW DEFINITION UPDATE (after adding Step 0)
\=======================================================================

The workflow JSON needs a new first step:

{
  "name": "platform\_parity\_check",
  "steps": [
    {
      "name": "platform\_parity\_parse\_discovery",
      "values": {
        "CSV\_PATH": ""
      }
    },
    {
      "name": "platform\_parity\_init",
      "values": {
        "TARGET\_PLATFORM": "",
        "OUTPUT\_FORMAT": "markdown",
        "SCOPE\_FILTER": "[]",
        "AWS\_REGION": "",
        "BEDROCK\_MODEL\_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
        "KB\_BASE\_PATH": "",
        "NO\_CACHE": false,
        "PROJECT\_ID": ""
      }
    },
    { "name": "platform\_parity\_load\_kb" },
    { "name": "platform\_parity\_compare" },
    {
      "name": "platform\_parity\_generate\_report",
      "activity\_options": {
        "start\_to\_close\_seconds": 120,
        "heartbeat\_seconds": 30,
        "retry\_policy": {
          "maximum\_attempts": 2,
          "non\_retryable\_error\_types": ["ScriptNotFoundError"]
        }
      }
    },
    { "name": "platform\_parity\_export" }
  ]
}

Note: SOURCE\_PLATFORM is now removed from init values — it comes from
parse\_discovery output via {{steps.platform\_parity\_parse\_discovery.source\_platform}}

\=======================================================================
SECTION 14 — KEY TECHNICAL DECISIONS ALREADY MADE
\=======================================================================

1\. Approach 3 (Hybrid) is the chosen path.

2\. New files to create inside platform\_parity/:
   \- scripts/platform\_parity\_parse\_discovery.py  (new Step 0)
   \- metadata/platform\_parity\_parse\_discovery.txt (metadata descriptor)
   \- platform\_parity\_run.py (new CLI entry point)

3\. Files to modify:
   \- scripts/platform\_parity\_init.py — SOURCE\_PLATFORM now reads from
     {{steps.platform\_parity\_parse\_discovery.source\_platform}}
   \- scripts/platform\_parity\_compare.py — receives usage\_signals, adds
     repo\_count/repo\_percentage/urgency to gap objects
   \- scripts/platform\_parity\_generate\_report.py — replace raw boto3 with
     LangChain ChatBedrock chain
   \- workflow/platform\_parity\_workflow\.json — add parse\_discovery as step 0
   \- test\_bedrock\_e2e.py — add optional CSV path argument, wire to
     parse\_discovery logic before running pipeline

4\. New Python dependencies to add:
   langchain>=0.2, langchain-aws, langchain-community, faiss-cpu, pandas

5\. The local test runner (test\_bedrock\_e2e.py) must still work in
   \--skip-bedrock mode without AWS credentials for CI/deterministic checks.

6\. All new .py files in scripts/ must follow the script writing rules
   in Section 2 of this document.

\=======================================================================
SECTION 15 — WHERE TO START (NEXT IMMEDIATE ACTION)
\=======================================================================

Build platform\_parity\_parse\_discovery.py first.

It is:
\- Self-contained (no LLM, no AWS, pure Python + pandas)
\- Independently testable: python platform\_parity\_parse\_discovery.py
\- The foundation that all other enhancements depend on
\- Can be tested against the real discovery CSV immediately

After that:
1\. Enhance platform\_parity\_compare.py
2\. Update platform\_parity\_init.py (remove SOURCE\_PLATFORM placeholder)
3\. Enhance platform\_parity\_generate\_report.py with LangChain
4\. Add platform\_parity\_run.py CLI entry point
5\. Update workflow JSON
6\. Update test\_bedrock\_e2e.py to accept CSV path

\=======================================================================
END OF CONTEXT DOCUMENT
\=======================================================================




Before starting the implementation, go through these 3 approaches and rate them. Tell me if there is any alternate approach which is better than these 3. I want the best approach before starting the implementation. Also, I got the 4th approach below. Go through all 4 approaches, rate and evaluate them and tell me which approach to finalize. If there is any new approach which is better than all these, tell that approach also. I want to finalize the best approach possible before starting implementation:


Yes. I would not start implementation yet. After looking at the three approaches against your actual architecture, I would change the recommendation slightly.

My rating
Approach	Architecture fit	Accuracy/control	Maintainability	Complexity	Future extensibility	Overall
1. CSV Enrichment Layer	9/10	10/10	10/10	9/10	6/10	8.8/10
2. Full LangChain Agent	5/10	6/10	5/10	3/10	10/10	5.8/10
3. Hybrid + LangChain	8/10	9/10	7/10	6/10	9/10	8.2/10
4. Recommended alternative — Deterministic Intelligence Pipeline + LLM as controlled narrator	10/10	10/10	9/10	8/10	9/10	9.4/10

I recommend Approach 4.

The important difference is that I would not make LangChain/RAG responsible for discovering or deciding parity facts.

1. What I think is wrong with the original three approaches

The biggest architectural question isn't:

"Should we use LangChain?"

It is:

"Which component is allowed to make a migration decision?"

For a migration assessment system, that distinction is extremely important.

You already have something very valuable:

                    ┌─────────────────────┐
                    │ Capability Taxonomy │
                    │ 54 canonical IDs    │
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
        Source Platform                 Target Platform
             YAML                            YAML
               │                               │
               └───────────────┬───────────────┘
                               ▼
                     Deterministic Compare

That is a strong architecture.

You shouldn't replace that deterministic decision-making with an LLM.

2. Approach 1 — CSV Enrichment Layer
Rating: 8.8/10

This is actually better than it initially looks.

The architecture is:

CSV
 │
 ▼
Parse Discovery
 │
 ▼
Usage Signals
 │
 ▼
Existing KB
 │
 ▼
Deterministic Compare
 │
 ▼
Bedrock Narrative
 │
 ▼
Report
Why I like it

It preserves the strongest property of your current system:

The facts are deterministic.

For example:

service_desk
    ↓
219 repositories
    ↓
90%
    ↓
HIGH urgency

There is no LLM interpretation involved.

Likewise:

repo.lfs
    ↓
33 repositories
    ↓
13.58%
    ↓
MEDIUM urgency

This is reproducible.

If you run the exact same CSV twice, you should get the same usage statistics.

That's extremely important for migration tooling.

Main weakness

The proposed parser has a potentially dangerous assumption:

CSV column → capability ID

Some mappings are straightforward:

lfs_enabled → repo.lfs
mr_draft_count → review.draft_pr
total_pipelines → cicd.pipelines

But others are not.

For example:

total_labels → labels.color

doesn't necessarily prove that the repositories use colored labels.

Similarly:

total_approval_rules > 0
    + approval_rules_code_owner_required
    → review.code_owners

is a more sophisticated inference.

And:

service_desk_enabled

doesn't have a canonical capability ID in your current taxonomy.

So Approach 1 needs a better evidence model, not just a column mapping.

That's the first thing I would change.

3. Approach 2 — Full LangChain Agent
Rating: 5.8/10

I would not choose this.

The proposed architecture:

CSV
 │
 ▼
LangChain Agent
 │
 ├── CSV reasoning
 ├── KB retrieval
 ├── capability interpretation
 ├── parity reasoning
 ├── migration reasoning
 └── report generation

looks intelligent.

But for your use case, that's actually the problem.

Imagine:

GitLab service desk
219 / 243 repositories
90%

You don't want an agent deciding whether that constitutes a blocker.

You already know the facts.

The agent shouldn't be allowed to say:

"Service Desk may have an equivalent through GitHub Issues."

unless your curated KB explicitly says that.

Otherwise you've introduced a hallucination path into a migration assessment system.

Another problem

Your current Temporal pipeline is intentionally modular:

init
 ↓
load_kb
 ↓
compare
 ↓
generate_report
 ↓
export

Replacing that with:

LangChain agent

creates a much larger blast radius.

Debugging becomes:

Why did the agent produce this conclusion?

instead of:

Which deterministic rule produced this classification?

The latter is much better for enterprise migration tooling.

4. Approach 3 — Hybrid
Rating: 8.2/10

This is good.

Much better than Approach 2.

The important idea is:

Deterministic
     +
LLM

rather than:

LLM everything

That's the correct direction.

However, I would change one major thing.

You proposed:

generate_report
      ↓
LangChain
      ↓
FAISS RAG
      ↓
Claude

I don't think you actually need FAISS for the first version.

Your KB is:

capability_taxonomy.yaml
known_gaps.yaml
gitlab.yaml
github.yaml
azure_devops.yaml
bitbucket.yaml

That's only a relatively small, highly structured dataset.

This isn't a huge document corpus where semantic retrieval is obviously necessary.

You can construct highly targeted context such as:

CAPABILITY:
review.draft_pr

SOURCE:
GitLab
supported: true
notes: ...

TARGET:
GitHub
supported: true
notes: ...

KNOWN GAP:
...

USAGE:
131 / 243 repositories
53.91%
HIGH

and send exactly that to Claude.

That is arguably better grounding than throwing the whole KB into a vector database.

5. The better architecture: Approach 4

I would build this:

Deterministic Intelligence Pipeline + Controlled LLM Narrator

The architecture becomes:

                     DISCOVERY CSV
                           │
                           ▼
              ┌─────────────────────────┐
              │  STEP 0                 │
              │  Discovery Parser       │
              │                         │
              │  • Detect platform      │
              │  • Validate CSV         │
              │  • Map evidence         │
              │  • Aggregate usage      │
              └────────────┬────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ Usage Evidence   │
                 │                 │
                 │ count           │
                 │ percentage      │
                 │ totals          │
                 │ examples        │
                 │ evidence type   │
                 │ confidence      │
                 └────────┬─────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │ Existing KB             │
              │                         │
              │ Taxonomy                │
              │ Source platform         │
              │ Target platform         │
              │ Known gaps              │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │ STEP 3                  │
              │ Deterministic Compare   │
              │                         │
              │ Capability parity       │
              │ + usage evidence        │
              │ + known gaps             │
              │ + behavioral diffs      │
              └────────────┬────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ PARITY FACTS     │
                 │                 │
                 │ BLOCKER         │
                 │ PARTIAL        │
                 │ BEHAVIORAL     │
                 │ SEAMLESS       │
                 │ NOT COVERED    │
                 │ USAGE IMPACT   │
                 │ RISK            │
                 └────────┬─────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │ STEP 4                  │
              │ Controlled LLM          │
              │                         │
              │ Claude / Bedrock        │
              │                         │
              │ ONLY explains facts    │
              │ NEVER decides facts    │
              └────────────┬────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ FINAL REPORT     │
                 └──────────────────┘

This is what I would implement.

6. The key architectural principle

I'd establish this rule:

LLM can explain, summarize and prioritize presentation — but cannot create or alter parity facts.

So:

Deterministic layer decides
Is GitLab feature X supported?
Is GitHub feature X supported?
Is there a workaround?
Is there a known gap?
How many repositories use it?
What percentage use it?
What is the urgency?
What is the risk?
LLM decides only
How should this be explained to a migration team?

What should the executive summary say?

What migration implications should be highlighted
based strictly on the supplied facts?

How can several related gaps be presented coherently?

That's a very strong separation of responsibilities.

7. I would also change your usage_signals model

Your current design says:

usage_signals:
  capability_id:
    repo_count:
    percentage:
    urgency:
    total_value:
    examples:

I'd make it slightly richer.

Something conceptually like:

usage_signals:
    capability_id:
        repo_count
        percentage
        urgency
        total_value
        examples

        evidence:
            source_columns
            detection_rule
            value_type

        confidence

For example:

review.draft_pr:
    repo_count: 131
    percentage: 53.91
    urgency: HIGH

    evidence:
        source_columns:
            - mr_draft_count
        detection_rule: "value > 0"
        value_type: numeric

    confidence: HIGH

This is extremely useful.

Now the report can answer:

"Why does the system believe 131 repositories use draft PRs?"

Because the evidence is:

mr_draft_count > 0

That's much more auditable.

8. Add an "evidence" layer

This is the biggest improvement I'd make over all three original approaches.

Instead of:

CSV → capability

think:

CSV
 ↓
Raw observations
 ↓
Evidence rules
 ↓
Capability usage

For example:

Raw CSV

mr_draft_count = 4

becomes:

Evidence:

capability = review.draft_pr
source_column = mr_draft_count
rule = > 0
observed_value = 4

then:

Usage:

review.draft_pr
131 / 243
53.91%
HIGH

This makes the system explainable.

9. Don't use the LLM to detect the platform

Your current proposed approach says:

URL fingerprint
      ↓
column fingerprint
      ↓
platform

Good.

Keep it deterministic.

I would make it even stronger:

URL evidence
     +
column evidence
     +
required fingerprint score
     ↓
platform detection

For example:

GitLab

URL evidence:       +100
GitLab columns:     +20 each
GitHub columns:     -20 each
Azure columns:      -20 each

Then produce:

detected_platform: gitlab
confidence: HIGH
evidence:
  url_matches: 243
  gitlab_columns: 5

If confidence is ambiguous:

RuntimeError:
Unable to confidently detect source platform.
Detected signals:
...

Don't ask Claude to resolve it.

10. I would NOT make the user manually confirm the platform

Your proposed CLI has:

Detected source platform: GitLab.
Is this correct? [Y/n]

That's okay for an interactive local CLI.

But it doesn't fit particularly well with a Temporal workflow.

Temporal shouldn't depend on:

stdin

Instead:

CLI
CSV
 ↓
detect platform
 ↓
display detection
 ↓
ask target platform
 ↓
start workflow
Temporal
CSV_PATH
TARGET_PLATFORM

The workflow itself remains non-interactive.

This separation is cleaner.

11. I would keep LangChain optional

This is another important change.

I wouldn't make:

LangChain = mandatory dependency for parity

Instead:

                 generate_report
                       │
              ┌────────┴────────┐
              │                 │
          deterministic       LLM mode
             mode              mode
              │                 │
          template          Bedrock
              │                 │
              └────────┬────────┘
                       ▼
                    report

That gives you:

CI mode
--skip-bedrock

No AWS.

No LangChain.

No LLM.

Fully deterministic.

Production mode
Bedrock enabled

Narrative generation.

This preserves one of the best properties of your existing system.

12. Do you actually need LangChain?

Not necessarily.

This is where I disagree most with the original Approach 3.

You currently have:

Bedrock Claude

already working.

You could simply improve:

generate_report.py

with:

deterministic facts
+
structured prompt
+
Bedrock

without introducing:

LangChain
FAISS
Chroma
PandasDataFrameAgent
Memory
RetrievalQA

That's a lot of machinery.

And importantly, LangChain does not automatically make the system more accurate.

For your particular dataset, structured retrieval from your YAML files can be much more precise than semantic retrieval.

13. When I WOULD introduce RAG

There is a future scenario where I'd recommend it.

Suppose your KB grows from:

54 capabilities
4 platforms

to:

1,000+ capabilities
20 platforms
hundreds of migration patterns
thousands of documentation records

Then:

Bedrock Knowledge Base / RAG

starts becoming much more attractive.

AWS itself recommends Bedrock Knowledge Bases as a managed RAG option, handling ingestion, indexing and retrieval rather than requiring you to build that infrastructure yourself.

And Bedrock Knowledge Bases can return retrieved source information and citations, which is useful for traceability.

But your current 54-capability YAML KB isn't large enough to justify that complexity.

14. An even better future architecture

I'd therefore design the system so it can evolve like this:

Phase 1 — Now
YAML KB
+
CSV evidence
+
deterministic engine
+
Bedrock
Phase 2 — Larger KB
Structured KB
+
Bedrock Knowledge Base
+
deterministic engine
+
Bedrock narrative
Phase 3 — Advanced migration intelligence
                    ┌─────────────────┐
                    │ Discovery Data  │
                    └────────┬────────┘
                             │
              ┌──────────────┴─────────────┐
              ▼                            ▼
       Deterministic               Knowledge Retrieval
       Evidence Engine             / Bedrock KB
              │                            │
              └──────────────┬─────────────┘
                             ▼
                     Migration Analyzer
                             │
                  ┌──────────┴─────────┐
                  ▼                    ▼
             Facts Engine         LLM Narrator
                  │                    │
                  └─────────┬──────────┘
                            ▼
                     Migration Report

That gives you a path toward a genuinely intelligent migration assistant without compromising the deterministic core.

15. My final recommendation

If I were reviewing this architecture as a production engineering design, I'd choose:

🥇 Approach 4 — Deterministic Intelligence + Controlled LLM

9.4/10

Use:

CSV parser
deterministic platform detection
deterministic column → capability evidence mapping
deterministic usage aggregation
existing YAML KB
deterministic parity engine
deterministic risk/urgency calculation
Bedrock Claude for narrative only
optional LangChain/RAG later
Not this:
CSV → Agent → RAG → LLM → decision
And not even this initially:
CSV → deterministic → LangChain/FAISS → LLM
Instead:
CSV
 ↓
Evidence Extraction
 ↓
Usage Signals
 ↓
KB
 ↓
Deterministic Parity Engine
 ↓
Deterministic Migration Facts
 ↓
Claude
 ↓
Narrative Report
16. Revised implementation plan

I would therefore change your implementation order to:

Phase 1 — Foundation

1. platform_parity_parse_discovery.py

Build:

CSV
 ↓
platform detection
 ↓
column validation
 ↓
evidence extraction
 ↓
usage aggregation
Phase 2 — Evidence model

2. Enhance capability usage representation

Add:

repo_count
percentage
urgency
total_value
examples
evidence
confidence
Phase 3 — Deterministic comparison

3. Modify platform_parity_compare.py

Produce:

gap
+
usage
+
evidence
+
urgency
+
migration impact
Phase 4 — Init

4. Modify platform_parity_init.py

Source platform comes from Step 0.

Phase 5 — Report generation

5. Improve platform_parity_generate_report.py

Initially:

structured deterministic context
             ↓
        Bedrock Claude

Do not introduce LangChain/FAISS yet.

Phase 6 — CLI

6. platform_parity_run.py

Interactive wrapper only.

Phase 7 — Workflow

7. Add Step 0 to Temporal workflow.

Phase 8 — Testing

8. Extend test_bedrock_e2e.py

Test:

CSV → detection → usage → parity

with:

--skip-bedrock

first.

Then:

--with-bedrock
One particularly important change

I would also not hard-code the CSV → capability mapping entirely inside Python.

Your current:

capability_taxonomy.yaml

is already the source of truth.

I'd consider adding a separate section/file for discovery evidence rules, for example conceptually:

discovery_mapping.yaml

Then:

CSV column
     ↓
evidence rule
     ↓
capability

becomes configuration rather than Python logic.

That gives you:

Taxonomy = What capabilities exist

and:

Discovery mapping = How we detect those capabilities in real repositories

That separation will become extremely valuable when you add GitHub, Azure DevOps and Bitbucket discovery reports.

Bottom line

Do not implement Approach 3 exactly as currently written.

Your existing architecture is already fundamentally good. The best improvement is to add a deterministic evidence/usage layer, not to make the system more agentic.

My recommendation is:

Approach 4: Deterministic Evidence + Deterministic Parity + Controlled Bedrock Narrative, with RAG/LangChain kept as a future extension.

This gives you the best combination of accuracy, auditability, reproducibility, enterprise suitability, testability, and future extensibility.

And importantly, it keeps the core migration answer explainable:

WHY is this a blocker?
        ↓
Known gap + target capability data

WHY is it urgent?
        ↓
219 / 243 repositories = 90%

WHERE did that number come from?
        ↓
service_desk_enabled column

WHAT does the LLM contribute?
        ↓
Clear human-readable explanation

That's the architecture I would be comfortable implementing for this project.







You said:
Ok. Let's finalize approach 4.1.

Can you give me a complete detailed implementation plan for it. And also the corresponding prompt which I can give in copilot which makes it to implement exactly as desired
Copilot said:
Yes. If you're committing engineering time, I would freeze the design at Approach 4.1 and avoid introducing LangChain/FAISS initially.

The biggest reason is that your system is already fundamentally strong:




Plain Text
Discovery Data
     +
Knowledge Base
     +
Deterministic Rules
You only need to add:




Plain Text
Evidence Layer
not an Agent Layer.

Final Architecture (Recommended)



Plain Text
                ┌──────────────────────────┐
                │ Discovery CSV            │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Step 0                   │
                │ Parse Discovery          │
                │                          │
                │ Platform Detection       │
                │ Evidence Extraction      │
                │ Usage Aggregation        │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Usage Signals            │
                │ Evidence Metadata        │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Step 1                   │
                │ platform_parity_init     │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Step 2                   │
                │ Load KB                  │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Step 3                   │
                │ Compare                  │
                │                          │
                │ KB Facts                 │
                │ + Usage Signals          │
                │ + Evidence              │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Parity Facts             │
                │                          │
                │ Hard Blockers            │
                │ Behavioral Differences   │
                │ Partial Support          │
                │ Seamless                 │
                │ Risk                     │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Step 4                   │
                │ Bedrock Claude           │
                │                          │
                │ Narrative Only           │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Step 5                   │
                │ Export                   │
                └──────────────────────────┘

Show more lines
Implementation Plan
Phase 1 — Discovery Evidence Framework
New File



Plain Text
capability_kb/discovery_mapping.yaml
Purpose:

Move all CSV→Capability mapping logic out of Python.

Current design:




Python
COLUMN_TO_CAPABILITY = {...}
Recommended:




YAML
repo.lfs:
  columns:
    - lfs_enabled
    - total_lfs_files
    - lfs_objects_size_bytes
 
  detection_rule: any_positive
 
  confidence: HIGH
 
review.draft_pr:
  columns:
    - mr_draft_count
 
  detection_rule: any_positive
 
  confidence: HIGH
 
cicd.pipelines:
  columns:
    - total_pipelines
 
  detection_rule: any_positive
 
  confidence: HIGH

Show more lines
Benefits:

Configuration driven
Easier maintenance
Easier future GitHub discovery support
No code changes for mapping updates
Phase 2 — Step 0
New Script



Plain Text
scripts/platform_parity_parse_discovery.py
Inputs



Plain Text
CSV_PATH
EXECUTION_ID
Responsibilities
1 Platform Detection
Use score-based detection.

Example:




Plain Text
GitLab URL found
+100
 
GitLab column found
+20
 
GitHub column found
-20
Output:




JSON
{
  "source_platform": "gitlab",
  "platform_confidence": "HIGH",
  "platform_evidence": {
    "url_matches": 243,
    "gitlab_columns": 5
  }
}
2 CSV Validation
Validate:




Plain Text
CSV exists
CSV readable
Header exists
Rows exist
Mapped columns exist
3 Evidence Extraction
Transform:




Plain Text
mr_draft_count=7
into




JSON
{
  "capability": "review.draft_pr",
  "column": "mr_draft_count",
  "rule": "value > 0",
  "observed_value": 7
}
4 Usage Aggregation
Calculate:




Plain Text
repo_count
percentage
total_value
examples
5 Confidence Calculation
Example:




Plain Text
Explicit feature column
HIGH
 
Derived inference
MEDIUM
 
Weak proxy
LOW
Outputs



JSON
{
  "source_platform": "",
  "platform_confidence": "",
  "total_repos": 243,
 
  "usage_signals": {},
 
  "column_stats": {},
 
  "csv_columns": [],
 
  "evidence_summary": {}
}
Phase 3 — Usage Signal Model
Current proposal:




JSON
{
  "repo_count": 219
}
Replace with:




JSON
{
  "repo_count": 219,
 
  "percentage": 90.12,
 
  "urgency": "HIGH",
 
  "confidence": "HIGH",
 
  "total_value": 0,
 
  "examples": [
    "repo-a",
    "repo-b",
    "repo-c"
  ],
 
  "evidence": {
    "columns": [
      "service_desk_enabled"
    ],
 
    "detection_rule": "boolean_true",
 
    "value_type": "boolean"
  }
}

Show more lines
Phase 4 — Modify Init Script
Change:




Plain Text
SOURCE_PLATFORM placeholder
to:




Plain Text
{{steps.platform_parity_parse_discovery.source_platform}}
Remove manual source input.

Keep:




Plain Text
TARGET_PLATFORM
as the only platform selection.

Phase 5 — Compare Enhancements
Modify



Plain Text
platform_parity_compare.py
Current Gap Object



JSON
{
  "capability_id": "",
  "classification": ""
}
New Gap Object



JSON
{
  "capability_id": "",
 
  "classification": "",
 
  "repo_count": 219,
 
  "repo_percentage": 90.12,
 
  "urgency": "HIGH",
 
  "confidence": "HIGH",
 
  "examples": [
    "repo1",
    "repo2"
  ],
 
  "evidence": {
      ...
  }
}

Show more lines
Add Risk Weighting
Current:




Plain Text
Hard blocker exists
→ Critical
New:




Plain Text
Hard blocker
+
90% usage
=
Critical
 
Hard blocker
+
1% usage
=
Medium
More intelligent.

Phase 6 — Report Generation
Keep Existing Bedrock
Do NOT introduce:




Plain Text
LangChain
FAISS
Agents
Memory
RetrieverQA
yet.

Change Prompt Inputs
Provide Claude:




JSON
{
  "parity_facts": {},
  "usage_signals": {},
  "risk": {}
}
Important System Rule
Add:




Plain Text
The supplied facts are authoritative.
 
Do not invent capabilities.
 
Do not infer unsupported capabilities.
 
Do not alter classifications.
 
Do not introduce workarounds not present in input.
 
Your responsibility is explanation only.
This is critical.

New Report Content
Example:

Instead of:




Plain Text
Service Desk
Hard Blocker
Generate:




Plain Text
Service Desk
 
Classification:
HARD_BLOCKER
 
Impact:
 
219 of 243 repositories
(90.1%)
 
Urgency:
HIGH
 
Evidence:
service_desk_enabled=true
 
Migration Impact:
This feature is heavily used and requires
replacement before migration.

Show more lines
Phase 7 — New CLI
New File



Plain Text
platform_parity_run.py
Responsibilities:




Plain Text
Ask for CSV path
 
Detect source
 
Display evidence
 
Ask target platform
 
Execute pipeline
Example:




Plain Text
Detected Platform:
GitLab
 
Confidence:
HIGH
 
Evidence:
243 GitLab URLs
5 GitLab-specific columns
 
Target Platform:
github
Then run workflow.

Phase 8 — Workflow Update
Add new Step 0.




Plain Text
parse_discovery
↓
init
↓
load_kb
↓
compare
↓
generate_report
↓
export
Phase 9 — Testing
Unit Tests
Platform Detection
Inputs:




Plain Text
GitLab CSV
GitHub CSV
ADO CSV
Bitbucket CSV
Expected:




Plain Text
Correct platform
Correct confidence
Evidence Extraction
Input:




Plain Text
mr_draft_count=5
Expected:




Plain Text
review.draft_pr
Usage Aggregation
Verify:




Plain Text
count
percentage
examples
Compare
Verify:




Plain Text
usage attached to gaps
Report
Verify:




Plain Text
No capability invented
No classification modified
Future Version (Not Now)
When KB reaches:




Plain Text
10+ platforms
1000+ capabilities
large documentation corpus
Then add:




Plain Text
Bedrock Knowledge Base
not FAISS.

Future architecture:




Plain Text
Deterministic Engine
        +
Bedrock Knowledge Base
        +
Claude
But not in Phase 1.

Copilot Implementation Prompt
Use the prompt below as-is:




Plain Text
Implement Approach 4.1 for the platform_parity module.
 
ARCHITECTURAL RULES
 
1. Deterministic components own ALL migration facts.
2. LLM may ONLY explain supplied facts.
3. LLM must never:
   - create new capabilities
   - change classifications
   - infer workarounds
   - alter risk levels
4. Discovery evidence must be traceable and auditable.
5. Follow all script-writing rules from guide_to_write_scripts.md.
 
IMPLEMENTATION GOALS
 
Create a deterministic evidence layer between discovery CSV input and the parity engine.
 
PHASE 1
 
Create:
 
capability_kb/discovery_mapping.yaml
 
Move CSV column-to-capability mappings into this YAML file.
 
Each capability should support:
 
- columns
- detection_rule
- confidence
- value_type
 
Example:
 
review.draft_pr:
  columns:
    - mr_draft_count
  detection_rule: any_positive
  confidence: HIGH
  value_type: numeric
 
PHASE 2
 
Create:
 
scripts/platform_parity_parse_discovery.py
 
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
 
Responsibilities:
 
1. Validate CSV.
2. Detect source platform using deterministic scoring.
3. Load discovery_mapping.yaml.
4. Extract capability evidence.
5. Aggregate usage statistics.
6. Produce auditable evidence objects.
 
Platform detection priority:
 
- URL fingerprint
- Column fingerprint
- Score-based confidence
 
If confidence is ambiguous:
raise RuntimeError.
 
PHASE 3
 
Extend usage_signals structure to include:
 
{
  repo_count,
  percentage,
  urgency,
  confidence,
  total_value,
  examples,
  evidence: {
      columns,
      detection_rule,
      value_type
  }
}
 
Urgency:
 
>50% = HIGH
>10% = MEDIUM
otherwise LOW
 
PHASE 4
 
Modify platform_parity_init.py.
 
SOURCE_PLATFORM must come from:
 
{{steps.platform_parity_parse_discovery.source_platform}}
 
Remove user-provided source platform input.
 
PHASE 5
 
Modify platform_parity_compare.py.
 
Attach usage_signals metadata to every capability result.
 
Every gap object must include:
 
repo_count
repo_percentage
urgency
confidence
examples
evidence
 
Maintain deterministic classification logic.
 
PHASE 6
 
Modify platform_parity_generate_report.py.
 
Keep boto3/Bedrock architecture.
 
Do NOT introduce:
- LangChain
- FAISS
- Agents
- Memory
- RetrievalQA
 
Provide structured parity facts and usage evidence to Claude.
 
Add prompt rules:
 
"The provided facts are authoritative.
Do not invent capabilities.
Do not alter classifications.
Do not introduce unsupported workarounds."
 
Claude should only generate narrative.
 
PHASE 7
 
Create:
 
platform_parity_run.py
 
Responsibilities:
 
- accept CSV path
- run platform detection
- display confidence and evidence
- prompt for target platform
- start workflow
 
Workflow remains non-interactive.
 
PHASE 8
 
Update workflow/platform_parity_workflow.json
 
Add Step 0:
 
platform_parity_parse_discovery
 
before platform_parity_init.
 
PHASE 9
 
Update test_bedrock_e2e.py
 
Add optional CSV path support.
 
Ensure --skip-bedrock mode remains fully deterministic and works without AWS credentials.
 
PHASE 10
 
Create tests covering:
 
- platform detection
- evidence extraction
- usage aggregation
- compare enrichment
- report generation
 
Success Criteria:
 
- deterministic parity results unchanged
- discovery usage statistics attached to parity findings
- generated reports show repository impact and urgency
- full audit trail exists from CSV column -> evidence -> capability -> parity finding
- no LangChain introduced
- no parity decision delegated to LLM

Show more lines
This is the architecture I would lock before writing a single line of implementation code.





You said:
Sorry.But i need to use LangChain 
Copilot said:
If LangChain is a hard requirement, then I would still not choose the original Approach 3 exactly as written. I'd create a revised architecture:

✅ Approach 4.2 (Recommended if LangChain is Mandatory)
Deterministic Evidence Engine + Deterministic Parity Engine + LangChain-Orchestrated Bedrock Narrator

This keeps all migration decisions deterministic while using LangChain where it actually adds value.

What I Would NOT Do
I would not use LangChain for:

Platform detection
Capability detection
Gap classification
Risk calculation
Workaround determination
Behavioral difference determination
Those are already solved better by your KB and deterministic rules.

This would be a bad pattern:




Plain Text
CSV
 ↓
LangChain Agent
 ↓
"Reasoning"
 ↓
Gap Classification
That effectively makes the LLM the migration engine.

What I WOULD Use LangChain For
Use LangChain as an orchestration framework around Claude.




Plain Text
Discovery CSV
        ↓
Parse Discovery
        ↓
Usage Evidence
        ↓
Load KB
        ↓
Deterministic Compare
        ↓
Parity Facts
        ↓
LangChain
        ↓
Claude
        ↓
Report

Show more lines
LangChain becomes the presentation layer, not the decision layer.

Revised Architecture



Plain Text
Step 0
platform_parity_parse_discovery.py
        ↓
Usage Signals
        ↓
Step 1
platform_parity_init.py
        ↓
Step 2
platform_parity_load_kb.py
        ↓
Step 3
platform_parity_compare.py
        ↓
Deterministic Facts
        ↓
Step 4
platform_parity_generate_report.py
        ↓
LangChain Pipeline
        ↓
Bedrock Claude
        ↓
Markdown Report
        ↓
Step 5
platform_parity_export.py

Show more lines
Where LangChain Should Be Introduced
Only inside:




Plain Text
platform_parity_generate_report.py
Nowhere else.

This minimizes blast radius.

Recommended LangChain Components
Use
ChatBedrock



Python
from langchain_aws import ChatBedrock
Purpose:




Plain Text
Claude access through LangChain
PromptTemplate



Python
from langchain.prompts import PromptTemplate
Purpose:

Build strongly structured prompts.

RunnableSequence



Python
prompt
    |
model
    |
parser
Much cleaner than raw boto3.

PydanticOutputParser
Force report structure.

Example:




Python
ExecutiveSummary
HardBlockers
BehavioralDiffs
Seamless
Coverage
Document Objects
Convert KB content to documents.




Python
Document(
    page_content=...
)
What I Would NOT Use
Not yet:




Plain Text
Agents
Tools
Memory
Graph
ReAct
CSV Agent
DataFrame Agent
No need.

Should You Use FAISS?
For the current KB:




Plain Text
54 capabilities
4 platforms
known_gaps.yaml
My answer:

No.

The KB is too small.

You already know precisely which capability is being discussed.

Retrieval adds complexity.

Better Alternative
Build contextual payloads directly.

Example:




JSON
{
  "capability": "review.draft_pr",
 
  "source_support": true,
 
  "target_support": true,
 
  "known_gap": false,
 
  "usage": {
      "repos": 131,
      "percentage": 53.9,
      "urgency": "HIGH"
  }
}

Show more lines
Send this to Claude.

Much more reliable than vector search.

If You Really Want RAG
Then use RAG only for documentation enrichment.

Not for decision making.

Example:




Plain Text
Deterministic Compare
            ↓
Need supporting docs?
            ↓
Retriever
            ↓
Claude
Never:




Plain Text
Retriever
    ↓
Claude
    ↓
Gap Classification
The Best LangChain Design
I would build:




Plain Text
LangChain Chain 1
----------------
 
Deterministic Facts
       ↓
Prompt Builder
       ↓
Claude
       ↓
Narrative JSON
 
 
LangChain Chain 2
----------------
 
Narrative JSON
       ↓
Markdown Formatter
       ↓
Final Report

Show more lines
This gives:

deterministic inputs
deterministic sections
flexible language generation
Recommended New Files
New



Plain Text
scripts/platform_parity_parse_discovery.py
New



Plain Text
capability_kb/discovery_mapping.yaml
New



Plain Text
platform_parity_run.py
Modified Files



Plain Text
platform_parity_init.py



Plain Text
platform_parity_compare.py



Plain Text
platform_parity_generate_report.py



Plain Text
workflow/platform_parity_workflow.json



Plain Text
test_bedrock_e2e.py
Final Recommendation
Since you've stated that LangChain must be used, I would finalize:

✅ Approach 4.2
Deterministic Evidence Engine + Deterministic Parity Engine + LangChain-Orchestrated Bedrock Reporting

Use LangChain for:

Prompt orchestration
Structured output parsing
Claude integration
Optional future RAG
Do not use LangChain for:

parity decisions
capability detection
platform detection
risk calculation
workaround determination
That gives you the benefits of LangChain while preserving the strongest part of your current design: fully explainable, auditable, deterministic migration intelligence.





You said:
explain in simple words what we are doing and how we want to do it.
Copilot said:
Sure. In very simple terms, here's what we're actually building.

Today's Problem
Currently your platform parity system works like this:




Plain Text
GitLab YAML
      +
GitHub YAML
      +
Known Gaps YAML
      ↓
Compare
      ↓
Report
Example:




Plain Text
GitLab Service Desk = Supported
GitHub Service Desk = Not Supported
 
Result:
HARD_BLOCKER
This is technically correct.

But it doesn't answer the most important migration question:

"How many repositories actually use Service Desk?"

Maybe:




Plain Text
1 repo uses it
or




Plain Text
219 repos use it
Those are very different situations.

Today the system has no idea.

What New Information We Have
We now have the Discovery CSV.

The CSV contains real usage data from the customer's GitLab environment.

Example:




Plain Text
243 repositories
And:




Plain Text
service_desk_enabled = true
for 219 repositories
Meaning:




Plain Text
90% of repositories use Service Desk
Now we can say:




Plain Text
Service Desk is a HARD_BLOCKER
 
AND
 
219 repositories are affected.
This makes the report much more useful.

What We Want To Build
We want to combine:




Plain Text
Static Knowledge Base
with




Plain Text
Real Usage Data
to produce:




Plain Text
Intelligent Migration Report
High-Level Flow
New flow:




Plain Text
Discovery CSV
      ↓
Analyze Usage
      ↓
Find Which Features Are Actually Used
      ↓
Load Platform KB
      ↓
Compare Source vs Target
      ↓
Calculate Impact
      ↓
Generate Report
Step 1: Parse Discovery CSV
New Script:




Plain Text
platform_parity_parse_discovery.py
Its job:

Detect Source Platform
Example:




Plain Text
gitlab.com URLs found
auto_devops_enabled column found
service_desk_enabled column found
Conclusion:




Plain Text
Source Platform = GitLab
Find Feature Usage
Example:




Plain Text
mr_draft_count > 0
means:




Plain Text
Draft Merge Requests are used
Example:




Plain Text
total_pipelines > 0
means:




Plain Text
CI/CD Pipelines are used
Example:




Plain Text
service_desk_enabled = true
means:




Plain Text
Service Desk is used
The script counts usage across all repositories.

Step 2: Build Usage Signals
The parser creates something like:




JSON
{
  "service_desk": {
    "repo_count": 219,
    "percentage": 90.12,
    "urgency": "HIGH"
  },
 
  "review.draft_pr": {
    "repo_count": 131,
    "percentage": 53.9,
    "urgency": "HIGH"
  }
}
Now we know:




Plain Text
WHAT feature is used
HOW MANY repos use it
HOW IMPORTANT it is
Step 3: Existing KB Still Does The Comparison
This part remains deterministic.

Example:




Plain Text
GitLab Service Desk
     Supported
 
GitHub Service Desk
     Unsupported
Result:




Plain Text
HARD_BLOCKER
Nothing changes here.

The KB still remains the source of truth.

Step 4: Attach Usage Information
Before:




Plain Text
Service Desk
HARD_BLOCKER
After:




Plain Text
Service Desk
HARD_BLOCKER
 
Usage:
219 of 243 repositories
 
Impact:
90.1%
 
Urgency:
HIGH
Now leadership immediately understands the risk.

Step 5: LangChain Comes In
This is important.

LangChain is not deciding migration facts.

We do NOT want:




Plain Text
LangChain decides blocker
LangChain decides risk
LangChain decides workaround
Instead:




Plain Text
Deterministic Engine
      ↓
Produces Facts
      ↓
LangChain
      ↓
Claude
      ↓
Human-Friendly Explanation
Example
Deterministic engine produces:




JSON
{
  "capability": "service_desk",
  "classification": "HARD_BLOCKER",
  "repo_count": 219,
  "percentage": 90.1
}
Claude receives this.

Claude writes:




Plain Text
Service Desk represents a significant migration challenge.
 
219 of the 243 repositories (90.1%)
currently rely on Service Desk functionality.
 
Because GitHub does not provide an equivalent
capability, teams should plan replacement
processes before migration.
Notice:

Claude didn't decide anything.

Claude only explained.

Why We Need LangChain
Technically we could call Bedrock directly.

But LangChain gives us:

Structured Prompting



Plain Text
Facts
    ↓
Prompt Template
    ↓
Claude
Structured Outputs
We can enforce:




Plain Text
Executive Summary
Hard Blockers
Behavioral Differences
Seamless Migrations
Coverage Report
every time.

Future RAG
Later if KB becomes huge:




Plain Text
1000+ capabilities
many platforms
migration history
documentation
we can easily add:




Plain Text
Retriever
Vector DB
Knowledge Base
through LangChain.

What LangChain Will NOT Do
We do NOT want:




Plain Text
CSV
 ↓
Agent
 ↓
Guess capabilities
 ↓
Guess blockers
 ↓
Report
That's dangerous.

Migration reports must be auditable.

Final System



Plain Text
Discovery CSV
      ↓
Parse Discovery
      ↓
Usage Signals
      ↓
Platform KB
      ↓
Deterministic Comparison
      ↓
Migration Facts
      ↓
LangChain
      ↓
Claude
      ↓
Final Report

Show more lines
In One Sentence
We are enhancing the existing parity engine by feeding it real repository usage data from the discovery CSV, letting the deterministic engine calculate migration facts and impact, and then using LangChain + Claude only to turn those facts into a professional human-readable migration report.
