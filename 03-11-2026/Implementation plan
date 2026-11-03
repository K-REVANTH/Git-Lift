# Implementation Plan: Bitbucket to GHEC Initial Fast Discovery Phase

## Document Metadata
- **Project**: PACE SCM Migration Tooling (GitLift)
- **Phase**: Initial Fast Discovery
- **Source Platform**: Bitbucket Cloud (REST API v2.0) & Bitbucket Data Center / Server (REST API v1.0)
- **Target Platform**: GitHub Enterprise Cloud with Enterprise Managed Users (GHEC EMU)
- **Target Repository**: `pace-scm-migration-scripts/bitbucket_to_ghec/`
- **Execution Engine**: Temporal Workflow Engine / PACE Script Executor Worker Pods

---

## 1. Overview & Architecture Summary

### 1.1 Objective & Scope Boundaries
The **Initial Fast Discovery** phase is the initial operational gate of the Bitbucket-to-GHEC migration pipeline. Its primary objective is to rapidly interrogate Bitbucket instances (Cloud and Data Center), establish authenticated sessions, catalog structural hierarchies (workspaces/projects/repositories), harvest repository-level baseline metadata and git physical metrics, validate target GHEC prerequisites, and persist a canonical discovery snapshot into both relational storage and distributed filesystems.

- **In Scope**:
  - Dual-variant source authentication (Bitbucket Cloud App Passwords/OAuth 2.0/API Tokens and Bitbucket DC Personal/HTTP Access Tokens).
  - Target GHEC pre-flight authentication and organization validation.
  - Structural entity discovery: Workspaces (Cloud), Projects (Cloud/DC), Personal Repositories (`~user` in DC), and Repositories.
  - High-performance repository-level metadata harvesting (identity, slug, description, visibility, size, default branch, timestamps, fork status, language).
  - Lightweight metric queries: branch counts, tag counts, pull request counts, milestone/version counts, deployment/environment counts.
  - Bare Git clone introspection: `git-sizer` maximum blob size, submodule extraction across all branches, Git notes (`refs/notes/*`), large file threshold analysis (50MB/100MB), default-branch size-distribution histogram (7 buckets).
  - Centralized audit persistence: `migration_repo_audit`, `discovery_documents`, `migration_documents` tables, and shared EFS JSON caching (`{safe_id}_get_project_details.json`).
  - Workspace/Project-wide inventory reporting: Automated CSV and JSON inventory generation for migration batch planning.
- **Out of Scope**:
  - Full Git commit history migration, LFS content transfer, and Git ref rewriting.
  - Full pull request comments, review states, diff annotations, and approvals (handled in Detailed Discovery / Migration).
  - Issue tracker, wiki page content, and snippet migration.
  - Branch permissions/ruleset replication, deployment environments/secrets migration, and CI/CD pipelines cutover.

### 1.2 Architectural System Context & Runtime Boundary
Scripts execute within the PACE Script Executor architecture running on Temporal worker pods. The execution model separates workflow orchestration from script execution:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GitLift Control Plane (API Pod)                        │
│  - Receives POST /workflow/run                                                  │
│  - Parameter sanitizer validates parameters                                     │
│  - Renders {{PLACEHOLDER}} into Python repr() literals                          │
│  - Dispatches workflow to Temporal Queue ("discovery")                          │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Temporal Task Queue
┌────────────────────────────────────────▼────────────────────────────────────────┐
│                        Temporal Worker Pod (Execution Runtime)                  │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │ Workflow: bitbucket_to_ghec_fast_discovery.json                           │  │
│  │                                                                           │  │
│  │  Step 1: discovery_bitbucket_init.py                                      │  │
│  │  ├── Input validation & safety sanitization                               │  │
│  │  ├── Next audit version dynamic resolution (collision-safe)               │  │
│  │  ├── Delta detection via previous audit rows & bare clone cache           │  │
│  │  └── EFS path generation (/mnt/efs/migrations/{job_id}/discovery/...)     │  │
│  │                                                                           │  │
│  │  Step 2: discovery_bitbucket_git_sizer.py                                 │  │
│  │  ├── get_token(job_id, side="source") -> Fresh source token               │  │
│  │  ├── Ephemeral bare clone via git CLI                                     │  │
│  │  ├── git-sizer execution -> Max blob size                                 │  │
│  │  ├── Submodule detection across refs/heads/* via ls-tree + .gitmodules    │  │
│  │  ├── Large file sweep (>=50MB, >=100MB) via rev-list + cat-file           │  │
│  │  ├── Git notes detection via refs/notes/*                                 │  │
│  │  ├── Default branch size histogram (7 buckets) via ls-tree HEAD           │  │
│  │  └── DB submodule audit write & local clone purge                         │  │
│  │                                                                           │  │
│  │  Step 3: discovery_bitbucket_fast_summary.py                              │  │
│  │  ├── get_token(job_id, side="source") -> Fresh source token               │  │
│  │  ├── Bitbucket REST API v2.0 (Cloud) or v1.0 (DC) client queries          │  │
│  │  ├── Lightweight concurrency metrics (PRs, branches, tags, milestones)   │  │
│  │  ├── Synthesis with git-sizer output                                      │  │
│  │  ├── DB persistence (migration_repo_audit, discovery_documents)           │  │
│  │  └── EFS project details JSON persistence                                 │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  Standalone Pre-Flight / Inventory CLI:                                         │
│  ├── bitbucket_workspace_inventory.py (Enumerates all repos in Workspace/Proj)  │
│  └── bitbucket_discovery_validator.py (Pre-flight credential & scope audit)     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Platform Concept Equivalence Mapping

| Bitbucket Cloud Concept | Bitbucket Data Center Concept | GitLab Concept | GHEC EMU Target Equivalent |
|---|---|---|---|
| **Workspace** (`workspace_slug`) | **Instance** / Host URL | Top-Level Group | **GitHub Enterprise Organization** |
| **Project** (`project_key`) | **Project** (`project_key`) | Subgroup | **Custom Property** (`legacy_project`) + **Team** |
| **Personal Workspace** (User context) | **Personal Project** (`~username`) | User Namespace | **Dedicated Org** or Prefix (`personal-{user}`) |
| **Repository** (`repo_slug`) | **Repository** (`repo_slug`) | Project | **Repository** |
| **User / Account UUID** | **User** (`username`) | User / Identity | **EMU User** (via SCIM / SAML attribute mapping) |
| **Default Reviewers** | **Default Reviewers** | Code Owners / Approval Rules | **CODEOWNERS** / Branch Ruleset Approvals |
| **Deployment Environments** | **Deployment Environments** | Environments | **Environments** (Repo-level) |

---

## 2. Folder & File Structure

The `bitbucket_to_ghec` directory will reside in `pace-scm-migration-scripts/bitbucket_to_ghec/`, matching the exact conventions established by `gitlab_to_github` and `ado_to_ghec`.

```
pace-scm-migration-scripts/
├── bitbucket_to_ghec/
│   ├── README.md
│   ├── config/
│   │   ├── discovery_config.example.yaml
│   │   └── discovery_config.schema.json
│   ├── scripts/
│   │   └── initial_fast_discovery/
│   │       ├── discovery_bitbucket_init.py
│   │       ├── discovery_bitbucket_git_sizer.py
│   │       ├── discovery_bitbucket_fast_summary.py
│   │       ├── bitbucket_workspace_inventory.py
│   │       └── bitbucket_discovery_validator.py
│   └── workflow/
│       └── bitbucket_to_ghec_fast_discovery.json
```

### 2.1 File Inventory & Purpose

| File Relative Path | Primary Purpose |
|---|---|
| `bitbucket_to_ghec/README.md` | Developer documentation, workflow registration instructions, and execution guides. |
| `bitbucket_to_ghec/config/discovery_config.example.yaml` | Sample configuration template for standalone discovery and inventory runs. |
| `bitbucket_to_ghec/config/discovery_config.schema.json` | JSON Schema specifying validation constraints for the discovery configuration. |
| `bitbucket_to_ghec/scripts/initial_fast_discovery/discovery_bitbucket_init.py` | Step 1 of fast discovery workflow. Validates inputs, resolves audit version, checks delta state, computes EFS directories. |
| `bitbucket_to_ghec/scripts/initial_fast_discovery/discovery_bitbucket_git_sizer.py` | Step 2 of fast discovery workflow. Clones bare repo, computes git-sizer blob metrics, scans submodules, notes, and large files. |
| `bitbucket_to_ghec/scripts/initial_fast_discovery/discovery_bitbucket_fast_summary.py` | Step 3 of fast discovery workflow. Gathers Bitbucket REST metadata, aggregates counts, merges git metrics, updates DB and EFS. |
| `bitbucket_to_ghec/scripts/initial_fast_discovery/bitbucket_workspace_inventory.py` | Standalone CLI script to enumerate entire Bitbucket Workspaces/Projects and output discovery inventory CSV/JSON. |
| `bitbucket_to_ghec/scripts/initial_fast_discovery/bitbucket_discovery_validator.py` | Standalone CLI script to perform pre-flight connectivity, credential, and scope validation for Bitbucket and GHEC. |
| `bitbucket_to_ghec/workflow/bitbucket_to_ghec_fast_discovery.json` | Temporal workflow definition specifying the execution chain of steps 1, 2, and 3. |

---

## 3. Configuration & Environment Specification

The discovery phase operates in two modes:
1. **Orchestrated Workflow Mode (Worker Pod)**: Injected via Temporal activity templates using `{{PLACEHOLDER}}` values, reading secrets dynamically from Vault via `get_token()`.
2. **Standalone Inventory CLI Mode**: Configured via YAML configuration file (`config/discovery_config.yaml`) or environment variables for bulk workspace enumeration.

### 3.1 YAML Configuration Specification (`discovery_config.yaml`)

```yaml
version: "1.0"

source:
  type: "bitbucket_cloud" # Options: "bitbucket_cloud" | "bitbucket_dc"
  base_url: "https://api.bitbucket.org/2.0" # For DC: "https://bitbucket.internal.company.com/rest/api/1.0"
  git_host: "bitbucket.org" # For DC: "bitbucket.internal.company.com"
  
  # Workspace (Cloud) or Project Key (DC)
  workspace: "enterprise-core-org" # Cloud workspace slug or DC Project key
  
  # Authentication (For Standalone Mode only; Worker Pod uses Vault via get_token)
  auth:
    method: "api_token" # Cloud: "api_token" | "basic_app_password" | "oauth2". DC: "bearer_token" | "basic"
    username: "${BITBUCKET_USERNAME}" # Required for Basic Auth / App Password
    token: "${BITBUCKET_TOKEN}" # App Password, API Token, PAT, or OAuth Access Token
  
  # Scoping & Filtering
  filters:
    include_projects: [] # Specific project keys to include (empty = all)
    exclude_projects: ["ARCHIVE", "TEMP"]
    include_repos: [] # Specific repo slugs to include (empty = all)
    exclude_repos: []
    include_personal_repos: false # Bitbucket DC only (~username)
    include_archived: false

target:
  platform: "ghec"
  api_base_url: "https://api.github.com"
  enterprise_slug: "enterprise-managed-corp"
  target_org: "ghec-migration-target"
  auth:
    token: "${GITHUB_TARGET_PAT}" # classic PAT (repo, admin:org) or GitHub App Installation Token

execution:
  efs_mount_path: "/mnt/efs"
  output_dir: "./output/discovery"
  concurrency_limit: 5 # Maximum parallel API calls (conserves 1,000 req/hr rate limit)
  page_size: 100 # Bitbucket max pagelen
  rate_limit_headroom: 150 # Pause when remaining requests fall below this threshold
  git_timeout_seconds: 600 # Bare clone timeout
```

### 3.2 Authentication Handling Matrix

| Platform Variant | Auth Strategy | Credentials | Required Permissions / Scopes |
|---|---|---|---|
| **Bitbucket Cloud** | Basic (App Password) | `username` + `app_password` | `repository:read`, `project:read`, `account:read`, `pullrequest:read` |
| **Bitbucket Cloud** | Bearer (API Token) | API Token | Repository, Project, Workspace read permissions |
| **Bitbucket Cloud** | OAuth 2.0 | `access_token` (Bearer) | `repository`, `project`, `account`, `pullrequest` |
| **Bitbucket DC** | HTTP / Personal Token | `Bearer <token>` | `PROJECT_READ`, `REPO_READ` |
| **Bitbucket DC** | Basic Auth | `username` + `password` | Global Read or specific Project/Repository Read access |
| **GHEC EMU (Target)** | Personal Access Token | `token <pat>` | `repo` (Full control), `read:org`, `admin:org` (read) |
| **GHEC EMU (Target)** | GitHub App | Installation Token | `Administration: read`, `Metadata: read`, `Contents: read` |

---

## 4. API Endpoint Catalog

### 4.1 Bitbucket Cloud REST API v2.0

All Bitbucket Cloud requests use base URL `https://api.bitbucket.org/2.0`. Pagination is cursor/URL-based via the `next` link in the JSON payload, with page length set via `?pagelen=100`.

| Category | Endpoint | Method | Query Parameters | Response Fields Extracted |
|---|---|---|---|---|
| **Workspace Profile** | `/workspaces/{workspace}` | GET | None | `uuid`, `slug`, `name`, `is_privacy_enforced`, `created_on` |
| **Projects List** | `/workspaces/{workspace}/projects` | GET | `pagelen=100`, `page={n}` | `values[].key`, `values[].uuid`, `values[].name`, `values[].is_private`, `values[].description` |
| **Project Details** | `/workspaces/{workspace}/projects/{project_key}` | GET | None | `key`, `uuid`, `name`, `description`, `is_private`, `has_publicly_visible_repos` |
| **Repository Inventory** | `/repositories/{workspace}` | GET | `pagelen=100`, `q={filter}`, `sort=-updated_on` | `values[].uuid`, `values[].slug`, `values[].name`, `values[].full_name`, `values[].is_private`, `values[].project.key`, `values[].project.name`, `values[].mainbranch.name`, `values[].size`, `values[].language`, `values[].created_on`, `values[].updated_on`, `values[].fork_policy`, `values[].parent`, `values[].links.clone` |
| **Repository Details** | `/repositories/{workspace}/{repo_slug}` | GET | None | Full repository entity: `uuid`, `slug`, `name`, `full_name`, `description`, `is_private`, `fork_policy`, `mainbranch.name`, `size`, `has_wiki`, `has_issues`, `parent`, `links.clone[].href` |
| **Pull Requests Count** | `/repositories/{workspace}/{repo_slug}/pullrequests` | GET | `pagelen=1`, `state=ALL`, `fields=size` | `size` (Top-level count field in Bitbucket Cloud) |
| **Branches Count** | `/repositories/{workspace}/{repo_slug}/refs/branches` | GET | `pagelen=1`, `fields=size` | `size` (Top-level count field) |
| **Tags Count** | `/repositories/{workspace}/{repo_slug}/refs/tags` | GET | `pagelen=1`, `fields=size` | `size` (Top-level count field) |
| **Environments List** | `/repositories/{workspace}/{repo_slug}/environments` | GET | `pagelen=100` | `total`, `values[].uuid`, `values[].name`, `values[].environment_type` |
| **Deploy Keys Count** | `/repositories/{workspace}/{repo_slug}/deploy-keys` | GET | `pagelen=1`, `fields=size` | `size` |
| **Webhooks Count** | `/repositories/{workspace}/{repo_slug}/hooks` | GET | `pagelen=1`, `fields=size` | `size` |

> [!IMPORTANT]
> **Bitbucket Cloud `fields=size` Optimization**: Bitbucket Cloud returns a top-level `size` integer when querying collections (e.g. `/pullrequests?pagelen=1&fields=size`). This allows extracting the exact item count in a single request without downloading pages or encountering 10,000-record caps.

### 4.2 Bitbucket Data Center REST API v1.0

All Bitbucket Data Center requests use base URL `https://<bb-host>/rest/api/1.0`. Pagination uses `start` (zero-indexed item offset) and `limit` (page size, max 100), with response envelope `{isLastPage: bool, nextPageStart: int, values: [...]}`.

| Category | Endpoint | Method | Query Parameters | Response Fields Extracted |
|---|---|---|---|---|
| **Projects List** | `/projects` | GET | `limit=100`, `start={n}` | `values[].key`, `values[].id`, `values[].name`, `values[].description`, `values[].public`, `values[].type` |
| **Project Details** | `/projects/{project_key}` | GET | None | `key`, `id`, `name`, `description`, `public`, `type` |
| **Repository Inventory (Project)** | `/projects/{project_key}/repos` | GET | `limit=100`, `start={n}` | `values[].id`, `values[].slug`, `values[].name`, `values[].project.key`, `values[].public`, `values[].forkable`, `values[].origin`, `values[].links.clone` |
| **Repository Inventory (Global)** | `/repos` | GET | `limit=100`, `start={n}` | Global repository enumeration across all projects |
| **Personal Repositories** | `/users/{user_slug}/repos` | GET | `limit=100`, `start={n}` | Repositories in personal project `~username` |
| **Repository Details** | `/projects/{project_key}/repos/{repo_slug}` | GET | None | Full repository object: `id`, `slug`, `name`, `state`, `forkable`, `public`, `project`, `origin`, `links` |
| **Branches** | `/projects/{project_key}/repos/{repo_slug}/branches` | GET | `limit=1`, `details=true` | `size` (or calculate via `isLastPage` and `nextPageStart`) |
| **Tags** | `/projects/{project_key}/repos/{repo_slug}/tags` | GET | `limit=1` | `size` (or calculate via pagination) |
| **Pull Requests** | `/projects/{project_key}/repos/{repo_slug}/pull-requests` | GET | `limit=1`, `state=ALL` | `size` |
| **Default Branch** | `/projects/{project_key}/repos/{repo_slug}/default-branch` | GET | None | `id`, `displayId` |

### 4.3 Target GHEC Pre-Flight API Catalog

| Endpoint | Method | Query / Headers | Purpose |
|---|---|---|---|
| `GET /orgs/{org}` | GET | `Accept: application/vnd.github+json` | Validate target organization exists and verify plan/EMU status. |
| `GET /user` | GET | `Accept: application/vnd.github+json` | Validate PAT/App Token identity and check token expiration. |
| `GET /orgs/{org}/repos` | GET | `per_page=1`, `type=all` | Verify target org read permissions and check existing repository count. |
| `GET /repos/{org}/{repo}` | GET | `Accept: application/vnd.github+json` | Pre-flight namespace collision check (404 = available, 200 = conflict). |

---

## 5. Script-by-Script Implementation Details

The fast discovery workflow consists of three chained scripts matching the exact execution pattern of `gitlab_to_github`. In addition, two utility scripts provide standalone inventory enumeration and pre-flight validation.

```
bitbucket_to_ghec/scripts/initial_fast_discovery/
├── discovery_bitbucket_init.py           (Workflow Step 1)
├── discovery_bitbucket_git_sizer.py      (Workflow Step 2)
├── discovery_bitbucket_fast_summary.py   (Workflow Step 3)
├── bitbucket_workspace_inventory.py     (Standalone Inventory CLI)
└── bitbucket_discovery_validator.py       (Pre-flight Validation CLI)
```

### 5.1 Script 1: `discovery_bitbucket_init.py`

#### Purpose & Boundary
First script in the Temporal workflow chain (`Sequence: 1 of 3`). Collects workflow inputs, normalizes Bitbucket identifiers, dynamically resolves collision-safe audit version numbers, detects delta run state, constructs versioned EFS paths, and emits JSON configuration for downstream scripts. **Makes zero external API calls.**

#### Input Placeholders
- `{{MIGRATION_JOB_ID}}` (UUID string)
- `{{EXECUTION_ID}}` (UUID string)
- `{{SOURCE_URL}}` (Base URL: e.g. `https://api.bitbucket.org/2.0` or `https://bb.internal.net/rest/api/1.0`)
- `{{SOURCE_REPO_PATH}}` (Repository path: `workspace/repo_slug` for Cloud, `PROJECT/repo_slug` for DC)
- `{{SOURCE_REPO_ID}}` (UUID for Cloud, Integer/Safe ID for DC)
- `{{EFS_MOUNT_PATH}}` (Base mount path, e.g. `/mnt/efs`)
- `{{WORKFLOW_VERSION}}` (Workflow definition version integer)

#### Function Specifications

##### `build_api_url(base_url: str) -> str`
- **Parameters**: `base_url` (Raw source URL).
- **Return**: Normalized Bitbucket API root URL.
- **Logic**: Strips trailing slashes. Detects whether URL points to Bitbucket Cloud or DC. For Cloud, ensures suffix is `/2.0`. For DC, ensures suffix is `/rest/api/1.0`.

##### `_resolve_next_audit_version(migration_job_id: str, source_repo_id: str) -> tuple[int, str]`
- **Parameters**: `migration_job_id`, `source_repo_id`.
- **Return**: `(next_audit_version: int, dir_prefix: str)`.
- **Logic**:
  1. Opens `db_session()`.
  2. Queries `git_lift.workflow_execution_progress` for an active `DISCOVERY` workflow with status `IN ('PENDING', 'RUNNING')` for this job and repo.
  3. If active row exists, sets candidate version from WEP row and `dir_prefix = "fd"`.
  4. Self-healing guard: Checks `MigrationRepoAudit` for an existing completed row at this version. If already completed, computes `MAX(version) + 1` to prevent overwriting previous completed snapshots.
  5. If no active WEP row exists, calculates `MAX(version) + 1` from `MigrationRepoAudit` and sets `dir_prefix = "d"`.

##### `_detect_delta_mode(migration_job_id: str, source_repo_id: str, clone_path: str) -> tuple[bool, str | None, int | None]`
- **Parameters**: `migration_job_id`, `source_repo_id`, `clone_path`.
- **Return**: `(is_delta_run: bool, last_discovery_at: str | None, prev_version: int | None)`.
- **Logic**:
  1. Queries `MigrationRepoAudit` for the most recent `INITIAL` audit record.
  2. If none found, returns `(False, None, None)`.
  3. Checks if bare clone exists at `clone_path`. If clone is missing on EFS, logs warning and returns `(False, None, None)` (forces full discovery).
  4. If audit row and clone both exist, returns `(True, prev_audit.timestamp.isoformat(), prev_audit.version)`.

##### `validate_inputs() -> None`
- **Logic**: Validates non-empty status for all mandatory placeholders. Validates that `SOURCE_URL` uses `https://`. Validates that `SOURCE_REPO_PATH` contains exactly one `/` separator:
  - Bitbucket Cloud: `{workspace_slug}/{repo_slug}` (e.g. `fintech-cloud/payment-service`)
  - Bitbucket DC Standard Project: `{PROJECT_KEY}/{repo_slug}` (e.g. `PAY/payment-service`)
  - Bitbucket DC Personal Project: `~{username}/{repo_slug}` (e.g. `~john.doe/utility-script`)
  Raises `ValueError` on validation failure.

##### `main() -> None`
- **Logic**:
  1. Validates inputs via `validate_inputs()`.
  2. Parses `source_org` (workspace or project) and `repo_name` (repo slug) from `SOURCE_REPO_PATH`.
  3. Computes sanitized `safe_id` via regex `[^0-9A-Za-z._-] -> '_'`.
  4. Constructs EFS paths:
     - `clone_path = {EFS_BASE}/migrations/{job_id}/clone/{safe_id}/repo.git`
     - `versioned_discovery_dir = {EFS_BASE}/migrations/{job_id}/discovery/{safe_id}/{dir_prefix}{version}`
  5. Emits single JSON payload to `stdout` containing normalized variables. Progress logs to `sys.stderr`.

---

### 5.2 Script 2: `discovery_bitbucket_git_sizer.py`

#### Purpose & Boundary
Second script in the Temporal chain (`Sequence: 2 of 3`). Performs an authenticated bare clone of the Bitbucket repository, executes `git-sizer` to parse the maximum blob size, extracts submodule references across all local branches, detects Git notes (`refs/notes/*`), scans for large files (>=50MB and >=100MB), computes the 7-bucket size distribution histogram of the default branch, records submodule audit entries to PostgreSQL, and purges the temporary clone.

#### Input Placeholders
- Sourced from `discovery_bitbucket_init`:
  - `{{steps.discovery_bitbucket_init.source_url}}`
  - `{{steps.discovery_bitbucket_init.source_repo_path}}`
  - `{{steps.discovery_bitbucket_init.source_repo_id}}`
  - `{{steps.discovery_bitbucket_init.migration_job_id}}`
  - `{{steps.discovery_bitbucket_init.efs_mount_path}}`
  - `{{steps.discovery_bitbucket_init.next_audit_version}}`

#### Function Specifications

##### `build_bitbucket_clone_url(source_url: str, repo_path: str, token: str) -> str`
- **Parameters**: `source_url`, `repo_path`, `token`.
- **Return**: Authenticated HTTPS Git clone URL.
- **Logic**:
  - For Bitbucket Cloud (`api.bitbucket.org` or `bitbucket.org`): Uses `x-token-auth` username:
    `https://x-token-auth:{token}@bitbucket.org/{repo_path}.git`
  - For Bitbucket DC (`/scm/` path pattern): Uses token bearer syntax:
    `https://{token}@{dc_host}/scm/{repo_path}.git`

##### `parse_maximum_blob_size(output: str) -> str | None`
- **Parameters**: `output` (Raw text output of `git-sizer`).
- **Return**: Parsed human-readable size string (e.g., `42.5 MiB`) or `None`.
- **Logic**: Scans `git-sizer` stdout for table section `Biggest objects`, locates `Blobs` sub-row `Maximum size`, extracts column value.

##### `detect_submodules(clone_path: str, warnings: list) -> dict`
- **Parameters**: `clone_path`, `warnings`.
- **Return**: Dictionary containing submodule inventory across all branches:
  `{has_submodules: bool, total_submodules: int, submodules: list, by_branch: dict, unique_submodule_paths: list, total_branches_scanned: int}`.
- **Logic**:
  1. Lists all local branches using `git for-each-ref --format="%(refname)" refs/heads/`.
  2. For each branch, inspects tree for gitlink mode `160000` via `git ls-tree -r {ref}`.
  3. If gitlinks exist, resolves `.gitmodules` on that branch via `git show {ref}:.gitmodules` (memoized by blob SHA).
  4. Maps each submodule `path`, `url`, and `commit_sha`.

##### `compute_git_ref_metrics(clone_path: str, warnings: list) -> dict`
- **Parameters**: `clone_path`, `warnings`.
- **Return**: `{total_branches: int, total_tags: int, total_commits: int}`.
- **Logic**:
  1. Counts branches using local `git -C {clone_path} for-each-ref --format="%(refname)" refs/heads/`.
  2. Counts tags using local `git -C {clone_path} for-each-ref --format="%(refname)" refs/tags/`.
  3. Counts reachable commits using `git -C {clone_path} rev-list --count --all`.
  4. **Significance**: Reuses the bare clone already on disk. Costs **zero REST API calls**, completely bypassing Bitbucket Cloud 1,000 req/hr rate limits and eliminating Bitbucket DC pagination complexity.

##### `detect_git_notes(clone_path: str, warnings: list) -> dict`
- **Parameters**: `clone_path`, `warnings`.
- **Return**: `{has_git_notes: bool, git_notes_count: int, git_notes_refs: list}`.
- **Logic**: Runs `git for-each-ref --format="%(refname)" refs/notes/`. For each note ref found, counts notes via `git notes --ref {ref} list`.

##### `scan_large_files(clone_path: str, warnings: list) -> tuple[int, int]`
- **Parameters**: `clone_path`, `warnings`.
- **Return**: `(large_files_over_50mb: int, large_files_over_100mb: int)`.
- **Logic**:
  1. Executes `git rev-list --objects --all` to list all reachable Git object SHAs across the entire DAG.
  2. Pipes SHAs to `git cat-file --batch-check="%(objectname) %(objecttype) %(objectsize)"`.
  3. Filters for `objecttype == "blob"`.
  4. Tallies count for `50MB <= size < 100MB` and count for `size >= 100MB`.

##### `compute_size_distribution(clone_path: str, warnings: list) -> dict`
- **Parameters**: `clone_path`, `warnings`.
- **Return**: 7-bucket dictionary `<1KB`, `1KB-10KB`, `10KB-100KB`, `100KB-1MB`, `1MB-10MB`, `10MB-100MB`, `>100MB`.
- **Logic**: Runs `git ls-tree -r -l HEAD` on default branch. Buckets every blob by byte size.

##### `_write_submodules_detail_file(efs_mount_path: str, migration_job_id: str, safe_repo_id: str, submodules_info: dict, warnings: list) -> str | None`
- **Logic**: Writes full submodule breakdown to `/mnt/efs/migrations/{job_id}/discovery/{safe_repo_id}_git_sizer_submodules.json` to keep stdout within Temporal's 1.5MB limit.

##### `main() -> None`
- **Logic**:
  1. Resolves source token via `asyncio.run(get_token(job_id=migration_job_id, side="source"))`.
  2. Clones bare repository to local scratch directory via `subprocess.run(["git", "clone", "--bare", ...])`.
  3. Executes `git-sizer`, submodule scanner, notes detector, large file counter, size distributor, and `compute_git_ref_metrics`.
  4. Persists submodule audit rows to database table `git_lift.discovery_submodule_audit` via `from activities.commons.db.submodule_audit_store import record_submodule_audit_rows`:
     ```python
     record_submodule_audit_rows(
         migration_job_id=migration_job_id,
         source_repo_id=source_repo_id,
         source_phase="initial_fast_discovery",
         source_script="discovery_bitbucket_git_sizer",
         audit_version=next_audit_version,
         is_delta_run=False,
         submodule_items=submodules_info["submodules"],
     )
     ```
  5. Cleans up bare clone directory in `finally:` block.
  6. Emits stable JSON metrics to `stdout` containing:
     - `maximum_blob_size`, `submodules`, `has_submodules`, `submodules_detail_file`
     - `has_git_notes`, `git_notes_count`, `git_notes_refs`
     - `large_files_over_50mb`, `large_files_over_100mb`, `size_distribution`
     - `total_branches`, `total_tags`, `total_commits` (zero-API Git ref counts)

---

### 5.3 Script 3: `discovery_bitbucket_fast_summary.py`

#### Purpose & Boundary
Third script in the chain (`Sequence: 3 of 3`). Queries the Bitbucket REST API for repository profile and lightweight entity counts, ingests chained Git metrics from `discovery_bitbucket_git_sizer`, normalizes data into GHEC-compatible summary structures, persists the record into PostgreSQL database tables (`MigrationRepoAudit`, `discovery_documents`, `migration_documents`), writes `{safe_id}_get_project_details.json` to EFS, and emits final JSON output.

#### Input Placeholders
- `JOB_ID = {{MIGRATION_JOB_ID}}`
- `SOURCE_REPO_ID = {{SOURCE_REPO_ID}}`
- `SOURCE_URL = {{SOURCE_URL}}`
- `SOURCE_REPO_PATH = {{SOURCE_REPO_PATH}}`
- Git Sizer chained values:
  - `{{steps.discovery_bitbucket_git_sizer.maximum_blob_size}}`
  - `{{steps.discovery_bitbucket_git_sizer.has_submodules}}`
  - `{{steps.discovery_bitbucket_git_sizer.submodules}}`
  - `{{steps.discovery_bitbucket_git_sizer.submodules_detail_file}}`
  - `{{steps.discovery_bitbucket_git_sizer.has_git_notes}}`
  - `{{steps.discovery_bitbucket_git_sizer.git_notes_count}}`
  - `{{steps.discovery_bitbucket_git_sizer.large_files_over_50mb}}`
  - `{{steps.discovery_bitbucket_git_sizer.large_files_over_100mb}}`
  - `{{steps.discovery_bitbucket_git_sizer.size_distribution}}`
  - `{{steps.discovery_bitbucket_git_sizer.total_branches}}`
  - `{{steps.discovery_bitbucket_git_sizer.total_tags}}`
  - `{{steps.discovery_bitbucket_git_sizer.total_commits}}`

#### Function Specifications

##### `fetch_bitbucket_cloud_metadata(api_url: str, workspace: str, repo_slug: str, token: str, warnings: list) -> dict`
- **Logic**: Uses `ApiRequestBuilder` to execute `GET /2.0/repositories/{workspace}/{repo_slug}`. Extracts `uuid`, `name`, `full_name`, `is_private`, `size`, `mainbranch.name`, `language`, `has_wiki`, `has_issues`, `parent`, `links`.

##### `fetch_bitbucket_dc_metadata(api_url: str, project_key: str, repo_slug: str, token: str, warnings: list) -> dict`
- **Logic**: Uses `ApiRequestBuilder` to execute `GET /rest/api/1.0/projects/{project_key}/repos/{repo_slug}`. Fetches default branch via `/default-branch`. Normalizes into unified project dictionary.

##### `fetch_cloud_counts_concurrently(api_url: str, workspace: str, repo_slug: str, token: str, warnings: list) -> dict`
- **Logic**: Concurrently queries lightweight collection size endpoints using `asyncio.gather`:
  - Pull requests: `/repositories/{workspace}/{repo_slug}/pullrequests?pagelen=1&state=ALL&fields=size`
  - Branches: `/repositories/{workspace}/{repo_slug}/refs/branches?pagelen=1&fields=size`
  - Tags: `/repositories/{workspace}/{repo_slug}/refs/tags?pagelen=1&fields=size`
  - Deploy keys: `/repositories/{workspace}/{repo_slug}/deploy-keys?pagelen=1&fields=size`
  - Webhooks: `/repositories/{workspace}/{repo_slug}/hooks?pagelen=1&fields=size`
  - Environments: `/repositories/{workspace}/{repo_slug}/environments?pagelen=1`

##### `build_unified_summary(...) -> dict`
- **Logic**: Merges Bitbucket REST attributes and Git sizer metrics into the canonical GHEC-compatible summary schema (matching GitLab fast summary keys: `id`, `name`, `full_name`, `visibility`, `default_branch`, `size`, `total_commits`, `total_branches`, `total_tags`, `total_pull_requests`, `largest_file_size`, `has_submodules`, `total_large_files>50mb`, `size_distribution`).

##### `upsert_repo_audit(job_id: str, repo_id: str, repo_name: str, summary: dict) -> None`
- **Logic**:
  1. Opens `db_session()`.
  2. Resolves run version via `_resolve_discovery_run_version()`.
  3. Writes `{safe_id}_get_project_details.json` to `/mnt/efs/migrations/{job_id}/discovery/`.
  4. Upserts `MigrationRepoAudit` row:
     - Sets `migration_type = "INITIAL"`.
     - Sets `source_data = {**summary, "completed": True, "discovery_phase": "fast"}`.
     - Guards against downgrading a previous `detailed` discovery phase.
  5. Upserts `discovery_documents` row with `status = "DISCOVERY_COMPLETED"`.
  6. Upserts `migration_documents` row linking to EFS directory.
  7. Commits database transaction.

##### `main() -> None`
- **Logic**: Validates inputs, fetches fresh token via `get_token(job_id, side="source")`, queries Bitbucket API, aggregates counts, computes summary, executes `upsert_repo_audit()`, and emits final JSON output on `stdout`.

---

### 5.4 Utility 1: `bitbucket_workspace_inventory.py` (Standalone Enumeration CLI)

#### Purpose & Boundary
Standalone CLI tool run prior to individual repository discovery workflows. Interrogates a Bitbucket Cloud Workspace or Bitbucket DC Instance/Project, enumerates all repositories, applies inclusion/exclusion filters, extracts basic repository metadata, and generates an inventory report in CSV and JSON formats.

#### Command-Line Interface
```bash
python bitbucket_workspace_inventory.py \
  --source-type cloud \
  --base-url https://api.bitbucket.org/2.0 \
  --workspace my-workspace-slug \
  --token "${BITBUCKET_TOKEN}" \
  --output-csv ./output/bitbucket_inventory.csv \
  --output-json ./output/bitbucket_inventory.json \
  --include-projects PROJA,PROJB \
  --exclude-archived
```

#### Key Functions
- `enumerate_cloud_repositories(base_url, workspace, token, filters) -> list[dict]`: Traverses `GET /2.0/repositories/{workspace}` following opaque `next` pagination links, respecting rate limits.
- `enumerate_dc_repositories(base_url, project_key, token, filters) -> list[dict]`: Traverses `GET /rest/api/1.0/projects/{key}/repos` using `start` and `limit` offsets.
- `write_inventory_csv(repositories, output_path)`: Exports tabular repository inventory for migration scheduling.
- `write_inventory_json(repositories, output_path)`: Exports full JSON payload for programmatic ingestion into GitLift database.

---

### 5.5 Utility 2: `bitbucket_discovery_validator.py` (Pre-Flight Validation CLI)

#### Purpose & Boundary
CLI validation script to verify connectivity, credential validity, permission scopes, and target GHEC constraints before executing migration jobs.

#### Pre-Flight Checks Performed
1. **Source Connectivity**: Tests TCP connectivity and TLS handshake to Bitbucket host.
2. **Source Authentication**: Performs authenticated `GET` to verify token identity.
3. **Source Permissions**: Verifies `read` permissions on specified Workspace / Projects.
4. **Target GHEC Connectivity**: Validates HTTPS connectivity to `api.github.com`.
5. **Target GHEC Permissions**: Validates PAT / App Token against `GET /orgs/{target_org}` to ensure `admin:org` / `repo` permissions.
6. **Rate Limit Status**: Reads Bitbucket and GitHub rate limit headers and warns if available quota is insufficient.

---

## 6. Data Model & Output Schema

### 6.1 Database Persistence Models

The discovery output integrates with GitLift's existing SQLAlchemy ORM models:

```mermaid
erDiagram
    MIGRATION_JOBS ||--o{ MIGRATION_REPO_AUDIT : contains
    MIGRATION_JOBS ||--o{ DISCOVERY_DOCUMENTS : tracks
    MIGRATION_JOBS ||--o{ MIGRATION_DOCUMENTS : archives
    MIGRATION_REPO_AUDIT {
        uuid id PK
        string migration_job_id FK
        string source_repo_id
        string migration_type
        int version
        jsonb source_data
        timestamp timestamp
    }
    DISCOVERY_DOCUMENTS {
        uuid id PK
        string migration_job_id FK
        string repository_id
        string status
    }
    MIGRATION_DOCUMENTS {
        string id PK
        string migration_job_id FK
        string doc_type
        string path
        string format
        int version
        timestamp created_at
    }
```

### 6.2 Canonical Repository Metadata Schema (`{safe_id}_get_project_details.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BitbucketFastDiscoverySummary",
  "type": "object",
  "required": [
    "id",
    "name",
    "full_name",
    "visibility",
    "default_branch",
    "size",
    "total_branches",
    "total_tags",
    "total_pull_requests",
    "largest_file_size",
    "has_submodules",
    "size_distribution"
  ],
  "properties": {
    "id": { "type": "string", "description": "Bitbucket UUID (Cloud) or repository ID (DC)" },
    "name": { "type": "string", "description": "Repository slug/name" },
    "full_name": { "type": "string", "description": "workspace/slug or PROJECT/slug" },
    "description": { "type": ["string", "null"] },
    "visibility": { "type": "string", "enum": ["private", "public", "internal"] },
    "private": { "type": "boolean" },
    "archived": { "type": "boolean" },
    "created_at": { "type": ["string", "null"], "format": "date-time" },
    "updated_at": { "type": ["string", "null"], "format": "date-time" },
    "default_branch": { "type": "string" },
    "html_url": { "type": "string" },
    "clone_url": { "type": "string" },
    "ssh_url": { "type": "string" },
    "owner_login": { "type": "string", "description": "Workspace slug or Project key" },
    "owner_type": { "type": "string", "enum": ["Workspace", "Project", "User"] },
    "project_key": { "type": "string" },
    "project_name": { "type": "string" },
    "size": { "type": "integer", "description": "Repository size in bytes" },
    "total_branches": { "type": "integer" },
    "total_tags": { "type": "integer" },
    "total_pull_requests": { "type": "integer" },
    "total_milestones": { "type": "integer" },
    "total_deploy_keys": { "type": "integer" },
    "total_webhooks": { "type": "integer" },
    "total_environments": { "type": "integer" },
    "wiki_exists": { "type": "boolean" },
    "has_wiki": { "type": "boolean" },
    "has_issues": { "type": "boolean" },
    "largest_file_size": { "type": ["string", "null"] },
    "has_submodules": { "type": "boolean" },
    "total_submodules": { "type": "integer" },
    "submodules": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": { "type": "string" },
          "url": { "type": "string" },
          "commit_sha": { "type": "string" },
          "branch": { "type": "string" }
        }
      }
    },
    "has_git_notes": { "type": "boolean" },
    "git_notes_count": { "type": "integer" },
    "total_large_files>50mb": { "type": "integer" },
    "total_large_files>100mb": { "type": "integer" },
    "size_distribution": {
      "type": "object",
      "properties": {
        "<1KB": { "type": "integer" },
        "1KB-10KB": { "type": "integer" },
        "10KB-100KB": { "type": "integer" },
        "100KB-1MB": { "type": "integer" },
        "1MB-10MB": { "type": "integer" },
        "10MB-100MB": { "type": "integer" },
        ">100MB": { "type": "integer" }
      }
    }
  }
}
```

### 6.3 Sample Discovery Output JSON

```json
{
  "id": "{e18b4567-e89b-12d3-a456-426614174000}",
  "name": "payment-gateway-service",
  "full_name": "fintech-cloud/payment-gateway-service",
  "description": "Core payment processing service migrated from Bitbucket Cloud",
  "visibility": "private",
  "private": true,
  "archived": false,
  "created_at": "2022-04-15T08:30:00Z",
  "updated_at": "2026-10-31T14:22:18Z",
  "default_branch": "main",
  "html_url": "https://bitbucket.org/fintech-cloud/payment-gateway-service",
  "clone_url": "https://bitbucket.org/fintech-cloud/payment-gateway-service.git",
  "ssh_url": "git@bitbucket.org:fintech-cloud/payment-gateway-service.git",
  "owner_login": "fintech-cloud",
  "owner_type": "Workspace",
  "project_key": "PAY",
  "project_name": "Payments Platform",
  "size": 184569200,
  "total_branches": 24,
  "total_tags": 112,
  "total_pull_requests": 648,
  "total_milestones": 0,
  "total_deploy_keys": 3,
  "total_webhooks": 2,
  "total_environments": 4,
  "wiki_exists": false,
  "has_wiki": false,
  "has_issues": false,
  "largest_file_size": "74.2 MiB",
  "has_submodules": true,
  "total_submodules": 1,
  "submodules": [
    {
      "path": "vendor/crypto-lib",
      "url": "https://bitbucket.org/fintech-cloud/crypto-lib.git",
      "commit_sha": "d41d8cd98f00b204e9800998ecf8427e",
      "branch": "main"
    }
  ],
  "has_git_notes": false,
  "git_notes_count": 0,
  "total_large_files>50mb": 1,
  "total_large_files>100mb": 0,
  "size_distribution": {
    "<1KB": 142,
    "1KB-10KB": 380,
    "10KB-100KB": 115,
    "100KB-1MB": 24,
    "1MB-10MB": 6,
    "10MB-100MB": 1,
    ">100MB": 0
  }
}
```

### 6.4 Inventory CSV Schema (`discovery_inventory.csv`)

| Column Name | Data Type | Source API Field | Description |
|---|---|---|---|
| `workspace_or_project` | String | `workspace.slug` / `project.key` | Owning container in Bitbucket |
| `project_key` | String | `project.key` | Bitbucket Project Key |
| `repo_slug` | String | `repository.slug` | Repository URL identifier |
| `repo_name` | String | `repository.name` | Repository display name |
| `repo_uuid_or_id` | String | `uuid` / `id` | Unique source repository ID |
| `is_private` | Boolean | `is_private` / `public` | Repository privacy status |
| `default_branch` | String | `mainbranch.name` | Default Git branch |
| `size_bytes` | Integer | `size` | Size in bytes |
| `size_mb` | Float | Calculated (`size / 1048576`) | Human-readable size in MB |
| `language` | String | `language` | Primary programming language |
| `created_on` | ISO Timestamp | `created_on` | Creation timestamp |
| `updated_on` | ISO Timestamp | `updated_on` | Last activity timestamp |
| `clone_url_https` | String | `links.clone[https]` | HTTPS clone URL |
| `clone_url_ssh` | String | `links.clone[ssh]` | SSH clone URL |
| `migration_readiness` | String | Calculated | Readiness rating (`READY`, `OVERSIZE`, `LFS_AUDIT_REQUIRED`) |

---

## 7. Execution Flow & Entry Point

### 7.1 Temporal Workflow Definition (`workflow/bitbucket_to_ghec_fast_discovery.json`)

```json
{
  "workflow_name": "BITBUCKET_TO_GITHUB_FAST_DISCOVERY",
  "task_queue": "discovery",
  "scripts": [
    {
      "name": "discovery_bitbucket_init",
      "values": {
        "SOURCE_URL": "",
        "EXECUTION_ID": "",
        "EFS_MOUNT_PATH": "",
        "SOURCE_REPO_ID": "",
        "MIGRATION_JOB_ID": "",
        "SOURCE_REPO_PATH": "",
        "WORKFLOW_VERSION": ""
      },
      "disabled": false,
      "activity_options": {
        "start_to_close_seconds": 300,
        "heartbeat_seconds": 60,
        "retry_policy": {
          "initial_interval_seconds": 10,
          "maximum_interval_seconds": 60,
          "backoff_coefficient": 2.0,
          "maximum_attempts": 3,
          "non_retryable_error_types": ["ValueError", "ScriptNotFoundError"]
        }
      }
    },
    {
      "name": "discovery_bitbucket_git_sizer",
      "values": {},
      "disabled": false,
      "activity_options": {
        "start_to_close_seconds": 1800,
        "heartbeat_seconds": 60,
        "retry_policy": {
          "initial_interval_seconds": 30,
          "maximum_interval_seconds": 300,
          "backoff_coefficient": 2.0,
          "maximum_attempts": 3,
          "non_retryable_error_types": ["ScriptNotFoundError", "ScriptExecutionError"]
        }
      }
    },
    {
      "name": "discovery_bitbucket_fast_summary",
      "values": {
        "SOURCE_URL": "",
        "SOURCE_REPO_ID": "",
        "MIGRATION_JOB_ID": "",
        "SOURCE_REPO_PATH": ""
      },
      "disabled": false,
      "activity_options": {
        "start_to_close_seconds": 900,
        "heartbeat_seconds": 60,
        "retry_policy": {
          "initial_interval_seconds": 20,
          "maximum_interval_seconds": 180,
          "backoff_coefficient": 2.0,
          "maximum_attempts": 3,
          "non_retryable_error_types": ["ApiPermissionError", "ApiNotFoundError"]
        }
      }
    }
  ],
  "exported_at": "2026-11-03T11:30:00.000Z"
}
```

### 7.2 End-to-End Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    participant UI as GitLift API / UI
    participant Temp as Temporal Orchestrator
    participant Init as discovery_bitbucket_init
    participant Sizer as discovery_bitbucket_git_sizer
    participant Summary as discovery_bitbucket_fast_summary
    participant Vault as HashiCorp Vault
    participant BB as Bitbucket REST API
    participant Git as Bitbucket Git Endpoint
    participant DB as PostgreSQL DB
    participant EFS as Shared EFS Storage

    UI->>Temp: POST /workflow/run (BITBUCKET_TO_GITHUB_FAST_DISCOVERY)
    Temp->>Init: Execute Step 1 (discovery_bitbucket_init)
    Init->>DB: Query existing audit versions & delta status
    Init->>Init: Validate inputs & compute EFS paths
    Init-->>Temp: Return JSON (paths, audit_version, delta_mode)

    Temp->>Sizer: Execute Step 2 (discovery_bitbucket_git_sizer)
    Sizer->>Vault: get_token(job_id, "source")
    Vault-->>Sizer: Return Bitbucket credentials
    Sizer->>Git: git clone --bare (ephemeral)
    Sizer->>Sizer: git-sizer analysis -> max_blob_size
    Sizer->>Sizer: Submodule scan across refs/heads/*
    Sizer->>Sizer: Large files scan (>=50MB, >=100MB)
    Sizer->>Sizer: Default branch size distribution
    Sizer->>DB: Record submodule_audit rows
    Sizer->>EFS: Write {safe_id}_git_sizer_submodules.json
    Sizer->>Sizer: Clean up bare clone directory
    Sizer-->>Temp: Return Git metrics JSON

    Temp->>Summary: Execute Step 3 (discovery_bitbucket_fast_summary)
    Summary->>Vault: get_token(job_id, "source")
    Vault-->>Summary: Return Bitbucket credentials
    Summary->>BB: GET /repositories/{workspace}/{repo_slug}
    Summary->>BB: GET concurrent counts (PRs, branches, tags, envs)
    Summary->>Summary: Build unified summary
    Summary->>EFS: Write {safe_id}_get_project_details.json
    Summary->>DB: Upsert MigrationRepoAudit
    Summary->>DB: Update discovery_documents (DISCOVERY_COMPLETED)
    Summary->>DB: Update migration_documents
    Summary-->>Temp: Return final summary JSON
    Temp-->>UI: Workflow Status: SUCCESS
```

---

## 8. Logging, Error Handling & Rate Limiting Strategy

### 8.1 Logging Framework & Redaction Standard
- **Stdout Contract**: Strictly reserved for the final step output: exactly one `print(json.dumps({...}))`. Downstream steps chain from this output.
- **Stderr Logging**: All operational logging, diagnostics, and progress updates must be written to `sys.stderr` with standardized prefix tags (e.g. `[bb_init]`, `[bb_git_sizer]`, `[bb_fast_summary]`).
- **Trace Context**: Auto-injects `GITLIFT_TRACE_ID` from `os.environ` on every log record:
  ```python
  trace_id = os.environ.get("GITLIFT_TRACE_ID", "unknown")
  sys.stderr.write(f"[{trace_id}] [bb_fast_summary] Fetching repository metadata...\n")
  ```
- **Sensitive Data Masking**: All Git clone commands and API URLs containing tokens or passwords must pass through `_mask(text, token)` before being written to stderr. Tokens are replaced with `********` or `REDACTED`.

### 8.2 Rate Limiting Mitigation (Bitbucket Cloud & DC)
1. **Cloud 1,000 Req/Hour Boundary**:
   - Bitbucket Cloud enforces an account-level rate limit of 1,000 requests per hour for standard endpoints.
   - **Mitigation 1 (Payload Optimization)**: Use `fields=size` to retrieve total counts for branches, tags, and pull requests in a single HTTP request without pagination.
   - **Mitigation 2 (Git Protocol Offloading)**: Branch counts, tag counts, and submodule trees are extracted from the local bare clone in `discovery_bitbucket_git_sizer.py`. This costs zero REST API calls.
   - **Mitigation 3 (Layer 1 Client Backoff)**: `ApiRequestBuilder` inspects response headers:
     - `X-RateLimit-NearLimit: true` -> Inserts dynamic sleep jitter.
     - `HTTP 429 Too Many Requests` -> Inspects `Retry-After` header. If present, sleeps for `Retry-After + 10s`.
   - **Mitigation 4 (Layer 2 Temporal Durable Sleep)**: If rate limit quota is exhausted, `ApiRateLimitRetryError` is raised. Temporal intercepts this and triggers a durable workflow timer, putting the activity to sleep without consuming worker pod CPU or memory.
2. **Bitbucket Data Center Instance Throttling**:
   - DC instances utilize administrator-configured rate limiting.
   - Script applies exponential backoff with full jitter:
     $$\text{sleep} = \min\left(300, 2^{\text{attempt}} \times 2.0 + \text{random}(0, 5)\right)$$

### 8.3 Checkpoint & Resume Mechanism for Large Inventories
For the standalone workspace inventory script (`bitbucket_workspace_inventory.py`), enumeration of workspaces with thousands of repositories incorporates checkpointing:
- After every page of 100 repositories is fetched, intermediate progress is flushed to `bitbucket_inventory.checkpoint.json`.
- The checkpoint records `{ "last_cursor": next_url, "processed_count": 1200, "timestamp": "..." }`.
- If interrupted by network failure or rate-limit cutoff, re-invoking the script with `--resume` detects the checkpoint and continues from the exact page offset without re-fetching previous items.

---

## 9. Validation & Success Criteria

### 9.1 Pre-Flight, In-Flight, and Post-Flight Verification

```mermaid
flowchart TD
    subgraph PreFlight["1. Pre-Flight Validation"]
        PF1[Test Bitbucket Connectivity] --> PF2[Validate Source Credentials]
        PF2 --> PF3[Verify Read Scopes]
        PF3 --> PF4[Test Target GHEC Token]
        PF4 --> PF5[Check Rate Limit Headroom]
    end

    subgraph InFlight["2. In-Flight Execution Validation"]
        IF1[Validate API JSON Envelope] --> IF2[Detect Truncated Cursors]
        IF2 --> IF3[Monitor Git Clone Exit Code]
        IF3 --> IF4[Verify git-sizer Blob Metric]
    end

    subgraph PostFlight["3. Post-Flight Audit & Success Criteria"]
        PO1[Reconcile Branch/Tag Counts vs Git Refs] --> PO2[Verify EFS JSON File Integrity]
        PO2 --> PO3[Validate DB MigrationRepoAudit Row]
        PO3 --> PO4[Check discovery_documents Status = DISCOVERY_COMPLETED]
    end

    PreFlight --> InFlight --> PostFlight
```

### 9.2 Acceptance Criteria
The Initial Fast Discovery phase for a repository is considered **COMPLETE** when all of the following conditions are met:
1. **Database Audit State**: A row exists in `git_lift.migration_repo_audit` with `migration_type = 'INITIAL'`, version matching current discovery run, `source_data.completed = true`, and `source_data.discovery_phase = 'fast'`.
2. **Discovery Documents State**: A record in `git_lift.discovery_documents` has status `DISCOVERY_COMPLETED`.
3. **EFS Cache Integrity**: The JSON file at `/mnt/efs/migrations/{job_id}/discovery/{safe_id}_get_project_details.json` exists, is valid JSON, and adheres strictly to the canonical schema defined in Section 6.2.
4. **Git Introspection Coverage**: `git-sizer` maximum blob size, submodule detection, large file buckets (50MB/100MB), and default-branch size-distribution histogram are populated without command failures.
5. **Zero Credential Leakage**: No plain-text tokens or passwords exist in stdout, stderr logs, EFS output files, or database records.

---

## 10. Dependencies & Prerequisites

### 10.1 Python & System Packages
- **Python Version**: `>= 3.10, < 3.13`
- **System Binaries**:
  - `git` CLI (version `>= 2.39.0`)
  - `git-sizer` (pre-compiled binary in PATH)
- **Worker Pod Python Libraries** (available at runtime):
  - `requests >= 2.28.0` / `httpx >= 0.24.0`
  - `sqlalchemy >= 2.0.0`
  - `portalocker >= 2.7.0` (for token file caching)
  - `activities.script_executor.http_client` (`ApiRequestBuilder`)
  - `activities.commons.auth.script_token` (`get_token`)
  - `activities.commons.db.db_session` (`db_session`)
  - `activities.commons.db.discovery_store` (`store_discovery_data`)
  - `models.repo_comparison` (`MigrationRepoAudit`)
  - `models.discovery_documents` (`discovery_documents`)
  - `models.migration_documents` (`migration_documents`)

### 10.2 Permission Requirements
- **Bitbucket Cloud App Password / OAuth Scopes**:
  - `Account: Read`
  - `Workspace membership: Read`
  - `Projects: Read`
  - `Repositories: Read`
  - `Pull requests: Read`
- **Bitbucket Data Center**:
  - Global permission `Bitbucket User` or explicit `PROJECT_READ` / `REPO_READ` on target repositories.
- **Target GHEC EMU Personal Access Token / App**:
  - `repo` (Full control of private repositories)
  - `read:org`, `admin:org` (to inspect organization configuration and membership)

---

## 11. Open Questions & Assumptions

### 11.1 Documented Assumptions
1. **Network Connectivity**: Worker pods have direct egress to `api.bitbucket.org` (for Cloud) or route-table access to internal Bitbucket DC hosts over HTTPS (port 443).
2. **Vault Secret Provisioning**: The GitLift Control Plane has already provisioned source credentials into Vault at `{base_path}/tool/{job_id}_source` before initiating the discovery workflow.
3. **Bitbucket Cloud Wikis**: As confirmed in the spike analysis, native Cloud wikis were deprecated and removed on August 20, 2026. The discovery phase checks wiki existence via `git ls-remote` against the `.wiki.git` endpoint for historical repositories without failing if unreachable.
4. **EMU Username Mapping**: Account UUIDs in Bitbucket Cloud and usernames in Bitbucket DC will be mapped to GHEC EMU usernames during the Migration phase using the external user mapping service; fast discovery records raw source user identifiers without attempting identity resolution.
5. **Project Nesting**: In Bitbucket Cloud, projects cannot be nested. In Bitbucket DC, projects cannot be nested. Therefore, project paths are strictly single-level (`workspace/project/repo` or `PROJECT/repo`).

### 11.2 Edge Cases Handled in Implementation Plan
- **Empty Repositories**: Handled gracefully. If `git-sizer` encounters a repository with zero commits, it records `maximum_blob_size = None`, `size = 0`, and an empty size distribution without failing.
- **Detached / Broken Submodules**: Missing `.gitmodules` files or corrupted gitlink entries are logged to `warnings[]` and return an empty submodule list, never crashing the script.
- **Large Workspace Throttling**: The standalone inventory tool implements cursor checkpointing to resume gracefully across hourly rate-limit resets.
- **Audit Version Collisions**: Dynamic resolution via `_resolve_next_audit_version()` ensures fast discovery (`fd`) and detailed discovery (`d`) runs never overwrite each other's database records.
