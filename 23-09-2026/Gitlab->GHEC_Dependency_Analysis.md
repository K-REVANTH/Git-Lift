# GitLab Hierarchy Dependencies and Target Placement Analysis for GHEC / GHEC EMU

**Analysis Date:** September 24, 2026  
**Executed By:** Revanth (Analysis Team)  
**Status:** Ready for Product Owner Review  
**Report Version:** 1.0

---

## Executive Summary

This analysis covers the GitLab hierarchy dependencies affecting repository placement during migration to GHEC or GHEC EMU. The discovery data reveals:

- **2 Top-level Groups** identified in scope
- **2 Nested Subgroup Paths** requiring flattening treatment
- **75 Total Projects** across all hierarchy levels
- **1 Target Enterprise Context** (to be confirmed)
- **Multiple Target Organization Decisions** pending approval

The analysis identifies which hierarchy decisions must be resolved before each migration stage can proceed.

---

## Source Hierarchy Overview

### Confirmed GitLab Hierarchy Structure

```
GitLab Instance
├── burner-group1 (Top-level Group)
│   ├── Direct Projects (43 projects)
│   ├── subgroup1 (Nested Level 1)
│   │   ├── Direct Projects (1 project)
│   │   ├── sub-subgroup1 (Nested Level 2)
│   │   │   └── Projects (4 projects)
│   │   └── sub-subgroup2 (Nested Level 2)
│   │       └── Projects (2 projects)
│   └── [Other structure elements]
└── chiraguniworld-group (Top-level Group)
    └── Direct Projects (1 project)
```

### Source Instance Boundary
- **GitLab Instance:** GitLab SaaS (gitlab.com)
- **Classification:** Single instance migration
- **Enterprise Context Mapping:** Not yet determined

---

## Hierarchy Dependency Analysis

### 1. Enterprise Boundary Dependency

| Field | Value |
|-------|-------|
| **Source Instance** | GitLab SaaS (gitlab.com) |
| **Source Classification** | Single GitLab instance |
| **Proposed Target Enterprise** | *NEEDS VALIDATION* |
| **Enterprise Boundary Decision** | Select target GHEC or GHEC EMU enterprise account |
| **Dependency Status** | **Unresolved** |
| **Blocking Status** | **BLOCKING** |
| **Affected Stages** | Connection, Discovery, Estimation, Planning, Migration, Validation |
| **Decision Owner** | Product Owner / Customer Leadership |
| **Evidence** | CSV discovery data shows single instance; enterprise selection required before resource allocation |

**Details:**
- Single GitLab instance is confirmed in scope
- No multi-instance consolidation complexity identified at this stage
- GHEC or GHEC EMU target must be pre-selected before proceeding
- This decision affects all downstream organizational hierarchy decisions

**Decision Required:**
- Which GHEC or GHEC EMU enterprise account will host the migrated organizations?
- Should this be a new dedicated enterprise or an existing shared enterprise?

---

### 2. Top-Level Group Dependency

#### Group 1: burner-group1

| Field | Value |
|-------|-------|
| **Source Instance** | GitLab SaaS |
| **Source Top-Level Group** | burner-group1 |
| **Source Full Path** | burner-group1 |
| **Direct Child Count** | 43 direct projects + 3 subgroups |
| **Total Contained Projects** | 50 projects (43 direct + 7 in subgroups) |
| **Source Classification** | Direct (primary) |
| **Proposed Target Organization** | *NEEDS VALIDATION* - Default: "burner-group1" organization |
| **Baseline Mapping** | One-to-one organization mapping |
| **Consolidation Candidate** | No consolidation identified |
| **Split Candidate** | Possible split by regulatory/operational boundary (requires validation) |
| **Dependency Status** | **Needs Validation** |
| **Blocking Status** | **BLOCKING** |
| **Affected Stages** | Discovery, Estimation, Planning, Migration, Validation |
| **Decision Owner** | Product Owner / Operations Leadership |

**Analysis:**
- 43 direct projects in burner-group1 root level
- Contains 2 subgroups with nested projects
- No regulatory/operational split explicitly identified in discovery data
- Recommend: Map to single target organization unless split criteria identified
- Flat project structure at root level enables direct repository migration

**Pending Decision:**
- Confirm one-to-one organization mapping for burner-group1
- Identify any regulatory/operational boundaries requiring split
- Validate naming convention for target organization

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
| **Affected Stages** | Discovery, Estimation, Planning, Migration, Validation |
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

#### Connection Stage

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Source Instance Identification** | GitLab SaaS instance confirmed | ✅ Resolved |
| **Target Enterprise Selection** | Enterprise account must be selected | ⚠️ Blocking |
| **Authentication Configuration** | Connection requires enterprise selection | ⚠️ Blocking |
| **API Access Validation** | Possible after enterprise confirmed | ⚠️ Pending |

**Stage Can Proceed When:** Enterprise account is selected and validated for connection capability

---

#### Discovery Stage

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Enterprise Boundary Confirmed** | Required before discovery filtering | ⚠️ Blocking |
| **Top-Level Group Mapping Confirmed** | Required to scope discovery scope | ⚠️ Blocking |
| **Instance Structure Mapped** | Discovery data currently available | ✅ In Progress |
| **Project-Level Details** | Available in discovery CSV | ✅ Complete |

**Stage Can Proceed When:** Enterprise and top-level group decisions are approved

---

#### Estimation Stage

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Target Organization Confirmed** | Required for capacity planning | ⚠️ Blocking |
| **Subgroup Flattening Approved** | Required for complexity estimation | ⚠️ Blocking |
| **Naming Conflict Resolution** | Required for error prevention planning | ⚠️ Blocking |
| **Repository Size Assessment** | Available from discovery data | ✅ Complete |
| **Team Composition Analysis** | Available from discovery data | ✅ Complete |

**Stage Can Proceed When:** Organization placement and naming decisions approved

---

#### Planning Stage

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **All Hierarchy Decisions Approved** | Critical gate: cannot plan without approval | ⚠️ Blocking |
| **Target Organization Structure Finalized** | Required for detailed migration sequencing | ⚠️ Blocking |
| **Team Structure Approved** | Required for access plan creation | ⚠️ Blocking |
| **Migration Sequence Determined** | Depends on organizational decisions | ⚠️ Pending |
| **Naming Conflict Resolution Confirmed** | Required for repository creation plan | ⚠️ Blocking |

**Stage Can Proceed When:** All unresolved blocking dependencies are approved

---

#### Migration Stage

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Planning Complete and Approved** | Gate: plan must be finalized | ⚠️ Pending |
| **Target Repositories Created** | Organizations and repositories must exist | ⚠️ Pending |
| **Access Structure Configured** | Teams and permissions must be in place | ⚠️ Pending |
| **Data Migration Execution** | Can proceed once structure ready | ⚠️ Pending |

**Stage Can Proceed When:** Planning stage is complete and approved

---

#### Validation Stage

| Dependency | Resolution | Status |
|------------|-----------|--------|
| **Migration Complete** | All repositories must be migrated | ⚠️ Pending |
| **Target Placement Verification** | Confirm each project in target organization | ⚠️ Pending |
| **Subgroup Flattening Confirmation** | Validate no nested organization artifacts | ⚠️ Pending |
| **Naming Conflict Resolution Verified** | Confirm no naming duplicates remain | ⚠️ Pending |
| **Team Membership Validation** | Confirm groups mapped to teams correctly | ⚠️ Pending |
| **Customer Acceptance** | Stakeholder approval of placement | ⚠️ Pending |

**Stage Can Proceed When:** Migration is complete and ready for validation

---

## Hierarchy Dependency Assessment Summary

### Unresolved Dependencies (BLOCKING)

| # | Dependency | Decision Required | Decision Owner | Affected Stages | Priority |
|---|------------|-------------------|-----------------|-----------------|----------|
| 1 | Enterprise Account Selection | Which GHEC/GHEC EMU enterprise account? | Product Owner / Leadership | All | **CRITICAL** |
| 2 | burner-group1 Organization Mapping | Confirm 1:1 mapping to target organization | Product Owner | Discovery+ | **CRITICAL** |
| 3 | chiraguniworld-group Decision | Separate org or consolidate with burner-group1? | Product Owner | Discovery+ | **CRITICAL** |
| 4 | thisisrepo Naming Collision | Approve resolution strategy for duplicate names | Product Owner / Ops | Planning+ | **CRITICAL** |
| 5 | Subgroup Flattening Approval | Confirm flattening approach; approve team structure | Product Owner / Ops | Planning+ | **CRITICAL** |
| 6 | Team-Based Grouping Convention | Define naming and permission model for teams | Product Owner | Planning+ | **HIGH** |

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
- Estimation: Org + naming decisions required
- Planning: All hierarchy decisions required
- Migration: Planning approval required
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
- `burner-group1/subgroup1/sub-subgroup2/thisisrepo` (Nested)

**Impact:** When flattened to single organization, both cannot coexist with same name in GHEC/GHEC EMU

**Resolution Required:** BEFORE migration planning can proceed

**Recommended Actions:**
1. Rename nested version: `thisisrepo` → `sub-subgroup2-thisisrepo`
2. Document reason for rename in repository description
3. Update team assignment to preserve source context
4. Notify stakeholders of naming change

**Status:** **BLOCKING** - Prevents Planning Stage

---

### ALERT 2: Enterprise Account Selection Gap
**Severity:** 🔴 CRITICAL  
**Issue:** No target enterprise account has been selected or approved

**Impact:** Cannot proceed with Connection, Discovery, Estimation, or Planning stages

**Resolution Required:** BEFORE any subsequent stage

**Recommended Actions:**
1. Determine target enterprise (new or existing GHEC/GHEC EMU)
2. Validate enterprise has sufficient capacity
3. Confirm enterprise contact and approval authority
4. Document enterprise selection in migration plan

**Status:** **BLOCKING ALL STAGES** - Prevents Stage Progression

---

### ALERT 3: Organization Mapping Decisions Pending
**Severity:** 🟠 HIGH  
**Issue:** Two top-level groups await organizational placement decisions:
1. burner-group1: Assume 1:1 mapping unless split criteria identified
2. chiraguniworld-group: Consolidate or remain separate?

**Impact:** Cannot estimate complexity or plan resources until decided

**Recommended Actions:**
1. Evaluate operational relationships between groups
2. Check for regulatory/compliance boundaries within burner-group1
3. Assess whether chiraguniworld-group should be independent or nested
4. Document approval of organizational structure

**Status:** **BLOCKING** - Prevents Estimation and Planning

---

### ALERT 4: Large Repository with LFS
**Severity:** 🟡 MEDIUM  
**Issue:** Repository "big-one" contains 681.5 MB with 2 LFS files

**Impact:** LFS file migration during flattening requires validation

**Recommended Actions:**
1. Test LFS file handling during flattening
2. Validate file references remain valid post-migration
3. Include in performance testing
4. Monitor for LFS-related issues

**Status:** Non-blocking; recommend inclusion in migration testing plan

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
│ ESTIMATION STAGE                                         │
│ Status: BLOCKED                                          │
│ Blocking Dependencies: Org Mapping + Naming Collision    │
│ Cannot: Plan complexity/resources                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ PLANNING STAGE                                           │
│ Status: BLOCKED                                          │
│ Blocking Dependencies: All hierarchy decisions           │
│ Cannot: Create detailed migration plan                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ MIGRATION STAGE                                          │
│ Status: BLOCKED (dependent on Planning)                 │
│ Blocking Dependency: Planning approval                  │
│ Cannot: Execute migration                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ VALIDATION STAGE                                         │
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

### Immediate Actions (Week 1)
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

### Short-term Actions (Week 2-3)
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

### Preparation Actions (Week 3-4)
7. **Planning Stage Preparation**
   - Detailed migration sequencing
   - Resource allocation planning
   - Risk assessment and mitigation
   - Validation test planning

### Execution Actions (Week 4+)
8. **Discovery Stage**
   - Detailed repository analysis
   - Access and permission discovery
   - Validation of all placement decisions

9. **Estimation Stage**
   - Complexity and risk estimation
   - Resource and timeline planning
   - Capacity validation

10. **Planning Finalization**
    - Complete migration plan
    - Stakeholder approval
    - Team readiness confirmation

---

## Summary of Decisions Required

### DECISION 1: Enterprise Account Selection
- **Question:** Which GHEC or GHEC EMU enterprise account will host migrated organizations?
- **Options:**
  - New dedicated enterprise (isolated for this migration)
  - Existing shared enterprise (consolidate with current infrastructure)
- **Impact:** Blocks all subsequent stages
- **Owner:** Product Owner / Executive Leadership
- **Timeline:** CRITICAL - Require decision by end of week 1

### DECISION 2: burner-group1 Organization Mapping
- **Question:** Confirm burner-group1 maps to single target organization?
- **Options:**
  - Yes, 1:1 mapping (baseline, 50 repositories in single org)
  - Split across multiple organizations (specify split criteria)
- **Impact:** Affects complexity, resource planning, team structure
- **Owner:** Product Owner
- **Timeline:** Required before Estimation stage

### DECISION 3: chiraguniworld-group Organization
- **Question:** Should chiraguniworld-group remain separate or consolidate?
- **Options:**
  - Separate: Create independent chiraguniworld-group organization
  - Consolidate: Move project to burner-group1 organization
  - Clarify operational relationship before deciding
- **Impact:** Organizational structure, team configuration
- **Owner:** Product Owner
- **Timeline:** Required before Estimation stage

### DECISION 4: thisisrepo Naming Collision Resolution
- **Question:** How to resolve duplicate "thisisrepo" names?
- **Options:**
  - Rename nested: thisisrepo → sub-subgroup2-thisisrepo
  - Rename direct: thisisrepo → root-thisisrepo
  - Consolidate repositories (merge if appropriate)
- **Impact:** Critical for migration execution
- **Owner:** Product Owner / Ops Leadership
- **Timeline:** CRITICAL - Must resolve before Planning stage

### DECISION 5: Subgroup Flattening Approval
- **Question:** Approve complete removal of 3 subgroup hierarchy levels?
- **Options:**
  - Yes, approve flattening (7 nested projects become peer repositories)
  - No, request alternative hierarchy model (not GHEC/GHEC EMU compatible)
- **Impact:** Organization structure, team requirements, complexity
- **Owner:** Product Owner
- **Timeline:** Required before Planning stage

### DECISION 6: Team-Based Grouping Structure
- **Question:** Approve GitHub Teams to represent original subgroup structure?
- **Options:**
  - Yes, create teams: subgroup1-team, sub-subgroup1-team, sub-subgroup2-team
  - Alternative: Different grouping strategy (specify)
- **Impact:** Access management, organizational context preservation
- **Owner:** Product Owner / Ops Leadership
- **Timeline:** Required before Migration stage

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
  │   └─→ GATES Planning Stage
  │
  ├─→ [DECISION 5] Subgroup Flattening Approval
  │   └─→ GATES Planning Stage
  │
  └─→ [DECISION 6] Team-Based Grouping Structure
      └─→ GATES Migration Stage

Once ALL DECISIONS Approved:
  │
  ├─→ Discovery Stage (Enabled)
  ├─→ Estimation Stage (Enabled)
  ├─→ Planning Stage (Enabled)
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

## Document Control

| Field | Value |
|-------|-------|
| **Report Title** | GitLab Hierarchy Dependencies and Target Placement Analysis for GHEC / GHEC EMU |
| **Analysis Date** | September 24, 2026 |
| **Executed By** | Revanth (Analysis Team) |
| **Version** | 1.0 |
| **Status** | Ready for Product Owner Review |
| **Scope** | GitLab SaaS instance (gitlab.com) - 2 top-level groups, 3 subgroup paths, 51 active projects |
| **Target Systems** | GHEC and GHEC EMU (both use identical hierarchy model) |
| **Last Updated** | September 24, 2026 |
| **Next Review** | Post-decision implementation |

---

**Report prepared for Jira ticket: Analyse GitLab Hierarchy Dependencies and Target Placement for GHEC / GHEC EMU**

**Status:** NEEDS VALIDATION - All blocking hierarchy decisions require Product Owner approval before proceeding to migration stages.

**Recommendation:** Schedule stakeholder review meeting within 1 week to address DECISION 1-6 and unblock downstream stages.
