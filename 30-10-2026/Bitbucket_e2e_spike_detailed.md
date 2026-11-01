# Bitbucket Cloud and Data Center/Server to GHEC EMU
## End-to-End Migration Capability Assessment

| Document control | Details |
|---|---|
| Analysis date | 2026-10-29 |
| Sources | Bitbucket Cloud (C) and Bitbucket Data Center/Server (DC) |
| Target | GitHub Enterprise Cloud with Enterprise Managed Users (GHEC EMU) |
| Tool | GitLift (GL) |
| Inputs | Spike ticket (objective, questions A-U, deliverables, AC1-AC17); `Gitlab_e2e_spike`; existing GitLift scripts; `Bitbucket-to-GHEC_Metadata_Migration.md` |
| Companion | Cloud and Data Center/Server are assessed separately in each answer, then consolidated in sections 4-7 |

## How to Read This Document

* Every question in the ticket (A1 ... U10) is answered under the same ID.
* Each answer has a Cloud line, a DC line (or "Both" when identical) and one
  Finding line:

    => Src: <C | DC | C,DC> | Result: <per source> | GitLift: <status> |
       Impact: <area> | Ev: <evidence IDs>

  Capability = the question text of that ID.
* Result values : Supported / Partially Supported / Unsupported /
                  Requires Validation (written "NEEDS VALIDATION (NV-nn)").
* GitLift status: Existing            = provider-agnostic component already in
                                        GitLift (evidence E16, E17, E20)
                  Enhancement Required = exists for another source (GitLab,
                                        ADO) and needs a Bitbucket adapter
                  New Capability Required = nothing exists today (for example
                                        Bitbucket collectors, DC support)
* Impact values : Discovery / Planning / Migration / Delta / Validation / Cutover
* Evidence IDs (E1 ...) are listed in section 10. NV-nn items are listed in
  section 9 with what must be validated and how.
* "Supported" describes the SOURCE/TARGET platform capability. It is never
  GitLift readiness (AC17): no capability is classified migration-ready here
  without trial-migration evidence (backlog story BB-030).
* Statements marked "design assumption" follow the GitLift GitLab design
  (Gitlab_e2e_spike) and still need team confirmation.


## 1. Executive Summary

1. Cloud and DC are two different products behind one name. Different REST
   APIs (Cloud /2.0 on api.bitbucket.org; DC /rest/api/1.0 on the customer's
   host), pagination (next link vs start/limit/isLastPage), identity model,
   permission model, rate limiting, and feature set. GitLift needs two source
   adapters, not one.
2. Cloud Issues and Wikis were removed on 2026-08-20 (UI and API). Content is
   recoverable only from pre-removal exports/clones. DC never had native
   Wikis or Pipelines; its CI integration is build-status/webhook based.
3. Hierarchy: Cloud = (Atlassian org) > workspace > project > repository.
   DC = instance > project > repository, plus personal projects (~user).
   GHEC EMU = enterprise > organization > repository. Projects have no GHEC
   container equivalent: use Teams (access) + custom properties (grouping).
4. Rate limits differ sharply. Cloud: about 1,000 requests/hour per user by
   default. DC: admin-configurable token bucket (default 60 burst, 5/second)
   when enabled. Discovery effort must be planned per source.
5. Original authors and timestamps of PRs/comments/reviews cannot be set by a
   normal GHEC API call. Only commit authors survive. EMU adds a constraint:
   a managed user has exactly one IdP-supplied email; commits link to the EMU
   user only if the commit email matches it.
6. GitHub Enterprise Importer (GEI) documents Bitbucket Server/Data Center
   (5.14+) only. No Bitbucket Cloud route is documented. GEI migrates Git
   source and pull requests (with mannequin attribution); it does not migrate
   branch permissions, repository settings, CI, commit comments or LFS
   objects, and has no delta migration.
7. GitLift already has provider-agnostic engines (mirror clone/push, LFS push,
   wiki push, history rewrite, user mapping, submodule mapping, git-sizer,
   evidence/validation compare, fast/detailed/delta discovery stages, ghei
   checkpoint). It has no Bitbucket collectors or migrators; the platform
   parity module lists Bitbucket only as a capability matrix (E18).
8. DC product lifecycle: Atlassian announced Data Center end of life on
   2029-03-28 (new-customer sales ended 2026-03-30). Bitbucket Server is a
   legacy product line (its end-of-support date was not re-verified in this
   spike). Many DC customers will migrate in the near term, which raises the
   value of DC support.
9. Closed, merged and declined pull requests cannot be migrated as native PRs
   by GitLift (same rule as GitLab). Fallback: archival issue/record plus
   evidence. GEI can migrate PRs for DC; this is the main GEI advantage.
10. All findings are traceable: 214 questions, 17 acceptance criteria, 31
    NEEDS VALIDATION items and a 35-story backlog (sections 7, 8, 9).


## 2. Cloud Versus Data Center/Server: Comparison Matrix

| Topic | Bitbucket Cloud | Bitbucket Data Center/Server |
|-------|-----------------|------------------------------|
| Hosting | SaaS, api.bitbucket.org | Self-hosted (single node or cluster), customer URL, optional context path |
| Product status | Active | DC end of life 2029-03-28, new-customer sales ended 2026-03-30 (E10); Server is legacy (support end date not re-verified) |
| REST base | /2.0 | /rest/api/1.0 (also /rest/api/latest); separate /rest/<feature>/ trees |
| Pagination | page/next link, pagelen 10-100; commits iterator-style | start/limit, isLastPage, nextPageStart; default limit 25; resource hard limits set by admin |
| Authentication | API token (Basic with email, or Bearer), repo/project/workspace access tokens, OAuth 2.0, app passwords (deprecated) | Basic (user/password or token), HTTP access tokens (user, project, repository), OAuth, session cookie |
| Rate limit | 1,000/hour default per user, scaled up to 10,000; Git ops 60,000/hour (E4) | None by default; optional admin token bucket per user (default 60 burst, 5/s), 429 when empty; SSH separate (E9) |
| Hierarchy | Workspace > Project > Repository (personal workspace) | Project > Repository; personal project ~user |
| Users | Atlassian accounts (account_id, uuid, nickname) | Directory users (internal, LDAP, Crowd, Jira): name, slug, id, email |
| Groups | Workspace groups | Global groups (directory) |
| Permissions | Workspace, project, repository; user and group; levels admin/write/read | Global, project, repository; user and group; levels READ/WRITE/ADMIN; repo inherits project |
| Branch rules | Branch restrictions (16 kinds), branching model | Branch permissions (restrictions) and branch model, merge checks (repository hooks) |
| Tag protection | Not documented | Branch permissions can cover tags (confirm, NV-09) |
| PR states | OPEN, MERGED, DECLINED, SUPERSEDED | OPEN, MERGED, DECLINED |
| PR extras | Tasks, default reviewers, approvals, draft | Tasks, reviewers with status (APPROVED, NEEDS_WORK), default reviewers, merge checks |
| Pipelines/CI | Bitbucket Pipelines (YAML, variables, runners, deployments) | None native; external CI via build status and webhooks (Bamboo, Jenkins, others) (E7) |
| Wiki | Removed 2026-08-20 (archive only) | No native wiki; Confluence links |
| Issues | Removed 2026-08-20 (archive only) | No native issue tracker; Jira links |
| Archive state | None | Repository archive supported in newer versions (NV-10) |
| Forks | Supported (parent field) | Supported (origin field) |
| LFS | Supported | Supported (enable per repository); Bearer + LFS issue BSERV-13613, use Basic (E8) |
| Webhooks | Repository/workspace; secret_set flag | Repository/project; secret support (retrievability NV-24) |
| GraphQL | None | None |
| Admin-only data | Workspace admin; repo admin (permissions, restrictions) | Global/system admin (users, groups, apps, links, audit) |
| GEI route | Not documented | Documented, version 5.14+ (E12, E13, E14) |
| Typical network | Internet | Private network: GitLift needs connectivity (VPN/agent/allow list) |


## 3. Findings (one answer per ticket question)

### A. Authentication and Access

**A1**. What authentication methods are supported by Bitbucket Cloud?
  **C:** API tokens (personal; Basic = Atlassian email + token, or Bearer since
     2026-08-18; mandatory expiry, max 1 year; scoped). Repository, project and
     workspace access tokens (resource-bound, scoped, not user accounts).
     OAuth 2.0 consumers (authorization-code, client-credentials, JWT; access
     token 1 hour, refresh token rotates). App passwords: deprecated. SSH keys
     and repository access keys for Git transport.
  => Src: C | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E5

**A2**. What authentication methods are supported by Bitbucket Data Center/Server?
  **DC:** HTTP Basic (over TLS) and OAuth are preferred; also session cookies and
      HTTP access tokens (user tokens, plus project and repository tokens with a
      Data Center license). Tokens can be used as the password for Git over
      HTTPS and for REST. SSH user keys and SSH access keys (system use) for
      Git.
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E7, E8

**A3**. What permissions are required to discover repositories, projects, users,
    and metadata?
  **C:** Read scopes: read:repository, read:pullrequest, read:project,
     read:workspace, read:user, read:pipeline, read:webhook (API-token
     naming). Branch restrictions need admin:repository. Repository
     permissions need repository admin and a user-level credential (access
     tokens cannot query permissions). Groups/members need workspace admin.
  **DC:** PROJECT_READ / REPO_READ for projects, repositories, PRs, branches. Project
      or repository admin to read project/repo permissions, webhooks and branch
      permissions. Global admin or system admin for all users, groups,
      application links, installed apps and audit log (exact minimum per
      resource: NEEDS VALIDATION (NV-04)). HTTP token combinations: project
      read/write/admin and repository read/write/admin (repo level must be at
      least the project level).
  => Src: C,DC | Result: C=Supported, DC=Requires Validation | GitLift: New
     Capability Required | Impact: Discovery | Ev: E1, E7, E8 | NV-04

**A4**. What permissions are required to migrate repositories and metadata?
  Source (both): the discovery read rights plus Git clone rights; admin-level
    read for permissions and rules. Target (GHEC EMU): an EMU managed user
    (service identity) that is organization owner or has the migrator role;
    repository admin for settings; organization owner for teams; classic PAT
    scopes repo, workflow, admin:org (owner) or read:org (migrator) when GEI
    is used. GitLift GitHub App installation tokens are preferred for writes
    (NEEDS VALIDATION (NV-02): EMU policy on GitHub Apps and PATs).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E13, E11 | NV-02

**A5**. What differences exist between Cloud and DC/Server authentication?
  | Aspect | Cloud | DC |
  |--------|-------|----|
  | Credential owner | Atlassian account; access tokens bound to resource | Directory user; tokens for user/project/repo |
  | Basic auth user | Atlassian email (API token) | username (token or password) |
  | Bearer | Supported (API tokens, OAuth) | Project/repository tokens (Basic needs username x-token-auth); user tokens via Basic |
  | OAuth | OAuth 2.0 consumer, rotating refresh tokens | Application link OAuth |
  | Permissions API | Not available to access tokens | Needs admin rights |
  | Throttling | Per user, fixed hourly | Optional bucket per user and per node |
  | Expiry | Mandatory (API token 1 year max) | Optional, admin may require |
  | SSH | ssh.bitbucket.org (migration from bitbucket.org) | Customer host |
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E5, E8, E9

**A6**. How can GitLift identify repositories or metadata that cannot be accessed
    with the provided permissions?
  **Both:** record an access status for every object and surface:
        ACCESSIBLE, FORBIDDEN (401/403), NOT_FOUND (404), NOT_ATTEMPTED,
        UNKNOWN_SCOPE. List endpoints return only what the credential sees, so
        a missing repository is invisible. Mitigate with (a) an expected
        inventory from an administrator account or customer-supplied list,
        compared with the discovered list; (b) per-surface probe calls; (c) a
        coverage field in the discovery report (see F5, C9).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E1, E7

**A7**. What authentication and permission constraints must be considered for
    GHEC EMU migration?
  **Both:** identities come from the IdP (SAML or OIDC + SCIM); usernames are
        generated from the IdP identifier; profile name and email are IdP-owned
        (one email, cannot be changed by the user). The migrating identity must
        be a provisioned managed user. Restricting classic PATs blocks GEI
        (classic PAT only). IP allow lists must admit the migration source
        (GEI IP ranges if GEI is used). SAML/SSO PAT authorization applies.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E11, E13 | NV-02

**A8**. Can existing GitLift authentication capabilities be reused for Bitbucket?
  **Both:** partially. Reusable: token retrieval and request-builder pattern, token
        pooling (provider-agnostic by design), global rate-limit handling and
        retry. Gaps: Bitbucket credential types (Basic/Bearer variants, OAuth
        refresh rotation), per-user rate budgets, DC token-bucket handling, and
        the health daemon that is hard-coded for GitHub.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E20, E16

**A9**. What restrictions apply when migrating to GHEC EMU using managed identities?
  **Both:** managed users cannot create public content or collaborate outside the
        enterprise, so public Bitbucket repositories become private or internal.
        No outside collaborators (guest collaborator role instead). Usernames are
        normalized from the IdP (conflicts possible). A user's single email must
        match commit emails for contribution linking. Membership and repository
        access can be driven by IdP groups mapped to teams. Personal-account
        repository ownership by managed users is limited (NEEDS VALIDATION
        (NV-03)).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E11 | NV-03


### B. Hierarchy Discovery and Mapping

**B1**. What is the complete hierarchy of Bitbucket Cloud?
  **C:** Atlassian organization (billing/identity, optional) > Workspace > Project >
     Repository. Every repository belongs to exactly one project. Each user has
     a personal workspace. Groups and members are workspace-scoped. Forks are
     separate repositories with a parent link.
  => Src: C | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E2

**B2**. What is the complete hierarchy of Bitbucket Data Center/Server?
  **DC:** Instance (one base URL; a customer may have several) > Project (key) >
      Repository (slug). Personal projects use key ~username. Forks live in the
      forking user's personal project or another project and keep an origin
      link. Global groups and users sit at instance level.
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E7

**B3**. How should Cloud workspaces, projects and repositories map to GHEC EMU?
  **C:** Workspace -> organization (default 1:1; consolidation is a customer
     decision, see U2). Project -> Team (access) + custom repository property
     `bb_project_key` (+ topic). Repository -> repository (name sanitized,
     max 100 chars). Workspace group -> Team. Visibility: private -> private or
     internal; public -> private or internal (EMU cannot have public).
  => Src: C | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E11, E19

**B4**. How should DC projects and repositories map to GHEC EMU?
  **DC:** Do not assume one organization per project (GEI guidance). Map a small
      number of target organizations; project -> Team + property
      `bb_project_key`, `bb_instance`; repository -> repository. Project
      permissions are expanded into team grants per repository.
  => Src: DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E14

**B5**. How should personal repositories and personal projects be handled?
  **C:** Personal workspace repositories: map to a designated org (for example
     `personal-migrated`) with owner recorded in a property, or skip by
     customer decision.
  **DC:** Personal projects (~user): GEI does not migrate personal repositories
      (E12). GitLift default: discover and report; migrate into a designated
      organization with a `bb_personal_owner` property after customer approval.
      Where the user is not provisioned in EMU, ownership is by a team/service
      account.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E7, E12 | NV-03

**B6**. How can GitLift discover all repositories across workspaces, projects and
    instances?
  **C:** GET /workspaces (visible), then GET /repositories/{workspace} per
     workspace (follow `next`, pagelen=100); projects via
     /workspaces/{ws}/projects.
  **DC:** GET /rest/api/1.0/projects and /projects/{key}/repos (start/limit), or
      GET /rest/api/1.0/repos; personal repos via /users/~slug/repos or
      projects/~slug. One adapter instance per DC base URL (multi-instance: T1).
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E2, E7

**B7**. How should repositories belonging to multiple projects or workspaces be
    organized in the target?
  **Both:** a Bitbucket repository belongs to exactly one project/workspace, so the
        situation does not arise except for forks and mirrored copies, which
        are separate repositories. Each is migrated as its own repository; extra
        grouping uses additional custom properties or topics.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E1, E7

**B8**. How should hierarchy levels without a direct GHEC EMU equivalent be handled?
  **Both:** Project (no container), Atlassian organization, personal workspace/
        project, DC instance. Represent with Teams, custom properties,
        naming prefix (optional), and a persisted mapping table. Keep the
        source path in properties so rulesets can target groups of repos.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E14, E19

**B9**. What happens when multiple source projects or repositories have conflicting
    names?
  **Both:** slugs are unique per workspace (C) or per project (DC), but GHEC names
        are unique per organization and case-insensitive. Apply a deterministic
        rule: keep the name if free; otherwise `<project-key>-<slug>`, then a
        numeric suffix; replace invalid characters; truncate to 100. Record the
        rename in the mapping table and report it to the customer.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E19

**B10**. How should source hierarchy relationships be preserved or represented?
  **Both:** properties (workspace/project/instance), teams per project, optional
        topic `bb-project-<key>`, README banner (optional), and the persisted
        mapping/evidence table (source path <-> target path).
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E19


### C. Repository Discovery

**C1**. What information can be collected during fast discovery?
  **C:** repository list with uuid, full_name, privacy, project, main branch, size,
     created/updated, language, fork parent; plus `git ls-remote` ref counts.
  **DC:** repository list with id, slug, project key, state, forkable, public,
      archived (where supported), clone links; plus `git ls-remote`. Size is
      not in the list response (NV-05).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E1, E2, E7 | NV-05

**C2**. What information can be collected during detailed discovery?
  **Both:** all surfaces in section D (see also Appendix A and B): branches, tags,
        commits (local Git), PRs and child objects, permissions, branch rules,
        webhooks, pipelines (C), build statuses (DC), LFS, submodules, files,
        sizes.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E7

**C3**. What differences exist between Cloud and DC/Server discovery capabilities?
  **C:** internet API, 1,000/hour budget, no admin-wide user listing for access
     tokens, Pipelines data available, Issues/Wiki gone.
  **DC:** private network access, optional rate limiting, admin endpoints for
      users/groups/apps, no Pipelines/Wiki/Issues, version-specific fields,
      server-side Git access possible for very large estates (NV-06).
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E4, E9

**C4**. Can GitLift retrieve all accessible repositories and their metadata?
  **Both:** yes for what the credential can see. Completeness is bounded by
        credential scope (A6) and API limits. Use an administrator credential
        for the inventory pass.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E7

**C5**. What repository statistics are available for migration assessment?
  **Both:** repository size (C: size field; DC: NV-05 or local), ref counts, commit
        count and authors (local Git), file counts/largest files (git-sizer,
        local), PR counts by state, comment/task counts, LFS object count/size,
        submodule count, webhook count, permission entry count, branch-rule
        count. C adds pipeline counts and build minutes. There are no stars or
        topics on either source.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E2, E16

**C6**. Can archived, inactive, empty and inaccessible repositories be identified?
  **C:** archived = not available (no archive state); inactive = derived from last
     commit/PR/updated_on; empty = no commits (git ls-remote); inaccessible =
     403/404 or absent from inventory.
  **DC:** archived = repository flag where the version supports archiving (NV-10);
      inactive = derived; empty = no default branch/commits; inaccessible =
      401/403/404; repository state field for initialising/failed repos
      (NV-11).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E7 | NV-10, NV-11

**C7**. How can repository size, activity and migration complexity be assessed?
  **Both:** complexity score from git-sizer metrics, LFS volume, open PR count,
        comment count, submodule/dependency count, rule/webhook/variable counts,
        unsupported-feature flags, and activity (last commit, last PR update).
        The planner weights these (J3).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E16

**C8**. What discovery limitations exist for each Bitbucket variant?
  **C:** hourly request budget; no GraphQL; Issues and Wikis removed; secured
     variable values unreadable; some features plan-gated; permission data
     needs admin credentials; Atlassian states limits and page sizes can
     change.
  **DC:** version-dependent fields and endpoints; admin rights for users, groups,
      apps, links; hard page-size limits; optional rate limiting; connectivity
      to the private network; plugin-provided data (apps) varies by instance.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E4, E6, E7, E9

**C9**. How should incomplete or partially accessible discovery results be
    represented?
  **Both:** per-surface coverage record {surface, status = COMPLETE | PARTIAL |
        UNAVAILABLE | FORBIDDEN | NOT_APPLICABLE | NOT_ATTEMPTED, reason,
        observed_count, page_count, timestamp}; roll up to a per-repository
        confidence (HIGH, MEDIUM, LOW). The planner and UI show the confidence
        and the excluded surfaces. Never show an unavailable count as zero.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E20

**C10**. Can existing GitLift discovery capabilities be reused for Bitbucket?
  **Both:** the framework is reusable (init, fast, detailed, finalize stages; hybrid
        clone, git-sizer, LFS, submodule and file-detail scripts; delta
        discovery stages; evidence storage). Bitbucket collectors and field
        mapping are new.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E16, E20


### D. Metadata Collection and Logical Grouping

**D1**. What repository identity and descriptive metadata can be discovered?
  **C:** uuid, full_name, name, slug, description, is_private, project, mainbranch,
     language, size, created_on, updated_on, fork_policy, parent, website, links.
  **DC:** id, slug, name, description, project (key, name, type), state, public,
      forkable, origin (forks), archived (NV-10), links (clone URLs).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E2, E7

**D2**. What branch, tag and commit information can be discovered?
  **Both:** branch/tag names, target SHAs, default branch; commits with author,
        committer, dates, parents (local Git preferred for volume). C commits
        are iterator-paginated; DC uses start/limit.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E1, E7

**D3**. What repository settings and governance rules can be discovered?
  **C:** branch restrictions (kind, match kind, pattern or branch type, users,
     groups, value), branching model, default reviewers, merge checks,
     project-level overrides, fork policy.
  **DC:** branch permissions and branch model, default reviewers, merge checks
      (repository hooks), merge strategy settings, fork permissions, project
      and repository permission settings (REST paths per documented group,
      NV-04).
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E3, E7 | NV-04

**D4**. What pull request information can be discovered?
  **Both:** id, title, description, state, source/destination repository and branch,
        author, reviewers/participants, created/updated dates, merge commit,
        commits, comments, activity, tasks. C also: SUPERSEDED state, draft;
        **DC:** reviewer status.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E1, E7

**D5**. What reviewer, approval, comment and task information can be discovered?
  **Both:** reviewers and approval state, general and inline comments with anchors,
        threads, tasks and their state. Original author/time are readable
        (but not writable on the target).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E1, E7

**D6**. What user, group, role and permission information can be discovered?
  **C:** workspace members, groups and members, project permissions, repository
     user/group permissions (admin, write, read, none). Email often hidden.
  **DC:** users (name, slug, id, display name, email for admins, active), groups,
      global/project/repository permissions for users and groups, directory
      source. Admin rights required for the full set.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E7 | NV-04

**D7**. What repository files, large files and Git LFS information can be discovered?
  **Both:** local clone gives file tree, sizes, large files, `.gitattributes`, LFS
        pointers (oid, size). DC also exposes the LFS enabled flag per
        repository (NV-12).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Discovery |
     Ev: E16 | NV-12

**D8**. What wiki and documentation information can be discovered?
  **C:** wiki removed 2026-08-20; only a retained clone/export. README/docs are
     repository files.
  **DC:** no native wiki; README/docs files; Confluence/Jira links (project links).
  => Src: C,DC | Result: C=Partially Supported (archive only), DC=Unsupported |
     GitLift: Enhancement Required | Impact: Discovery | Ev: E5, E6, E7

**D9**. What pipeline, deployment and automation information can be discovered?
  **C:** bitbucket-pipelines.yml, pipelines, steps, schedules, variables (key,
     scope, secured), runners, environments, deployments, caches.
  **DC:** no native pipelines. Build statuses per commit and deployments via the
      Builds and Deployments API group; external CI config lives in the CI
      tool (Jenkinsfile in repo, Bamboo specs). Webhooks and app links show
      integrations.
  => Src: C,DC | Result: C=Supported, DC=Partially Supported |
     GitLift: New Capability Required | Impact: Discovery | Ev: E7

**D10**. What webhook and external integration information can be discovered?
  **C:** repository and workspace webhooks (url, events, active, secret_set), OAuth
     consumers, installed apps, Jira/Slack/Teams (partly UI-only).
  **DC:** repository and project webhooks, application links, installed apps (admin),
      Jira integration, repository hooks. Webhook secrets are not exposed
      (NV-24).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E1, E7 | NV-24

**D11**. What repository dependency and submodule information can be discovered?
  **Both:** `.gitmodules` and gitlinks from the clone; cross-repo references from
        pipelines config (C), build/CI config in repo (DC), package manifests.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Discovery |
     Ev: E16

**D12**. What metadata differs between Cloud and DC/Server?
  | Metadata | Cloud | DC |
  |----------|-------|----|
  | Pipelines/variables/environments | Yes | No (external CI) |
  | Wiki | Removed (archive) | None |
  | Issues | Removed (archive) | None (Jira) |
  | Archive state | None | Yes (version-dependent) |
  | PR SUPERSEDED state | Yes | No |
  | Draft PRs | Yes | Version-dependent (NV-22) |
  | Reviewer needs-work status | No (approvals, changes requested) | Yes |
  | Users/groups source | Atlassian accounts | Directory (LDAP/Crowd) |
  | Personal containers | Personal workspace | Personal project ~user |
  | Rate-limit data | Fixed limits, headers on scaled limits | Admin-configured |
  | Admin/audit data | Atlassian audit (licensed) | Audit log, apps, links |
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E7

**D13**. Which metadata has a direct GHEC EMU equivalent?
  **Both:** repository name/description/default branch, branches, tags, commits, LFS
        pointers, submodules, open PR (title, body, branches), reviewers (as
        assignment), repository variables/secrets (as new objects), webhooks
        (new, different payload), deploy keys, branch rules (as rulesets),
        repository roles (admin, write, read).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E19

**D14**. Which metadata requires transformation or separate handling?
  **Both:** projects (teams + properties), groups (teams, IdP-driven in EMU),
        permissions (expand to team grants), branch rules (translate kind to
        ruleset rule), default reviewers (CODEOWNERS), tasks (checklist), PR
        states (SUPERSEDED, DECLINED), pipelines (convert to Actions), build
        statuses (checks), webhooks (event/payload mapping), mentions
        (account id to login), cross-references (ID mapping).
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E19

**D15**. Which metadata cannot be migrated to GHEC EMU?
  **Both:** original authors/timestamps of PRs/comments/reviews, secret and token
        values, webhook secrets, historical runtime data (pipeline runs, logs,
        deployments, delivery history, audit log), closed/merged PRs as native
        PRs, per-user state (watchers, notification preferences), original IDs
        and URLs, SUPERSEDED/"smart reset approvals" semantics, DC personal
        repositories when GEI is used, Issues/Wikis (C) without an archive.
  => Src: C,DC | Result: Unsupported | GitLift: Existing (reporting rules) |
     Impact: Migration | Ev: E12, E19, E20


### E. Dependencies and Submodules

**E1**. How can GitLift identify repositories containing Git submodules?
  **Both:** read `.gitmodules` and gitlink entries from the mirror clone (hybrid
        submodule discovery already exists for GitLab).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Discovery |
     Ev: E16

**E2**. How can cross-repository dependencies be discovered?
  **C:** submodules; pipeline config references (pipes, trigger pipeline via API,
     clone of other repos with keys/tokens); package manifests; Jira keys.
  **DC:** submodules; CI config in repo and CI tool (jobs triggering jobs);
      webhooks targets; application links; package manifests.
  **Both:** build a dependency graph from URLs that match the source host.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E16

**E3**. How should source-to-target submodule relationships be preserved?
  **Both:** rewrite `.gitmodules` URLs to target URLs using the mapping table
        (existing submodule mapping script for GitLab). A rewrite creates a new
        commit; the policy (rewrite during migration vs post-cutover developer
        action) follows the existing submodule cutover guide.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E16 | NV-13

**E4**. How should dependencies between repositories in different workspaces or
    projects be handled?
  **Both:** the mapping table resolves targets regardless of source location. If
        the targets land in different organizations, grant cross-organization
        access (GitHub App installation, deploy key) and validate checkout.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E19

**E5**. How should missing, inaccessible or unmigrated dependent repositories be
    identified?
  **Both:** any dependency URL with no mapping entry is flagged UNRESOLVED (not in
        scope, not migrated yet, inaccessible, external). The planner lists it;
        cutover treats it as blocking unless the customer accepts it (P6).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E20

**E6**. What happens when dependent repositories are migrated in separate batches?
  **Both:** references to a repository not yet migrated stay pointing at the source
        until its batch completes; rewrite is deferred and re-validated after
        each batch (delta). Group tightly coupled repositories in one batch
        (J5).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E16

**E7**. How should dependencies between branches, pull requests and repositories be
    handled?
  **Both:** fork-based PRs require fork relationships first (migrate parent, then
        fork via the fork action); PRs from other repositories are migrated only
        if both repositories are in scope; dependent PR gating (Cloud
        require_all_dependencies_merged) has no native GitHub equivalent
        (use a required status check).
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E3

**E8**. How can GitLift validate that migrated dependencies reference the intended
    target repositories?
  **Both:** after migration, re-read `.gitmodules` and dependency URLs on the target,
        compare with the mapping table, verify the pinned commit SHA exists, and
        run a test clone from the target runner (existing submodule validation
        for GitLab).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E16


### F. Fast and Detailed Discovery

**F1**. Can Bitbucket Cloud support both fast and detailed discovery?
  **C:** yes. Fast = repository list + repository detail + Git signals + selected
     counts. Detailed = all REST resources and child calls. No GraphQL.
  => Src: C | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E4

**F2**. Can Bitbucket DC/Server support both fast and detailed discovery?
  **DC:** yes with the same split; faster per call on a local network, but needs
      version checks and admin credentials for users/groups.
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E7

**F3**. What metadata counts are available during fast discovery?
  **Both:** repository count, size (C list; DC NV-05), branch/tag/ref counts
        (git ls-remote), default branch, last activity, fork/parent flags,
        public/private. Not available: PR/comment counts, permissions,
        webhooks, pipelines, rules (these need detailed discovery).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E2, E7 | NV-05

**F4**. What additional information becomes available during detailed discovery?
  **Both:** everything in section D: PRs and child objects, permissions, groups,
        rules, webhooks, variables (keys), pipelines/build statuses, LFS,
        submodules, file/size detail, commits and authors.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E7

**F5**. How does incomplete discovery information affect migration planning accuracy?
  **Both:** estimates exclude unknown surfaces, so time and effort are
        underestimated; confidence drops and the planner must show it. PR count
        dominates DC/GEI-style time estimates; unknown PR counts invalidate the
        time estimate.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E14

**F6**. How should GitLift communicate limitations in migration estimates?
  **Both:** show discovery level (fast/detailed), per-surface coverage, confidence,
        list of excluded or unavailable surfaces, assumptions (rate budget,
        credential scope) and a "not an estimate for X" statement.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E20

**F7**. Can detailed discovery be performed only for selected repositories?
  **Both:** yes. Detailed stages run per repository with a selection list
        (existing GitLift pattern); the inventory pass stays global.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Discovery |
     Ev: E16

**F8**. What differences exist in discovery effort between Cloud and DC/Server?
  **C:** bounded by 1,000 requests/hour per user (scaled to 10,000 with qualifying
     plan and access tokens). Example: 10,000 calls need at least 10 hours for
     one identity.
  **DC:** no fixed budget; if the admin enabled the token bucket, sustained rate is
      refill rate (default 5/s = 18,000/hour per node per user). Without
      limiting, load on a production instance is the constraint; throttle
      politely and use a dedicated service account, possibly off-hours.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E4, E9

### G. Discovery, Migration, and Validation Effort

Notation: pages(X) = ceil(count of X / page size). Cloud page size up to 100
(pagelen). DC default limit 25, requested up to the hard limit (often 1,000,
admin-configurable; always read `limit` in the response). Git operations are not
REST calls. GH = GitHub REST/GraphQL call to the target.

**G1**. How many source requests or operations are required for repository discovery?
  **C:** pages(repositories per workspace) + 1 per workspace for projects pages
     + optional 1 GET per repository. Example: 1,000 repositories = 10 list
     pages (pagelen 100) + 1,000 detail GETs if detail is needed.
  **DC:** pages(projects) + pages(repos per project) or pages(global repos); 1 GET
      per repository for detail. Example: 1,000 repositories at limit 1,000 =
      1 call; at the default 25 = 40 calls.
  Local Git (`ls-remote`, `rev-list`, git-sizer) adds Git operations, not REST.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E1, E7

**G2**. What additional operations are required for detailed metadata discovery?
  Both, per repository (formula, N = number of repositories):
    branches/tags (0 REST if local), branch rules pages, webhooks pages,
    permissions pages (users + groups), PR pages per state, per PR child pages
    (commits, comments/activity, tasks), LFS/submodule/file scans (local).
  C extra: pipelines pages, steps pages per pipeline, schedules, variables
     (workspace, repository, deployment scopes), environments, deployments,
     downloads, snippets.
  DC extra: build statuses per commit (optional), application links, project
     level settings, users and groups (instance level, once).
  Dominant cost: PRs x (1 + number of child collections). A repository with
  P PRs and 3 child collections costs about P x 3 child calls plus pages(PR).
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1, E7

**G3**. What operations are required for repository migration?
  **Both:** 1 mirror clone (or fetch), 1 push of branches/tags, optional LFS fetch
        and push, 1 GH create-repository call, 1 GH default-branch/settings
        call. Git/LFS operations, not REST, dominate. GEI alternative (DC only):
        one migration job per repository (queue, wait).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E16

**G4**. What operations are required for metadata migration?
  **Both:** per object GH calls: topics/properties, rulesets/branch protection (1
        per rule), team and membership calls (1 each), webhooks (1 list + 1
        create each), variables/secrets (1 each + 1 key fetch per scope),
        deploy keys (1 each), PRs (1 create + children: comments, reviewers),
        archival issues for closed/merged PRs (1 each). Plus a Bitbucket fetch
        for each object class (reuse discovery data when fresh).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E19

**G5**. What operations are required for migration validation?
  **Both:** reads the evidence table (0 source calls). Target reads: 1 GET per
        repository, paginated reads for rules, teams, webhooks, PRs (+ child
        reads), `git ls-remote` on target, wiki/LFS comparison. The GitLab
        spike excluded validation from source call counts; that remains true
        here, but target reads must be budgeted against GitHub limits (5,000
        per hour per PAT; 15,000 for qualifying apps; secondary limits).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E16, E21

**G6**. How does required effort vary with repository size and metadata volume?
  **Both:** Git effort scales with size (clone/push time, LFS bytes). REST effort
        scales with PR and comment counts (linear), permissions (users +
        groups per repository) and rules. For GEI-style migration, time is
        driven mostly by PR count (GitHub guidance). Use: estimate = (git bytes
        / throughput) + (REST calls / allowed rate) + (GH writes / allowed
        content-creation rate: about 80 per minute, 500 per hour secondary
        limit).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E14, E21

**G7**. What source restrictions affect discovery and migration?
  **C:** 1,000/hour per user (scaled to 10,000), webhook endpoints 1,000/hour,
     Git ops 60,000/hour, raw files 5,000/hour, archives 1,500/hour; admin
     scope for permissions/rules; removed features.
  **DC:** optional token bucket (429); node-by-node buckets in clusters; hard page
      limits; admin rights; Git over SSH not covered by the HTTP limiter;
      firewall/VPN; maintenance windows and load.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E4, E9

**G8**. What differences exist between Cloud and DC/Server (effort)?
  See F8, G7. Cloud is budget-bound and internet-based; DC is load-bound,
  network-bound and version-bound. DC lacks Pipelines/Wiki/Issues, so detailed
  discovery has fewer surfaces but more admin-level surfaces.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E4, E9

**G9**. Which existing GitLift capabilities can be reused?
  Mirror clone/push, push to target, LFS fetch/push, history rewrite, user
  mapping fetch, submodule mapping, wiki clone/push, create target repo,
  default branch, webhooks/variables fetch-push pattern, topics, merge-method
  settings, CODEOWNERS migration, validation compare and store, source/target
  count fetch, fast/detailed/delta discovery stages, ghei checkpoint, git-sizer,
  cleanup. See E16 for file-level evidence.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E16


### H. Initial Migration

**H1**. What repository content can be migrated from Bitbucket to GHEC EMU?
  **Both:** Git history (all branches, tags, annotated tags, notes), LFS objects
        (explicit transfer), submodule configuration, repository files
        (README, CODEOWNERS, templates). Not: platform-only data (section D15).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E16

**H2**. How should branches, tags and commit history be preserved?
  **Both:** `git clone --mirror` then push branches and tags explicitly (avoid
        reserved/hidden refs such as pull request refs; GitHub rejects refs/pull
        updates). SHAs are preserved unless history is rewritten (LFS pointer
        or submodule URL rewrite), in which case the SHA mapping is recorded
        (Git notes, existing pattern).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E16 | NV-14

**H3**. How should repository descriptions, settings and visibility be migrated?
  **Both:** description and homepage via repository PATCH; default branch; topics
        from project key; merge settings (merge, squash, rebase); issues/wiki
        flags per target policy. Visibility: EMU allows private or internal only;
        map public and private-with-wide-access to internal by policy; default
        private. GEI migrates repositories as private (E13).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E11, E19

**H4**. How should pull requests and associated metadata be migrated?
  **Both:** open PRs are recreated as GHEC PRs (title, body with provenance header,
        base/head branches, reviewers, comments). Requirement: head and base
        branches exist on the target. Closed/merged/declined/superseded PRs are
        not migrated as PRs (see Q5). Fork PRs need fork lineage (E7).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E3, E12, E19 | NV-15

**H5**. How should reviewers, approvals, comments and tasks be handled?
  **Both:** reviewers -> requested reviewers (mapped users); approvals and
        "needs work" -> not recreated as native reviews unless a tested method
        exists (stored as evidence and a summary comment); comments -> issue
        comments with author/time header; inline comments -> review comments
        anchored to commit SHA (SHAs preserved); tasks -> checklist in PR body
        or comment (C task state, DC task state).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E19 | NV-15

**H6**. How should repository permissions and governance rules be handled?
  **Both:** expand effective access to team grants; EMU users receive access through
        IdP groups -> teams where the IdP is the source of truth. Branch rules
        become rulesets (translation table in Appendix C). Rules requiring
        unsupported semantics are reported.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E3, E11, E19 | NV-03

**H7**. How should Git LFS content be migrated?
  **Both:** `git lfs fetch --all` from the source (DC: use Basic auth, E8) and
        `git lfs push --all` to the target after the Git push. Validate pointer
        oids against target. Quotas apply. GEI does not migrate LFS objects (E12).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E8, E12, E16

**H8**. How should repository forks and their relationships be handled?
  **C:** parent field; DC: origin field. Migrate the parent first, then create the
     fork with the GitHub fork action where the fork is in scope, then push
     differing branches. A separately pushed repository has no fork lineage;
     record the relationship in a property (`bb_fork_of`).
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E2, E7 | NV-16

**H9**. How should Git submodules be migrated?
  **Both:** see E3. Rewrite URLs through the mapping table; verify pinned SHAs;
        keep the superproject and submodules in the same or compatible
        batches.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E16

**H10**. What source metadata requires separate migration activities?
  **Both:** users/teams/permissions (identity workstream), branch rules (rulesets),
        webhooks and integrations (consumer changes), secrets/variables
        (re-supply), CI conversion (C Pipelines to Actions; DC external CI
        re-pointing), wiki (C archive), snippets (C), downloads (C), PR
        history policy, deploy keys.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E19

**H11**. How should unsupported metadata be reported to the customer?
  **Both:** per-repository "migration exceptions" report: object class, count,
        reason (unsupported / skipped / needs customer action), workaround, owner,
        and acceptance status. Same data feeds validation expected-differences
        and cutover readiness. (GitLift already records expected differences.)
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E20


### I. Delta Discovery and Migration

**I1**. How can GitLift identify repository changes after initial migration?
  **Both:** compare against checkpoints. Git: fetch into the retained mirror and
        diff refs. Metadata: stored snapshots in the evidence table plus
        source-side change signals (I3, I4). GEI offers no delta (ticket
        reference; no incremental feature documented).
  => Src: C,DC | Result: Supported | GitLift: Existing (framework), Enhancement
     Required (Bitbucket collectors) | Impact: Delta | Ev: E16, E12

**I2**. How can changes to branches, tags and commits be identified?
  **Both:** `git ls-remote` against the stored ref map; fetch into the retained
        bare clone; compare reachable objects. Deleted, force-pushed and
        re-created refs are detected by SHA divergence (non-fast-forward).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Delta |
     Ev: E16

**I3**. How can new or modified pull requests be identified?
  **C:** `q=updated_on > <ts>` and `sort=-updated_on` on pullrequests; then compare
     to the snapshot.
  **DC:** PR list sorted by updated date (order parameter) until the checkpoint is
      reached; activities per PR for detail; no server-side "since" filter
      is documented (NV-17).
  => Src: C,DC | Result: C=Supported, DC=Partially Supported | GitLift:
     Enhancement Required | Impact: Delta | Ev: E1, E7 | NV-17

**I4**. How can changes to repository settings and permissions be identified?
  **Both:** re-fetch and hash-compare (settings, rules, permissions, webhooks).
        Neither product exposes a general change feed for these. C has audit
        data with licensing; DC has an audit log API for administrators
        (NV-18). Full reconciliation per delta run is the reliable method.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Delta | Ev: E7 | NV-18

**I5**. How can newly created repositories be identified?
  **Both:** re-run the repository inventory and diff against the mapping table
        (new uuid/id). C: sort by created_on. DC: compare ids.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Delta |
     Ev: E16

**I6**. Can both fast and detailed delta discovery be supported?
  **Both:** yes. Fast delta = repository list, refs, summary fields vs checkpoints
        (existing delta fast stage). Detailed delta = changed objects per
        surface (existing delta detailed stages, pattern from GitLab).
  => Src: C,DC | Result: Supported | GitLift: Existing (framework) | Impact:
     Delta | Ev: E16

**I7**. What differences exist between Cloud and DC/Server delta discovery?
  **C:** server-side `updated_on` filters on several collections; request budget
     limits how often a full reconciliation can run.
  **DC:** no equivalent documented filters on most collections; rely on sort order,
      activity and snapshots; cheaper calls but load on the instance.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Delta | Ev: E1, E7 | NV-17

**I8**. How should GitLift distinguish new, modified, deleted and unchanged metadata?
  **Both:** key = (source type, source id). Compare normalized hash with the stored
        snapshot: absent in snapshot = NEW; hash differs = MODIFIED; present in
        snapshot but absent in source = DELETED; same hash = UNCHANGED. Count
        each; the planner uses NEW + MODIFIED + DELETED.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Delta |
     Ev: E16, E20

**I9**. How should previously migrated metadata be handled during delta migration?
  **Both:** idempotent upsert using the stored target ID (update, not recreate).
        Closed/merged PR archival records are not updated unless the source
        state changed. Skip objects the target owner changed (I10).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Delta | Ev: E20

**I10**. How should changes made in the target after initial migration be handled?
  **Both:** detect target drift by comparing the target against the evidence hash
        before writing. Policy (default): do not overwrite target-side
        changes; report as CONFLICT for customer decision. Git: refuse
        non-fast-forward pushes onto a target branch that has diverged;
        require explicit approval to force. Define a freeze rule per repository
        after cutover (source read-only).
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Delta | Ev: E20

**I11**. What limitations exist for repeated delta migrations?
  **Both:** platform-object authorship cannot be corrected; timestamps are
        migration time; deletions on source need explicit policy; renamed
        repositories need identity by uuid/id, not name; rate budgets limit
        run frequency (C); repeated PR sync on DC is O(PR count) without
        filters; history rewrites invalidate prior SHA mappings.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Delta | Ev: E1, E7

**I12**. How can GitLift confirm the target reflects the approved source state after
     delta migration?
  **Both:** run delta validation (same engine as O): ref/SHA equality, counts,
        evidence vs target compare, expected-difference list; produce a signed
        evidence pack tied to the approved source checkpoint (commit SHAs and
        snapshot hashes at approval time).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E16


### J. Migration Planning

**J1**. What discovery information is required to generate an initial migration plan?
  **Both:** counts (repositories, size, refs, LFS, PRs by state, comments, tasks,
        permissions, rules, webhooks, variables, pipelines (C), submodules,
        forks), coverage and confidence (C9), unsupported-feature flags,
        dependency graph, name-conflict list, identity-match rate.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E20

**J2**. What information is required to generate a delta migration plan?
  **Both:** delta counts (new, modified, deleted per surface), changed refs and
        bytes, checkpoint reference, drift/conflict list, completeness
        statement.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Planning |
     Ev: E16

**J3**. How should repository size and metadata counts influence migration estimates?
  **Both:** time = git transfer (bytes / measured throughput) + LFS bytes /
        throughput + source REST calls / source rate + GH writes / secondary
        content limit (about 80 per minute) + fixed overhead. PR and comment
        counts are the main multipliers for metadata time. Keep coefficients
        configurable and calibrate with trial migrations.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E14, E21

**J4**. How should dependencies influence repository migration order?
  **Both:** topological order of the dependency graph (submodule targets before
        superprojects; parents before forks; shared libraries first); cycles
        are put in one batch.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E16

**J5**. How should repositories be grouped into migration batches?
  **Both:** by target organization (GitHub guidance), then by dependency cluster,
        team/owner readiness, size, and risk (unsupported items). Keep
        dependent repositories in one batch. Run a trial batch into a sandbox
        organization first.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E14

**J6**. How should incomplete discovery information affect planning confidence?
  **Both:** confidence = min(per-surface coverage); show LOW when PR counts or
        permissions are unknown; block "ready" status below a configurable
        threshold (see J9).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E20

**J7**. How should unsupported metadata influence migration planning?
  **Both:** adds customer-action tasks (re-supply secrets, convert pipelines,
        re-point webhooks, decide PR history policy) and risk flags; may move a
        repository to a later batch or to "manual" status.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E19

**J8**. What differences exist between Cloud and DC/Server planning?
  **C:** budget-based scheduling per credential; Pipelines conversion workstream;
     Issues/Wikis archive check; no network access issues.
  **DC:** instance load windows, network access/VPN/allow lists, version
      compatibility, directory/IdP user mapping, no pipelines but CI
      re-pointing, product end-of-life deadline.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E4, E9, E10

**J9**. What conditions should prevent a repository from being considered
    migration-ready?
  **Both:** any of: no accessible credential; discovery coverage below threshold;
        unresolved name conflict; unresolved dependency without acceptance;
        repository exceeds a target limit (E12 limits: file over 100 MiB
        without LFS, ref name over 255 bytes, commit over 2 GiB); ruleset in the
        target that rejects the history (E12); no identity mapping for required
        owners; unaccepted unsupported items; open conflict from drift.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E12, E20


### K. User Identity, Teams, and Permissions

**K1**. How are users and groups represented in Bitbucket Cloud?
  **C:** Atlassian account: account_id, uuid, nickname, display_name (email hidden by
     privacy). Workspace groups with slug; membership per workspace. Access
     tokens appear as user-like principals.
  => Src: C | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1

**K2**. How are users and groups represented in Bitbucket DC/Server?
  **DC:** user: id, name (username), slug, displayName, emailAddress, active,
      directory (internal, LDAP, Crowd, Jira). Groups are global names. Project
      and repository permissions reference users and groups.
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E7

**K3**. How should Bitbucket users be mapped to GHEC EMU managed users?
  **Both:** matching keys in order: verified email (IdP) > username/UPN > employee
        id attribute > manual CSV from the customer. Managed usernames are
        IdP-derived (shortcode suffix), so mapping is to the EMU login, not to
        the Bitbucket name. Output = mapping table with status MATCHED /
        AMBIGUOUS / UNMATCHED. Use the customer's IdP export as the
        authoritative list.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E11, E16

**K4**. How should users without an identified target identity be handled?
  **Both:** keep the work, lose the link: reviewers/assignees are dropped (listed in
        the exceptions report); authorship kept in text provenance; permissions
        for that user are not granted; offer a placeholder/"ghost" convention
        only if the customer approves. Departed users are reported separately.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E11, E20

**K5**. How should commit authorship be preserved?
  **Both:** Git commit author/committer are preserved by the Git push. EMU linking:
        GitHub links a commit to the managed user only if the commit email matches
        the (single) email in the IdP profile. For mismatches either accept an
        unlinked display, or perform a controlled history rewrite (mailmap) with
        customer approval (changes SHAs; high impact). Default: no rewrite.
  => Src: C,DC | Result: Supported | GitLift: Existing (history rewrite) |
     Impact: Migration | Ev: E11, E16 | NV-19

**K6**. How should PR authors, reviewers and approvers be handled?
  **Both:** PR author = the migration identity (native limitation); original author
        and creation time in a header; reviewers assigned to mapped users;
        approvals stored as evidence and a summary line. GEI would attribute to
        mannequins that can be reclaimed (DC only); GitLift cannot.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E12, E19

**K7**. How should comments and historical user attribution be preserved?
  **Both:** each migrated comment gets a header with original author (display name,
        mapped login if any) and original timestamp; the structured original
        is stored in evidence. Native author/time fields cannot carry original
        values.
  => Src: C,DC | Result: Partially Supported | GitLift: Existing (pattern from
     GitLab) | Impact: Migration | Ev: E19, E20

**K8**. How should workspace, project and repository permissions be mapped?
  **C:** workspace admin -> organization owner (only designated); workspace member
     -> organization member; project and repository permissions -> team grants
     (admin -> Admin, write -> Write, read -> Read).
  **DC:** global admin/system admin -> not mapped automatically (customer decision);
      project admin/write/read and repo admin/write/read -> team grants
      (ADMIN -> Admin, WRITE -> Write, READ -> Read).
  EMU: if the IdP drives teams (IdP group sync), grants should target IdP-backed
  teams; GitLift must not create membership that the IdP will remove.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E7, E11 | NV-03

**K9**. How should Bitbucket groups be mapped to GitHub teams?
  **Both:** one team per group, same slug (sanitized), membership from mapped users.
        In EMU prefer linking the team to the IdP group (membership managed by
        the IdP); static membership is only an interim step. Groups with
        unmatched users are reported.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E11

**K10**. How should inherited permissions be handled?
  **C:** effective access = workspace role + project permission + group grants +
     repository permission; compute effective per repository.
  **DC:** repository permission inherits from project; global permissions;
      repository-level explicit entries override; project "public" access.
  **Both:** compute effective permission per (principal, repository), then write the
        minimal team grants; do not copy inheritance structure.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E7 | NV-20

**K11**. What identity and permission information cannot be migrated?
  **Both:** passwords, 2FA state, SSH/GPG user keys (user-owned), tokens, SSO
        sessions, notification preferences, watchers, user avatars (managed by
        IdP in EMU), per-user settings, DC directory configuration, Cloud
        Atlassian Access/SCIM configuration.
  => Src: C,DC | Result: Unsupported | GitLift: Existing (reporting) |
     Impact: Migration | Ev: E11

**K12**. What identity-related restrictions apply specifically to GHEC EMU?
  **Both:** users must be provisioned by SCIM; usernames are normalized, conflicts
        possible; profile name and email are IdP-controlled (one email); cannot
        collaborate outside the enterprise; no public content; org membership
        and repository access can be IdP-group driven; Okta + Entra ID mixed
        SSO/SCIM is unsupported; GEI mannequins can only be reclaimed to
        enterprise members.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E11 | NV-03


### L. Wiki and Documentation Migration

**L1**. What wiki capabilities are available in Bitbucket Cloud?
  **C:** none now. Native wiki (separate Git repository) removed 2026-08-20.
  => Src: C | Result: Unsupported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E5, E6

**L2**. What wiki capabilities are available in Bitbucket DC/Server?
  **DC:** no native wiki. Documentation is repository files (README, docs folder)
      and Confluence links. Marketplace apps may add wiki-like features
      (NV-21).
  => Src: DC | Result: Unsupported | GitLift: Existing (reporting) |
     Impact: Discovery | Ev: E7 | NV-21

**L3**. What documentation content can be discovered and migrated?
  **Both:** README and docs files (migrated with Git), CODEOWNERS/templates
        (Git), PR/issue templates (Git), Confluence pages (outside scope;
        report links), C retained wiki clone (archive).
  => Src: C,DC | Result: Partially Supported | GitLift: Existing | Impact:
     Migration | Ev: E16

**L4**. How should wiki content be mapped to GitHub Wiki?
  C archive: push the retained wiki Git history to the target wiki repository
     (same mechanism as GitLab wiki: clone, optional rewrite, push, init page).
  **DC:** nothing to map; offer README/docs into a `docs/` folder or Confluence link
      listing as a customer action.
  => Src: C,DC | Result: C=Partially Supported, DC=Unsupported | GitLift:
     Existing | Impact: Migration | Ev: E16

**L5**. How should wiki history, attachments and links be handled?
  C archive: history preserved by Git; attachments inside the wiki repository
     move with it; links to Bitbucket URLs and Creole markup need a rewrite
     (existing wiki rewrite script handles link rewriting for GitLab).
  => Src: C | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E16

**L6**. Can existing GitLift wiki migration capabilities be reused?
  Yes (clone, rewrite, push, check, snapshot, init scripts and wiki validation
  exist). New work: accept an archive path as the source instead of a live API.
  => Src: C | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E16

**L7**. What differences exist between Cloud and DC/Server wiki migration?
  **C:** archive-only migration possible. DC: none; no wiki migration exists.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E5, E7

**L8**. How should unsupported documentation content be reported?
  **Both:** exception entries (Confluence links, missing wiki archive, markup that
        cannot be converted) with count and owner action.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E20

**L9**. How should migrated wiki content be validated?
  C archive: compare page list, content hashes and Git history (commit count,
     head SHA) between the retained clone and the target wiki repository
     (existing wiki source/target validation).
  => Src: C | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E16


### M. Git LFS and Repository Size

**M1**. How can GitLift identify repositories using Git LFS?
  **Both:** `.gitattributes` filters and pointer files in the clone (existing hybrid
        LFS discovery). DC may also expose an LFS-enabled flag (NV-12).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Discovery |
     Ev: E16 | NV-12

**M2**. How can large files and repository size limitations be identified?
  **Both:** git-sizer and file-detail scans; compare against GitHub limits: 100 MiB
        per file after migration (400 MiB during GEI migration), 255-byte ref
        names, 2 GiB per commit, 40 GiB GEI archive limit (E12).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Discovery |
     Ev: E12, E16

**M3**. What differences exist between Cloud and DC/Server LFS handling?
  **C:** LFS enabled by default per repository, storage in Bitbucket-managed store,
     limits by plan.
  **DC:** LFS enabled per repository (admin/repository admin), stored on the server's
      shared home; Bearer auth issue with LFS (BSERV-13613): use Basic.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E8 | NV-12

**M4**. Can existing GitLift Git LFS migration capabilities be reused?
  Yes: LFS fetch-all and push scripts exist; add Bitbucket auth for the LFS
  endpoint.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E16

**M5**. How should missing or inaccessible LFS objects be handled?
  **Both:** fetch reports missing oids; record each (path, oid); migrate remaining
        objects; mark the repository PARTIAL with the missing list; customer
        decides to accept (broken pointers) or fix at source. Never report
        success when pointers lack objects.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E16

**M6**. How should repositories exceeding target migration limits be handled?
  **Both:** files over 100 MiB: convert to LFS with history rewrite (customer
        approval) or exclude; refs over 255 bytes: rename; commit over 2 GiB:
        split; large repository: git-sizer thresholds -> manual track.
        Document each as a BLOCKER in readiness (J9).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E12

**M7**. Can Git Sizer be reused for Bitbucket repositories?
  Yes. It works on the local mirror regardless of provider (existing git-sizer
  discovery script).
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Discovery |
     Ev: E16

**M8**. How should migrated Git LFS content be validated?
  **Both:** compare the set of oids and sizes from source pointers against target LFS
        (batch API / `git lfs ls-files --all` on a target clone); verify
        download of a sample; report counts and bytes.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E16


### N. CI/CD, Webhooks, and Integrations

**N1**. What pipeline and automation metadata can be discovered from Bitbucket Cloud?
  **C:** bitbucket-pipelines.yml, pipeline runs/steps/logs, schedules, variables
     (key, scope, secured), runners, caches, deployment environments,
     deployments, OIDC usage.
  => Src: C | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E1 | NV-25

**N2**. What automation and integration metadata can be discovered from DC/Server?
  **DC:** webhooks (repository/project), repository hooks and merge checks,
      application links, installed apps, build statuses and deployments from
      the Builds and Deployments API, CI configuration files in the repository.
  => Src: DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E7

**N3**. Which automation capabilities have a GHEC EMU equivalent?
  **Both:** webhooks -> webhooks; C Pipelines -> Actions; variables/secrets ->
        Actions variables/secrets; environments -> environments; runners ->
        self-hosted runners; OIDC -> Actions OIDC; build status -> commit
        status/checks; DC external CI (Jenkins/Bamboo) -> re-point to GitHub
        webhooks or convert to Actions.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E19

**N4**. Which configurations can be migrated directly?
  **Both:** repository webhooks (URL, events mapped, active), plain (non-secret)
        variables, deploy keys (public keys), CODEOWNERS and templates (Git),
        environment names.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E16, E19

**N5**. Which configurations require transformation or customer action?
  **Both:** Pipelines YAML conversion; Pipes to Actions; secured variables and
        secrets (re-supply); webhook secret (new) and receiver change;
        OAuth apps/consumers (new GitHub Apps); OIDC trust; runner setup; DC
        Jenkins/Bamboo jobs; Jira/Slack/Teams links.
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E19

**N6**. How should sensitive configuration information be handled?
  **Both:** never persist secret values (variables, tokens, webhook secrets) in
        discovery or evidence; store key, scope, protection flags and a value
        hash only where the value is legitimately available; mask in logs; keep
        credentials in a secret store; separate source and target credentials.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Discovery |
     Ev: E20

**N7**. How should webhooks be migrated or recreated?
  **Both:** fetch -> dedup check on the target by URL -> create (PATCH on conflict).
        Map events: Cloud repo:push -> push; pullrequest:created/updated/
        fulfilled/rejected -> pull_request; DC repo:refs_changed -> push,
        pr:opened/merged/declined -> pull_request. Payload schemas differ, so
        consumers must change (customer action).
  => Src: C,DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E19

**N8**. How should unavailable webhook secrets be handled?
  **Both:** the source secret is not retrievable (C exposes `secret_set` only; DC
        NV-24). Create the target webhook with a newly generated secret, deliver
        it to the receiver owner through an approved channel, and report as
        "customer action: update receiver".
  => Src: C,DC | Result: Partially Supported | GitLift: Existing | Impact:
     Migration | Ev: E1 | NV-24

**N9**. How should third-party integrations be identified and reported?
  **C:** workspace OAuth consumers, installed Forge/Connect apps, Jira DVCS link,
     Slack/Teams connections (partly UI-only): collect what the API returns, ask
     the customer for the rest.
  **DC:** application links, installed apps (admin), repository hooks, webhook
      targets, Jira link.
  Report: integration, owner, target equivalent, action.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E7

**N10**. How should migrated automation and integration configurations be validated?
  **Both:** read back webhook URL/events/active; compare variable key/scope; run a
        test delivery to the receiver (customer-approved); for converted
        workflows run a smoke workflow. Secret values are never compared.
  => Src: C,DC | Result: Supported | GitLift: Existing (pattern) | Impact:
     Validation | Ev: E16

**N11**. What differences exist between Cloud and DC/Server (CI/CD, webhooks,
     integrations)?
  **C:** native Pipelines conversion workstream; workspace-level hooks and
     variables. DC: no native pipelines; project-level hooks; external CI
     ownership; application links; installed apps may change behavior.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E1, E7


### O. Validation and Migration Evidence

**O1**. What evidence should GitLift capture during initial migration?
  **Both:** run id, source (provider, instance/workspace, repository id/uuid), object
        class and id, source snapshot hash, source ref/SHA map, target ids/URLs,
        action/result/timestamps/retries, transformation reasons, exceptions,
        identity mapping used, git-sizer/LFS summaries, tool version, operator.
        Secrets redacted.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E16, E20

**O2**. What evidence should be captured during delta migration?
  **Both:** same as O1 plus checkpoint ids (previous and current), NEW/MODIFIED/
        DELETED/UNCHANGED classification, drift/conflict records, and the
        approved source state (SHAs and hashes) used for confirmation.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E16

**O3**. How should source and target repository content be compared?
  **Both:** ref list equality (name -> SHA) via `ls-remote`; commit count and
        tip tree hash; file tree comparison by hash for default and sampled
        branches; LFS oid set; submodule URLs; wiki hash (C archive). If history
        was rewritten, compare against the recorded SHA mapping instead.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E16

**O4**. How should branches, tags and commits be validated?
  **Both:** every source branch/tag exists on target with the same SHA (or mapped
        SHA); counts equal; annotated tag objects equal; default branch equal;
        extra target refs listed as unexpected.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E16

**O5**. How should pull requests and associated metadata be validated?
  **Both:** for each open PR: target PR exists, base/head match, title/body provenance
        present, reviewer assignments match mapping, comment count matches
        (migrated vs source), tasks present. Closed/merged/declined PRs:
        archival record exists or recorded as an accepted exception.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E16

**O6**. How should users, permissions and governance settings be validated?
  **Both:** compare the effective-permission set from evidence with the target
        (teams, repository roles); verify each ruleset against the translated
        rule list; test access with controlled accounts for a sample; flag
        users with no mapping.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Validation | Ev: E19

**O7**. How should submodule relationships and dependencies be validated?
  **Both:** see E8.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E16

**O8**. How should Git LFS and wiki content be validated?
  **Both:** see M8 and L9.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E16

**O9**. How should expected differences and unsupported metadata be recorded?
  **Both:** expected-difference register entries (object class, id, reason code, who
        approved, date). Reason codes: AUTHOR_NOT_SETTABLE, TIMESTAMP_REPLACED,
        STATE_MAPPED, SECRET_NOT_MIGRATED, FEATURE_UNSUPPORTED,
        SOURCE_REMOVED, CUSTOMER_EXCLUDED, REWRITE_APPLIED.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Validation |
     Ev: E20

**O10**. What conditions determine whether a repository passes validation?
  **Both:** PASS = all mandatory checks equal or explained by an approved expected
        difference: refs/SHAs, counts, LFS, submodules, rules, permissions,
        webhooks. PASS_WITH_EXCEPTIONS = only approved differences remain.
        FAIL = unexplained difference or any mandatory check not run.
        Unsupported capabilities are never PASS (AC17).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E20

**O11**. How should partial migration and validation failures be reported?
  **Both:** per-repository status ladder: NOT_STARTED, GIT_DONE, METADATA_PARTIAL,
        METADATA_DONE, VALIDATION_FAILED, VALIDATED, CUTOVER_READY. Report failed
        step, error class, retries, next action and whether safe to retry.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E20

### P. Cutover Readiness

**P1**. What repository and metadata conditions must be satisfied before cutover?
  **Both:** repository status VALIDATED (O10) with no unexplained differences; delta
        applied and validated against the approved source checkpoint; identity
        mapping complete for owners/admins; teams and access verified; rules in
        place; dependencies resolved or accepted; LFS complete; webhooks and
        integrations re-pointed or scheduled; secrets re-supplied; customer
        approvals recorded; rollback plan agreed; source freeze window set.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Cutover | Ev: E14, E20

**P2**. What governance settings must be verified in GHEC EMU?
  **Both:** enterprise/org policies (repository visibility, forking, base
        permissions, Actions policy), SSO/SCIM state, IdP group to team links,
        organization and enterprise rulesets (can reject migrated history),
        custom properties, secret scanning/Dependabot policy (if licensed), IP
        allow list, audit log streaming target.
  => Src: C,DC | Result: Requires Validation | GitLift: New Capability Required |
     Impact: Cutover | Ev: E11, E12 | NV-29

**P3**. How should repository visibility and access permissions be verified?
  **Both:** compare each repository's visibility to the approved decision (private or
        internal only in EMU; GEI migrates as private); compare effective
        access from evidence with target team grants; run an access test with
        controlled accounts (one per role) on a sample, and for all repositories
        flagged HIGH-risk.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Cutover | Ev: E13, E14

**P4**. How should branch protection and approval requirements be verified?
  **Both:** read target rulesets, compare with the translation output (Appendix C),
        list rules with no equivalent as accepted exceptions, and run a negative
        test (blocked push/merge) on a sandbox branch where policy allows.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Cutover | Ev: E3, E12

**P5**. How should repository ownership and target organization placement be
    confirmed?
  **Both:** compare the target organization, team owners and custom properties with
        the approved mapping table; each repository has a named customer
        owner; orphaned repositories (owner unmapped) block cutover.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Cutover | Ev: E14

**P6**. How should unresolved dependencies be handled before cutover?
  **Both:** list UNRESOLVED dependencies (E5); each requires one of: migrate the
        dependency, accept the cross-platform link with a documented owner, or
        remove the link. Without a decision the repository is not cutover-ready.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E20

**P7**. What happens when source repositories change during the cutover period?
  **Both:** freeze writes on the source (set read-only: C repository/branch
        restrictions or permission change; DC read-only branch permission or
        permission change by the customer admin), take the final checkpoint,
        run the final delta, validate, then switch. A change after the final
        checkpoint invalidates approval and requires another delta and
        validation. Document who may write during the window.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E16

**P8**. What conditions should block cutover?
  **Both:** validation FAIL or not run; coverage/confidence below threshold; unresolved
        name conflict, dependency, identity or permission gap; unresolved
        high-severity exception (for example LFS objects missing, ruleset
        rejection); target policy mismatch; missing customer approval; source
        changed after checkpoint; credentials/quota exhausted; unsupported item
        classified ready without evidence (AC17).
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Cutover | Ev: E20

**P9**. What customer approvals are required before cutover?
  **Both:** (1) mapping approval (hierarchy, names, visibility); (2) identity and
        permission approval; (3) exceptions/unsupported acceptance; (4) PR
        history policy acceptance; (5) validation evidence approval; (6) freeze
        window and rollback approval; (7) post-cutover consumer readiness
        (webhooks, CI, remotes). Record approver, date, evidence version.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Cutover | Ev: E14, E20

**P10**. How should unresolved migration limitations be communicated?
  **Both:** a customer-facing exceptions report per repository and per program
        (object class, count, reason, workaround, owner, due date), included in
        the approval pack and referenced by the validation report. No silent
        omissions.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E20

**P11**. What evidence confirms that a repository is ready for cutover?
  **Both:** evidence pack = final checkpoint id, validation report (PASS or
        PASS_WITH_EXCEPTIONS), SHA/ref comparison, counts, LFS check, rules
        comparison, access test results, identity mapping report, exceptions
        register with approvals, delta report, freeze confirmation.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E20


### Q. Migration Constraints and Failure Handling

**Q1**. What limitations apply to Bitbucket Cloud migrations?
  **C:** (1) 1,000 requests/hour default per user; (2) Issues and Wikis removed
     2026-08-20 (archive only); (3) secured variable and webhook secret values
     unreadable; (4) permissions and branch restrictions need admin; access
     tokens cannot query permissions; (5) no GraphQL; (6) API limits/pagelen
     can change; (7) no tag protection, archive, labels, releases, topics,
     registries to migrate; (8) SSH host change and OAuth refresh-token
     rotation require client updates; (9) Atlassian Connect app model ending
     (integrations must be rebuilt).
  => Src: C | Result: Supported | GitLift: Existing (reporting) | Impact:
     Migration | Ev: E1, E4, E5, E6

**Q2**. What limitations apply to Bitbucket DC/Server migrations?
  **DC:** (1) private network and admin cooperation needed; (2) version-specific REST
      fields; (3) optional rate limiting with per-node buckets; (4) users/groups
      and apps need admin rights; (5) no native Pipelines/Wiki/Issues, so these
      are external-system topics; (6) personal repositories (GEI excludes them);
      (7) webhook secrets not exposed (NV-24); (8) product end of life 2029-03-28;
      (9) Bearer auth issue with Git LFS (BSERV-13613); (10) project/repo
      tokens need a Data Center license.
  => Src: DC | Result: Supported | GitLift: Existing (reporting) | Impact:
     Migration | Ev: E7, E8, E9, E10

**Q3**. What source-version differences affect migration compatibility?
  **C:** continuous delivery; track deprecations in the Cloud changelog (examples:
     app passwords deprecated, SSH hostname, OAuth rotation, removed
     endpoints). Pin behavior with contract tests.
  **DC:** REST resources and fields vary by version; GEI requires 5.14+; features such
      as project/repository tokens (DC license), repository archiving, and newer
      PR features depend on version. Detect version at start (application
      properties endpoint, NV-22) and gate features per version.
  => Src: C,DC | Result: Requires Validation | GitLift: New Capability Required |
     Impact: Discovery | Ev: E5, E12 | NV-22

**Q4**. What repository objects or metadata cannot be migrated?
  See D15 and Q1/Q2. Summary: original actors and timestamps of platform
  objects, secret values, historical runtime data, closed/merged PRs as native
  PRs, per-user state, original IDs/URLs, unsupported-semantics rules, DC
  personal repositories under GEI, Cloud Issues/Wikis without archive.
  => Src: C,DC | Result: Unsupported | GitLift: Existing (reporting) | Impact:
     Migration | Ev: E12, E19

**Q5**. What restrictions apply to closed, merged or declined pull requests?
  **Both:** GitLift cannot create native merged/closed/declined PRs with original
        state, author or time through the standard API (same rule as GitLab).
        Fallback options (customer chooses per program): (a) archival issue per
        PR with key fields and link, (b) external archive (JSON/HTML) with the
        evidence table, (c) keep source read-only for reference. States:
        Cloud MERGED, DECLINED, SUPERSEDED; DC MERGED, DECLINED. GEI (DC only)
        migrates pull requests, including merged ones, with caveat (merged
        and head-branch-deleted PRs may fail to view, E12); this is the
        main reason to evaluate GEI for DC (BB-034).
  => Src: C,DC | Result: Unsupported | GitLift: Existing (GitLab fallback);
     Enhancement Required (Bitbucket) | Impact: Migration | Ev: E12, E20 | NV-15

**Q6**. What restrictions apply to historical user attribution?
  **Both:** only commit authors/committers survive. Everything else is attributed to
        the migration identity (or GEI mannequins for DC under GEI). EMU adds the
        single-email rule and IdP-controlled usernames (E11).
  => Src: C,DC | Result: Partially Supported | GitLift: Existing | Impact:
     Migration | Ev: E11, E12

**Q7**. What restrictions apply to repository permissions and governance settings?
  **Both:** no inheritance container on GHEC (project permissions expand);
        no actor-based "who can merge" allowlist (use rulesets with bypass
        actors, required reviews); several Cloud merge-check kinds have no
        native equivalent (Appendix C); DC repository hooks/merge checks are
        app-defined; GEI does not migrate branch permissions or repository
        settings (E12); EMU teams may be IdP-managed.
  => Src: C,DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E3, E11, E12

**Q8**. How should rate limits and access restrictions be handled?
  **C:** per-user budget governor (token bucket sized to 1,000/hour unless a higher
     scaled limit is confirmed), read X-RateLimit-* where returned, honor
     Retry-After if present, exponential backoff with jitter on 429/5xx,
     prefer local Git for bulk data.
  **DC:** client-side throttle below the configured bucket (default 60 burst, 5/s,
      per node); on 429 back off and reduce concurrency; request an exemption
      for the service account (admin REST/UI); avoid parallel request threads
      (Atlassian guidance).
  GitHub: respect primary and secondary limits (point costs, 100 concurrent,
      about 80 content creations per minute); use retry-after/reset headers;
      separate tokens per role.
  Access restrictions: surface per-object status (A6).
  => Src: C,DC | Result: Supported | GitLift: Existing (global handling);
     Enhancement Required (per provider) | Impact: Discovery | Ev: E4, E9, E21

**Q9**. How should interrupted or failed migrations be handled?
  **Both:** step-level checkpoints persisted after each successful step; resume from
        the last checkpoint; failed step recorded with error class; the
        repository status ladder (O11) shows the stage; target partial state is
        detected by comparing evidence with the target before retrying.
  => Src: C,DC | Result: Supported | GitLift: Existing | Impact: Migration |
     Ev: E16, E17

**Q10**. How should retries avoid duplicate or inconsistent migrated content?
  **Both:** idempotency keys = (run scope, source type, source id) stored with the
        target id; before create, look up the mapping/evidence (and query the
        target by a provenance marker where needed); upsert for repositories,
        webhooks (dedup by URL), variables, rules; PR/issue creation guarded by
        the marker; Git pushes are naturally idempotent; no blind re-run after
        timeouts (verify target first).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E16, E20

**Q11**. How should partially migrated repositories be identified?
  **Both:** status ladder + coverage comparison between evidence and target (objects
        expected vs found), listing missing classes; repositories in
        METADATA_PARTIAL or VALIDATION_FAILED are flagged and excluded from
        cutover until resolved.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E20

**Q12**. What conditions require customer intervention?
  **Both:** unmapped identities; name conflicts; visibility decisions; rejected
        history (ruleset or limit violation); secrets to re-supply; webhook
        receivers to update; LFS missing objects; closed/merged PR policy;
        unaccepted exceptions; credentials/permissions insufficient; network
        access (DC); EMU/IdP configuration gaps; Issues/Wikis archive
        availability (C).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E20

**Q13**. How should migration limitations be reflected in validation and cutover
     readiness?
  **Both:** every limitation is an exception entry with reason code (O9) that is
        either approved (validation PASS_WITH_EXCEPTIONS, readiness continues) or
        unapproved (validation FAIL, readiness blocked). Unsupported items are
        never PASS (AC17).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E20


### R. GitHub Enterprise Importer (GEI) Comparison

**R1**. Does GEI support migration from Bitbucket Cloud?
  **C:** not documented. GitHub's documentation lists a Bitbucket Server / Data
     Center route only. Treat as unsupported; re-check GitHub docs at project
     start (NV-01).
  => Src: C | Result: Unsupported | GitLift: New Capability Required |
     Impact: Migration | Ev: E12 | NV-01

**R2**. Does GEI support migration from Bitbucket DC/Server?
  **DC:** yes, Bitbucket Server or Data Center version 5.14 or higher, repository by
      repository, using the BBS2GH CLI extension.
  => Src: DC | Result: Supported | GitLift: Enhancement Required (decision
     BB-034) | Impact: Migration | Ev: E12, E13

**R3**. What repository content does GEI support?
  **DC:** Git source including commit history; pull requests including comments,
      pull request reviews, file/line review comments, required reviewers and
      attachments.
  => Src: DC | Result: Supported | GitLift: Existing (Git); New Capability
     Required (PR parity) | Impact: Migration | Ev: E12

**R4**. What pull request metadata does GEI support?
  **DC:** comments, reviews, review comments at file and line level, required
      reviewers, attachments. Caveat: merged PRs whose head branch was deleted
      may be unviewable because Git objects are unavailable (HTTP 500 on view).
      State fidelity (open/closed/merged) to be confirmed in a trial (NV-26).
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E12 | NV-26

**R5**. What user attribution capabilities does GEI provide?
  **DC:** all activity other than Git commits is attributed to mannequins
      (placeholder identities); organization owners can reclaim mannequins to
      organization members (single or bulk). Commits keep Git authorship. This
      is the capability GitLift lacks (native author reattribution).
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E14 | NV-03

**R6**. What repository settings and governance metadata are excluded by GEI?
  **DC:** personal repositories, branch permissions, commit comments, repository
      settings, CI pipelines; repository permissions are not migrated (create
      teams manually); repositories migrate as private; LFS objects are not
      migrated (push separately).
  => Src: DC | Result: Unsupported | GitLift: Existing/Enhancement Required
     (GitLift covers settings, rules, permissions, LFS) | Impact: Migration |
     Ev: E12, E14

**R7**. What migration size and version restrictions apply to GEI?
  **DC:** source 5.14 or higher; repository archive limit 40 GiB (public preview);
      file size 400 MiB during migration (100 MiB afterwards); commit 2 GiB; ref
      name 255 bytes; code search re-index delay; org rulesets can make
      migrations fail; classic PAT only (blocked if classic PAT restriction
      policy is on); source needs admin/super admin credentials and SFTP (Linux) or
      SMB (Windows) access; IP allow lists must admit GEI ranges.
  => Src: DC | Result: Supported | GitLift: Existing (limit checks to add) |
     Impact: Planning | Ev: E12, E13

**R8**. Does GEI support delta migration?
  Not documented. Migration is per repository, run once; the ticket records
  that the documented importer does not support delta. A repeat run re-creates
  the migration (NV-26 to confirm behavior in a trial). GitLift delta: Git
  fetch/push plus metadata reconciliation (I-section).
  => Src: DC | Result: Unsupported | GitLift: Existing (framework) | Impact:
     Delta | Ev: E12 | NV-26

**R9**. What capabilities does GEI provide that GitLift does not currently support?
  (1) Native PR migration with comments, reviews and review comments including
      closed and merged PRs (DC); (2) mannequin-based attribution with
      reclaim; (3) GitHub-operated migration service, logs and states; (4)
      server-side archive export (SFTP/SMB) avoiding the REST budget for Git
      data; (5) migrator role model.
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E12, E13, E14

**R10**. What capabilities should GitLift provide beyond GEI?
  Cloud support; delta migration; discovery and planning (counts, confidence,
  batches); settings, rules (as rulesets), permissions/teams, webhooks,
  variables, LFS objects, wiki archive; identity mapping for EMU; validation
  with evidence and expected differences; cutover gates; exceptions reporting.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E12, E19

**R11**. Which GEI limitations require separate handling within GitLift?
  LFS push after GEI; permissions/teams; visibility change from private;
  branch rules; repository settings; webhooks/CI/integrations; personal
  repositories; classic PAT and IP allow list setup; ruleset conflicts;
  mannequin reclaim planning; post-migration validation and evidence (GEI logs
  are not a validation report). A GitLift "GEI-assisted" mode for DC would run
  GEI for Git+PRs and GitLift for everything else (BB-034).
  => Src: DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E12, E13, E14, E17


### S. Bitbucket Cloud-Specific Scenarios

**S1**. How should multiple workspaces belonging to the same Atlassian organization
    be handled?
  **C:** discover every workspace the credential can access; treat each as an
     independent source container with its own mapping (default: one target
     organization per workspace; consolidation per U2). Rate budgets are per
     user, shared across workspaces for one identity. Atlassian-organization
     level settings (identity, billing) are out of scope and reported.
  => Src: C | Result: Requires Validation | GitLift: New Capability Required |
     Impact: Planning | Ev: E1 | NV-08

**S2**. How should workspace-level permissions and project-level permissions be
    distinguished?
  **C:** capture workspace role, group membership, project permissions and
     repository permissions as separate evidence records and compute effective
     access. Workspace roles map to organization roles; project/repository
     grants map to team grants (K8, K10).
  => Src: C | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E1 | NV-20

**S3**. How should repositories transferred between workspaces be handled?
  **C:** Bitbucket supports repository transfer (repository admin scope). Key the
     migration by repository uuid, not full_name (the repository can be
     resolved by uuid); detect rename/transfer by uuid match with a changed
     full_name; update the mapping instead of creating a duplicate.
  => Src: C | Result: Supported | GitLift: New Capability Required |
     Impact: Delta | Ev: E1 | NV-30

**S4**. How should workspace ownership changes affect migration planning?
  **C:** changes to the workspace owner/admin can remove the migration credential's
     visibility; re-run an access check before each batch and delta, and keep a
     second admin credential approved by the customer.
  => Src: C | Result: Requires Validation | GitLift: Enhancement Required |
     Impact: Planning | Ev: E1 | NV-30

**S5**. How should Bitbucket Cloud pull request tasks and discussions be migrated?
  **C:** tasks -> markdown checklist (state preserved as checked/unchecked) in the PR
     body or a comment; inline discussions -> review comments anchored by
     commit SHA with threading and resolved state where API allows; general
     comments -> PR comments with provenance header. Native task objects do
     not exist on GHEC.
  => Src: C | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E19 | NV-15

**S6**. How should Bitbucket Pipelines configuration be assessed for GHEC EMU
    migration?
  **C:** parse bitbucket-pipelines.yml per repository; classify constructs (default/
     branches/tags/PR/custom pipelines, steps, parallel, stages, services,
     caches, artifacts, pipes, deployments, size, max-time, clone options,
     condition/changesets, after-script, OIDC); mark each: direct, convertible,
     manual (pipes, runners, custom images); output an effort rating and list
     of variables/secrets used. Assessment only; conversion is a separate
     (customer or assisted) activity.
  => Src: C | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E19 | NV-25

**S7**. How should Bitbucket Cloud deployment configurations be handled?
  **C:** environments (name, type, restrictions) and deployment variables are
     discovered; recreate environment names and variables as GHEC environments
     (protection rules are customer-defined); deployment history is archived,
     not imported (audit/report only, design assumption).
  => Src: C | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E19 | NV-25

**S8**. What limitations arise from Cloud-specific access and administrative
    restrictions?
  **C:** access tokens cannot manage permissions/deploy keys; some endpoints accept
     only specific credential types; admin scopes needed for rules and
     permissions; workspace admin required for groups/members; plan-gated
     features (project/workspace tokens, scaled limits); Atlassian Access/SCIM
     configuration out of scope. Each failure is recorded as FORBIDDEN with
     the required scope.
  => Src: C | Result: Supported | GitLift: Enhancement Required |
     Impact: Discovery | Ev: E1, E4


### T. Bitbucket Data Center/Server-Specific Scenarios

**T1**. How should multiple Bitbucket instances be discovered and assessed?
  **DC:** model "source instance" as a first-class entity (base URL, version, auth,
      rate profile, network route). Run the inventory per instance and
      namespace all ids with the instance id. Detect version and node count per
      instance. Instances can differ in version, directory and hooks.
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E7 | NV-31

**T2**. How should repositories belonging to personal projects be migrated?
  **DC:** discover via ~slug projects and /users/~slug/repos; classify by owner
      status (active, disabled, departed); default policy: report, then migrate
      only on customer approval into a designated org with owner property.
      GEI excludes them, so GitLift's Git path is the only automated route.
  => Src: DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E7, E12

**T3**. How should project-level permissions be mapped to target organizations and
    teams?
  **DC:** project permissions (PROJECT_READ/WRITE/ADMIN) for users and groups -> one
      team per project and level (for example `<proj>-read|write|admin`) granted
      on every repository of that project; group principals map to IdP-linked
      teams where possible; direct user entries become team members. Global
      permissions (LICENSED_USER, PROJECT_CREATE, ADMIN, SYS_ADMIN) are not
      migrated.
  => Src: DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E7, E11 | NV-20

**T4**. How should inherited repository permissions be handled?
  **DC:** effective repository access = repository entries over project entries over
      default/public access; compute effective permission, then emit the
      minimum grants; report repositories with overrides separately (customer
      review).
  => Src: DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Migration | Ev: E7 | NV-20

**T5**. How should repository hooks and installed integrations be assessed?
  **DC:** list webhooks (repository/project), repository hooks and merge checks
      (names, enabled, config where readable), application links, installed
      apps (admin). Classify each: webhook (migrate), core hook (translate),
      app-defined hook (customer decision), Jira/Confluence link (re-link).
  => Src: DC | Result: Partially Supported | GitLift: New Capability Required |
     Impact: Discovery | Ev: E7 | NV-23

**T6**. How should differences between supported DC/Server versions be identified?
  **DC:** read the application version at start; maintain a version-to-capability
      matrix (REST resources, archive flag, token types, rate limiting, PR
      features); gate collectors; fail closed with "unsupported version" and
      report. Server (end of life) instances are treated as DC-compatible only
      after validation.
  => Src: DC | Result: Requires Validation | GitLift: New Capability Required |
     Impact: Discovery | Ev: E12 | NV-22

**T7**. How should repositories with inaccessible or unavailable historical metadata
    be handled?
  **DC:** PR activity or old objects may be missing (for example merged PR with
      deleted head objects, E12), repository in a bad state, missing LFS
      objects. Record per object as UNAVAILABLE with reason; migrate Git;
      customer decides to accept.
  => Src: DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Migration | Ev: E12

**T8**. How should source-specific repository settings be represented in the
    migration assessment?
  **DC:** capture and show: forkable, public/private, state, default branch, LFS flag,
      branch permissions, hooks, merge strategies, default reviewers, commit
      signing settings where exposed; classify each as migrated, translated,
      informational or unsupported.
  => Src: DC | Result: Partially Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E7 | NV-23

**T9**. How should migration readiness be determined when administrative permissions
    are incomplete?
  **DC:** readiness = Git-only ready if the credential can clone; metadata readiness
      is computed per surface from access status (A6); repository with missing
      admin surfaces is READY_WITH_GAPS (not READY), and the gap list needs
      customer approval or an admin re-run.
  => Src: DC | Result: Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E7, E20


### U. End-to-End Migration Scenarios

**U1**. Can a customer migrate selected repositories without migrating an entire
    workspace or project?
  **Both:** yes. Scope is a repository list (by id/uuid). Group-level objects
        (teams, properties) are created only as needed by the selected
        repositories; dependencies outside the list are reported (U5).
  => Src: C,DC | Result: Supported | GitLift: Existing (selection pattern) |
     Impact: Planning | Ev: E16

**U2**. Can repositories from multiple Bitbucket sources be consolidated into one
    GHEC EMU organization?
  **Both:** yes technically. Requires collision-safe naming (U4), source properties
        (`bb_source`, `bb_workspace_or_project`), per-source teams, and
        coordinated rulesets. Verify organization limits and EMU policies.
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E14, E19

**U3**. Can repositories from one workspace or project be distributed across multiple
    target organizations?
  **Both:** yes. Mapping is per repository. Cross-organization dependencies and
        team grants need explicit handling (E4).
  => Src: C,DC | Result: Supported | GitLift: New Capability Required |
     Impact: Planning | Ev: E14

**U4**. How should repository naming conflicts be handled during consolidation?
  **Both:** deterministic rule from B9 applied across sources (add source prefix or
        project key; numeric suffix last); conflicts shown before approval; the
        final name and original path are stored in the mapping and properties.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E19

**U5**. How should migration proceed when dependent repositories are excluded?
  **Both:** list the excluded dependencies; leave references pointing at the source;
        require customer acceptance; schedule a re-validation after the excluded
        repositories migrate; block cutover without acceptance (P6).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Planning | Ev: E20

**U6**. How should GitLift handle repositories that pass core migration but fail
    metadata migration?
  **Both:** status METADATA_PARTIAL; Git content stays valid; retry failed metadata
        steps idempotently (Q10); if not resolvable, record exceptions and ask
        the customer to accept or fix; no cutover until VALIDATED.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E16, E20

**U7**. How should GitLift handle repositories that pass initial migration but fail
    delta validation?
  **Both:** mark VALIDATION_FAILED; keep the last good checkpoint; diff cause
        (source change, drift, tool defect); re-run delta or correct target;
        never overwrite target changes without approval (I10).
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Delta | Ev: E20

**U8**. How should GitLift distinguish migration-complete from cutover-ready?
  **Both:** migration-complete = all in-scope steps executed (status METADATA_DONE).
        validated = validation evidence PASS or PASS_WITH_EXCEPTIONS.
        cutover-ready = validated + approvals (P9) + dependencies resolved +
        final delta applied + freeze confirmed. Three distinct statuses.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E20

**U9**. What customer actions are required for objects that cannot be automatically
    migrated?
  **Both:** re-supply secrets; update webhook receivers; convert pipelines (Cloud) or
        re-point CI (DC); configure IdP groups and SCIM; decide closed/merged PR
        policy; provide issues/wiki archive (Cloud); approve visibility;
        update developer remotes and automation; accept or fix missing LFS
        objects; review rules with no equivalent.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Cutover | Ev: E19, E20

**U10**. How should GitLift demonstrate end-to-end migration completeness for each
     repository?
  **Both:** a per-repository completeness report with a matrix of object classes x
        {discovered, migrated, validated, exception (approved), not applicable}
        and counts source vs target, linked to the evidence pack (P11). Totals
        roll up to program level.
  => Src: C,DC | Result: Supported | GitLift: Enhancement Required |
     Impact: Validation | Ev: E20


## 4. Expected Deliverables: Separate Cloud and Data Center/Server Assessments

Each row records Result and GitLift status for that source (AC16). Details:
IDs in section 3.

| Deliverable | Cloud assessment | Data Center/Server assessment | Questions |
|-------------|------------------|-------------------------------|-----------|
| Authentication assessment | API token (Basic/Bearer), access tokens, OAuth 2.0; admin scopes for rules/permissions; 1,000/hour budget. Result: Supported. GitLift: New Capability Required. | Basic, HTTP access tokens (user/project/repo), OAuth; admin for users/groups/apps; optional rate limiter. Result: Supported (NV-04). GitLift: New Capability Required. | A1-A9 |
| Hierarchy mapping | Workspace>Project>Repo -> org + Team + property + repo. Result: Partially Supported. | Project>Repo (+personal) -> few orgs + Team + property + repo. Result: Partially Supported. | B1-B10, S1, T1-T3 |
| Metadata inventory | Section 5 (Cloud column). | Section 5 (DC column). | D1-D15 |
| Discovery assessment | Fast and detailed supported, REST only, budget-bound. | Fast and detailed supported, version/admin/load-bound. | C1-C10, F1-F8 |
| Migration capability assessment | Git/LFS/open PR/settings/rules/webhooks supported or partial; closed PRs unsupported; Issues/Wikis archive only. | Same plus GEI option; closed/merged PRs via GEI only; no Pipelines/Wiki/Issues. | G, H, Q |
| Delta migration assessment | Filters (`updated_on`), refs, snapshots. Supported with limits. | Refs, sort order, snapshots; filters undocumented. Partially Supported (NV-17). | I1-I12 |
| Identity mapping | Atlassian accounts -> EMU via email/IdP export; groups -> teams. | Directory users -> EMU via email/username/IdP export; groups -> teams. | K1-K12 |
| Dependency assessment | Submodules, pipelines triggers, forks. | Submodules, CI jobs, hooks, forks. | E1-E8 |
| Migration planning assessment | Budget scheduling, Pipelines workload, archive check. | Instance load, network, version, personal repos, EOL. | J1-J9 |
| Validation assessment | Evidence-based compare; Git/LFS/PR/rules/permissions/webhooks. | Same. | O1-O11 |
| Cutover readiness assessment | Gates P1-P11; freeze via restrictions. | Same; freeze via permissions/branch permissions. | P1-P11 |
| Importer comparison | GEI: not documented for Cloud. | GEI: documented (5.14+): Git + PRs; no permissions/settings/LFS/CI/personal repos; no delta. | R1-R11 |
| Implementation backlog | Section 7. | Section 7. | all |


## 5. Metadata Inventory Classification (AC3)

Classes: D = direct equivalent; T = transformation/separate handling;
U = unsupported; A = archive only; N/A = does not exist at source.

| Metadata | Cloud | DC/Server |
|----------|-------|-----------|
| Repository name, description, default branch | D | D |
| Visibility (public/private) | T (EMU: private or internal only) | T |
| Branches, tags, commits, annotated tags | D | D |
| Git LFS objects | D (explicit push) | D (explicit push, Basic auth) |
| Submodules | D (URL rewrite) | D (URL rewrite) |
| Forks | T (re-fork) | T (re-fork) |
| Archive state | N/A | T (version-dependent) |
| Topics, stars, labels, releases | N/A | N/A |
| Project / workspace / instance hierarchy | T | T |
| Personal repositories | T (personal workspace) | T (personal project; GEI excludes) |
| Users | T (mapping; IdP-owned in EMU) | T |
| Groups | T (teams) | T |
| Permissions | T (expanded grants) | T |
| Branch rules | T (rulesets, partial) | T (rulesets, partial) |
| Tag protection | N/A | T (if branch permissions cover tags, NV-09) |
| Default reviewers | T (CODEOWNERS) | T (CODEOWNERS) |
| Open PRs | T | T |
| Closed/merged/declined PRs | U (fallback record) | U for GitLift, GEI supports |
| PR comments, reviews, approvals, tasks | T (provenance, checklist) | T |
| Issues | A (removed) | N/A (Jira) |
| Wiki | A (removed) | N/A |
| Snippets | T (Gist/repo) | N/A |
| Downloads | T (release assets) | N/A |
| Pipelines config | T (convert) | N/A |
| Pipeline runs/logs/deployments | U (archive) | N/A |
| Variables (plain) | T | N/A |
| Variables/secrets (secured) | U (re-supply) | N/A |
| Environments | T | N/A |
| Build statuses | U (history) | U (history) |
| Webhooks | T | T |
| Webhook secrets | U | U (NV-24) |
| Deploy/access keys | T (re-add) | T (re-add) |
| OAuth apps/consumers, installed apps | T (new GitHub Apps) | T (app links, apps) |
| Jira/Slack/Teams links | T (re-link) | T |
| Audit log | U (archive) | U (archive) |
| Tokens, passwords, 2FA, SSH user keys | U | U |
| Watchers, notifications | U | U |
| Original authors/timestamps (platform objects) | U | U (GEI: mannequins) |


## 6. Limitations (AC11)

Bitbucket Cloud: Q1 (items 1-9), D15, section 5 class U and A.
Bitbucket Data Center/Server: Q2 (items 1-10), D15, section 5 class U.
Common to both: Q4, Q5, Q6, Q7.


## 7. Implementation Backlog (AC14, AC16)

Status: Existing / Enhancement Required (E) / New Capability Required (N).

| ID | Story | Src | Status | Impact | AC |
|----|-------|-----|--------|--------|----|
| BB-001 | Cloud auth adapter: API token Basic/Bearer, access tokens, OAuth refresh rotation, SSH host change | C | N | Discovery | 1 |
| BB-002 | DC auth adapter: Basic, HTTP tokens (Bearer, x-token-auth), LFS Basic rule | DC | N | Discovery | 1 |
| BB-003 | Provider-aware token pool and health daemon | C,DC | E | Discovery | 1, 13 |
| BB-004 | Per-provider rate governors (Cloud budget, DC token bucket, GitHub primary/secondary) | C,DC | E | Discovery | 6, 11 |
| BB-005 | Access/coverage model: per-object access status, expected-inventory comparison | C,DC | E | Discovery | 1, 4 |
| BB-006 | Cloud inventory collector (workspaces, projects, repositories, personal) | C | N | Discovery | 2, 3 |
| BB-007 | DC inventory collector (instances, version detect, projects, personal projects) | DC | N | Discovery | 2, 3 |
| BB-008 | Fast discovery for Cloud and DC (counts, Git signals, confidence) | C,DC | N | Discovery | 4 |
| BB-009 | Detailed discovery: PRs and child objects (comments, tasks, reviewers) | C,DC | N | Discovery | 3 |
| BB-010 | Detailed discovery: users, groups, permissions (effective access) | C,DC | N | Discovery | 3, 7 |
| BB-011 | Detailed discovery: branch rules, settings, default reviewers | C,DC | N | Discovery | 3 |
| BB-012 | Cloud Pipelines/variables/environments discovery and assessment | C | N | Discovery | 8 |
| BB-013 | DC builds, hooks, app links, installed apps discovery | DC | N | Discovery | 8 |
| BB-014 | Webhook/integration inventory without secrets | C,DC | E | Discovery | 8 |
| BB-015 | Cloud Issues/Wikis archive ingestion (export JSON, wiki clone) | C | E | Discovery | 8 |
| BB-016 | Hierarchy mapping engine (org/team/property, naming conflicts, personal) | C,DC | N | Planning | 2 |
| BB-017 | Identity mapping for EMU (IdP export, status MATCHED/AMBIGUOUS/UNMATCHED) | C,DC | E | Migration | 7 |
| BB-018 | Permission mapping to teams (IdP-group aware, effective access) | C,DC | N | Migration | 5, 7 |
| BB-019 | Git/LFS/submodule adapters (auth, reserved refs, LFS Basic, URL rewrite) | C,DC | E | Migration | 5, 8 |
| BB-020 | Repository settings and EMU visibility migration | C,DC | E | Migration | 5 |
| BB-021 | Branch rules to rulesets translator (Appendix C) | C,DC | N | Migration | 5 |
| BB-022 | Open PR migration with provenance, reviewers, comments, tasks | C,DC | E | Migration | 5 |
| BB-023 | Closed/merged/declined PR archival fallback | C,DC | E | Migration | 5, 11 |
| BB-024 | Webhook migration and event mapping (new secret workflow) | C,DC | E | Migration | 8 |
| BB-025 | Cloud variables/secrets migration with re-supply workflow | C | E | Migration | 8 |
| BB-026 | Pipelines conversion assistance (Cloud); CI re-pointing report (DC) | C,DC | N | Migration | 8 |
| BB-027 | Fork relationship handling | C,DC | N | Migration | 5 |
| BB-028 | Delta discovery/migration: Cloud filters, DC snapshot/sort, drift detection | C,DC | E | Delta | 6 |
| BB-029 | Planner: counts, confidence, dependency order, batching, readiness gating | C,DC | E | Planning | 4, 10 |
| BB-030 | Trial migrations into sandbox EMU org; evidence-based classification | C,DC | N | Validation | 17 |
| BB-031 | Validation extensions (PR, permissions, rules, webhooks, LFS) and expected-difference register | C,DC | E | Validation | 9 |
| BB-032 | Cutover gates, approvals, freeze handling, evidence pack | C,DC | N | Cutover | 10 |
| BB-033 | Exceptions/unsupported reporting (program and repository) | C,DC | E | Cutover | 9, 10 |
| BB-034 | Decision story: GEI-assisted mode for DC (Git+PRs via GEI, rest via GitLift) | DC | N | Migration | 12 |
| BB-035 | Compatibility matrix and deprecation monitor (DC 5.14+ to current; Cloud changelog) | C,DC | N | Discovery | 11 |


## 8. Acceptance Criteria Coverage

| AC | Where satisfied |
|----|-----------------|
| AC1 | Section A (A1-A9), section 4 (Authentication), E1, E7, E8 |
| AC2 | Section B, S1, T1-T3, section 4 (Hierarchy) |
| AC3 | Section D, section 5 |
| AC4 | Sections C, F, G; F5-F6 (impact and communication) |
| AC5 | Sections H, K, E, J |
| AC6 | Section I, BB-028 |
| AC7 | Section K, R5, S2, T3-T4 |
| AC8 | Sections L, M, N, E |
| AC9 | Section O, Q9-Q13 |
| AC10 | Section P |
| AC11 | Section 6, Q1-Q2 |
| AC12 | Section R, section 4 (Importer comparison) |
| AC13 | G9, E16, E17, E20 and "Existing" findings |
| AC14 | Section 7 (35 stories categorized E/N) |
| AC15 | All 214 questions answered; NV items in section 9 |
| AC16 | Section 4 (separate assessments) and section 7 (consolidated backlog) |
| AC17 | Rule in "How to read", J9, O10, P8, Q13, BB-030 |


## 9. Needs Validation Register

| ID | What must be validated | How |
|----|------------------------|-----|
| NV-01 | GEI source support for Bitbucket Cloud and current DC minimum version | Re-read GitHub docs at project start; test BBS2GH against a sandbox DC |
| NV-02 | EMU policy on GitHub Apps and PATs for the migration identity; classic PAT restriction | Review enterprise policies with customer admin; test token creation by a managed user |
| NV-03 | EMU limits on personal-repository ownership, mannequin reclaim, IdP-managed team membership | Sandbox EMU enterprise test |
| NV-04 | Minimum permissions per REST resource (Cloud scopes, DC permission levels) | Probe matrix with least-privilege test credentials |
| NV-05 | DC repository size available through REST (or alternative: server-side measurement) | Query test on target DC version; fall back to local clone/git-sizer |
| NV-06 | Server-side discovery option for very large DC estates (customer-run script) | Customer workshop; pilot |
| NV-07 | DC cluster size and Mesh effect on clone throughput and per-node rate buckets | Admin interview; measured trial clone |
| NV-08 | Listing all workspaces under one Atlassian organization with the credential | Test with customer organization |
| NV-09 | DC branch permissions applying to tags | Create sample restriction with tag ref pattern |
| NV-10 | DC repository archive flag per version | Test on instances with archived repository |
| NV-11 | DC repository state values (AVAILABLE, INITIALISING, INITIALISATION_FAILED) | Read repository state on test instance |
| NV-12 | LFS enabled flag and Basic-auth LFS transfer per source | Test LFS fetch on both sources |
| NV-13 | Submodule URL rewrite policy (during migration or after) | Customer decision; follow existing cutover guide |
| NV-14 | Source-specific hidden refs that must not be pushed | Compare `ls-remote` refs on test repositories |
| NV-15 | PR recreation fidelity: review states, inline comment anchors, task rendering | Trial migration with sample PRs |
| NV-16 | Fork creation inside EMU and fork policy | Sandbox test |
| NV-17 | DC PR listing options for incremental scans | Test order/filter parameters on target version |
| NV-18 | Audit log API availability (Cloud licensed, DC admin) as a change signal | Test with admin credential |
| NV-19 | EMU commit-to-user linking with mismatched emails; need for rewrite | Sandbox test with sample commits |
| NV-20 | Effective-permission computation correctness (inheritance, public access, defaults) | Compare against UI for sample users |
| NV-21 | DC marketplace apps that add wiki-like content | Installed-apps inventory |
| NV-22 | DC version detection and per-version REST differences | Application-properties call and contract tests on several versions |
| NV-23 | DC repository hooks/merge checks readable via REST; branch-permission types | Test with admin credential; compare with UI |
| NV-24 | Webhook secret retrievability on DC (assume not retrievable) | API read test |
| NV-25 | Cloud Pipelines API coverage (steps, logs, schedules, variables) and field details | Run against sample repository; compare with Atlassian reference |
| NV-26 | GEI repeat-run behavior and PR state fidelity (merged/closed) | Trial runs in sandbox |
| NV-27 | Cloud scaled-limit eligibility (plan, seats, token type) | Check workspace plan and response headers |
| NV-28 | Customer DC rate-limiting configuration and exemption process | Admin setting review |
| NV-29 | EMU org/enterprise policies and rulesets effect on migrated history | Sandbox migration |
| NV-30 | Cloud repository transfer/ownership change detection by uuid | Test transfer between two workspaces |
| NV-31 | Heterogeneous multi-instance DC estates | Inventory per instance |


## 10. Evidence Register

Verified = fetched from the source on 2026-10-29. Internal = workspace file.

| ID | Evidence | Status |
|----|----------|--------|
| E1 | Bitbucket Cloud REST intro: authentication, pagination, filtering, partial responses, scopes. https://developer.atlassian.com/cloud/bitbucket/rest/intro/ | Verified |
| E2 | Bitbucket Cloud repositories API group. https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/ | Verified |
| E3 | Bitbucket Cloud branch restrictions API group (kinds, match kinds). https://developer.atlassian.com/cloud/bitbucket/rest/api-group-branch-restrictions/ | Verified |
| E4 | Bitbucket Cloud API request limits. https://support.atlassian.com/bitbucket-cloud/docs/api-request-limits/ | Verified |
| E5 | Bitbucket Cloud API changelog (Issue Tracker API removal 2026-08-20, SSH hostname, GCM, API token Bearer). https://developer.atlassian.com/cloud/bitbucket/changelog/ | Verified |
| E6 | Atlassian community: sunset of Bitbucket Issues and Wikis (updated 2026-08-21). https://community.atlassian.com/forums/Bitbucket-articles/Announcing-sunset-of-Bitbucket-Issues-and-Wikis/bc-p/3217861 | Verified |
| E7 | Bitbucket Data Center REST reference (v1000): paging, authentication, personal repositories, resource groups. https://developer.atlassian.com/server/bitbucket/rest/v1000/intro/ | Verified |
| E8 | Bitbucket Data Center HTTP access tokens. https://confluence.atlassian.com/bitbucketserver/http-access-tokens-939515499.html | Verified |
| E9 | Bitbucket Data Center rate limiting. https://confluence.atlassian.com/bitbucketserver/improving-instance-stability-with-rate-limiting-976171954.html | Verified |
| E10 | Atlassian Ascend: Data Center end-of-life dates. https://www.atlassian.com/blog/announcements/atlassian-ascend | Verified |
| E11 | GitHub: About Enterprise Managed Users. https://docs.github.com/en/enterprise-cloud@latest/admin/concepts/identity-and-access-management/enterprise-managed-users | Verified |
| E12 | GitHub: About migrations from Bitbucket Server to GHEC (migrated data, exclusions, limits). https://docs.github.com/en/migrations/using-github-enterprise-importer/migrating-from-bitbucket-server-to-github-enterprise-cloud/about-migrations-from-bitbucket-server-to-github-enterprise-cloud | Verified |
| E13 | GitHub: Managing access for a migration from Bitbucket Server. https://docs.github.com/en/migrations/using-github-enterprise-importer/migrating-from-bitbucket-server-to-github-enterprise-cloud/managing-access-for-a-migration-from-bitbucket-server | Verified |
| E14 | GitHub: Overview of a migration from Bitbucket Server (planning, permissions, mannequins). https://docs.github.com/en/migrations/using-github-enterprise-importer/migrating-from-bitbucket-server-to-github-enterprise-cloud/overview-of-a-migration-from-bitbucket-server-to-github-enterprise-cloud | Verified |
| E15 | Bitbucket Data Center REST resource groups (same page as E7, Modules list) | Verified |
| E16 | GitLift scripts: pace-scm-migration-scripts/gitlab_to_github (Migration, validation, initial_fast_discovery, initial_detailed_discovery, delta_* stages; LFS, wiki, submodule, history rewrite, user mapping, git-sizer) | Internal |
| E17 | GitLift: gitlab_to_github_via_ghei (GEI-based path, ghei_checkpoint) | Internal |
| E18 | GitLift: platform_parity (Bitbucket listed as a capability-matrix platform only; no Bitbucket discovery or migration scripts found) | Internal |
| E19 | Bitbucket-to-GHEC_Metadata_Migration.md (feature parity inventory, not independently re-verified) | Internal |
| E20 | Gitlab_e2e_spike and the previous Bitbucket Cloud analysis (design baseline, "design assumption" items) | Internal |
| E21 | GitHub REST API rate limits. https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api | Verified |


## 11. Carry-Over from the GitLab Spike

The ticket extends the GitLab spike. Items in the GitLab spike that are not a
separate ticket question are answered here so nothing is lost.

### 11.1 Per-Resource API Call Estimates

pages(X) = ceil(count / page size). Cloud pagelen up to 100; DC limit default
25, up to the instance hard limit. "GH" = GitHub call. Validation reads only
the evidence table on the source side (0 source calls).

| Resource | Cloud discovery | DC discovery | Migration (push to GHEC) |
|----------|-----------------|--------------|--------------------------|
| Project / repository details | pages(repos) + 1 GET per repo | pages(projects) + pages(repos) + 1 GET per repo | 1 GH create repo; 1 call for topics/properties; 1 call for default branch |
| Repository status and merge settings | In repo GET; merge strategies NV | In repo GET (state, archived NV-10); merge settings via settings endpoints (NV-23) | 1 GH PATCH merge settings; no archive call for Cloud; archive call for DC archived repos (if policy) |
| Branches | pages(refs/branches) or ls-remote | pages(branches) or ls-remote | Git push |
| Tags | pages(refs/tags) or ls-remote | pages(tags) or ls-remote | Git push |
| Commits | iterator pages or local Git (preferred) | pages(commits) or local Git (preferred) | Git push; 1 local Git notes op per rewritten commit |
| Branch protection | pages(branch-restrictions) | pages(restrictions) per repo (+project level) | Fetch pages; 1 GH call per rule; reconciliation reads |
| Tag protection | none | covered by branch permissions (NV-09) | none (optional new tag ruleset) |
| Issues | none live (archive) | none (Jira) | archive: 1 GH call per issue + children |
| Pull requests | pages(PRs) per state + child pages | pages(PRs) per state + activity/participants pages | Fetch pages + Git fetch of branches; 1 GH call per open PR + children; archival record per closed/merged PR |
| Labels | none | none | 1 GH call per label created from convention |
| Milestones | none live | none | none unless archive |
| Releases | none; pages(downloads) | none | optional: 1 GH call per synthesized release + asset uploads |
| Pipelines and steps | pages(pipelines) + pages(steps) per pipeline | none (build statuses pages per commit, optional) | Audit/report only (design assumption) |
| Pipeline schedules | pages(schedules) | none | Audit/report only |
| CI/CD variables | pages(variables) per scope | none | 1 GH call per variable (repo scope); 1 env call + 1 per variable (env scope); secrets +1 key fetch per scope |
| Deployments and environments | pages(environments) + pages(deployments) | deployments via builds-and-deployments API (optional) | Audit/report only; environments only when needed for variables |
| Webhooks | pages(hooks) repo + workspace | pages(webhooks) repo + project | 1 GH list (dedup) + 1 GH create per webhook |
| Members | pages(members, groups, permissions) | pages(users, groups, permissions) (admin) | Used for identity mapping; optional team/grant calls |
| Wikis | none live (archive clone) | none | archive: 1 enable call + 1 init call + Git push |
| Files, trees, sizes | local clone + git-sizer | local clone + git-sizer | Git push |
| Git LFS | local scan | local scan | git lfs fetch/push |
| Submodules | local scan | local scan | managed through Git |
| Container registries / packages | none | none | none |
| Integrations | webhook pages + manual | hooks, links, apps (admin) | Audit/report only |

### 11.2 Project Identity and Statistics Field Map

See C-D sections. Summary: id/uuid, path_with_namespace -> full_name (Cloud) or
projectKey/slug (DC); description; topics = none; archived = none (Cloud),
version-dependent (DC); repository_status and days_of_inactivity = derived from
last commit/PR activity; stars = none; forks, branches, tags, commits, authors,
size, files = counts from API or local Git; labels = none; issues = archive only
(Cloud) or none (DC).

### 11.3 Rate Limits and Failure Handling

| Provider | Limit | Handling |
|----------|-------|----------|
| Bitbucket Cloud | 1,000/hour default per user (scaled to 10,000 under conditions); webhooks 1,000/hour; Git ops 60,000/hour | Budget governor; backoff on 429/5xx; local Git for bulk |
| Bitbucket DC | Optional bucket per user per node (default 60, refill 5/s); 429 | Client throttle; exemption request; single-threaded or low concurrency |
| GitHub | 5,000/hour PAT; 15,000 qualifying GHEC apps; secondary: 100 concurrent, 900 points/min, about 80 content creates/min, 500/hour | Honor retry-after / reset; exponential backoff; cap retries |

The GitLab spike assumed identical GitHub/GitLab limits, so one sleep policy
could serve both. This does not hold for Bitbucket: use per-provider settings.

### 11.4 Teams and Collaborators

| GitHub concept | Bitbucket Cloud | Bitbucket DC/Server |
|----------------|-----------------|---------------------|
| Organization team (@org/team) | Workspace group | Global group |
| Nested teams | None | None |
| Team access to a repository | Group permission (workspace, project or repository) | Group permission (project or repository) |
| Repository collaborator (direct) | Direct user repository permission (must be workspace member) | Direct user repository permission |
| Outside collaborator | No distinct role | No distinct role (user with repository-only access) |
| Team mention (@org/backend) | No verified group mention (validate in the tenant) | No verified group mention (validate per version) |
| Organization owner / member | Workspace admin / member | Global (system) admin / licensed user (not mapped automatically) |
| Repository roles | admin, write, read | REPO_ADMIN, REPO_WRITE, REPO_READ (project equivalents) |

### 11.5 Cross-Repository Dependencies

* Pipeline A triggers pipeline B: Cloud via the Pipelines API/pipe with a
  stored token; DC via the external CI tool. On GitHub use workflow_dispatch /
  repository_dispatch with a GitHub App installation token that has access to
  the target repository. The default GITHUB_TOKEN is repository-scoped.
* Submodules: relative URLs are plain Git behavior; access to other private
  repositories must be granted explicitly on GitHub.
* Issues linked across projects and epics: Cloud issue tracker was
  repository-scoped and is removed; DC has no tracker. Cross-project planning
  is in Jira (outside this migration).

### 11.6 Canonical Format and API Versions (TBD)

* Canonical format for discovery to validation: TBD (undecided in the GitLab
  spike). Proposal for review: provider-neutral envelope
  {run_id, source_provider, source_instance, source_container, object_type,
  object_id, source_updated_at, source_hash, target_id, status, reason_code}
  with provider-specific payload namespaced.
* API instance versions vs API labels: TBD (query unclear). Facts: Cloud has one
  public path version (/2.0); DC REST is versioned per resource family
  (/rest/api/1.0, /rest/branch-permissions/2.0 and others) and varies by
  product version; GitHub uses the X-GitHub-Api-Version header. Bitbucket has no
  labels. Confirm intent with the requester.

### 11.7 Token Pooling

Provider-agnostic by design, so usable for Bitbucket (A8). Gaps: GitHub-only
health daemon; per-user budgets mean tokens of one user share a limit; DC
buckets are per node; only pool distinct identities permitted by the customer.

### 11.8 Metadata Considered for Cutover

Repository visibility; snippets (Cloud); repository-level settings adjacent to
branch protection (default branch, fork policy, merge strategies, default
reviewers, branching model); branch protection rules; badges (README links,
recreate where an equivalent exists); member roles and permissions; teams.
See P1-P11 for gates.

### 11.9 CI/CD Parameters and Webhooks

Variables (Cloud only): discovery by REST, metadata only, never the value;
migration by fetch then GitHub PUT/POST with PATCH fallback, secured values
re-supplied; validation compares evidence to target (names, scope), never
values. Webhooks (both): discovery by REST without secrets; migration by dedup
check then create (PATCH on conflict) with a new secret because the source
secret is not retrievable; validation compares evidence to target and tests
delivery. See N4-N10.

### 11.10 Delta Storage

Core delta: persist the bare clone (EFS) and fetch into it. SCM delta: evidence
table plus snapshot files on the same storage. Delta discovery reuses the
migration checkpoints. See I1-I12.

### 11.11 Coverage Map

| GitLab spike topic | Section |
|--------------------|---------|
| Authentication types | A1-A9 |
| Hierarchy | B1-B10 |
| Get all repo list | B6, C1 |
| Dependencies / submodules / packages | E1-E8, 11.5 |
| Layered discovery (fast, detailed) | C, F |
| Metadata grouping | D, 11.2, section 5 |
| API calls (discovery, migration, validation) | G, 11.1 |
| Delta migration / discovery | I, 11.10 |
| Planner payload | J1-J2, F3-F4 |
| Metadata for cutover | P, 11.8 |
| User details history rewrite | K |
| Validation with evidence | O |
| CI/CD parameters, webhooks | N, 11.9 |
| Constraints | Q, section 6 |
| GEI comparison | R |
| Scenarios (fast vs detailed, change detection, fast+detailed delta) | F5-F8, I6 |
| API/token constraints, failures, sleep/retry | Q8, 11.3 |
| Wiki equivalent, challenges, CLI approach | L |
| Git sizer | M7 |
| LFS | M |
| Issues in SCM | Q5, 11.1 (issues), U |
| Canonical format | 11.6 (TBD) |
| APIs for sub-items / dependent bundles | G2, 11.1, Appendices A-B |
| Token pooling | A8, 11.7 |
| API instance versions vs labels | 11.6 (TBD) |
| Cross-repo dependencies | E, 11.5 |
| Teams / collaborators and roles | K, 11.4 |

## Appendix A. Bitbucket Cloud Endpoint Inventory (REST v2.0)

Base: https://api.bitbucket.org/2.0 . Verified groups: repositories,
branch restrictions, commit statuses, webhooks (E1-E3). Other paths are the
documented resource groups listed in the REST reference menu (Pipelines,
Pullrequests, Refs, Projects, Workspaces, Users, Snippets, Downloads,
Deployments, Source) and must be probed per NV-25.

| Data | Path pattern |
|------|--------------|
| Workspaces | /workspaces ; /workspaces/{ws}/projects |
| Repositories | /repositories/{ws} ; /repositories/{ws}/{repo} |
| Forks, watchers | /repositories/{ws}/{repo}/forks ; /watchers |
| Branches, tags | /repositories/{ws}/{repo}/refs/branches ; /refs/tags |
| Commits | /repositories/{ws}/{repo}/commits (iterator paging) |
| Branch restrictions | /repositories/{ws}/{repo}/branch-restrictions |
| Pull requests | /repositories/{ws}/{repo}/pullrequests ; child: commits, comments, activity, tasks |
| Permissions | /repositories/{ws}/{repo}/permissions-config/users|groups |
| Webhooks | /repositories/{ws}/{repo}/hooks ; /workspaces/{ws}/hooks |
| Commit statuses | /repositories/{ws}/{repo}/commit/{sha}/statuses |
| Pipelines | /repositories/{ws}/{repo}/pipelines ; steps ; schedules ; variables |
| Environments, deployments | /repositories/{ws}/{repo}/environments ; /deployments |
| Downloads, snippets | /repositories/{ws}/{repo}/downloads ; /snippets/{ws} |
| Issues, wiki | removed 2026-08-20 |


## Appendix B. Bitbucket Data Center Endpoint Inventory (REST 1.0 Families)

Base: https://<host>[/context]/rest/... . Paging: start, limit, isLastPage,
nextPageStart (verified, E7). Path families below are documented resource
groups (E15) or well-known DC paths; exact availability per version is NV-22.

| Data | Path pattern |
|------|--------------|
| Version | /rest/api/1.0/application-properties |
| Projects, repositories | /rest/api/1.0/projects ; /projects/{key}/repos ; /repos |
| Personal | /projects/~{slug}/repos ; /users/~{slug}/repos (verified, E7) |
| Branches, tags, commits | /projects/{key}/repos/{slug}/branches | tags | commits |
| Pull requests | /projects/{key}/repos/{slug}/pull-requests?state=ALL&order=NEWEST ; activities ; participants ; tasks/comments |
| Permissions | /projects/{key}/permissions/users|groups ; /repos/{slug}/permissions/users|groups |
| Users, groups (admin) | /rest/api/1.0/admin/users ; /admin/groups ; /users ; /groups |
| Branch permissions | /rest/branch-permissions/2.0/projects/{key}/repos/{slug}/restrictions |
| Webhooks | /rest/webhooks/1.0/projects/{key}/repos/{slug}/webhooks |
| Build status | /rest/build-status/1.0/commits/{sha} |
| Default reviewers | /rest/default-reviewers/1.0/projects/{key}/repos/{slug}/conditions |
| Audit | /rest/auditing/1.0/events |


## Appendix C. Branch Rule Translation to GHEC Rulesets

| Source rule | GHEC equivalent | Fidelity |
|-------------|-----------------|----------|
| Cloud push (restrict write by users/groups) | Ruleset: restrict updates + bypass actors | Partial |
| Cloud force | Block force pushes | Direct |
| Cloud delete | Restrict deletions | Direct |
| Cloud restrict_merges | Required reviews + bypass actors (no actor allowlist for merge) | Partial |
| Cloud require_approvals_to_merge (value N) | Required approving reviews (N) | Direct |
| Cloud require_default_reviewer_approvals_to_merge | CODEOWNERS + require code owner review | Partial |
| Cloud require_no_changes_requested | Inherent: changes-requested review blocks | Direct |
| Cloud require_passing_builds_to_merge | Required status checks (names change after CI conversion) | Partial |
| Cloud require_commits_behind (0) | Require branches up to date | Direct for 0 |
| Cloud require_commits_behind (N>0) | Strict up-to-date only | Partial |
| Cloud require_tasks_to_be_completed | Require conversation resolution | Partial |
| Cloud reset_pullrequest_approvals_on_change | Dismiss stale approvals | Direct |
| Cloud smart_reset_pullrequest_approvals | Dismiss stale approvals (less precise) | Partial |
| Cloud reset_pullrequest_changes_requested_on_change | None | Unsupported |
| Cloud require_all_dependencies_merged | None (use a required status check from Actions) | Unsupported |
| Cloud allow_auto_merge_when_builds_pass | Repository auto-merge setting | Direct |
| Cloud branching model (prefixes) | Ruleset branch-name patterns | Partial |
| DC read-only | Restrict updates (no bypass) | Direct |
| DC no-deletes | Restrict deletions | Direct |
| DC fast-forward-only | Block force pushes | Direct |
| DC pull-request-only | Restrict updates + required pull request | Direct |
| DC merge checks (minimum approvals, required builds) | Required reviews / required status checks | Partial |
| DC app-defined repository hooks | Customer decision | Unsupported |

(DC permission type names and merge-check mapping: NV-23.)

End of document.
