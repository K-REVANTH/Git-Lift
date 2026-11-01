# Bitbucket → GHEC EMU Migration: Complete Q&A Session Guide

> **Purpose:** End-to-end preparation for a technical Q&A session covering Bitbucket Cloud and Data Center/Server migration to GitHub Enterprise Cloud with Enterprise Managed Users (GHEC EMU) via GitLift. Every answer is grounded in the spike documents and official documentation.

---

## Part 0: Your Three Specific Questions — Definitive Answers

### Q0.1 Issues & Wikis Were Removed. What About Older Repos — How Do We Migrate Them?

**The removal on 2026-08-20 applies universally — age of the repo does not matter.** Bitbucket removed the Issue Tracker and Wiki features (both UI and API) for *all* repositories, old and new. The legacy `has_issues` and `has_wiki` flags may still appear in the repository API response, but they are **flags only** — they do not mean the content still exists or is retrievable.

**Recovery is strictly archive-based:**

| Content | Recovery Method | What's Preserved | What's Lost |
|---------|----------------|------------------|-------------|
| **Issues** | Locate a **JSON export** made before 2026-08-20 (workspace admin could export). | Issue IDs, titles, descriptions, state, kind, priority, component, milestone, version, assignee, reporter, comments, votes, watchers. | **Attached images** (Atlassian's export did NOT include image data). Separately saved attachments must be located. |
| **Wikis** | Locate a **retained Git clone** of the wiki repository (the wiki was a separate Git repo at `git@bitbucket.org:{workspace}/{repo}.git/wiki`). | All wiki pages, full Git history, files that were in the clone at the time. | Anything not captured in the clone. |

**Where to look for archives:**
- Migration backup archives / snapshots
- Build artifacts / CI artifact stores
- Repository owners' local workstations (`git clone` of the wiki)
- Corporate backup systems (disk/tape)
- Atlassian workspace admin export history

**If no archive exists:** Record the object as `unavailable`, **never** as `empty`. Do not promise recovery from the live Bitbucket API. If an archive is found later, ingest it at that point.

**Migration path if archive exists:**
- **Issues →** Map `kind`/`priority`/`component`/`version` to GitHub labels. Map `status` to open/closed + label. Original reporter goes into the body as annotation (`*Originally reported by @user on <date>*`). 1 GitHub API call per issue + child calls for comments/labels.
- **Wiki →** Enable wiki on GHEC repo, initialize first page, then `git push` the retained wiki clone history. Convert Creole/Bitbucket markup to GitHub Flavored Markdown. Rewrite internal links.

> [!CAUTION]
> Never tell a customer "we can migrate Issues/Wikis from Bitbucket" without first confirming a pre-removal archive exists. The live API returns nothing.

---

### Q0.2 Rate Limit Is Only 1,000 — Can We Create Multiple User IDs to Multiply Throughput? Will Our Account Get Banned?

**Do NOT create or rotate synthetic user IDs to multiply the request budget. This violates Atlassian's terms and risks account suspension.**

**Why it won't work / is dangerous:**

| Aspect | Reality |
|--------|---------|
| **Legal** | Atlassian Customer Agreement §2.2 explicitly prohibits circumventing product usage limits. Atlassian Acceptable Use Policy reinforces this. |
| **Enforcement** | Atlassian can throttle, suspend, or ban access for policy violations. Whether a particular account gets banned can't be guaranteed in advance, but the risk is real. |
| **Multi-token same user** | Multiple tokens for the **same** user share ONE budget. Creating 5 tokens for one user ≠ 5× quota. The limit is per **user ID**, not per token. |
| **Detection** | Atlassian monitors usage patterns. Coordinated high-throughput requests from multiple freshly-created accounts targeting the same workspace is a detectable anomaly. |

**What to do instead — legitimate throughput maximization:**

1. **Scaled limits (best option):** On Standard/Premium workspaces with ≥100 paid users, using workspace/project/repository access tokens or a Forge app `asApp`, Atlassian provides +10 requests/hour per paid user above the first 100, up to **10,000/hour**. Check `X-RateLimit-*` response headers.

2. **Prefer local Git over REST:** Git operations have a **60,000/hour** limit (vs 1,000 REST). Use `git clone --mirror`, `git ls-remote`, `git rev-list`, `git log`, `git-sizer` for bulk data instead of REST endpoints. This is the single biggest throughput optimization.

3. **Reduce REST calls:**
   - Use `pagelen=100` (max page size) to minimize pagination calls.
   - Use `fields=` (partial responses) to cut payload size.
   - Use `q=updated_on > <date>` filters for delta scans.
   - Cache and checkpoint everything — never re-fetch what you already have.

4. **Budget planning:** At 1,000/hour, 10,000 API calls = at least 10 hours for one identity. Plan discovery windows accordingly.

5. **Token pooling (legitimate):** Pool tokens of **distinct** identities (e.g., different repository/workspace access tokens that are resource-bound, not user-bound) only where Atlassian terms allow. Each distinct identity gets its own 1,000/hour budget.

6. **Honor 429s properly:** Read `Retry-After` header, use exponential backoff with jitter, classify errors, persist checkpoints so failed runs resume without repeating writes.

**Comparison table:**

| Provider | Default Limit | Max Achievable | Git Ops |
|----------|--------------|----------------|---------|
| Bitbucket Cloud | 1,000/hr per user | 10,000/hr (scaled, qualifying) | 60,000/hr |
| GitHub (GHEC) | 5,000/hr per PAT | 15,000/hr (GHEC GitHub App) | No separate limit |
| Bitbucket DC | Admin-configurable (default 60 burst, 5/s ≈ 18,000/hr) | Exemption possible | SSH separate |

> [!IMPORTANT]
> The source-side (Bitbucket) throughput — not GitHub — is the bottleneck. All throughput planning must be Bitbucket-budget-first.

---

### Q0.3 Workspace & Project — Are They Nested? How Does the Hierarchy Work?

**Yes, they are nested. The Bitbucket Cloud hierarchy is strictly:**

```
Atlassian Organization (billing/identity layer — NOT a code container)
  └── Workspace (main ownership + access boundary, URL namespace)
        └── Project (groups repos, carries default permissions)
              └── Repository
```

**Key rules:**
- Every repository belongs to **exactly one** project.
- Projects do NOT nest inside other projects (no subgroups like GitLab).
- If you create a repo without specifying a project, Bitbucket assigns it to the workspace's oldest project.
- The workspace slug is the URL namespace: `bitbucket.org/{workspace}/{repo_slug}`.
- The project key does NOT appear in URLs or clone paths — it's an internal grouping/governance construct.
- Atlassian Organization is an identity/billing layer that sits above workspaces. It is NOT the workspace and should NOT be assumed to map 1:1 to a workspace.

**For Data Center/Server it's different:**

```
Instance (self-hosted server/cluster)
  └── Project (key, e.g. PROJ)
        └── Repository
  └── Personal Project (~username)
        └── Repository (user's personal repos)
```

- DC has no "workspace" concept.
- Personal repos live under `~username` project namespace.
- Groups are global (instance-level), not project-scoped.

**How this maps to GHEC EMU:**

| Bitbucket (Cloud) | Bitbucket (DC) | GHEC EMU | Notes |
|---|---|---|---|
| Atlassian Organization | Instance | **Enterprise** | Top-level governance, SAML/SCIM, audit log |
| Workspace | *(no equivalent — use Project or Instance)* | **Organization** | 1:1 default; consolidation is a customer decision |
| Project | Project | **Team** (access) + **Custom Property** `bb_project_key=KEY` (grouping) | No GHEC container equivalent; GitHub Projects V2 is a planning board, NOT a repo container |
| Repository | Repository | **Repository** | Private or Internal visibility under EMU |
| Workspace Group | Global Group | **Team** | IdP-synced in EMU |
| *(N/A)* | Personal Project `~user` | **Dedicated Organization** (e.g., `org-personal-repos`) | EMU prohibits personal repos on managed accounts |

> [!WARNING]
> A common mistake: assuming GitHub's "Projects V2" is equivalent to Bitbucket's "Project." It is NOT. GitHub Projects V2 is a Kanban/planning board. Bitbucket's Project is a **repository security container** with permission inheritance. The GHEC equivalent is a **Team** (for permissions) + **Custom Repository Property** (for grouping).

---

## Part 1: Authentication — Everything You Need to Know

### Q1.1 What authentication mechanisms does Bitbucket Cloud support?

| Mechanism | Details | Used by GitLift? |
|-----------|---------|-------------------|
| **API Token (Personal)** | Scoped, mandatory expiry (max 1 year). Auth: Basic (`email:token`) or Bearer (since 2026-08-18). Acts as the owning user. | ✅ Primary for discovery |
| **Repository / Project / Workspace Access Token** | Tied to a resource, not a user. Appears as a "user" in logs. Cannot query permissions. Cannot call deploy-key APIs. Cannot be viewed after creation. | ✅ For specific scopes |
| **OAuth 2.0 Consumer** | Authorization-code, client-credentials, JWT grants. Access tokens expire 1 hour; refresh tokens rotate (used = replaced). Must go to `api.bitbucket.org`. | ✅ Alternative |
| **App Passwords** | ⚠️ **Deprecated** by Atlassian in favor of API tokens. Do not build on them. | ❌ Inventory only |
| **SSH Keys / Access Keys** | Git transport only. SSH via `bitbucket.org` is deprecated → use `ssh.bitbucket.org`. | For Git clones only |
| **Pipelines OIDC / Connect JWT / Forge** | Runtime CI credentials. | ❌ Not for migration |

### Q1.2 What authentication mechanisms does Bitbucket DC/Server support?

| Mechanism | Details |
|-----------|---------|
| **HTTP Basic** (over TLS) | `username:password` or `username:token` |
| **HTTP Access Tokens** | User-scoped, project-scoped, repository-scoped (DC license needed for project/repo tokens). Permissions: read/write/admin. Optional expiration. |
| **OAuth** | Application Link OAuth (bi-directional with Jira/Confluence/Bamboo) |
| **SSH** | User keys and system-level access keys for Git |

### Q1.3 What minimum scopes does GitLift need on Bitbucket Cloud?

```
read:repository, read:pullrequest, read:project,
read:workspace, read:user, read:pipeline, read:webhook,
admin:repository        (branch restrictions require admin),
read:permission         (+ user-level credential with repo admin
                         rights — access tokens CANNOT query permissions)
```

### Q1.4 What does the target (GHEC EMU) side need?

- A **provisioned EMU managed user** (service identity) as organization owner or with migrator role.
- **Classic PAT** scopes: `repo`, `workflow`, `admin:org` (owner) or `read:org` (migrator).
- **GitHub App installation tokens** preferred for writes (higher rate limit: 15,000/hr).
- Enterprise policies must allow: the migration identity, classic PATs (if GEI is used), and the source IP range.

### Q1.5 Key differences between Cloud and DC authentication?

| Aspect | Cloud | DC |
|--------|-------|----|
| Credential owner | Atlassian account | Directory user (LDAP/AD/Crowd) |
| Basic auth user | Atlassian email | Username |
| Bearer support | API tokens, OAuth | Project/repo tokens (user tokens via Basic) |
| Permissions API | NOT available to access tokens | Needs admin rights |
| Rate throttling | Per user, fixed hourly | Optional bucket per user per node |
| Expiry | Mandatory (1 year max) | Optional, admin may require |
| SSH | `ssh.bitbucket.org` (migration from old host) | Customer host |

### Q1.6 What's the SSH situation?

Bitbucket is changing SSH access: SSH via `bitbucket.org` is deprecated (brownouts announced 2026-10-28). **Prefer HTTPS with a scoped token**, or use the new `ssh.bitbucket.org` hostname. If Git Credential Manager is used with OAuth, it must be version 3.0.0+ before 2026-11-30 or OAuth Git requests are blocked.

---

## Part 2: Hierarchy Deep-Dive

*(Covered comprehensively in Q0.3 above. Additional Q&A below.)*

### Q2.1 Can repos belong to multiple projects?

**No.** A Bitbucket repository belongs to exactly one project within its workspace. Forks and mirrored copies are separate repositories.

### Q2.2 What happens with naming conflicts during migration?

GHEC repository names are unique per organization and **case-insensitive** (unlike Bitbucket slugs which are unique per workspace). Deterministic resolution: keep the name if free → `<project-key>-<slug>` → numeric suffix → replace invalid characters → truncate to 100 chars. Record every rename in the mapping table.

### Q2.3 How do you handle personal repos (DC)?

DC has personal projects (`~username`). GEI does NOT migrate personal repositories. GitLift: discover and report → migrate into a designated organization (e.g., `org-personal-repos`) with a `bb_personal_owner` property after customer approval. If the user isn't provisioned in EMU, ownership goes to a team/service account.

---

## Part 3: GitLift Migration Phases — Complete Walkthrough

### Phase 1: Initial Fast Discovery

**What it does:** Quick inventory scan — repository list + lightweight signals.

**What we get:**
- Repository list with uuid, full_name, privacy, project, main branch, size, created/updated, language, fork parent
- `git ls-remote` ref counts (branches, tags)
- Basic counts (repos, sizes, fork flags)

**What we DON'T get (requires detailed discovery):**
- PR/comment counts, permissions, webhooks, pipelines, branch rules

**API calls:** `pages(repositories)` + 1 GET per repo + Git `ls-remote` per repo

**Issues we face:**
- No GraphQL (Bitbucket has no public GraphQL API) — everything is REST v2.0 with pagination
- At 1,000 calls/hour, 1,000 repos = ~11 pages + 1,000 detail GETs = 1,011 calls ≈ 1 hour minimum
- The planner must label estimates as "limited accuracy" since many surfaces are unknown

**Workaround:** Prefer `git ls-remote` and local Git signals (0 REST calls) for ref counts, commit counts, sizes.

### Phase 2: Initial Detailed Discovery

**What it does:** Full metadata enumeration for every in-scope repository.

**What we collect per repo:**
- Branches, tags, commits (local Git preferred)
- Branch restrictions (16 kinds on Cloud)
- Pull requests (all states) + child objects (comments, activity, tasks, reviewers, approvals)
- Repository permissions (users + groups) — **requires admin credential**
- Webhooks (repository + workspace)
- Pipelines config, schedules, variables (Cloud only)
- Environments, deployments (Cloud only)
- LFS pointers, submodules, file trees (local clone)
- Downloads, snippets (Cloud)

**Dominant cost:** PRs × (1 + number of child collections). A repo with P PRs and 3 child collections costs ~P×3 child calls + pages(PR).

**Issues we face:**

| Issue | Details | Workaround |
|-------|---------|------------|
| **Rate limit exhaustion** | 1,000/hr per user; a repo with 500 PRs × 3 children = 1,500 calls = 1.5 hours just for PRs | Use scaled limits (access tokens on Premium); schedule overnight; checkpoint everything |
| **Admin-only data** | Branch restrictions need `admin:repository`; permissions need repo admin + user-level credential; access tokens CANNOT query permissions | Use a workspace admin's personal API token for discovery |
| **Issues/Wikis gone** | `has_issues`/`has_wiki` flags are misleading — content doesn't exist | Check for archives; never report "0 issues" — report "unavailable" |
| **Commit pagination** | Cloud commits use iterator-style pagination (no total, only `next`) | Use local Git (`git rev-list --count`, `git log`) — 0 REST calls |
| **Hidden email** | User email is often hidden due to privacy settings | Use account_id → IdP export matching instead |
| **No GraphQL** | Cannot batch queries like GitLab | Accept higher call count; use `fields=` partial responses |

### Phase 3: Migration (Initial)

**Sequence (order matters):**

```
1. Provision GHEC enterprise, orgs, SSO, SCIM
2. Provision users via IdP/SCIM
3. Configure enterprise/org policies, custom properties, teams
4. Mirror-clone Git data (branches, tags, commits, notes)
5. Push to GHEC target repos
6. Transfer LFS objects (git lfs fetch --all → git lfs push --all)
7. Migrate repo settings (description, visibility, merge strategies, default branch)
8. Migrate branch protection → GHEC Rulesets
9. Migrate open PRs (title, body with provenance header, branches, reviewers, comments)
10. Archive closed/merged/declined PRs as issues or external records
11. Migrate issues (from archive, if available)
12. Migrate wiki (from archive clone, if available)
13. Migrate webhooks (new secret required — source secret is NOT retrievable)
14. Migrate CI/CD variables (plain values; secured values must be re-supplied)
15. Create environments
16. Configure security scanning
```

**Issues we face:**

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Original authors can't be set** | PR/comment/review author = migration bot identity | Annotate body: `*Originally by @user on <date>*`. Store original in evidence. |
| **Original timestamps can't be set** | `created_at` = migration time, not original | Same body annotation approach. Git commit dates are preserved. |
| **Closed/merged PRs can't be migrated as PRs** | GitLift cannot create native merged/closed/declined PRs via standard API | Fallback: archival issue per PR with key fields + link, or external JSON/HTML archive, or keep source read-only |
| **Secret values can't be read** | Secured variables, webhook secrets, OAuth secrets are write-only/hashed | Must be re-obtained from corporate vaults / manual re-entry. Pre-migration inventory is essential. |
| **GitHub rejects certain refs** | `refs/pull/*` are reserved; blind `--mirror` push will fail | Push branches and tags explicitly, skip reserved refs |
| **Fork relationships** | Can't arbitrarily set fork parent on GHEC — must use fork action | Migrate parent first, create fork via GHEC fork API, then push differing branches |
| **Files > 100 MiB** | GitHub rejects files over 100 MiB | Convert to LFS with history rewrite (customer approval required) — changes SHAs |
| **Repo name > 100 chars** | Bitbucket allows 128; GHEC allows 100 | Truncate with deterministic rule; record rename in mapping table |
| **EMU visibility restrictions** | No public repos in EMU | All repos become Private or Internal |
| **OIDC trust policies** | Cloud provider trust policies (AWS IAM, GCP, Azure) point to Bitbucket's OIDC issuer | Must be updated with GHEC OIDC issuer and claim mappings — cross-team coordination |

### Phase 4: Delta Discovery & Delta Migration

**What it does:** Identifies and migrates changes since the initial migration.

**How it works:**
- **Git delta:** Fetch into the retained bare clone (kept on durable storage like EFS), compute changed refs and objects, push only the delta.
- **Metadata delta:** Compare stored evidence/snapshots against current source state using `q=updated_on > <date>` filters (Cloud), or sort order + snapshot comparison (DC).

**Issues we face:**

| Issue | Details | Workaround |
|-------|---------|------------|
| **Deletions are invisible** | `updated_on` filters don't catch deleted objects | Run periodic full-inventory comparisons |
| **DC has no `updated_on` filters** | No server-side "since" filter documented for most collections | Use sort order + watermark; rely on snapshots |
| **Target drift** | Someone may have changed things on GHEC after initial migration | Detect by comparing target against evidence hash before writing; policy: do NOT overwrite target-side changes — report as CONFLICT |
| **Source ref deletions** | A branch deleted on source since last run | Handle explicitly; don't use blind `--mirror` push |
| **Authorship of updates** | Re-running migration still uses the bot identity | Same annotation approach |
| **Rate budget for repeated runs** | Each full reconciliation costs the same as initial detailed discovery | Use change filters where available; prioritize changed repos |

### Phase 5: Validation

**What we validate:**

| Check | Method |
|-------|--------|
| Git refs (branches, tags) | `git ls-remote` on source vs target — every branch/tag exists with same SHA |
| Commit count | Local Git comparison |
| LFS objects | Compare oid set from source pointers against target LFS |
| Submodule URLs | Verify rewritten URLs resolve on target |
| Open PRs | Target PR exists, base/head match, title/body provenance present, reviewer assignments match mapping, comment count matches |
| Closed/merged PRs | Archival record exists or recorded as accepted exception |
| Branch rules → Rulesets | Read target rulesets, compare with translation output |
| Permissions | Compare effective-permission set from evidence with target teams/roles |
| Webhooks | Read back URL/events/active on target |
| Variables | Compare key/scope (never compare values) |
| Wiki | Page list, content hashes, Git history (commit count, head SHA) |

**Validation statuses:**
- **PASS** = all mandatory checks equal or explained by approved expected difference
- **PASS_WITH_EXCEPTIONS** = only approved differences remain
- **FAIL** = unexplained difference or any mandatory check not run

**Repository status ladder:** `NOT_STARTED → GIT_DONE → METADATA_PARTIAL → METADATA_DONE → VALIDATION_FAILED → VALIDATED → CUTOVER_READY`

### Phase 6: Cutover

**Pre-cutover checklist (all must be satisfied):**

- [ ] Repository status = VALIDATED with no unexplained differences
- [ ] Final delta applied and validated against approved source checkpoint
- [ ] Identity mapping complete for all owners/admins
- [ ] Teams and access verified (including controlled-account access test)
- [ ] Rulesets in place and negative-tested (blocked push/merge on sandbox branch)
- [ ] Dependencies resolved or accepted
- [ ] LFS complete (no missing oid pointers)
- [ ] Webhooks and integrations re-pointed or scheduled
- [ ] Secrets re-supplied from vaults
- [ ] Customer approvals recorded (7 distinct approvals needed)
- [ ] Rollback plan agreed
- [ ] Source freeze window set and communicated

**Cutover sequence:**

```
1. Freeze writes on Bitbucket (set read-only via branch restrictions or permission change)
2. Take final checkpoint
3. Run final delta migration (Git fetch/push + metadata reconciliation)
4. Run final validation
5. Verify validation = PASS or PASS_WITH_EXCEPTIONS
6. Export blocker-class historical data (pipeline runs, deployments, audit log)
7. Switch DNS / update URLs
8. Re-point webhook consumers
9. Switch CI triggers
10. Enable GHEC audit log streaming
11. Communicate to developers: update remotes, re-subscribe to notifications
```

**What blocks cutover:**
- Validation FAIL or not run
- Coverage/confidence below threshold
- Unresolved name conflict, dependency, identity, or permission gap
- Missing customer approval
- Source changed after checkpoint
- Credentials/quota exhausted
- Unsupported item classified as "ready" without trial-migration evidence

---

## Part 4: Rate Limit & API Token Constraints — Deep Dive

### Q4.1 Full rate limit comparison

| Provider | Limit | Scope | Git Ops | Notes |
|----------|-------|-------|---------|-------|
| **BB Cloud** (default) | 1,000/hr | Per user ID, rolling window | 60,000/hr | Measured per Atlassian user, not per token |
| **BB Cloud** (scaled) | Up to 10,000/hr | Per user, Standard/Premium, ≥100 paid users, access tokens or Forge asApp | Same | +10/hr per paid user above 100 |
| **BB Cloud** (webhooks) | 1,000/hr | Webhook list/add/remove | N/A | Separate limit |
| **BB Cloud** (raw files) | 5,000/hr | Per user | N/A | |
| **BB Cloud** (archive downloads) | 1,500/hr | Per user | N/A | |
| **BB Cloud** (anonymous) | 60/hr | Per IP | N/A | |
| **BB DC** | Admin-configurable | Per user, per node; default 60 burst, 5/s refill | SSH separate | Can be exempted per service account |
| **GitHub** (PAT) | 5,000/hr | Per PAT | N/A | |
| **GitHub** (GHEC App) | 15,000/hr | Per installation | N/A | |
| **GitHub** (secondary) | ~80 content creates/min, 500/hr; 100 concurrent; 900 pts/min | Per endpoint group | N/A | The real write bottleneck |

### Q4.2 How to maximize throughput within limits?

1. **Local Git over REST** — `git clone --mirror`, `git ls-remote`, `git rev-list`, `git-sizer` count as Git ops (60,000/hr), NOT REST (1,000/hr).
2. **`pagelen=100`** — Maximum page size; cuts pagination calls by 10× vs default.
3. **`fields=` partial responses** — Request only the fields you need.
4. **`q=updated_on > <date>` + `sort=`** — Only fetch changed objects for delta.
5. **Checkpoint everything** — Resume from last success, never re-fetch.
6. **Workspace/repo access tokens on Premium** — Enables scaled limits.
7. **Separate read and write budgets** — Source reads (Bitbucket) vs target writes (GitHub).
8. **Per-provider rate governors** — Different sleep/backoff settings per provider.

### Q4.3 What happens when we hit 429?

- Read `Retry-After` header if present; else wait at least 60 seconds.
- Exponential backoff with jitter on 429 and 5xx.
- Persist checkpoint — failed run resumes without repeating writes.
- Classify errors: auth (401) vs not-found (404) vs validation vs throttle (429) vs transient (5xx).

---

## Part 5: Migration Constraints & Hard Blockers — What Can't Be Migrated

### Things that absolutely cannot be migrated

| Item | Why | Workaround |
|------|-----|------------|
| Original authors of PRs/comments/reviews | GHEC public API records the token owner as creator | Body annotation: `*Originally by @user on <date>*` |
| Original timestamps of platform objects | `created_at` = API-call time | Body annotation |
| Closed/merged/declined PRs as native PRs | Standard GHEC API cannot create pre-merged PRs | Archival issue with key fields + link |
| Secret/token values | Hashed/write-only on source | Re-supply from vaults |
| Webhook secrets | Not retrievable from source | Generate new secret, deliver to receiver owner |
| Pipeline run history & logs | GHEC Actions has no injection API | Export to external archive (S3/SIEM) |
| Deployment history | Can't inject with original timestamps/actors | External archive + optional backfill via Deployments API |
| Audit log history | GHEC audit log is append-only, starts fresh | Export to SIEM before migration |
| Webhook delivery history | GHEC delivery log starts fresh | Export if operationally important |
| Issues & Wikis (Cloud, post-2026-08-20) | API removed | Only from pre-removal archive |
| DC server-side pre-receive hooks | GHEC SaaS doesn't allow server-side scripts | Decompose into Rulesets + GitHub Actions |
| DC Java OSGi plugins | No in-process extension model on GHEC | Re-architect as GitHub Apps |
| Bitbucket Pipes | Different ecosystem | Manual mapping to GitHub Actions |
| `SUPERSEDED` PR state | No GHEC equivalent | Map to `closed` with label |
| Per-user state (watchers, notifications) | User-preference data, can't bulk-assign | Users re-subscribe |
| Original IDs, UUIDs, URLs | Auto-generated on target | Store in mapping table |

---

## Part 6: GEI (GitHub Enterprise Importer) Comparison

### Q6.1 Does GEI support Bitbucket Cloud?

**No.** GEI's documented Bitbucket route is for **Bitbucket Server / Data Center 5.14+ only**. No Bitbucket Cloud route is documented. For Cloud, GitLift (custom migration) is the only route.

### Q6.2 What does GEI migrate (DC only)?

| Migrated | NOT Migrated |
|----------|--------------|
| Git source with history | Branch permissions |
| Pull requests (including merged) | Commit comments |
| PR comments, reviews, file/line review comments | Repository settings |
| Required reviewers, attachments | CI pipelines |
| Mannequin attribution (reclaimable) | LFS objects |
| | Personal repositories |
| | Webhooks, CI variables |

### Q6.3 When would we use GEI vs GitLift?

**GEI advantage:** Migrates closed/merged PRs (GitLift cannot via public API) and provides mannequin-based attribution with reclaim.

**GitLift advantage:** Cloud support, delta migration, discovery & planning, settings, rulesets, permissions/teams, webhooks, variables, LFS, wiki archive, identity mapping for EMU, validation with evidence, cutover gates, exceptions reporting.

**Hybrid approach (BB-034):** For DC, use GEI for Git+PRs, then GitLift for everything else (settings, rules, permissions, LFS, webhooks, variables).

---

## Part 7: Identity & EMU Constraints

### Q7.1 How does user mapping work?

Matching keys in priority order:
1. Verified email (from IdP)
2. Username / UPN
3. Employee ID attribute
4. Manual CSV from customer

Output: mapping table with status `MATCHED` / `AMBIGUOUS` / `UNMATCHED`.

### Q7.2 What are the EMU-specific constraints?

- Users must be provisioned by **SCIM** — cannot create manually
- Usernames are `[idp_username]_[shortcode]` — determined by IdP, not GitHub
- Profile name and email are IdP-controlled (one email, immutable on GitHub)
- Cannot collaborate outside the enterprise
- No public content (repos, gists)
- No traditional outside collaborators — only Guest Collaborators via IdP
- Commit linking: GitHub links a commit to the EMU user **only if the commit email matches** the single IdP email
- If emails don't match → commits show as unlinked (or requires controlled history rewrite / mailmap — changes SHAs, high impact)

---

## Part 8: CI/CD Migration

### Q8.1 Bitbucket Pipelines → GitHub Actions: What changes?

| Bitbucket Pipelines | GitHub Actions |
|---|---|
| `bitbucket-pipelines.yml` | `.github/workflows/*.yml` |
| `pipe:` steps | Marketplace Actions |
| `size: 1x`–`32x` (container resources) | `runs-on:` with Larger Runners |
| `clone: depth: N` | `actions/checkout` with `fetch-depth: N` |
| `caches: - docker` | `docker/build-push-action` with `cache-from: type=gha` |
| `condition.changesets.includePaths` | `on.push.paths` or `dorny/paths-filter` |
| `max-time` | `timeout-minutes` |
| Deployment environments | GHEC Environments with protection rules |
| OIDC to AWS/GCP/Azure | OIDC (different issuer — trust policies must be updated) |
| Bitbucket Runners (Docker containers) | Self-hosted runners (installed agents) |

### Q8.2 What about DC CI (Bamboo/Jenkins)?

DC has no native Pipelines. CI is external (Bamboo, Jenkins, TeamCity) via build-status webhooks. Options:
- Re-point CI tool to GHEC via commit status webhooks
- Convert to GitHub Actions
- Keep external CI and use GHEC commit status API

---

## Part 9: Branch Protection / Governance Migration

### Q9.1 Branch rule translation (Appendix C from detailed spike)

| Bitbucket Rule | GHEC Equivalent | Fidelity |
|---|---|---|
| `push` (restrict write by users/groups) | Ruleset: restrict updates + bypass actors | Partial |
| `force` | Block force pushes | Direct |
| `delete` | Restrict deletions | Direct |
| `require_approvals_to_merge` (N) | Required approving reviews (N) | Direct |
| `require_default_reviewer_approvals_to_merge` | CODEOWNERS + require code owner review | Partial |
| `require_no_changes_requested` | Inherent: changes-requested blocks merge | Direct |
| `require_passing_builds_to_merge` | Required status checks (names change after CI conversion) | Partial |
| `require_commits_behind` (0) | Require branches up to date | Direct |
| `require_tasks_to_be_completed` | Require conversation resolution | Partial |
| `reset_pullrequest_approvals_on_change` | Dismiss stale approvals | Direct |
| `smart_reset_pullrequest_approvals` | Dismiss stale approvals (less precise) | Partial |
| `reset_pullrequest_changes_requested_on_change` | **None** | ❌ Unsupported |
| `require_all_dependencies_merged` | **None** (use required status check from Actions) | ❌ Unsupported |
| `allow_auto_merge_when_builds_pass` | Repository auto-merge setting | Direct |

---

## Part 10: Quick-Fire Q&A — Anticipating Session Questions

**Q: Can we migrate selected repos without migrating an entire workspace?**
Yes. Scope is a repository list by id/uuid. Group-level objects (teams, properties) are created only as needed by selected repositories.

**Q: Can repos from multiple workspaces go into one GHEC org?**
Yes, but requires collision-safe naming, source properties (`bb_source`, `bb_workspace`), per-source teams, and coordinated rulesets.

**Q: What about Snippets?**
Cloud-only. Options: migrate to Gists (user-scoped, no org ownership) or to a dedicated "snippets" repository within the org.

**Q: What about Downloads?**
Migrate to GHEC release assets. **All external consumer URLs will break** — URL scheme is completely different. Deploy a redirect service if needed.

**Q: What about Jira integration?**
GitHub for Jira app provides equivalent integration going forward. Historical Jira Development Panel entries stay pointing at Bitbucket URLs (will 404 after decommission). Jira-side link rewrite is a separate project.

**Q: What happens if the target org has rulesets that reject migrated history?**
Migration will fail. Must verify org/enterprise rulesets and custom properties in the target EMU environment before migration.

**Q: How long does a typical migration take?**
Formula: `time = (git_bytes / throughput) + (LFS_bytes / throughput) + (source_REST_calls / source_rate) + (GH_writes / secondary_content_limit) + fixed_overhead`. PR and comment counts are the main multipliers for metadata time.

**Q: What's the rollback plan?**
Keep Bitbucket in read-only mode for a grace period. If migration fails validation, the source is still intact. Git data is immutable. Platform metadata can be re-migrated.

**Q: How do we handle in-flight PRs during cutover?**
Freeze window: set Bitbucket read-only → final delta Git sync → final delta PR sync → validate → switch. Any change after the final checkpoint invalidates approval and requires another delta + validation.

---

*End of Q&A Session Guide*
