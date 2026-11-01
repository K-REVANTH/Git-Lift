# Bitbucket Cloud to GitHub Enterprise Cloud (GHEC)
## End-to-End Migration Spike

| Document control | Details |
|---|---|
| Analysis date | 2026-10-29 |
| Source | Bitbucket Cloud (REST API v2.0 and Git) |
| Target | GitHub Enterprise Cloud (GHEC) |
| Reference | `Gitlab_e2e_spike`; coverage is mapped in section 27 |

## Scope and Ground Rules

* Bitbucket Server / Data Center is out of scope.
* "Migrated" means the object or setting is recreated on GHEC and a
  source-to-target mapping is kept. It does not mean original authors,
  timestamps, IDs, or event history are preserved.
* API-call counts depend on real inventory sizes. Counts below are formulas
  and endpoint patterns, not fixed numbers.
* Items marked "design assumption" mirror how the GitLab spike scoped GitLift
  (for example "audit/report only") and must be confirmed by the team.
* Items marked "TBD" were undecided or unclear in the GitLab spike and stay
  undecided here.

## Executive Findings

1. Bitbucket Cloud Issues and Wikis were removed (UI and API) on 2026-08-20
   (Atlassian community announcement and Bitbucket API changelog). Their
   content can only be migrated from a pre-removal export (issues JSON) or a
   retained wiki Git clone. Nothing about them can be discovered live.
2. Bitbucket Cloud has no public GraphQL API. Discovery is REST v2.0 plus
   local Git analysis.
3. Bitbucket Cloud has no native stars, topics, repository archive state,
   labels, releases, tag protection, package registry, or container registry.
   Each is marked "not available at source" below instead of being invented.
4. Bitbucket's default authenticated rate limit (1,000 requests/hour, measured
   per user ID) is far lower than GitHub's (5,000/hour). Source-side
   throughput, not GitHub, is the bottleneck. The GitLab statement that both
   providers have the same limits does not carry over.
5. GitHub Enterprise Importer (GEI) documents a Bitbucket route for Bitbucket
   Server / Data Center only. No Bitbucket Cloud route is documented.
6. Original authors/timestamps of platform objects (PRs, comments, reviews)
   cannot be set through the normal GHEC API. Only commit authors survive,
   because they live inside Git objects.
7. Bitbucket is changing SSH access: SSH via bitbucket.org is deprecated in
   favor of ssh.bitbucket.org (brownouts announced 2026-10-28). Prefer HTTPS
   with a scoped token, or use the new SSH hostname.


## 1. Source Authentication

GitLab spike: PATs, scoped tokens, OAuth apps; others not used by GitLift.

Bitbucket Cloud equivalents (verified against Atlassian REST docs):

| GitLab mechanism            | Bitbucket Cloud mechanism             | Notes |
|-----------------------------|---------------------------------------|-------|
| Personal Access Token (PAT) | API token (personal)                  | Scoped, mandatory expiry (max 1 year). Auth is Basic (Atlassian email + token) or Bearer (Bearer added 2026-08-18). Acts as the owning user. Used for developer CLI, local tooling, user-scoped scripts. |
| Project / Group Access Token| Repository / Project / Workspace access token | Tied to a resource, not a user. Appears in the UI/logs as a "user". Cannot query or manipulate permissions. Cannot call deploy-key APIs. Cannot be viewed after creation. |
| OAuth 2.0 application       | OAuth 2.0 consumer                    | Authorization-code, client-credentials, and JWT grants. Access tokens expire after 1 hour; refresh tokens rotate (a used refresh token is replaced). OAuth requests must go to api.bitbucket.org. Alternative to a GitHub App on the GitHub side. |

Mechanisms that exist but are not relevant to GitLift scope (design assumption):

* App passwords: deprecated by Atlassian in favor of API tokens. Do not build
  on them; inventory and replace any that exist.
* SSH keys and repository access (deploy) keys: Git transport only.
* Pipelines OIDC tokens, Connect JWT, Forge app credentials: not used by a
  migration tool.

Minimum Bitbucket scopes for discovery (Forge/API-token style names):

* read:repository:bitbucket, read:pullrequest:bitbucket,
  read:project:bitbucket, read:workspace:bitbucket, read:user:bitbucket
* read:pipeline:bitbucket (pipelines, steps, variables, environments)
* read:webhook:bitbucket
* admin:repository:bitbucket - required to list branch restrictions (documented)
* read:permission:bitbucket plus a user-level credential with repository admin
  rights - repository user/group permission endpoints are admin-only, and
  access tokens cannot query permissions.

GitHub (target) side: GitLift uses a PAT/GitHub App on GHEC. The identity that
writes PRs/issues becomes their author (see section 11).

Git transport: use HTTPS with a token. For SSH use ssh.bitbucket.org. If Git
Credential Manager is used with OAuth, it must be version 3.0.0+ before
2026-11-30 or OAuth Git requests are blocked.


## 2. Hierarchy

GitLab spike: Enterprise account - org - repo; GitLab is User namespace -
Group - Subgroup - Project.

| GHEC                  | Bitbucket Cloud                                  |
|-----------------------|--------------------------------------------------|
| Enterprise account    | Atlassian organization (billing/identity only)   |
| Organization          | Workspace                                        |
| (no equivalent)       | Project (groups repos, carries default access)   |
| Repository            | Repository                                       |
| Team                  | Workspace group                                  |

* Bitbucket hierarchy is Workspace -> Project -> Repository. There are no
  subgroups; nesting depth is fixed.
* Every repository belongs to exactly one project.
* GHEC has no repository container below an organization. Represent a
  Bitbucket project with a Team (access) plus a custom repository property or
  topic (grouping). GitHub Projects (V2) is a planning board, not a container.
* Persist workspace UUID/slug and project key/UUID in the mapping table.


## 3. Repository Inventory and Access

Endpoint (paginated):

    GET https://api.bitbucket.org/2.0/repositories/{workspace}

* Follow the `next` URL in each response; treat it as opaque. Request
  `pagelen=100` (minimum 10, maximum 100; some endpoints differ).
* Optional `role=` (owner/admin/contributor/member), `q=` filter, `sort=`.
* Per-repository detail: GET /2.0/repositories/{workspace}/{repo_slug}.
* Workspaces visible to the credential: GET /2.0/workspaces (or the
  user-scoped workspace listing). GitLab's `membership=true` has no equivalent;
  results are limited to what the credential can see.
* Projects: GET /2.0/workspaces/{workspace}/projects.
* The response may carry legacy `has_issues` / `has_wiki` flags. They are
  flags only; they do not mean the content still exists.


## 4. Dependencies and Submodules

### Submodules

* Submodules are a core Git feature on Bitbucket as on GitLab/GitHub:
  `.gitmodules` (path, URL) plus a gitlink commit SHA in the tree.
* Mirror the superproject and every submodule repository; verify each pinned
  SHA exists on the target.
* Rewrite `.gitmodules` URLs that point at Bitbucket to GHEC URLs.
* Relative URLs are plain Git behavior and work on any host if the repository
  layout is preserved. The authentication difference is separate: Bitbucket
  Pipelines clones with the repository's configured key, whereas a GitHub
  Actions `GITHUB_TOKEN` is scoped to one repository and cannot read other
  private repositories. Use a GitHub App installation token (or deploy key)
  for cross-repository checkout.

### Dependencies and Package Registries

* Bitbucket Cloud has no native package registry or container registry, so
  there is no project/group-scope registry to enumerate (GitLab has both).
* Discover dependencies from `bitbucket-pipelines.yml`, manifests, and
  variables (npm, Maven, PyPI, Docker Hub, ECR, etc.). Keep external
  registries; move credentials to GHEC secrets and rewrite publish steps.
* Bitbucket "Downloads" are plain files, not a registry. Move to GHEC release
  assets or an artifact store and update consumer URLs.


## 5. Fast and Detailed Discovery Paths

### Fast Discovery

* Possible, but not through GraphQL. Fast discovery = paginated repository
  list + repository GET + local Git signals (`git ls-remote`, `git rev-list
  --count`, `git count-objects`, git-sizer) + a few cheap counts.
* It covers only part of the metadata, so the planner must show that its
  estimate is limited (same conclusion as the GitLab spike, different reason).

### Detailed Discovery

* Possible. Bitbucket has REST v2.0 endpoints for each metadata type listed in
  section 6, with page-based or iterator-based pagination. Some data needs
  child calls (PR comments, pipeline steps, permissions per repository).
* Use `fields=` (partial response) to cut payload size, and `q=`/`sort=`
  filtering where the endpoint documents it.


## 6. Metadata Inventory and Grouping

Legend: AVAIL = discoverable now; N/A = not available at source;
ARCHIVE = only from a pre-2026-08-20 export/clone; DERIVED = computed locally.

### 6.1 Project and Repository Identity

| GitLab field            | Bitbucket Cloud                                          |
|-------------------------|----------------------------------------------------------|
| id                      | uuid (AVAIL)                                             |
| path_with_namespace     | full_name = workspace/repo_slug (AVAIL)                  |
| description             | description (AVAIL)                                      |
| topics                  | N/A (no topics); project key/name used instead           |
| archived status         | N/A (no archive state)                                   |
| repository_status       | DERIVED (active/inactive from last commit/PR activity)   |
| last_activity_date      | updated_on (AVAIL, candidate signal) + last commit date (DERIVED) |
| days_of_inactivity      | DERIVED                                                  |

Also collect: name, slug, is_private, project, mainbranch, language, size,
fork_policy, created_on, website, parent (fork source), clone links.

### 6.2 Engagement and High-Level Statistics

| GitLab field         | Bitbucket Cloud                                       |
|----------------------|-------------------------------------------------------|
| total_star           | N/A (no stars)                                        |
| total_forks          | forks endpoint count (AVAIL)                          |
| total_commits        | DERIVED from local Git (REST commits is iterator-paginated) |
| total_branches       | refs/branches count (AVAIL) or Git                    |
| total_tags           | refs/tags count (AVAIL) or Git                        |
| total_issues         | ARCHIVE only                                          |
| total_merge_requests | pullrequests count per state (AVAIL)                  |
| total_labels         | N/A (Bitbucket has no labels)                         |
| total_files          | DERIVED from local Git                                |
| total_authors        | DERIVED from local Git (`git shortlog`)               |
| repository_size      | size (AVAIL, bytes) and git-sizer (DERIVED)           |

Also: watchers count (AVAIL).

### 6.3 Repositories, Branches, and Commits

* default branch: mainbranch (AVAIL).
* Branch objects and branch-to-commit mapping: refs/branches.
* Tag objects and tag-to-commit mapping (annotated vs lightweight): refs/tags
  plus Git for annotation detail.
* Commits: SHA, short SHA, message/title, author and committer (name, email,
  date), parent SHAs; per-author commit counts and lists. Use local Git; the
  REST commits endpoint uses iterator pagination (only `next` and `pagelen`).
* Submodule configuration: path, URL, pinned commit SHA, mode/type - from
  `.gitmodules` and the Git tree locally.

### 6.4 Repository Rules and Governance

* Branch restrictions (REST: `/repositories/{ws}/{repo}/branch-restrictions`):
  `kind`, `branch_match_kind` (glob or branching_model), `pattern` or
  `branch_type`, `users`, `groups`, `value`. Documented kinds: push, force,
  delete, restrict_merges, require_tasks_to_be_completed,
  require_approvals_to_merge, require_default_reviewer_approvals_to_merge,
  require_no_changes_requested, require_passing_builds_to_merge,
  require_commits_behind, reset_pullrequest_approvals_on_change,
  smart_reset_pullrequest_approvals,
  reset_pullrequest_changes_requested_on_change,
  require_all_dependencies_merged, enforce_merge_checks,
  allow_auto_merge_when_builds_pass.
* Branching model and effective branching model; default reviewers;
  project-level inheritance/override state.
* Protected tags: N/A. Bitbucket branch restrictions match branches (glob or
  branching model), and no tag-protection resource is documented. GHEC tag
  rulesets would be a new capability, not a migration.
* Merge methods (merge commit, squash, fast-forward and variants): repository
  setting; confirm REST availability in the tenant, otherwise capture
  manually (design assumption).

### 6.5 Files, Large Files, and LFS

* File tree entries, sizes and counts by extension, large-file flags: local Git.
* LFS pointers (path, oid, oid type, pointer size, size on disk, verification
  status): local `git lfs` commands and pointer-file parsing.

### 6.6 Pull Requests, Issues, and Collaboration

* Pull requests: id, title, description, source/destination repository and
  branch, state (OPEN, MERGED, DECLINED, SUPERSEDED), author, reviewers,
  participants, approvals, tasks, comments/activity, created/updated, close
  source branch flag, merge strategy. (GitLab MR "iid", assignee, labels and
  milestone: Bitbucket PRs have no labels or milestones.)
* Issues: ARCHIVE only (id, title, content, state, kind, priority, assignee,
  reporter, component, milestone, version, votes, watchers, comments).
* Labels: N/A. Milestones, components, versions: ARCHIVE only (issue-tracker
  concepts).

### 6.7 Releases and Documentation

* Releases: N/A (Bitbucket has tags and Downloads only).
* Downloads: file name, size, creation/download metadata (AVAIL).
* Wiki: ARCHIVE only (retained Git clone: pages, history, attachments).
* Snippets: id, title, owner, visibility, files, comments, forks (AVAIL via
  snippets API; confirm availability in the tenant).

### 6.8 CI/CD, Pipelines, and Jobs

* Pipelines: uuid/build number, state/result, trigger, target ref, commit SHA,
  creator, created/completed on, duration, build_seconds_used.
* Steps (GitLab "jobs"): step uuid, parent pipeline, name, stage/deployment
  environment, state/result, started/completed, duration, image, runner,
  artifacts, logs (optional archive).
* Schedules: uuid, target ref/pattern, cron expression, enabled, created.
* Variables (workspace, repository, deployment scopes): key, secured flag,
  scope. Values: never persisted; secured values are unreadable anyway.
* Configuration: `bitbucket-pipelines.yml` read from Git.

### 6.9 Environments and Deployments

* Environments: uuid, name, environment type/category, rank, restrictions,
  lock/deployment status.
* Deployments: uuid, state, release (commit, ref), environment, deployer,
  pipeline, started/completed.

### 6.10 Registries

* N/A. Bitbucket Cloud has no native package or container registry (GitLab's
  package_id/registry/tags/cleanup-policy fields have no source).

### 6.11 Members and Access

* Workspace members, groups and group membership; project permissions;
  repository direct user and group permissions (admin, write, read, none);
  user uuid, account_id, display name, nickname, account status. Email is
  often unavailable because of privacy settings.

### 6.12 Webhooks and External Integrations

* Repository and workspace webhooks: uuid, description, url, active, events,
  created_at, secret_set (boolean only). GitLab-style SSL-verification flag is
  not exposed.
* Integrations (Jira DVCS link, Slack, Teams, OAuth consumers, installed
  apps): no single endpoint; collect what each API exposes and the rest
  manually (design assumption: audit/report only).


## 7. API Call Estimates

### Pagination Model

* pages(X) = ceil(count of X / 100) when `pagelen=100` is honored. Some
  endpoints (for example commits) are iterator-paginated: no total, follow
  `next` until absent.
* "GH" = GitHub REST call. Git operations (clone, fetch, push, LFS) are not
  REST calls.

### Per-Resource Call Estimates

| Resource | Discovery (Bitbucket) | Migration | Notes |
|----------|-----------------------|-----------|-------|
| Project (repository) details | pages(repositories) + 1 GET per repository | Fetch: reuse discovery data. Push: 1 GH call to create the repository (description, visibility, homepage), 1 call to set topics/custom properties, 1 call to set default branch (if not set by the first push) | Replaces GitLab's single project call |
| Repository status and merge settings | Included in the repository GET; merge strategies only if a REST source is confirmed | 1 GH PATCH for merge settings (allow_merge_commit, allow_squash_merge, allow_rebase_merge) | Bitbucket has no archive state, so there is no "set archived" call |
| Branches | pages(refs/branches) per repository, or `git ls-remote` | Git push | |
| Tags | pages(refs/tags) per repository, or `git ls-remote` | Git push | |
| Commits | pages(commits) iterator-paginated, or 0 REST calls with local `git rev-list`/`git log` (preferred) | Git push; 1 local Git notes call per rewritten commit when rewriting LFS pointers (provider-independent) | |
| Branch protection (restrictions) | pages(branch-restrictions) per repository | Fetch: pages as discovery. Push: 1 GH call per rule (ruleset or branch protection) + reconciliation reads | Needs admin:repository scope |
| Tag protection | None (not available at source) | None (optional new tag rulesets on GHEC) | |
| Issues | 0 live calls (removed 2026-08-20) | If an export exists: 1 GH call per issue + child calls (comments, labels, assignees) | ARCHIVE only |
| Pull requests | pages(pullrequests) per state + child pages (commits, comments, activity, tasks, approvals) | Fetch: same pages + Git fetch of source branches. Push: 1 GH call per PR (open PRs) + child calls | See section 14 for closed/merged policy |
| Labels | None (not available at source) | 1 GH call per label created from the mapping convention (kind, priority, component) | |
| Milestones | 0 live calls (issue tracker, removed) | If export exists: 1 GH call per milestone + reconciliation for state | ARCHIVE only |
| Releases | None (no releases); pages(downloads) per repository | Optional: 1 GH call per release synthesized from tags + 1 upload per asset | Policy-driven |
| Pipelines and steps | pages(pipelines) per repository, then pages(steps) per pipeline | Audit/report only (design assumption); not pushed to GitHub | Logs optional archive: +1 call per step |
| Pipeline schedules | pages(schedules) per repository | Audit/report only (design assumption) | Conversion to `on: schedule` is a separate workflow-conversion workstream |
| CI/CD variables | pages(variables) per scope (workspace, repository, each deployment environment) | Fetch: same pages (non-secured values are readable; secured are not). Push: repository scope = 1 GH call per variable (secrets +1 call per scope for the public key); environment scope = 1 call to create the environment + 1 per variable | Secured values must be re-supplied |
| Deployments and environments | pages(environments) + pages(deployments) per environment | Audit/report only (design assumption); environments are created on GHEC only if environment-scoped variables are migrated | |
| Webhooks | pages(hooks) at repository scope and at workspace scope | Fetch: same pages. Push: 1 GH list call (dedup check) + 1 GH POST per webhook | Secret cannot be read |
| Project (workspace) members | pages(workspace members), pages(groups), per-repository pages(permissions-config/users and /groups) | Used for identity-mapping resolution (PR/issue reviewers and assignees); optional team/permission creation = 1 GH call per team, member and grant | Admin credential required |
| Wikis | 0 live calls (removed) | If a clone exists: 1 GH call to enable the wiki, 1 to initialize the first page, then Git push | ARCHIVE only |
| Files, file trees and sizes | 0 REST calls: local clone + git-sizer (REST `src` listing is per directory and not recommended) | Git clone and push | Replaces GitLab's GraphQL blob-size call |
| Git LFS | 0 REST calls: read `.gitattributes`, parse pointers locally | `git lfs fetch --all` then `git lfs push --all` | |
| Submodules | 0 REST calls: read `.gitmodules` and tree locally (or 1 GET of the file) | Managed inside `.gitmodules` through Git | |
| Container registries | None (not available at source) | None | |
| Packages | None (not available at source) | None; artifacts re-published through CI | Audit/report only |
| Integrations | No single call: webhook pages + manual inventory | Audit/report only; configured manually or at organization level | |

### Validation

* GitLab spike: "Validation is ignored as validation doesn't need to make any
  API calls."
* Bitbucket: same position for the source. Validation reads the stored
  evidence/checkpoints (section 12) and makes 0 Bitbucket calls.
* It still has to read the target. Plan GH reads (1 or more per migrated
  object, plus Git `ls-remote`) when sizing GitHub rate budget, even though
  they are excluded from source-side discovery/migration counts.

### Throughput Planning

* Source budget: hours >= total_bitbucket_calls / hourly_limit (see section 17).
  At the default 1,000/hour, 10,000 calls take at least 10 hours for one
  identity.
* Prefer local Git over REST wherever the table says so; it moves load from
  the rate-limited REST API to Git operations (60,000/hour limit).


## 8. Delta Discovery and Migration

### Core Delta Migration

* Keep the bare/mirror clone from the initial migration instead of cleaning it
  up (store on durable storage such as EFS, as in the GitLab design).
* At delta time: fetch from Bitbucket into the clone, compute changed refs and
  objects, push only the delta to GHEC.
* A source ref deleted since the last run must be handled explicitly; do not
  use a blind `--mirror` push if the target should keep extra refs. GitHub
  also rejects updates to reserved refs such as refs/pull/*; push branches and
  tags explicitly.

### SCM Metadata Delta

* PRs, permissions, rules, webhooks, variables and similar data are not in the
  Git clone. Use the evidence table: store each migrated object's source ID,
  observed source timestamp/version, normalized hash, target ID and status.
  The same snapshot can also be stored on EFS next to the bare clone.
* Bitbucket supports `q=updated_on > <date>` and `sort=-updated_on` on
  repositories, pullrequests, refs and (formerly) issues. Use them to fetch
  only changed objects, then reconcile against the evidence table.
* Not every endpoint has a change filter, and deletions are invisible to
  `updated_on`. Run periodic full-inventory comparisons.
* Issues and Wikis: no live source; delta is possible only between successive
  retained archives.

### Delta discovery

* Uses the same checkpoints set for delta migration and shows the difference
  (added, changed, deleted) per resource.


## 9. Planner Payloads

* The planner payload is the count data from the discovery stage (counts and
  sizes only: repositories, size, refs, LFS volume, PRs, comments, permissions,
  rules, variable keys, webhooks, pipelines, downloads; plus measurement time,
  discovery level and per-surface completeness). No secrets or values.

### Initial fast discovery

* Discovers only some counts (repository list and details, Git-derived signals,
  selected cheap counts) because Bitbucket has no GraphQL and no single call for
  all counts. The planner still uses this limited data and the UI states that
  the estimated time has limited accuracy.

### Initial detailed discovery

* Discovers all counts of all in-scope metadata (section 6), giving a better
  estimate. The payload is still counts of metadata.

### Delta discovery

* Same payload, but only the delta counts, so the planner shows the estimate
  for the delta migration only.


## 10. Cutover Metadata

* Repository visibility (public/private; GHEC "internal" is optional).
* Project snippets (and snippet ownership decision: Gist vs repository).
* Repository-level settings adjacent to branch protection (default branch,
  fork policy, merge strategies, default reviewers, branching model).
* Branch protection rules (branch restrictions -> rulesets/branch protection).
* Badges (README/repository links; recreate only where a target equivalent
  exists; not a Bitbucket metadata object).
* Member roles and permissions (workspace, project, repository).
* Teams (workspace groups -> GHEC teams and team repository grants).
* Webhooks, deployment/CI variables, environments, OIDC trust, Jira/Slack links.
* Downloads and externally consumed URLs.
* Final export of data that cannot be imported (pipeline runs, deployments,
  audit log), then source freeze and final delta.


## 11. User Identity and History Rewrites

* Creating users and assigning high-level permissions needs an admin
  credential on the target (organization owner; with EMU/SCIM, users are
  provisioned by the identity provider) and a source credential that can read
  workspace members and repository permissions.
* Author, reviewer, etc. - what can be migrated:

| Item                 | Migratable? | How |
|----------------------|-------------|-----|
| Commit author        | Yes         | Preserved in Git objects by the core migration. GitHub links it to an account only if the commit email matches that account. |
| Reviewers, assignees | Yes (current assignment) | Set through an API call while creating the PR/issue, after identity mapping (Bitbucket account_id -> GitHub login). |
| Authors of platform metadata (PR, comment, issue, review) | No | Limited by the token used for the migration: the token owner becomes the author. Keep the original author and time in the body or evidence. |

* Do not use per-user PAT impersonation as a default; it is not scalable and
  carries token-custody risk.


## 12. Validation and Migration Evidence

* During migration, store checkpoints that validation can access. The stored
  checkpoints also act as the migration evidence.
* Evidence fields: run id, source workspace/repository UUID, object type and
  ID, source snapshot hash, target ID/URL, action and result, retry count,
  expected-difference reason. Redact secrets.
* After migration, validation compares the evidence with the target data and
  computes differences, then accounts for each difference with a reason if it
  is expected (for example author replaced by the migration identity, label
  mapped from kind/priority, SUPERSEDED mapped to closed).
* Report matched / transformed / missing / unexpected / not-verifiable
  separately. Validate access with effective-permission tests, not only
  configuration equality.


## 13. CI/CD Parameters and Webhooks

### CI/CD Parameters (Bitbucket Pipelines Variables)

Discovery
* REST API (pipelines variables at workspace, repository, deployment scopes).
* Actual values must not be persisted in the discovery report for security
  reasons; only the related metadata (key, scope, secured flag).

Migration
* Fetch through the same REST API. Non-secured values are readable; secured
  values are not and must be re-supplied (vault or manual).
* Push: GitHub PUT/POST per variable or secret (create), with PATCH fallback
  when it already exists. Use the verb each GitHub endpoint documents;
  secrets are PUT with an encrypted value.

Validation
* Same as other metadata: compare the evidence table with the target
  (names, scope, visibility). Never read or compare values.

### Webhooks

Discovery
* REST API (`/hooks` at repository and workspace scope). Do not persist secrets
  or secret-bearing URLs; the API exposes only `secret_set`.

Migration
* Same REST fetch, then GitHub POST per webhook with PATCH fallback for
  updates (after a dedup check).
* The Bitbucket signing secret cannot be retrieved, so the webhook secret is
  never migrated; the target webhook is created with a newly generated secret.
  Receivers must also adapt to GitHub payloads and the X-Hub-Signature-256
  header (Bitbucket uses X-Hub-Signature).

Validation
* Same as other metadata: evidence table versus target. Secret equality cannot
  be verified.


## 14. Migration Constraints

* Any author other than the commit author (limited by the token used).
* Closed and merged pull requests cannot be migrated as pull requests
  (carried over from the GitLab spike). Fallback (as in GitLab): create an
  issue/archival record per closed or merged PR with a link and the key
  fields. Bitbucket states: OPEN (migrated), MERGED and DECLINED
  (fallback), SUPERSEDED (fallback).
* Fields that require an admin token cannot be migrated unless the admin
  credential is supplied (for example branch restrictions, permissions).
* Secret values (secured variables, tokens, webhook secrets, OAuth secrets).
* Native historical runtime data: pipeline runs, logs, deployments, webhook
  delivery history, audit log.
* Original IDs, UUIDs and timestamps of platform objects.
* Votes, watchers and other per-user state.
* Issues and Wikis unless a pre-2026-08-20 export or clone exists.
* Items without a GitHub equivalent: Bitbucket Pipes (must be replaced by
  Actions), branching-model semantics, SUPERSEDED state, "smart reset of
  approvals" (GitHub dismisses stale approvals on any push).
* GitHub limits that affect Git push: 100 MiB per file (use LFS), 255-byte ref
  names, 2 GiB per commit.


## 15. GitHub Enterprise Importer Comparison

* GEI's documented Bitbucket route is Bitbucket Server / Data Center 5.14+.
  Bitbucket Cloud is not a documented GEI source, so for this project GitLift
  (custom migration) is the only route; do not assume GEI behavior applies.
* For reference, GEI (Server/DC) migrates Git source with history and pull
  requests including comments, reviews, file/line review comments, required
  reviewers and attachments, and attributes content to mannequins that can be
  reclaimed. It does not migrate branch permissions, commit comments,
  repository settings, CI pipelines, or LFS objects.
* Parameters that show where GEI exceeds GitLift (if a Server/DC source ever
  appears): correct SCM authors via mannequin reclaim (GitLift cannot), and
  migration of pull requests beyond GitLift's open-PR scope (confirm
  closed/merged states in a trial migration).
* Parameters where GitLift exceeds GEI: branch rules and repository settings
  (GEI documents branch permissions and repository settings as not migrated).
  Webhooks and CI variables are not listed as migrated by GEI either.


## 16. Scenarios

### Fast and Detailed Discovery: Planner Impact

* Bitbucket also cannot return all the data in fast discovery, so it impacts
  the planner: fast counts are partial and the UI labels the estimate as
  limited. Detailed discovery gives complete counts and a better estimate.

### Identifying Repository Changes for Delta Discovery

* Use fast comparison data (repository list/detail fields, ref SHAs from
  `git ls-remote`). This is limited by how many metadata fields fast discovery
  captures.
* Use the repository `updated_on` (GitLab used last_activity_at) as a
  prioritization signal only. It is not a complete change log.

### Combining Fast and Detailed Delta Discovery

* Yes. Fast delta: compare repository list, refs and summary fields to
  checkpoints. Detailed delta: query changed objects with `updated_on`
  filters and reconcile. GitLab used GraphQL for this; Bitbucket uses REST
  filters and local Git.


## 17. API and Token Constraints

### Rate Limits

Bitbucket Cloud (Atlassian "API request limits"):

| Limit type | Limit |
|------------|-------|
| Authenticated requests (default) | 1,000 per hour, rolling window, measured per user ID |
| Anonymous | 60 per hour per IP |
| /2.0/repositories/* (repository data) | 1,000 to 10,000 per hour (scaled) |
| Webhook list/add/remove | 1,000 per hour |
| Git operations (HTTPS and SSH) | 60,000 per hour |
| Raw file access | 5,000 per hour |
| Archive downloads | 1,500 per hour |
| Scaled limit | +10 per paid user above 100, max 10,000/hour; needs Standard/Premium, >=100 paid users, and access tokens or Forge asApp |

* Atlassian states that limits and page sizes are subject to change. Read
  X-RateLimit-* headers where provided (scaled endpoints) and handle 429.

GitHub: 5,000/hour for a PAT; 15,000/hour for GHEC-owned apps; secondary
limits: 100 concurrent requests, 900 points/minute per endpoint, about 80
content-creating requests/minute and 500/hour.

### Throttling and Retry Strategy

* GitLab spike: GitHub and GitLab limits are the same, so sleep time can be
  similar. Not true here: Bitbucket's budget is smaller and per user, so sleep
  and retry settings must be per provider.
* On 403/429 from GitHub: wait for retry-after or x-ratelimit-reset; if neither
  is present wait at least 1 minute, then back off exponentially with a retry
  cap. On Bitbucket 429/5xx: honor Retry-After if present, else exponential
  backoff with jitter and a retry cap.
* Persist checkpoints so a failed run resumes without repeating writes.
  Classify errors: auth, not found, validation, throttling, transient.


## 18. Wiki Migration, Repository Sizing, and LFS

### Wiki Migration to GHEC

* Equivalent: the Bitbucket repository wiki (a separate Git repository),
  corresponding to the GitLab project wiki. Bitbucket has no group wikis, so
  the GitLab group-wiki challenge does not arise.
* Biggest challenge: the Bitbucket wiki feature was removed on 2026-08-20. It
  can be migrated only from a retained clone; otherwise report "unavailable",
  never "empty".
* The current GitHub approach (enable wiki, initialize first page, push Git
  history) applies unchanged, since the target did not change. Convert
  markup/links as needed.

### Using git-sizer Across Providers

* Yes. git-sizer works on the .git object database and refs, so it is
  provider-agnostic and works on a Bitbucket mirror. It does not measure LFS
  payloads or hosting metadata.

### LFS Identification and Migration

* All GHEC LFS handling applies to Bitbucket as both are Git based: identify
  through `.gitattributes` and pointer files, migrate with `git lfs fetch
  --all` and `git lfs push --all`, and configure the target through the normal
  GHEC LFS setup. A mirror push moves pointers only, not LFS objects.
* Check GHEC LFS storage/bandwidth quota before migrating.


## 19. Issues in SCM

* GitLab: issues migrate one to one except a few caveats; closed/merged MRs
  are created as issues as fallback; issue author follows the PAT.
* Bitbucket: the native issue tracker no longer exists, so issues migrate only
  from a pre-removal export. Even then: kind/priority/component/version map to
  labels; status maps to open/closed plus label; issue author follows the PAT
  (original reporter kept in the body); attached images were not included in
  Atlassian's export; watchers/votes do not migrate.
* Closed/merged PRs are created as issues as fallback (same as GitLab).


## 20. Canonical Format for Discovery and Validation

* TBD, as in the GitLab spike: no canonical universal format is decided.
* Proposal for review (not decided): a provider-neutral record with
  source_provider, source workspace/repository UUID, object type, object id,
  source_updated_at, source hash, target id, status, transformation reason.
  Provider-specific fields are kept under a namespaced payload.


## 21. Sub-Item APIs and Migration Dependencies

* The sub-item APIs are listed in section 7 (per-resource table).
* Dependent bundles, in migration order: repository -> refs/Git/LFS ->
  settings and rules -> identity map -> PRs (and their comments, reviewers) ->
  variables and environments -> webhooks. A parent's success must not hide a
  child's failure; keep per-child evidence.


## 22. Token Pooling

* Token pooling is provider-agnostic and can be used for Bitbucket.
* Gap (same as GitLab spike): the health daemon is hardcoded for GitHub and
  must be made provider-aware.
* Bitbucket-specific caution: limits are measured per user ID, so several
  tokens of one user share one budget. Pool tokens of distinct identities
  (for example repository/workspace access tokens) only where Atlassian terms
  allow.


## 23. API Versions and Labels

* TBD: the query raised in the GitLab spike is not clear, so it stays open.
* Factual notes that may help the answer: Bitbucket Cloud has a single public
  API version path (/2.0); GitHub uses the X-GitHub-Api-Version header.
  Bitbucket has no labels at all (kind/priority/component are the nearest
  concepts) while GitHub labels are issue/PR metadata. Clarify with the
  requester which of these was meant.


## 24. Cross-Repository Dependencies, Branches, and Pull Requests

* Pipeline in repository A triggering repository B: Bitbucket does this through
  the pipelines REST API (custom pipeline trigger) or a pipe, using a stored
  token. No equivalent of GitLab's single CI job token is documented for
  Bitbucket (confirm in tenant). On GitHub, use workflow_dispatch /
  repository_dispatch with a GitHub App installation token that has access to
  the target repository; `GITHUB_TOKEN` is repository-scoped.
* Git submodules: relative paths are plain Git behavior (see section 4);
  access to other private repositories must be granted explicitly on GitHub.
* Issues linked across repositories (blocks, is blocked by, relates to) and
  group-level Epics: not available in Bitbucket (the issue tracker was
  repository-scoped and is removed). Epics and cross-project planning live in
  Jira, outside this migration.
* PR dependencies: Bitbucket has the branch restriction
  require_all_dependencies_merged. GitHub has no native equivalent; replace it
  with a required status check (Actions) if needed.
* Forks: migrate parent repositories first and recreate forks with the fork
  action; a push to a separate repository does not create fork lineage.


## 25. Teams, Collaborators, and Role Mapping

Concept mapping (GitLab spike table, answered for Bitbucket Cloud):

| GitHub concept | Bitbucket Cloud equivalent | How Bitbucket implements it |
|----------------|----------------------------|-----------------------------|
| Organization Team (@org/team-name) | Workspace group | Named set of users inside a workspace; granted access to projects/repositories. |
| Nested Teams (parent -> sub-team) | None documented | Groups are flat; no subgroup nesting like GitLab. |
| Granting a team access to a repo | Group permission | Group permission on a repository (permissions-config/groups) or project-level grant. |
| Repository collaborator (direct invite) | Direct user permission | Explicit user permission on one repository (permissions-config/users). |
| Outside collaborator | No distinct role | Atlassian documents that the user granted a repository permission must be a workspace member. |
| Team mention (@org/backend) | No verified group mention | Individual @-mentions only (account-based); verify group mentions in the tenant before promising parity. |

Permission levels:

| Bitbucket repository permission | GHEC repository role |
|---------------------------------|----------------------|
| admin | Admin |
| write | Write |
| read | Read |
| (none) | no access |
| no equivalent | Maintain, Triage (optional new GHEC roles; do not infer) |

Organization level: workspace administrator/owner -> organization Owner;
workspace member -> organization Member. Project permissions (admin, create,
write, read) have no inheritance on GHEC: expand them into team grants on every
repository of that project. Automation tokens (repository/project/workspace
access tokens) become GitHub App installation tokens.


## 26. Assumptions and Verification Gates

* Atlassian and GitHub limits and endpoints change; re-verify against current
  documentation and a representative workspace before building.
* Confirm in the tenant: merge-strategy REST availability, snippets API
  availability, group-mention behavior, cross-repo pipeline trigger tokens,
  and whether any pre-2026-08-20 issue/wiki archives exist.
* Run a trial migration covering: one small and one large repository, an LFS
  object, an open PR, a closed and a merged PR (fallback issue), a branch
  restriction, a webhook, a pipeline variable, and a project permission.


## 27. Coverage Map

| GitLab spike topic | Section |
|--------------------|---------|
| Authentication types for source tool | 1 |
| Hierarchy | 2 |
| Get all repo list | 3 |
| Dependencies / submodules / package registry | 4 |
| Layered discovery paths (fast, detailed) | 5 |
| Metadata collection and logical grouping | 6 |
| API calls for discovery, migration, validation | 7 |
| Delta migration (core, SCM, delta discovery) | 8 |
| Planner payload (initial fast, detailed, delta) | 9 |
| Metadata for cutover | 10 |
| User details history rewrite | 11 |
| Validation with evidence | 12 |
| CI/CD parameters, webhooks | 13 |
| Constraints for migration | 14 |
| GitHub Enterprise Importer comparison | 15 |
| Scenarios (fast vs detailed, change detection, delta) | 16 |
| API and token constraints (rate limit, failures, retries) | 17 |
| Wiki, git-sizer, LFS | 18 |
| Issues in SCM | 19 |
| Canonical format | 20 |
| APIs for sub-items / dependent bundles | 21 |
| Token pooling | 22 |
| API instance versions vs labels | 23 |
| Cross-repo dependencies, branches, PRs | 24 |
| Teams / collaborators and roles | 25 |


## 28. Answers to Stakeholder Questions

### 1. Issues and Wikis in Older Repositories

The August 20, 2026 removal applies to older repositories too; age does not
make their Issues or Wikis available through the current Bitbucket UI or API.
The legacy `has_issues` and `has_wiki` repository flags are not evidence that
the content is still retrievable.

Recovery is archive-based:

* Issues: locate a JSON export made before removal. Atlassian's export does not
  preserve attached image data, so look for separately saved attachments too.
* Wikis: locate a retained wiki Git clone or backup. It can preserve pages,
  history, and files that were present in the clone.
* Search migration archives, backup systems, build artifacts, and repository
  owners' workstations. Atlassian says workspace admins can request a list of
  repositories where these features were enabled; that list does not restore
  the content.
* If no export or clone can be found, record the object as `unavailable`, not
  `empty`. Do not promise recovery from the live Bitbucket API. If an archive
  exists, migrate from it and report any export limitations explicitly.

### 2. Rate Limits and Multiple User IDs

Do not create or rotate synthetic user IDs to multiply the request budget.
Although authenticated requests are accounted for per user ID, Atlassian's
Customer Agreement prohibits circumventing product usage limits. Atlassian can
throttle or suspend access for policy violations; whether a particular account
would be banned cannot be guaranteed in advance. Multiple tokens for the same
user do not create additional per-user quota.

Use the supported options instead:

* The default authenticated Bitbucket limit is 1,000 requests per hour per user
  ID in a rolling window. Some endpoint groups have separate limits.
* For eligible repository-data API calls, Atlassian offers scaled limits on
  Standard/Premium workspaces with at least 100 paid users, when using
  workspace/project/repository access tokens or a Forge app asApp. The increase
  is 10 requests/hour per paid user above the first 100, capped at 10,000/hour.
  This does not raise every endpoint's limit; check the response headers and
  current Atlassian documentation for the endpoint group.
* Reduce calls with pagination, partial responses, caching, checkpoints, and
  delta scans; honor throttling headers and back off on 429 responses.
* GitHub's higher limit applies on the target side only; it does not increase
  Bitbucket's source-side allowance.

### 3. Workspace and Project Hierarchy

The Bitbucket repository hierarchy is:

    Workspace
      └── Project
            └── Repository

The workspace is the main ownership and access boundary. It contains projects
and repositories. Projects group repositories and can carry project-level
permissions and default reviewers; projects do not nest inside other projects.
Every repository is assigned to one project. If a project is omitted when a
repository is created, Bitbucket assigns the workspace's oldest project.

An Atlassian organization/account is an identity and administration layer, not
the repository's URL namespace; it should not be assumed to map one-to-one to a
workspace. Repository API and clone paths use the workspace and repository slug
(`workspace/repo_slug`), not the project key. For GHEC, map the workspace to an
organization, the project to grouping/access metadata (for example a team plus
a repository property), and the repository to a repository. A GitHub Project
(V2) is a planning board, not the equivalent of a Bitbucket project container.


## 29. References


Atlassian:
* REST API v2.0 (authentication, pagination, filtering, partial responses):
  https://developer.atlassian.com/cloud/bitbucket/rest/
* Repositories, branch restrictions, commit statuses API groups (same site).
* API request limits:
  https://support.atlassian.com/bitbucket-cloud/docs/api-request-limits/
* Repository creation and project assignment:
  https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/
* Projects and project-level permissions:
  https://developer.atlassian.com/cloud/bitbucket/rest/api-group-projects/
* Issues and Wikis sunset announcement (updated 2026-08-21):
  https://community.atlassian.com/forums/Bitbucket-articles/Announcing-sunset-of-Bitbucket-Issues-and-Wikis/bc-p/3217861
* Atlassian Customer Agreement, section 2.2 (usage-limit circumvention):
  https://www.atlassian.com/legal/cloud-terms-of-service
* Atlassian Acceptable Use Policy:
  https://www.atlassian.com/legal/acceptable-use-policy
* Bitbucket Cloud API changelog (Issue Tracker API removal 2026-08-20, SSH
  hostname change, GCM requirement):
  https://developer.atlassian.com/cloud/bitbucket/changelog/

GitHub:
* REST API rate limits:
  https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
* Enterprise Importer, Bitbucket Server data migrated / not migrated:
  https://docs.github.com/en/migrations/using-github-enterprise-importer/migrating-from-bitbucket-server-to-github-enterprise-cloud/about-migrations-from-bitbucket-server-to-github-enterprise-cloud

Internal: Bitbucket-to-GHEC_Metadata_Migration.md (feature parity inventory).

End of document.
