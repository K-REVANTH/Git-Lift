# GitLab Hierarchy Dependencies and Target Placement Analysis for GHEC / GHEC EMU

**Analysis Date:** September 24, 2026  
**Project:** PACE Git Lift Enterprise Migration  
**Status:** Ready for Product Owner Review  
**Report Version:** 1.0  
**Integration:** This analysis informs the Git Lift migration pipeline (Connection → Discovery → High-Level & Repository Reports → Planner → Migration → Validation, with Delta Discovery & Delta Sync for post-migration incremental updates).

---

## Executive Summary

This analysis covers the GitLab hierarchy dependencies affecting repository placement during migration to GHEC or GHEC EMU using the PACE Git Lift migration platform. The discovery phase identified:

- **2 Top-level Groups** in scope for placement decision (burner-group1, chiraguniworld-group)
- **3 Nested Subgroup Paths** requiring Git Lift flattening treatment (Git Lift removes nested hierarchy; creates peer repositories)
- **51 Active Projects** requiring target organization assignment (via Git Lift repository tracking)
- **1 Target Enterprise Context** to be selected from available GHEC/GHEC EMU instances
- **6 Critical Blocking Decisions** required before Git Lift can proceed through High-Level & Repository Reports → Planner → Migration phases

**Key Finding:** Naming collision detected on 2 repositories sharing identical name (`thisisrepo`) at different hierarchy levels. This must be resolved before Git Lift's state store can create repositories in the target organization.

The analysis identifies which hierarchy decisions unblock each Git Lift phase and validates acceptance criteria at each decision gate: Connection (auth) → Discovery (metadata collection) → High-Level & Repository Reports (analysis) → Planner (strategy creation) → Migration (execution) → Validation (verification) → Delta operations (sync).

---

## Source Hierarchy Overview

### Confirmed GitLab Hierarchy Structure

Source GitLab Instance discovered structure (input to Git Lift discovery phase):

```
GitLab Instance (gitlab.com)
├── burner-group1 (Top-level Group / Namespace)
│   ├── Direct Projects: 43 repositories
│   ├── subgroup1 (Nested Level 1 - NO DIRECT GHEC EQUIVALENT)
│   │   ├── Direct Projects: 1 repository
│   │   ├── sub-subgroup1 (Nested Level 2 - NO DIRECT GHEC EQUIVALENT)
│   │   │   └── Projects: 4 repositories
│   │   └── sub-subgroup2 (Nested Level 2 - NO DIRECT GHEC EQUIVALENT)
│   │       └── Projects: 2 repositories (includes naming collision)
│   └── [Total contained: 50 repositories]
└── chiraguniworld-group (Top-level Group / Namespace)
    └── Direct Projects: 1 repository
    └── [Total contained: 1 repository]

TOTAL IN-SCOPE REPOSITORIES: 51 (Git Lift target)
```

**Migration Implication:** Git Lift's flattening strategy will remove all nested subgroup levels during repository creation in the target organization. All 7 projects from nested paths will be created as direct repositories under the target organization, sharing the same organizational ownership boundary as the 43 direct projects.

### Source Instance Boundary
- **GitLab Instance:** GitLab SaaS (gitlab.com)
- **Classification:** Single instance migration (no multi-instance consolidation in scope)
- **Git Lift Discovery Input:** Source instance confirmed; API credentials validated during discovery phase
- **Enterprise Context Mapping:** **PENDING** - Git Lift requires enterprise selection before Connection stage

---

## Hierarchy Dependency Analysis

### 1. Enterprise Boundary Dependency

| Field | Value |
|-------|-------|
| **Source Instance** | GitLab SaaS (gitlab.com) |
| **Source Classification** | Single GitLab instance |
| **Git Lift Phase** | Connection → Cannot establish target connection without enterprise selection |
| **Proposed Target Enterprise** | *NEEDS VALIDATION* - Select GHEC or GHEC EMU instance |
| **Enterprise Boundary Decision** | Confirm target GHEC/GHEC EMU enterprise account; validates GitHub App auth capability |
| **Dependency Status** | **Unresolved** |
| **Blocking Status** | **BLOCKING - ALL PHASES** |
| **Affected Git Lift Phases** | Connection (auth validation), Discovery (instance scope filtering), High-Level & Repository Reports (capacity analysis), Planner (scheduling), Migration (target setup), Validation (acceptance), Delta operations (scope) |
| **Git Lift State Store Impact** | Enterprise decision required to initialize state database schema (PostgreSQL Aurora); enables repository metadata tracking through Discovery and Migration execution tracking |
| **Decision Owner** | Product Owner / Customer Leadership |
| **Evidence** | CSV discovery data confirms single instance; enterprise account must exist before Git Lift CLI can connect to GitHub API and create repositories |

**Details:**
- Single GitLab instance confirmed in scope; Git Lift Connection phase will validate API credentials via GitLab API connectivity test
- No multi-instance consolidation complexity identified; single instance simplifies state store initialization (one database connection)
- GHEC or GHEC EMU target enterprise must be pre-selected before Git Lift Connection phase can authenticate to GitHub API via GitHub App token
- Enterprise decision cascades to all downstream organizational hierarchy decisions affecting Discovery scope
- Git Lift state store (PostgreSQL Aurora) requires enterprise selection to initialize schema; enables tracking across Connection → Discovery → Planner → Migration → Delta operations
- EMU (Enterprise Managed Users) vs. standard GHEC affects GitHub App token validation and user mapping strategy during Migration phase (impacts `user_map.py` CSV mapping)

**Decision Required:**
- Which GHEC or GHEC EMU enterprise account will host the migrated organizations?
  - If **EMU**: GitHub App must have EMU provisioning permissions; user mapping strategy required
  - If **Standard GHEC**: Direct GitHub user resolution; simpler auth but different access model
- Should this be a new dedicated enterprise or an existing shared enterprise?
- Is the target enterprise capacity sufficient for 51 repositories + estimated team structure?
- Have GitHub App credentials and API tokens been configured for target enterprise?

---

### 2. Top-Level Group Dependency

#### Group 1: burner-group1

| Field | Value |
|-------|-------|
| **Source Instance** | GitLab SaaS |
| **Source Top-Level Group** | burner-group1 |
| **Source Full Path** | burner-group1 |
| **Direct Child Count** | 43 direct projects + 3 subgroups |
| **Total Contained Projects** | 50 projects (43 direct + 7 in subgroups that will be flattened) |
| **Source Classification** | Direct (primary namespace) |
| **Git Lift Organization Mapping** | 1:1 baseline: burner-group1 → "burner-group1" GitHub organization (discovered and planned by Planner phase) |
| **Target Organization Name** | *NEEDS VALIDATION* (proposed: "burner-group1") |
| **Repository Count After Flattening** | 50 peer repositories under single organization (Planner creates this assignment) |
| **Consolidation Candidate** | No consolidation with chiraguniworld-group identified; business relationship unclear |
| **Split Candidate** | Possible split by regulatory/operational boundary; none currently identified |
| **Git Lift State Store Impact** | Organization decision required for Planner to initialize repository-to-organization mapping tables and sequencing |
| **Dependency Status** | **Needs Validation** |
| **Blocking Status** | **BLOCKING** |
| **Affected Git Lift Phases** | Discovery (scope filtering), High-Level & Repository Reports (organizational analysis), Planner (org assignment), Migration (org creation on GitHub), Validation (placement verification) |
| **Decision Owner** | Product Owner / Operations Leadership |

**Analysis:**
- 43 direct projects at burner-group1 root level will be created as peer repositories in target organization during Migration phase
- Contains 2 nested subgroups (subgroup1 parent; sub-subgroup1, sub-subgroup2 as children) with 7 contained projects
- Git Lift's Planner phase will execute flattening strategy; creates all 7 nested projects as direct repositories (removing hierarchy)
- No regulatory/operational split explicitly identified in Discovery data
- Flat project structure at root level enables efficient Git Lift migration (no prior flattening needed before Discovery)
- **Recommendation:** Map to single target organization (50 peer repositories) unless split criteria identified
- **Migration Risk:** 50 peer repositories in one organization; Git Lift team-based grouping recommended for organizational context in Planner configuration

**Pending Decision:**
- Confirm one-to-one organization mapping for burner-group1 (required for Planner phase)
- Identify any regulatory/operational boundaries requiring split (affects Planner strategy)
- Validate naming convention for target organization (proposed: "burner-group1") (used by Planner for repository naming)
- Define team-based grouping structure for 50 flattened repositories (configured in Planner for access control)

---

#### Group 2: chiraguniworld-group

| Field | Value |
|-------|-------|
| **Source Instance** | GitLab SaaS |
| **Source Top-Level Group** | chiraguniworld-group |
| **Source Full Path** | chiraguniworld-group |
| **Direct Child Count** | 1 direct project |
| **Total Contained Projects** | 1 project |
| **Source Classification** | Direct (separate) |
| **Proposed Target Organization** | *NEEDS VALIDATION* - Default: "chiraguniworld-group" organization |
| **Baseline Mapping** | One-to-one organization mapping |
| **Consolidation Candidate** | Possible - could consolidate with burner-group1 if operationally related |
| **Split Candidate** | No split required (single project) |
| **Dependency Status** | **Needs Validation** |
| **Blocking Status** | **BLOCKING** |
| **Affected Stages** | Discovery, High-Level & Repository Reports, Planner, Migration, Validation |
| **Decision Owner** | Product Owner |

**Analysis:**
- Minimal structure: single top-level group with single project
- No dependency complexity within this group
- Key decision: Keep separate from burner-group1 or consolidate?
- Consolidation feasibility depends on operational/business relationship

**Pending Decision:**
- Should chiraguniworld-group remain a separate target organization?
- Or consolidate as a sub-unit within burner-group1 organization?
- Clarify business relationship between two groups

---

### 3. Nested Subgroup Dependency

#### Subgroup Path 1: burner-group1/subgroup1

| Field | Value |
|-------|-------|
| **Source Instance** | GitLab SaaS |
| **Source Top-Level Group** | burner-group1 |
| **Source Subgroup Path** | burner-group1/subgroup1 |
| **Nesting Level** | Level 1 (immediate child of top-level) |
| **Subgroup Classification** | No direct target equivalent |
| **Direct Children** | 1 direct project + 2 sub-subgroups |
| **Total Contained Projects** | 7 projects (1 direct + 6 nested) |
| **Sub-Children Count** | 2 second-level subgroups |
| **Sub-Children Projects** | sub-subgroup1 (4 projects), sub-subgroup2 (2 projects) |
| **Flattening Treatment** | Subgroup path will be removed; projects placed directly under target organization |
| **Target Organization** | Same as parent: burner-group1 organization |
| **Grouping Context Required** | *NEEDS VALIDATION* - Consider team or naming convention to preserve subgroup identity |
| **Ambiguity Risk** | Moderate: 7 projects from nested path become peers; recommend grouping convention |
| **Dependency Status** | **Needs Validation** |
| **Blocking Status** | **BLOCKING** |
| **Affected Stages** | Planning, Migration, Validation |
| **Decision Owner** | Product Owner / Operations |

**Detailed Analysis:**

**Projects in burner-group1/subgroup1:**
- scriptRepoForDefaultBranch1

**Projects in burner-group1/subgroup1/sub-subgroup1:**
- sub-subgroup1project
- sub-subgroup1project2
- gitlift_automation_depot212
- big-one

**Projects in burner-group1/subgroup1/sub-subgroup2:**
- scriptRepo4
- thisisrepo

**Flattening Impact:**
All 7 projects will become direct repositories under the target "burner-group1" organization, appearing at the same hierarchy level as the 43 direct projects currently at burner-group1 root. This creates a total of 50 peer repositories in a single organization.

**Risk Assessment:**
- **Naming Clarity Risk:** Repository names like "sub-subgroup1project" may lack context after flattening
- **Discovery Risk:** Teams need to understand original source structure from repository naming or metadata
- **Mitigating Factor:** Repository descriptions and team assignments can retain organizational context

**Grouping Mitigation Strategy:**
Preserve organizational identity through:
1. **GitHub Teams:** Create teams reflecting original subgroup structure (e.g., "subgroup1-team", "sub-subgroup1-team")
2. **Repository Naming Convention:** Adopt consistent prefix (e.g., "subgroup1-" prefix for related repositories)
3. **Documentation:** Maintain mapping from original GitLab subgroup paths to repository locations

**Pending Decision:**
- Approve flattening of subgroup1 and all nested levels
- Define grouping convention for 7 flattened projects
- Confirm team-based organization structure in target

---

#### Subgroup Path 2: burner-group1/subgroup1/sub-subgroup1

| Field | Value |
|-------|-------|
| **Source Instance** | GitLab SaaS |
| **Source Top-Level Group** | burner-group1 |
| **Source Subgroup Path** | burner-group1/subgroup1/sub-subgroup1 |
| **Nesting Level** | Level 2 (nested under Level 1 subgroup) |
| **Subgroup Classification** | No direct target equivalent |
| **Direct Projects** | 4 projects |
| **Project Names** | sub-subgroup1project, sub-subgroup1project2, gitlift_automation_depot212, big-one |
| **Flattening Treatment** | Subgroup removed; projects flatten to target organization level |
| **Target Organization** | burner-group1 organization |
| **Target Repository Placement** | Direct repositories under burner-group1 organization |
| **Grouping Context** | Team-based grouping recommended |
| **Dependency Status** | **Needs Validation** |
| **Blocking Status** | **BLOCKING** |
| **Affected Stages** | Planning, Migration, Validation |
| **Decision Owner** | Product Owner |

**Analysis:**
- 4 projects require direct placement under target organization
- Original nesting depth of 2 levels will be completely removed
- Repository naming reflects original subgroup structure (prefix-based)
- No name collisions identified with other projects

**Pending Decision:**
- Confirm team-based grouping for these 4 repositories
- Validate naming convetion to preserve source structure identity

---

#### Subgroup Path 3: burner-group1/subgroup1/sub-subgroup2

| Field | Value |
|-------|-------|
| **Source Instance** | GitLab SaaS |
| **Source Top-Level Group** | burner-group1 |
| **Source Subgroup Path** | burner-group1/subgroup1/sub-subgroup2 |
| **Nesting Level** | Level 2 (nested under Level 1 subgroup) |
| **Subgroup Classification** | No direct target equivalent |
| **Direct Projects** | 2 projects |
| **Project Names** | scriptRepo4, thisisrepo |
| **Flattening Treatment** | Subgroup removed; projects flatten to target organization level |
| **Target Organization** | burner-group1 organization |
| **Target Repository Placement** | Direct repositories under burner-group1 organization |
| **Grouping Context** | Team-based grouping recommended |
| **Naming Collision** | **ALERT:** "thisisrepo" exists at multiple levels |
| **Collision Details** | Found at burner-group1/thisisrepo AND burner-group1/subgroup1/sub-subgroup2/thisisrepo |
| **Collision Resolution** | **REQUIRES DECISION** - Rename one repository to avoid conflict |
| **Dependency Status** | **Needs Validation** |
| **Blocking Status** | **BLOCKING** |
| **Affected Stages** | Planning, Migration, Validation |
| **Decision Owner** | Product Owner |

**Critical Finding - Naming Collision:**

Two repositories share the same name "thisisrepo" at different source levels:
1. `burner-group1/thisisrepo` (Level 1 direct)
2. `burner-group1/subgroup1/sub-subgroup2/thisisrepo` (Level 3 nested)

When flattened to a single organization, both cannot have identical names in GHEC/GHEC EMU.

**Resolution Options:**
1. **Rename nested repository:** `thisisrepo` → `sub-subgroup2-thisisrepo` or `thisisrepo-nested`
2. **Rename direct repository:** `thisisrepo` → `root-thisisrepo`
3. **Consolidate:** Merge nested into direct repository (if appropriate)

**Recommendation:** Rename nested version to preserve lineage: `sub-subgroup2-thisisrepo`

**Pending Decision:**
- **CRITICAL:** Approve collision resolution strategy
- Confirm team-based grouping for these 2 repositories
- Validate renamed repository will not create additional conflicts

---

### 4. Project Placement Dependency

#### Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Projects in Scope** | 75 projects |
| **Projects at Direct Level (Top-level Group root)** | 44 projects |
| **Projects in Nested Subgroups** | 7 projects (need flattening) |
| **Projects Requiring Target Placement Review** | 75 |
| **Projects with Target Organization Confirmed** | 0 (all need validation) |
| **Projects with Naming Conflicts** | 1 (thisisrepo) |
| **Projects with Unique Names** | 74 |

#### Key Projects Requiring Special Attention

**Project 1: Naming Collision - thisisrepo**
- Source Path 1: `burner-group1/thisisrepo`
- Source Path 2: `burner-group1/subgroup1/sub-subgroup2/thisisrepo`
- Conflict: Two repositories with identical name
- Status: **BLOCKING ISSUE**
- Resolution Required: Rename strategy approval

**Project 2: Large Repository - big-one**
- Source Path: `burner-group1/subgroup1/sub-subgroup1/big-one`
- Size: 681.5 MB
- LFS Enabled: Yes, 2 LFS files detected
- Note: Flattening treatment may impact LFS file handling
- Status: Migration staging review recommended

**Project 3: High Activity Repository - HighIssuesMrs**
- Source Path: `burner-group1/HighIssuesMrs`
- Issues: 15 total (14 open, 1 closed)
- Merge Requests: 1437 total
- Note: Complex activity requires careful migration validation
- Status: Requires validation stage planning

**Project 4: Large Repository - scriptRepo3**
- Source Path: `burner-group1/scriptRepo3`
- Commits: 2,423 total
- Authors: 10 team members
- Note: High commit density requires validation
- Status: Performance testing recommended

**Project 5: Enterprise Test Repository - scriptRepo4**
- Source Path: `burner-group1/subgroup1/sub-subgroup2/scriptRepo4`
- Description: "This project is for GitLift Testing"
- Note: Indicates test/migration-specific project; may have special handling
- Status: Clarify production vs. test status

---

### 5. Personal Namespace Dependency

| Finding | Status |
|---------|--------|
| **Personal Namespace Projects** | None identified in discovery data |
| **Personal Namespace Scope** | Out of current scope or not present in GitLab instance |
| **Re-parenting Required** | Not applicable |
| **Dependency Status** | **Resolved - No Personal Namespace Projects** |

**Analysis:**
The discovery data shows all projects belong to groups or group subgroups. No personal namespace projects (projects under user accounts) are included in the migration scope. If personal namespace projects exist outside the current scope, they will require separate handling and re-parenting to an approved organization.

---

### 6. Target Grouping Dependency

**Current Approach:** Team-based grouping within organizations

| Decision Area | Recommendation | Status |
|---------------|-----------------|--------|
| **Grouping Context Preservation** | Use GitHub Teams to represent original subgroup structure | Needs Approval |
| **Team Naming Convention** | Follow pattern: `{original-subgroup-path}` e.g., "subgroup1-team" | Needs Definition |
| **Repository Ownership** | Organizations remain repository owners; teams provide context | Confirmed per baseline |
| **Team Visibility** | Internal/private teams recommended | Needs Approval |
| **Team Permissions** | Triage/maintain access for original subgroup members | Needs Definition |

**Proposed Team Structure:**

```
Organization: burner-group1
├── Team: subgroup1-team (represents burner-group1/subgroup1)
│   └── Members: Subgroup members with original roles
├── Team: sub-subgroup1-team (represents burner-group1/subgroup1/sub-subgroup1)
│   └── Members: Subgroup members with original roles
└── Team: sub-subgroup2-team (represents burner-group1/subgroup1/sub-subgroup2)
    └── Members: Subgroup members with original roles
```

**Dependency Status:** **Needs Validation**  
**Blocking Status:** **NON-BLOCKING** (structure can be defined post-approval)  
**Affected Stages:** Migration, Validation

**Pending Decision:**
- Approve team-based grouping structure
- Define team naming convention
- Determine team permissions and access levels

---

### 7. Migration-Journey Dependency

### Connection Phase

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Source Instance Identification** | GitLab SaaS instance confirmed | ✅ Resolved |
| **Target Enterprise Selection** | Enterprise account must be selected | ⚠️ Blocking |
| **Authentication Configuration** | Connection requires enterprise selection + GitHub App credentials | ⚠️ Blocking |
| **API Access Validation** | Possible after enterprise confirmed; Git Lift validates connectivity via `--check-conn` flag | ⚠️ Pending |
| **Rate Limit Snapshot** | Captured at start of Connection phase before any operations | ⚠️ Pending |

**Phase Can Proceed When:** Enterprise account is selected and GitHub App credentials + GitLab token are provided

**Git Lift Operations:** `pace-git-lift-cli --check-conn` validates both GitLab and GitHub APIs

---

### Discovery Phase

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Enterprise Boundary Confirmed** | Required before Discovery can scope to target enterprise | ⚠️ Blocking |
| **Top-Level Group Mapping Confirmed** | Required to filter Discovery scope to in-scope groups | ⚠️ Blocking |
| **Instance Structure Mapped** | Discovery collects metadata at instance level (organizations, users, groups, repos, storage) | ✅ In Progress |
| **Repository-Level Details** | Discovery collects repo-level metadata (branches, MRs, issues, LFS, languages, releases, tags, CI/CD, webhooks) | ✅ Complete |
| **User Mapping** | If EMU, Discovery collects users for mapping to OKTA identity | ⚠️ Pending |

**Phase Can Proceed When:** Enterprise and top-level group decisions are approved; GitLab API connectivity confirmed

**Git Lift Operations:** `pace-git-lift-cli discovery` collects all repository and project metadata from GitLab SaaS

---

### High-Level & Repository Reports Phase

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Discovery Data Available** | Reports generated from Discovery phase output | ✅ Complete |
| **Instance-Level Analysis** | Report includes: Organization structure, users, groups, total repositories, storage usage | ✅ Available |
| **Repository-Level Analysis** | Report includes per-repo: branches, MRs, LFS usage, languages, releases, tags, CI/CD, webhooks, size | ✅ Available |
| **Organization Mapping Finalized** | Required to assign repositories to target organizations in reports | ⚠️ Blocking |
| **Naming Conflict Analysis** | Reports must identify naming collisions before Planner sequencing | ⚠️ Blocking |

**Phase Can Proceed When:** Discovery is complete and organizational decisions approved

**Git Lift Operations:** Metadata reports generated from Discovery phase data; informs Planner decisions

---

### Planner Phase

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **All Hierarchy Decisions Approved** | Critical gate: cannot create execution strategy without approval | ⚠️ Blocking |
| **Target Organization Structure Finalized** | Required for detailed repository-to-org assignment | ⚠️ Blocking |
| **Team Structure Approved** | Required for Planner to configure team-based access control | ⚠️ Blocking |
| **Migration Sequence Determined** | Planner creates execution order, dependencies, and batch groups | ⚠️ Pending |
| **Naming Conflict Resolution Confirmed** | Required for Planner to assign conflict-free repository names | ⚠️ Blocking |
| **Subgroup Flattening Strategy Approved** | Required for Planner to execute flattening logic | ⚠️ Blocking |

**Phase Can Proceed When:** All unresolved blocking dependencies are approved; High-Level & Repository Reports complete

**Git Lift Operations:** `pace-git-lift-cli plan` creates migration execution strategy, sequencing, and assignments

---

### Migration Phase

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Planner Complete and Approved** | Gate: execution strategy must be finalized | ⚠️ Pending |
| **Target Repositories Created** | Organizations must exist on GitHub (created by Planner strategy) | ⚠️ Pending |
| **Access Structure Configured** | Teams and permissions must be configured per Planner specifications | ⚠️ Pending |
| **Data Migration Execution** | Transfers: Repository history, branches, tags, issues, MRs, wiki, releases, attachments | ⚠️ Pending |
| **LFS File Handling** | Special handling for large repositories with LFS (e.g., big-one repository) | ⚠️ Pending |
| **User Mapping Applied** | EMU user mapping applied during issue/MR/comment migration | ⚠️ Pending |

**Phase Can Proceed When:** Planner phase is complete and approved; dry-run recommended before full execution

**Git Lift Operations:** 
- `pace-git-lift-cli migrate --plan migration-plan.json --dry-run` (recommended first)
- `pace-git-lift-cli migrate --plan migration-plan.json --execute` (actual migration)

---

### Validation Phase

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Migration Complete** | All repositories must be migrated to target | ⚠️ Pending |
| **Target Placement Verification** | Confirm each project in correct target organization | ⚠️ Pending |
| **Subgroup Flattening Confirmation** | Validate no nested organization artifacts exist | ⚠️ Pending |
| **Naming Conflict Resolution Verified** | Confirm no naming duplicates remain post-migration | ⚠️ Pending |
| **Team Membership Validation** | Confirm groups mapped to teams correctly | ⚠️ Pending |
| **Data Integrity Checks** | Verify branches, tags, issues, MRs, wiki migrated correctly | ⚠️ Pending |
| **Customer Acceptance** | Stakeholder approval of placement and data integrity | ⚠️ Pending |

**Phase Can Proceed When:** Migration is complete and ready for verification

**Git Lift Operations:** `pace-git-lift-cli validate` confirms migration success via source-target comparison

---

### Delta Discovery & Delta Sync (Post-Migration)

| Operation | Purpose | Status |
|-----------|---------|--------|
| **Delta Discovery** | Detects newly created or modified objects in source since last sync | ⚠️ Post-Migration |
| **Delta Sync** | Synchronizes incremental changes instead of repeating complete migration | ⚠️ Post-Migration |
| **Scope** | Applies to refs, metadata, MRs/PRs, issues, issue comments, and group milestones | ⚠️ Configured |

**Phase Can Proceed When:** Initial Migration phase is validated; continuous sync enabled during transition period

**Git Lift Operations:** `pace-git-lift-delta-sync` runs incremental synchronization based on Delta Discovery output

---

## Hierarchy Dependency Assessment Summary

### Unresolved Dependencies (BLOCKING)

| # | Dependency | Decision Required | Decision Owner | Affected Git Lift Phases | Priority |
|---|------------|-------------------|-----------------|-------------------------|----------|
| 1 | Enterprise Account Selection | Which GHEC/GHEC EMU enterprise account? | Product Owner / Leadership | All (starts at Connection) | **CRITICAL** |
| 2 | burner-group1 Organization Mapping | Confirm 1:1 mapping to target organization | Product Owner | Discovery, High-Level & Repository Reports, Planner, Migration+ | **CRITICAL** |
| 3 | chiraguniworld-group Decision | Separate org or consolidate with burner-group1? | Product Owner | Discovery, High-Level & Repository Reports, Planner, Migration+ | **CRITICAL** |
| 4 | thisisrepo Naming Collision | Approve resolution strategy for duplicate names | Product Owner / Ops | High-Level & Repository Reports, Planner, Migration+ | **CRITICAL** |
| 5 | Subgroup Flattening Approval | Confirm flattening approach; approve team structure | Product Owner / Ops | High-Level & Repository Reports, Planner, Migration | **CRITICAL** |
| 6 | Team-Based Grouping Convention | Define naming and permission model for teams | Product Owner | Planner, Migration, Validation | **HIGH** |

### Resolved Dependencies (NON-BLOCKING)

| # | Dependency | Resolution | Status |
|---|------------|-----------|--------|
| 1 | Instance Boundary | Single GitLab instance confirmed | ✅ Resolved |
| 2 | Personal Namespace Scope | No personal projects in current scope | ✅ Resolved |
| 3 | Project Count | 75 total projects identified | ✅ Resolved |
| 4 | Nested Subgroup Paths | 3 distinct paths mapped | ✅ Resolved |

---

## Target Placement Matrix

### Organization 1: burner-group1

| Source Path | Source Project Count | Target Org | Target Repository Count | Classification | Flattening Treatment | Grouping Context |
|------------|----------------------|------------|------------------------|-----------------|---------------------|------------------|
| burner-group1 (root) | 43 projects | burner-group1 | 43 repositories | Direct | None (already flat) | Direct org members |
| burner-group1/subgroup1 | 1 project | burner-group1 | 1 repository | Flattened | Subgroup removed | Team: subgroup1-team |
| burner-group1/subgroup1/sub-subgroup1 | 4 projects | burner-group1 | 4 repositories | Flattened | All levels removed | Team: sub-subgroup1-team |
| burner-group1/subgroup1/sub-subgroup2 | 2 projects | burner-group1 | 2 repositories* | Flattened | All levels removed | Team: sub-subgroup2-team |
| **TOTAL** | **50 projects** | **burner-group1** | **50 repositories** | | | |

*Note: Includes naming collision resolution for "thisisrepo"

### Organization 2: chiraguniworld-group (PENDING DECISION)

| Option | Source Projects | Target Org | Target Repositories | Status | Decision |
|--------|-----------------|-----------|---------------------|--------|----------|
| **Option A: Separate Org** | 1 project | chiraguniworld-group | 1 repository | Baseline | Awaiting approval |
| **Option B: Consolidate** | 1 project | burner-group1 | 1 repository (in burner-group) | Alternative | Awaiting decision criteria |

**Pending Decision:** Determine whether chiraguniworld-group should remain separate or consolidate with burner-group1 organization based on business/operational relationship.

---

## Acceptance Criteria Mapping

### AC1: Enterprise Boundary Documentation
**Status:** Pending  
**Requirement:** Given GitLab instance in migration scope, enterprise context shall be documented as highest placement boundary  
**Finding:** Single GitLab instance confirmed; enterprise account selection REQUIRED before documentation can be completed  
**Evidence:** Discovery data shows gitlab.com instance; no multi-instance consolidation  
**Next Step:** Product Owner must select target GHEC/GHEC EMU enterprise  

### AC2: Top-Level Group Classification
**Status:** Needs Validation  
**Requirement:** Top-level groups classified as Direct, Consolidated, or Split with target organization identified  
**Finding:** 2 top-level groups identified:
- burner-group1: Direct mapping recommended; awaiting confirmation
- chiraguniworld-group: Consolidation or separate org pending decision  
**Evidence:** Group discovery from namespace_kind and namespace_full_path fields  
**Next Step:** Approve organization mapping decisions  

### AC3: Default One-to-One Mapping
**Status:** Needs Validation  
**Requirement:** Top-level group without consolidation/split decision maps to one target organization  
**Finding:** burner-group1 has no identified split/consolidation criteria; baseline is one-to-one  
**Evidence:** 50 contained projects; no regulatory/operational boundary identified  
**Next Step:** Confirm one-to-one mapping; document any split criteria if applicable  

### AC4: Direct Project Placement
**Status:** Partial  
**Requirement:** Projects under top-level group without subgroup have one target organization and repository  
**Finding:** 43 direct projects in burner-group1 root; all mapped to burner-group1 organization  
**Evidence:** repo_full_path shows projects directly under burner-group1  
**Next Step:** Validate naming conventions; confirm no collisions  

### AC5: Nested Project Placement
**Status:** Needs Validation  
**Requirement:** Projects under subgroups classified as no direct equivalent; placed under target organization  
**Finding:** 7 nested projects identified across sub-subgroup levels; will be placed directly under burner-group1 org  
**Evidence:** namespace_full_path shows 3-level and 2-level nesting  
**Next Step:** Approve flattening; confirm grouping context via teams  

### AC6: Subgroup Flattening
**Status:** Needs Validation  
**Requirement:** Nested subgroup paths flattened; no nested organizations in target  
**Finding:** Subgroup1 and children (sub-subgroup1, sub-subgroup2) will be removed from ownership hierarchy  
**Evidence:** Target is flat (organization → repositories); teams provide grouping context  
**Next Step:** Approve team-based grouping; confirm no nested org artifacts  

### AC7: Repository Traceability
**Status:** Needs Validation  
**Requirement:** Repositories from multiple subgroups remain traceable; unambiguous placement  
**Finding:** 7 flattened repositories will become peers; naming and team structure preserves identity  
**Evidence:** Repository names reflect source structure (e.g., "sub-subgroup1project"); teams map to source groups  
**Next Step:** Define naming convention; confirm team assignment  

### AC8: Multiple Top-Level Group Assessment
**Status:** Needs Validation  
**Requirement:** Multiple groups classified as separate, consolidated, or split; unresolved decisions marked  
**Finding:** 2 top-level groups; chiraguniworld-group decision pending  
**Evidence:** Separate namespace_full_path entries; independent project sets  
**Next Step:** Approve consolidation/separation decision  

### AC9: Split Group Allocation
**Status:** N/A - Not Applicable  
**Requirement:** Split top-level groups have project-to-organization allocation  
**Finding:** No split requirement identified for current scope  
**Evidence:** No regulatory/operational boundaries documented  
**Note:** If split criteria later identified, AC9 must be revisited  

### AC10: Personal Namespace Classification
**Status:** Resolved - N/A  
**Requirement:** Personal namespace projects classified as re-parented with target organization  
**Finding:** No personal namespace projects identified in scope  
**Evidence:** All projects belong to groups; no user namespace entries in discovery data  
**Status:** **Resolved - No re-parenting required**  

### AC11: Source Classification
**Status:** In Progress  
**Requirement:** All hierarchy levels classified as Direct, Transformed, Consolidated, Split, Re-parented, or No Equiv  
**Classifications Assigned:**
| Source Level | Classification |
|--------------|-----------------|
| burner-group1 (org) | Direct |
| burner-group1 root projects | Direct |
| subgroup1 | No direct equivalent (flattened) |
| sub-subgroup1 | No direct equivalent (flattened) |
| sub-subgroup2 | No direct equivalent (flattened) |
| chiraguniworld-group | Direct (or Consolidated pending decision) |

**Next Step:** Complete pending organizational decisions  

### AC12: Migration Stage Dependency Mapping
**Status:** In Progress  
**Requirement:** Each dependency mapped to affected migration stages  
**Mapping Provided:** Section 7 (Migration-Journey Dependency) documents all stage dependencies  
**Dependencies Mapped:** 7 critical blocking dependencies  
**Next Step:** Validation via stakeholder review  

### AC13: Unresolved Dependency Documentation
**Status:** In Progress  
**Requirement:** Unresolved dependencies identify decision, decision owner, dependency status, blocking status, stages  
**Unresolved Count:** 6 critical blocking dependencies documented  
**Fields Populated:** All required fields present for each dependency  
**Details Provided:**
- Enterprise selection (blocking all stages)
- Organization mapping decisions (blocking Discovery+)
- Naming collision resolution (blocking Planning+)
- Subgroup flattening approval (blocking Planning+)
- Team structure definition (blocking Migration)
- Grouping convention (blocking Migration)

**Next Step:** Schedule decision approval meetings  

### AC14: Blocking Dependency Identification
**Status:** In Progress  
**Requirement:** Blocking dependencies explicitly identify stages that cannot proceed  
**Blocking Dependencies:** 6 identified  
**Blocked Stages:** All stages from Connection through Validation blocked by enterprise decision  
**Stage-Specific Blocks:**
- Connection: Enterprise selection required
- Discovery: Enterprise + org decisions required
- High-Level & Repository Reports: Org analysis required
- Planner: Naming/flattening decisions required
- Migration: All hierarchy decisions + Planner approval required
- Validation: All prior stages required

**Next Step:** Approve blocking dependencies to unblock stages  

### AC15: Final Target Placement Approval
**Status:** Pending  
**Requirement:** Every in-scope project has approved target organization and repository placement  
**Current State:** Placement logic determined; approval pending  
**Proposed Placement:**
| Organization | Repositories | Status |
|--------------|--------------|--------|
| burner-group1 | 50 | Needs Approval |
| chiraguniworld-group | 1 | Needs Decision (separate or consolidate) |
| **TOTAL** | **51** | |

*Note: Total corrected from initial 75 - discovery data analyzed; 75 refers to dataset size, 51 are active/in-scope projects*

**Next Step:** Product Owner approval of placement matrix  

### AC16: Team Grouping Context
**Status:** Needs Validation  
**Requirement:** Teams used only for grouping context; not as repository owners  
**Proposed:**
- Repository Owner: burner-group1 organization (confirmed per baseline)
- Grouping Context: Teams (subgroup1-team, sub-subgroup1-team, sub-subgroup2-team)
- Team Role: Provide access and organizational context; not ownership

**Next Step:** Approve team-based grouping approach  

### AC17: GHEC/GHEC EMU Alignment
**Status:** Confirmed  
**Requirement:** Both GHEC and GHEC EMU use same Enterprise → Organization → Repository model  
**Verification:** Analysis applies same hierarchy model to both targets  
**Model Confirmed:**
- Enterprise Account (highest)
- Organization (owns repositories)
- Repository (lowest)
- Teams (grouping only, don't own)

**Status:** ✅ Confirmed - both targets use identical placement model  

### AC18: Metadata Exclusion
**Status:** Confirmed  
**Requirement:** Assessment excludes metadata comparison, mapping, and migration  
**Scope Adherence:** This analysis focuses solely on hierarchy and placement  
**Excluded Items:** Metadata mapping, metadata rules, permission migration details  
**Next Step:** Separate metadata analysis in follow-on work  

### AC19: Follow-On Story Identification
**Status:** In Progress  
**Requirement:** Approved decisions creating additional customer behavior traced to follow-on stories  
**Identified Follow-On Needs:**
1. **Team Structure Implementation** - Create GitHub teams per approved structure
2. **Repository Naming Convention** - Implement approved naming/prefixing strategy
3. **Access Mapping** - Map GitLab group membership to GitHub team membership
4. **Naming Collision Resolution** - Execute approved thisisrepo naming strategy
5. **Metadata Mapping** - Separate story for metadata/descriptions migration

**Status:** These should be converted to separate stories after approval  
**Next Step:** Create follow-on epics/stories post-approval  

### AC20: Stakeholder Review
**Status:** Ready for Review  
**Requirement:** Product Owner and stakeholders review mapping, flattening, decisions, blocking dependencies, follow-on stories  
**Deliverable Status:** Complete analysis available for review  
**Review Checklist:**
- ✅ Source-to-target mapping documented
- ✅ Flattening treatment approved (pending business decision)
- ✅ Unresolved decisions identified (6 blocking)
- ✅ Blocking dependencies documented with stage impacts
- ✅ Follow-on stories identified
- ⚠️ Awaiting approval/sign-off

**Next Step:** Schedule stakeholder review meeting  

---

## Critical Findings and Alerts

### ALERT 1: Naming Collision - thisisrepo
**Severity:** 🔴 CRITICAL  
**Issue:** Two repositories share identical name at different hierarchy levels
- `burner-group1/thisisrepo` (Direct under top-level)
- `burner-group1/subgroup1/sub-subgroup2/thisisrepo` (Nested, will be flattened)

**Impact:** When Git Lift's Planner phase executes flattening strategy, both repositories cannot coexist with same name in GHEC/GHEC EMU. Git Lift's repository creation workflow (part of Migration phase) will attempt to create duplicate repositories and fail. State database rejects duplicate repository names within same organization scope.

**Git Lift Integration:** This collision will cause Migration phase to fail when `pace-git-lift-cli migrate` attempts to create repositories. The Planner phase (which executes before Migration) must validate naming to create conflict-free sequencing strategy.

**Resolution Required:** BEFORE Planner phase approval; affects repository naming strategy and sequencing

**Recommended Actions:**
1. Rename nested version: `thisisrepo` → `sub-subgroup2-thisisrepo`
2. Document reason for rename in Git Lift migration record
3. Update team assignment to preserve source context (e.g., sub-subgroup2-team)
4. Notify stakeholders of naming change; update any integrations
5. Validate rename in source GitLab before triggering Git Lift delta sync

**Status:** **BLOCKING** - Prevents Planning and Migration Stages

---

### ALERT 2: Enterprise Account Selection Gap
**Severity:** 🔴 CRITICAL  
**Issue:** No target enterprise account has been selected or approved

**Impact:** Git Lift **cannot proceed past Connection phase** without target enterprise. Connection phase requires GitHub API connectivity validation; state store initialization depends on enterprise context to properly scope database schema and repository tracking across all subsequent phases (Discovery, High-Level & Repository Reports, Planner, Migration, Validation, Delta operations).

**Git Lift Integration:** Enterprise selection is required input to `pace-git-lift-cli` Connection phase operations (auth validation via `--check-conn`). State store (PostgreSQL Aurora) requires enterprise selection to initialize schema; enables tracking across Connection → Discovery → Planner → Migration → Delta operations.

**Resolution Required:** BEFORE Connection phase execution

**Recommended Actions:**
1. Determine target enterprise (new or existing GHEC/GHEC EMU)
2. Verify GHEC/EMU capacity for 51 repositories + teams
3. Confirm GitHub App is registered and has appropriate permissions for target enterprise
4. If EMU: validate user mapping strategy and external identity provider (IdP) connectivity
5. Validate enterprise contact and approval authority
6. Document enterprise selection in Git Lift migration configuration

**Status:** **BLOCKING ALL PHASES** - Unblocks Connection → cascades to all downstream phases (Discovery, High-Level & Repository Reports, Planner, Migration, Validation, Delta operations)

---

### ALERT 3: Organization Mapping Decisions Pending
**Severity:** 🟠 HIGH  
**Issue:** Two top-level groups await organizational placement decisions:
1. burner-group1: Assume 1:1 mapping unless split criteria identified
2. chiraguniworld-group: Consolidate or remain separate?

**Impact:** Git Lift's **High-Level & Repository Reports and Planner phases blocked** until organizational structure is finalized. State store requires organization context to initialize migration tracking, sequencing, and delta sync scope.

**Git Lift Integration:** Organization decisions feed into Planner phase's repository assignment logic and sequencing strategy. Team-based grouping for flattened subgroups depends on organization finalization.

**Recommended Actions:**
1. Evaluate operational/business relationships between groups
2. Check for regulatory/compliance boundaries within burner-group1 requiring split
3. Assess whether chiraguniworld-group should be independent organization or consolidated into burner-group1
4. Document approval of organizational structure with business justification
5. Confirm organization names align with GitHub naming conventions

**Status:** **BLOCKING** - Prevents High-Level & Repository Reports, Planner phases, and downstream execution

---

### ALERT 4: Large Repository with LFS
**Severity:** 🟡 MEDIUM  
**Issue:** Repository "big-one" contains 681.5 MB with 2 LFS files

**Git Lift Consideration:** Git Lift's Migration phase supports LFS file migration with dedicated handling via `git/ops.py` LFS operations. Large repository size (681.5 MB) is near GHEC recommendation threshold (5 GB) but within limits. LFS files require special handling during mirror clone and push operations (via `--filter=blob:none` for large repos).

**Impact:** LFS file migration during Migration phase requires validation; may affect migration duration and require monitoring

**Recommended Actions:**
1. Validate Git Lift LFS handling for this repository during dry-run phase (`pace-git-lift-cli migrate --plan migration-plan.json --dry-run` includes LFS validation)
2. Confirm LFS pointer files maintain valid references post-migration
3. Include in Git Lift performance testing and capacity planning (Migration phase benchmark)
4. Monitor Git Lift delta sync operations for LFS-related issues in Delta operations
5. Document LFS file count and size in state store migration tracking record

**Status:** Non-blocking; recommend inclusion in Git Lift testing and monitoring plan (Migration and Delta phases)

---

### ALERT 5: High-Volume Repository Activity
**Severity:** 🟡 MEDIUM  
**Issue:** Repository "HighIssuesMrs" contains:
- 1,437 merge requests
- 15 issues (14 open, 1 closed)
- Significant activity history

**Impact:** Requires extended validation testing; risk of migration delays if issues identified

**Recommended Actions:**
1. Include in detailed validation testing
2. Test merge request reference handling
3. Validate issue tracking post-migration
4. Plan extended review window

**Status:** Non-blocking; recommend detailed validation planning

---

## Business Rules Verification

| Rule | Verification | Status |
|------|--------------|--------|
| Every project placed under exactly one organization | 51 projects assigned to 1-2 organizations | ✅ Confirmed |
| Top-level group maps 1:1 unless consolidation/split decision | burner-group1: 1:1 assumed; chiraguniworld-group: pending | ⚠️ Partial |
| Nested subgroups do not create nested organizations | Subgroups1, sub-subgroup1, sub-subgroup2 will flatten | ✅ Confirmed |
| Nested subgroup levels flatten from ownership path | 3 subgroup levels identified for flattening | ✅ Confirmed |
| Flattening doesn't leave projects without organization | All 7 flattened projects assigned to burner-group1 | ✅ Confirmed |
| Flattened projects become peers in same organization | 50 repositories in burner-group1 organization | ✅ Confirmed |
| One organization per subgroup is NOT default treatment | Flattening consolidates multiple subgroups into single org | ✅ Confirmed |
| Project maps 1:1 to repository unless consolidation/split | No consolidation/split identified | ✅ Confirmed |
| Personal namespace project re-parented to approved organization | No personal namespace projects in scope | N/A |
| Teams preserve context but don't own repositories | Teams proposed for grouping only | ✅ Proposed |
| GHEC and GHEC EMU use same hierarchy model | Same Enterprise → Org → Repo model applies | ✅ Confirmed |
| Source level not represented as target container unless exists | Subgroups won't be created as organizations | ✅ Confirmed |
| Metadata excluded from assessment | No metadata mapping included | ✅ Confirmed |
| Unresolved decisions marked and block stages identified | 6 blocking dependencies documented | ✅ Confirmed |
| Approved decisions creating behavior converted to follow-on stories | 5 follow-on stories identified | ✅ In Progress |

---

## Blocked Stage Analysis

### Stages Blocked Until Decisions Approved

```
BLOCKED STAGES (Cannot Proceed Without Approval)

┌─────────────────────────────────────────────────────────┐
│ CONNECTION STAGE                                         │
│ Status: BLOCKED                                          │
│ Blocking Dependency: Enterprise Account Selection        │
│ Cannot: Connect to target enterprise                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ DISCOVERY STAGE                                          │
│ Status: BLOCKED                                          │
│ Blocking Dependencies: Enterprise + Top-Level Groups     │
│ Cannot: Filter discovery by org structure               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ HIGH-LEVEL & REPOSITORY REPORTS PHASE                   │
│ Status: BLOCKED                                          │
│ Blocking Dependencies: Org Mapping + Naming Collision    │
│ Cannot: Plan complexity/resources                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ PLANNER PHASE                                            │
│ Status: BLOCKED                                          │
│ Blocking Dependencies: All hierarchy decisions           │
│ Cannot: Create detailed migration plan                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ MIGRATION PHASE                                          │
│ Status: BLOCKED (dependent on Planner)                  │
│ Blocking Dependency: Planner phase approval             │
│ Cannot: Execute migration                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ VALIDATION PHASE                                         │
│ Status: BLOCKED (dependent on Migration)                │
│ Blocking Dependency: Migration completion               │
│ Cannot: Validate placement                              │
└─────────────────────────────────────────────────────────┘
```

---

## Definition of Done Verification

- ✅ **Complete GitLab source hierarchy covered** - All 2 top-level groups, 3 subgroup paths, 51 active projects analyzed
- ✅ **Every source level has target classification** - Direct, Flattened, Re-parented classifications assigned
- ✅ **Every in-scope project has proposed placement** - 51 projects assigned to target organizations
- ⚠️ **Every subgroup has flattening treatment** - Flattening strategy defined; approval pending
- ⚠️ **Consolidated/split/re-parented explicitly identified** - Team-based grouping identified; specific team approval pending
- ✅ **Every dependency mapped to stage** - 7 dependencies mapped to affected stages
- ⚠️ **Every unresolved decision identified** - 6 blocking dependencies documented; ownership assigned; awaiting approval
- ✅ **Metadata excluded** - No metadata migration included in analysis
- ⚠️ **Findings attached to ticket** - This report serves as attachment
- ⚠️ **Product Owner review completed** - Ready for review; pending stakeholder meeting

---

## Recommended Next Steps

### Immediate Actions
1. **Schedule Stakeholder Review Meeting**
   - Product Owner review of analysis
   - Discussion of blocking dependencies
   - Decision on enterprise account selection

2. **Enterprise Account Selection**
   - Determine target GHEC/GHEC EMU enterprise
   - Validate capacity and access
   - Document selection decision

3. **Naming Collision Resolution**
   - Approve renaming strategy for "thisisrepo"
   - Document approved name for nested version
   - Plan communication of naming change

### Short-term Actions
4. **Top-Level Group Mapping Approval**
   - Confirm burner-group1 → 1:1 organization mapping
   - Decide: chiraguniworld-group separate or consolidated
   - Document approval

5. **Subgroup Flattening Approval**
   - Approve flattening of 3 subgroup paths
   - Confirm team-based grouping approach
   - Define team naming convention

6. **Convert to Follow-On Stories**
   - Team structure implementation
   - Naming convention adoption
   - Access mapping strategy
   - Metadata migration planning

### Preparation Actions
7. **Planner Phase Preparation**
   - Detailed repository-to-organization sequencing
   - Resource allocation planning
   - Risk assessment and mitigation for flattening strategy
   - Migration execution and validation test planning

### Execution Actions
8. **High-Level & Repository Reports Phase**
   - Comprehensive instance and repository-level metadata analysis
   - Organizational placement analysis
   - Complexity and risk assessment

9. **Planner Phase**
   - Execute Planner to create migration strategy
   - Validate sequencing logic
   - Confirm all assignments align with decisions

10. **Migration Phase Execution**
    - Execute initial `--dry-run` to validate all operations
    - Execute actual migration via `pace-git-lift-cli migrate --execute`
    - Monitor execution and track progress in state store
    - Complete Validation phase checks post-migration

---

## Summary of Decisions Required

### DECISION 1: Enterprise Account Selection
- **Question:** Which GHEC or GHEC EMU enterprise account will host migrated organizations?
- **Options:**
  - New dedicated enterprise (isolated for this migration)
  - Existing shared enterprise (consolidate with current infrastructure)
- **Git Lift Phase Impact:** **UNBLOCKS Connection phase** → enables `pace-git-lift-cli --check-conn` validation and all downstream phases
- **Git Lift Integration:** Enterprise selection is prerequisite for Connection phase auth validation. State store (PostgreSQL Aurora) initialization requires enterprise context for all subsequent phases (Discovery, High-Level & Repository Reports, Planner, Migration, Validation, Delta operations)
- **Owner:** Product Owner / Executive Leadership
- **Timeline:** **CRITICAL** - Required by end of week 1

### DECISION 2: burner-group1 Organization Mapping
- **Question:** Confirm burner-group1 maps to single target organization?
- **Options:**
  - Yes, 1:1 mapping (baseline, 50 repositories in single org)
  - Split across multiple organizations (specify split criteria)
- **Git Lift Phase Impact:** **UNBLOCKS Discovery** phase (scope filtering) → **informs High-Level & Repository Reports** (org analysis) → **required for Planner** (org assignment)
- **Git Lift Integration:** Organization decision required to configure repository tracking scope in state store. Planner phase uses this mapping to create org-to-repository assignment strategy
- **Owner:** Product Owner
- **Timeline:** Required before High-Level & Repository Reports analysis

### DECISION 3: chiraguniworld-group Organization
- **Question:** Should chiraguniworld-group remain separate or consolidate?
- **Options:**
  - Separate: Create independent chiraguniworld-group organization
  - Consolidate: Move project to burner-group1 organization
  - Clarify operational relationship before deciding
- **Git Lift Phase Impact:** **UNBLOCKS High-Level & Repository Reports analysis** → **required for Planner** organizational scope finalization
- **Git Lift Integration:** Organization count affects state store schema complexity and Planner's repository assignment logic. Determines whether 1 or 2 organizations are created in Migration phase
- **Owner:** Product Owner
- **Timeline:** Required before Planner phase execution

### DECISION 4: thisisrepo Naming Collision Resolution
- **Question:** How to resolve duplicate "thisisrepo" names?
- **Options:**
  - Rename nested: thisisrepo → sub-subgroup2-thisisrepo
  - Rename direct: thisisrepo → root-thisisrepo
  - Consolidate repositories (merge if appropriate)
- **Git Lift Phase Impact:** **BLOCKS High-Level & Repository Reports analysis** → **BLOCKS Planner execution** → **BLOCKS Migration phase repository creation**
- **Git Lift Integration:** Naming collision will cause Migration phase `pace-git-lift-cli migrate` to fail when attempting duplicate repository creation. Planner phase must validate naming to create conflict-free sequencing strategy. Resolution must be validated in Discovery phase before Planner execution
- **Owner:** Product Owner / Ops Leadership
- **Timeline:** **CRITICAL** - Must resolve before Planner phase execution

### DECISION 5: Subgroup Flattening Approval
- **Question:** Approve complete removal of 3 subgroup hierarchy levels?
- **Options:**
  - Yes, approve flattening (7 nested projects become peer repositories)
  - No, request alternative hierarchy model (not GHEC/GHEC EMU compatible)
- **Git Lift Phase Impact:** **UNBLOCKS Planner phase** → confirms flattening strategy is valid for sequencing
- **Git Lift Integration:** Flattening approval required to configure Planner's repository creation strategy via `migration/mapping.py` logic. No alternative exists in GHEC/GHEC EMU target (no nested organizations supported)
- **Owner:** Product Owner
- **Timeline:** Required before Planner phase execution

### DECISION 6: Team-Based Grouping Structure
- **Question:** Approve GitHub Teams to represent original subgroup structure?
- **Options:**
  - Yes, create teams: subgroup1-team, sub-subgroup1-team, sub-subgroup2-team
  - Alternative: Different grouping strategy (specify)
- **Git Lift Phase Impact:** **INFORMS Planner** → team structure affects migration execution strategy and access control configuration
- **Git Lift Integration:** Team structure decision influences Planner's access control assignments. Manual team creation required post-Migration phase (Git Lift creates repos, not teams). Team membership mapping configured via user_map.py during Migration phase
- **Timeline:** Required before Migration phase execution

---

## Follow-On Story Requirements

Based on approved hierarchy decisions, create the following follow-on stories:

### Story 1: GitHub Team Structure Implementation
**Title:** Create GitHub Teams for Organizational Context  
**Description:** Implement team-based grouping structure to preserve original GitLab subgroup context  
**Tasks:**
- Create teams: subgroup1-team, sub-subgroup1-team, sub-subgroup2-team
- Assign repositories to appropriate teams
- Configure team permissions and access levels
- Document team-to-source-group mapping

**Dependencies:** Approval of team-based grouping decision

---

### Story 2: Repository Naming Convention Implementation
**Title:** Apply Approved Naming Convention to Flattened Repositories  
**Description:** Ensure flattened repositories retain source context through naming  
**Tasks:**
- Implement naming prefix strategy (if approved)
- Update repository descriptions to indicate source origin
- Document naming rationale in repository metadata
- Create reference guide mapping names to source paths

**Dependencies:** Subgroup flattening approval; naming convention definition

---

### Story 3: Naming Collision Resolution
**Title:** Execute thisisrepo Naming Collision Resolution  
**Description:** Resolve duplicate "thisisrepo" naming before migration  
**Tasks:**
- Rename approved repository (nested or direct per decision)
- Update all references in documentation
- Notify team members of name change
- Update team assignments to reflect new name

**Dependencies:** Naming collision resolution approval

---

### Story 4: Access and Team Membership Mapping
**Title:** Map GitLab Group Membership to GitHub Team Membership  
**Description:** Establish access structure matching original GitLab organization  
**Tasks:**
- Audit GitLab group membership for each group/subgroup
- Map members to corresponding GitHub teams
- Configure team permissions (triage/maintain/admin)
- Validate access structure pre-migration

**Dependencies:** Team structure approval; member discovery

---

### Story 5: Metadata and Documentation Migration
**Title:** Migrate Repository Metadata and Documentation  
**Description:** Preserve repository descriptions, wikis, and organizational metadata  
**Tasks:**
- Map GitLab repository descriptions to GitHub
- Migrate wiki content where applicable
- Document source hierarchy in repository descriptions
- Create migration guide for teams

**Dependencies:** All hierarchy decisions approved

---

## Assumptions and Validation Requirements

### Assumptions

1. ✓ One top-level GitLab group maps to one target organization by default
2. ⚠️ Nested subgroup paths are flattened into the target organization mapped from top-level group *(Pending Approval)*
3. ✓ One GitLab project maps to one target repository by default
4. N/A Personal namespace projects are placed under an approved organization *(No personal projects in scope)*
5. ✓ GHEC and GHEC EMU follow the same repository placement hierarchy
6. ⚠️ Teams may retain grouping context but cannot own repositories *(Proposed for Approval)*
7. ⚠️ The approved target model may allow consolidation or split where documented decision exists *(Pending Decisions)*

### Validation Requirements

**Pre-Migration Validation Checklist:**

- [ ] Enterprise account selection confirmed and validated
- [ ] Target organization structure approved
- [ ] Naming collision resolution approved and executed
- [ ] Subgroup flattening approved
- [ ] Team structure approved and implemented
- [ ] All 51 projects have confirmed target placement
- [ ] No naming conflicts remain post-resolution
- [ ] Access structure configured and tested
- [ ] Documentation updated with approved hierarchy
- [ ] Stakeholders have reviewed and approved placement matrix

**Post-Migration Validation Checklist:**

- [ ] All 51 repositories present in target organizations
- [ ] No nested organization artifacts exist
- [ ] All repositories under exactly one organization
- [ ] Team membership correctly reflects source groups
- [ ] Naming collision resolution verified
- [ ] Access permissions match approved structure
- [ ] Repository descriptions preserve source context
- [ ] Stakeholder acceptance obtained

---

## Appendix A: Detailed Subgroup Project Listing

### burner-group1/subgroup1 Direct Project (1)
- scriptRepoForDefaultBranch1

### burner-group1/subgroup1/sub-subgroup1 Projects (4)
- sub-subgroup1project
- sub-subgroup1project2
- gitlift_automation_depot212
- big-one

### burner-group1/subgroup1/sub-subgroup2 Projects (2)
- scriptRepo4
- thisisrepo **(NAMING COLLISION ALERT)**

---

## Appendix B: Critical Path for Migration Approval

```
START
  │
  ├─→ [DECISION 1] Enterprise Account Selection ──→ GATES Connection Stage
  │
  ├─→ [DECISION 2] burner-group1 Organization Mapping
  │   └─→ GATES Discovery Stage
  │
  ├─→ [DECISION 3] chiraguniworld-group Organization
  │   └─→ GATES Discovery Stage
  │
  ├─→ [DECISION 4] Naming Collision Resolution
  │   └─→ GATES Planner Phase
  │
  ├─→ [DECISION 5] Subgroup Flattening Approval
  │   └─→ GATES Planner Phase
  │
  └─→ [DECISION 6] Team-Based Grouping Structure
      └─→ GATES Migration Stage

Once ALL DECISIONS Approved:
  │
  ├─→ Discovery Stage (Enabled)
  ├─→ High-Level & Repository Reports Phase (Enabled)
  ├─→ Planner Phase (Enabled)
  ├─→ Migration Stage (Enabled)
  ├─→ Validation Stage (Enabled)
  │
  └─→ END (Complete)

```

---

## Appendix C: Stakeholder Review Checklist

**Pre-Review Preparation:**
- [ ] Read Executive Summary (this section)
- [ ] Review Hierarchy Dependency Analysis (Section 3)
- [ ] Review Critical Findings and Alerts (highlighted sections)
- [ ] Review required Decisions (highlighted sections)

**Review Meeting Agenda:**

1. **Enterprise Account Selection** (Decision 1)
   - Which GHEC/GHEC EMU enterprise?
   - New or existing account?
   - Capacity validation

2. **Organization Structure** (Decisions 2-3)
   - Confirm burner-group1 1:1 mapping
   - Resolve chiraguniworld-group consolidation question

3. **Technical Blocking Issues** (Decision 4)
   - Address thisisrepo naming collision
   - Approve resolution approach

4. **Hierarchy Transformation** (Decision 5)
   - Approve subgroup flattening approach
   - Confirm no alternative models needed

5. **Team-Based Grouping** (Decision 6)
   - Review proposed team structure
   - Approve naming conventions
   - Confirm permission model

6. **Timeline and Next Steps**
   - Identify decision urgency
   - Assign decision owners
   - Schedule follow-up reviews

---

## Git Lift Integration and Implementation Path

### How This Analysis Feeds Git Lift Migration Pipeline

The hierarchy decisions documented in this analysis directly enable the PACE Git Lift migration platform to execute the enterprise migration workflow across all phases:

#### Phase 1: Connection (Requires DECISION 1)
- **Dependency:** Enterprise account selection (DECISION 1)
- **Git Lift Action:** `pace-git-lift-cli --check-conn` validates GitLab and GitHub API connectivity
- **Operations:** 
  - Verifies `GITLAB_TOKEN` and `GITHUB_APP_TOKEN` presence
  - Tests GitLab API, GitHub API, and state database connectivity
  - Validates version compatibility
  - Acquires advisory lock for target repository (if enabled)
- **State Store:** Initializes PostgreSQL Aurora connection; creates schema for enterprise context
- **Blocking Gate:** Cannot proceed without enterprise selection and credentials approved

#### Phase 2: Discovery (Requires DECISIONS 1-3)
- **Dependency:** Enterprise selection + organization mapping (DECISIONS 1, 2, 3)
- **Git Lift Action:** `pace-git-lift-cli discovery` collects metadata from GitLab SaaS
- **Instance-Level Collection:** Organizations, users, groups, total repositories, storage usage
- **Repository-Level Collection:** Branches, merge requests, LFS usage, languages, releases, tags, CI/CD, webhooks, repository size
- **State Store:** Records all repository metadata, hierarchy, user information, and source context from GitLab API
- **Blocking Gate:** Organization scope must be finalized for discovery filtering; authentication validated in Connection phase

#### Phase 3: High-Level & Repository Reports (Requires DECISIONS 1-3)
- **Dependency:** Discovery complete; organizational decisions approved (DECISIONS 2-3)
- **Git Lift Action:** Generates metadata reports at instance and repository levels
- **Instance-Level Report:** Organizational structure analysis, user count, group hierarchy, total repository count, storage assessment
- **Repository-Level Report:** Complexity analysis per repository, LFS impact assessment, naming conflict identification, team structure requirements
- **State Store:** Stores analysis results and reports for Planner phase consumption
- **Blocking Gate:** Naming conflict resolution (DECISION 4) must be identified before Planner phase

#### Phase 4: Planner (Requires DECISIONS 1-6)
- **Dependency:** All hierarchy and structural decisions approved (DECISIONS 1-6)
- **Git Lift Action:** `pace-git-lift-cli plan` creates migration execution strategy
- **Operations:**
  - Creates repository-to-organization assignment mapping
  - Determines migration sequencing and dependency order
  - Generates batch groups for parallel execution
  - Configures team-based access control strategy (if applicable)
  - Validates naming uniqueness within organization scopes
  - Plans LFS handling strategy for identified large repositories
- **State Store:** Records migration schedule, sequence order, team assignments, validation rules, and execution batches
- **Blocking Gate:** All hierarchy decisions must be approved; naming conflict resolution confirmed before sequencing

#### Phase 5: Migration (Executes planned work)
- **Dependency:** Planner complete and approved; all hierarchy decisions confirmed
- **Git Lift Action:** 
  - `pace-git-lift-cli migrate --plan migration-plan.json --dry-run` (recommended validation first)
  - `pace-git-lift-cli migrate --plan migration-plan.json --execute` (actual execution)
- **Transfers:** Repository history, branches, tags, issues, merge requests, wiki, releases, attachments
- **Operations:**
  - Creates target organizations on GHEC/GHEC EMU (per org mapping)
  - Executes `git clone --mirror` from GitLab for each repository
  - Handles LFS files via specialized rewrite flows for large repos
  - Migrates issues and merge requests with user mapping (EMU) if applicable
  - Applies GitHub App-based authentication for all operations
  - Tracks execution state in PostgreSQL Aurora state store
- **State Store:** Real-time tracking of repository creation, ref migration, metadata sync, delta tracking
- **Special Handling:**
  - Subgroup flattening (DECISION 5): Removes all nested paths; creates 50 peer repositories under burner-group1
  - Naming collision (DECISION 4): Applies approved rename strategy to eliminate duplicates
  - LFS handling (Alert 4): Special handling for "big-one" repository (681.5 MB with 2 LFS files)
  - User mapping (if EMU): Applies CSV user mapping for issue/MR/comment attribution

#### Phase 6: Validation (Post-migration verification)
- **Dependency:** Migration complete; all repositories created in target
- **Git Lift Action:** `pace-git-lift-cli validate` compares source and target repositories
- **Verification Points:**
  - Confirms all 50-51 repositories present in target organizations
  - Validates no nested organization artifacts exist (flattening confirmed)
  - Confirms no naming duplicates remain after collision resolution
  - Verifies team membership assignments (if teams configured)
  - Checks data integrity (branches, tags, issues, MRs, wiki)
  - Confirms LFS files remain valid post-migration
- **State Store:** Records verification results, placement confirmation, team membership validation
- **Customer Acceptance:** Stakeholder sign-off on placement and data integrity

#### Phase 7: Delta Discovery & Delta Sync (Post-migration, ongoing)
- **Dependency:** Initial Migration and Validation complete
- **Purpose:** Detects and synchronizes incremental changes during transition period
- **Scope:** Refs, metadata, merge requests, issues, issue comments, group milestones
- **Git Lift Action:** `pace-git-lift-delta-sync` handles ongoing incremental updates
- **Operations:**
  - Runs incrementally rather than repeating complete migration
  - Synchronizes only changes since last migration/sync
  - Maintains state store records for delta tracking
  - Enables smooth transition period before final cutover
- **State Store:** Maintains delta tracking records and completion timestamps

### Workflow Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ DECISION 1 REQUIRED: Enterprise Account Selection              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Connection Phase: pace-git-lift-cli --check-conn              │
│ - Validates GitLab + GitHub API connectivity                  │
│ - Initializes state store schema                              │
│ - Acquires repository lock (if enabled)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
   ┌────────▼──────┐          ┌──────────▼─────┐
   │ DECISION 2-3  │          │  DECISION 4-5  │
   │ ORG MAPPING   │          │ NAMING / FLAT  │
   └────────┬──────┘          └──────────┬─────┘
            │                             │
            └──────────────┬──────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Discovery Phase: pace-git-lift-cli discovery                   │
│ - Collects instance + repo metadata from GitLab SaaS           │
│ - Records users, groups, projects, storage                     │
│ - Populates state store with all discovery data                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ High-Level & Repository Reports Phase                          │
│ - Analyzes discovery data at instance + repo levels            │
│ - Identifies complexity, LFS impact, naming conflicts          │
│ - Prepares metadata for Planner consumption                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┴────────────────┐
           │                                │
   ┌───────▼──────┐             ┌──────────▼─────┐
   │ DECISION 6   │             │ All Decisions  │
   │ TEAM GROUPING│             │ Must Be Approved│
   └───────┬──────┘             └──────────┬─────┘
           │                               │
           └───────────────┬───────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Planner Phase: pace-git-lift-cli plan                           │
│ - Creates execution strategy + sequencing                       │
│ - Assigns repos to target organizations                        │
│ - Configures team-based access control                         │
│ - Generates migration batches                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Migration Phase (DRY-RUN): pace-git-lift-cli migrate --dry-run │
│ - Validates all operations without making changes              │
│ - Tests LFS handling, naming, flattening strategy              │
│ - Generates detailed execution plan                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                  (Review & Validate)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Migration Phase (EXECUTE): pace-git-lift-cli migrate --execute │
│ - Creates target organizations on GHEC/GHEC EMU                │
│ - Migrates repository content, branches, tags                  │
│ - Transfers issues, MRs, wiki, releases, attachments           │
│ - Applies naming collision resolution + flattening             │
│ - Tracks all operations in state store                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Validation Phase: pace-git-lift-cli validate                    │
│ - Confirms all 50-51 repos in target orgs                      │
│ - Verifies no nested org artifacts (flattening confirmed)      │
│ - Confirms no naming duplicates                                │
│ - Validates team assignments + data integrity                  │
│ - Records verification results in state store                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                  (Stakeholder Sign-Off)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Delta Operations (Post-Migration, Optional)                     │
│ - pace-git-lift-delta-sync for incremental updates             │
│ - Synchronizes changes during transition period                │
│ - Maintains state store delta tracking                         │
└─────────────────────────────────────────────────────────────────┘
```

### Git Lift Configuration from Hierarchy Decisions

```yaml
# Git Lift configuration generated from this analysis
# File: migration_config.yaml (used by Planner phase)

source:
  instance: gitlab.com
  authentication:
    token_env: GITLAB_TOKEN
    api_scope: [api, read_repo]

target:
  enterprise: <DECISION 1 - TO BE SELECTED>
  platform: GHEC  # or GHEC-EMU
  authentication:
    github_app_id_env: GITHUB_APP_ID
    github_app_token_env: GITHUB_APP_TOKEN
    github_installation_id_env: GITHUB_INSTALLATION_ID

state_store:
  type: postgres
  connection: aurora-prod  # PostgreSQL Aurora
  database: scm_migration_state
  schema_version: 1.0

organizations:
  - name: burner-group1
    source_path: burner-group1
    repository_count: 50
    flattening:
      enabled: true
      source_subgroups: [subgroup1, sub-subgroup1, sub-subgroup2]
      behavior: flatten_to_peer_repositories
  - name: chiraguniworld-group
    source_path: chiraguniworld-group
    repository_count: 1
    decision: <DECISION 3 - PENDING>
    flattening:
      enabled: false

special_handling:
  naming_collision:
    repositories:
      - source_1: burner-group1/thisisrepo
        source_2: burner-group1/subgroup1/sub-subgroup2/thisisrepo
    resolution: <DECISION 4 - TO BE APPROVED>
    options:
      - rename_nested_to: sub-subgroup2-thisisrepo
      - rename_direct_to: root-thisisrepo
  
  lfs:
    repositories:
      - name: big-one
        size_mb: 681.5
        lfs_file_count: 2
        handling: special_rewrite_flow
  
  team_grouping:
    strategy: <DECISION 6 - TO BE APPROVED>
    teams:
      - name: subgroup1-team
        repositories: [scriptRepoForDefaultBranch1]
        permissions: maintain
      - name: sub-subgroup1-team
        repositories: [sub-subgroup1project, sub-subgroup1project2, gitlift_automation_depot212, big-one]
        permissions: maintain
      - name: sub-subgroup2-team
        repositories: [scriptRepo4, <thisisrepo-renamed>]
        permissions: maintain

user_mapping:
  type: emu  # if EMU selected in DECISION 1
  csv_path: user_mapping.csv
  identity_provider: okta

risk_assessment:
  high_volume_repos:
    - name: HighIssuesMrs
      merge_requests: 1437
      issues: 15
  large_repos:
    - name: big-one
      size_mb: 681.5
      lfs_files: 2

migration_parameters:
  dry_run_first: true
  batch_size: 10
  parallel_repos: 3
  delta_sync_enabled: true
  delta_sync_schedule: daily
```

### Handoff to Git Lift Workflow

Once all 6 decisions are approved:

1. **Update Git Lift Configuration**
   - Populate `target.enterprise` from DECISION 1
   - Finalize organization mapping from DECISIONS 2-3
   - Confirm naming resolution strategy from DECISION 4
   - Set subgroup flattening behavior from DECISION 5
   - Apply team grouping configuration from DECISION 6

2. **Execute Connection Phase**
   - Run `pace-git-lift-cli --check-conn` to validate enterprise connectivity
   - Confirm GitHub App credentials are valid for target enterprise
   - Verify state store (PostgreSQL Aurora) connection
   - Validate GitLab API token

3. **Proceed Through Remaining Phases**
   - Discovery collects source repository metadata
   - High-Level & Repository Reports analyzes discovery data
   - Planner finalizes execution strategy and sequencing
   - Migration (dry-run first) executes repository creation and data sync
   - Validation confirms placement, team assignments, data integrity
   - Delta Sync handles incremental updates during transition period

---

## Document Control

| Field | Value |
|-------|-------|
| **Report Title** | GitLab Hierarchy Dependencies and Target Placement Analysis for GHEC / GHEC EMU |
| **Project** | PACE Git Lift Enterprise Migration Platform |
| **Version** | 1.0 |
| **Status** | Ready for Product Owner Review |
| **Scope** | GitLab SaaS (gitlab.com): 2 top-level groups, 3 subgroup paths, 51 active projects requiring target placement in GHEC/GHEC EMU |
| **Target Systems** | GitHub Enterprise Cloud (GHEC) and GHEC with Enterprise Managed Users (EMU) |
| **Integration** | This analysis is a deliverable input to the Git Lift migration platform pipeline. Hierarchy decisions enable Connection → Discovery → High-Level & Repository Reports → Planner → Migration → Validation phases (with Delta Discovery & Delta Sync for post-migration operations). |
| **Related Artifacts** | Git Lift Configuration (generated upon decision approval), Git Lift Migration Plan (generated during Planner phase), Git Lift State Database (PostgreSQL Aurora; tracks repository and organizational placement across all phases) |
| **Next Review** | Post-decision implementation; upon Git Lift Planner phase approval and Migration dry-run validation |

---

**Report prepared for:** Analyse GitLab Hierarchy Dependencies and Target Placement for GHEC / GHEC EMU migration (Git Lift project)

**Current Status:** Ready for stakeholder review. **6 blocking decisions** require Product Owner approval before Git Lift can proceed beyond Discovery phase.

**Next Action:** Schedule decision review meeting. Approval of DECISION 1 unblocks Connection stage immediately; approvals of DECISIONS 2-6 enable full pipeline execution.

**Integration Note:** This analysis document serves as the authoritative reference for organizational and hierarchy decisions throughout the Git Lift migration lifecycle. Updates to this analysis require project tracking and stakeholder communication.
