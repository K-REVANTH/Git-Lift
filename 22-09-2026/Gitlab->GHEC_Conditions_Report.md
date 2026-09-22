# GitLab → GitHub Enterprise Cloud (GHEC) Complete Conditions & Assumptions Mapping

Below is the complete mapping of **every condition and assumption** documented across all three parts of the metadata migration report, mapped to the specific metadata/attributes they govern and their coverage status in discovery.

---

## Complete Conditions & Assumptions Mapping

### Part 1 — Conditions from 🟢 Seamless / Direct Migrations

| # | Condition | What It Checks | Metadata / Attribute(s) | Available in Current Discovery |
|---|---|---|---|---|
| 1 | **Git Data Fidelity** | Verifies that all Git-native data (commits, branches, tags, refs) is transferred via bare-repo mirror (`git clone --mirror` + `git push --mirror`) to preserve SHAs, author/committer metadata, and timestamps. | `repo.commits`, `repo.branches`, `repo.tags`, `repo.git_notes`, `repo.signed_commits` | ✅ Yes — Items 6–9, 14 in Seamless table |
| 2 | **LFS Storage Quotas** | Checks that GHEC LFS storage and bandwidth quotas are sufficient for the volume of LFS objects being migrated. GHEC includes 1 GB storage + 1 GB/month bandwidth by default. | `repo.lfs` | ✅ Yes — Item 10 in Seamless table |
| 3 | **Deploy Key Uniqueness** | Checks that GHEC's global uniqueness constraint on deploy key public keys is handled. GitLab allows the same key on multiple projects; GHEC does not. | `access.deploy_keys` | ✅ Yes — Item 19 in Seamless table |
| 4 | **Emoji Reaction Vocabulary** | Checks that GitLab's broader emoji set for award reactions is mapped to GHEC's restricted 8-reaction set (+1, -1, laugh, confused, heart, hooray, rocket, eyes). | `pm.reactions` | ✅ Yes — Item 30 in Seamless table |
| 5 | **CODEOWNERS Adjustments** | Checks that CODEOWNERS file identity references (`@group/subgroup` → `@org/team`), file location (`.gitlab/` → `.github/`), and unsupported section headers (`[Section]`) are handled. | `review.codeowners_file` | ✅ Yes — Item 18 in Seamless table |
| 6 | **Release Date Backdating** | Checks that original release creation timestamps are preserved by creating releases as drafts first (which allows setting `created_at`), then publishing. | `releases.created_at` | ✅ Yes — Item 23 in Seamless table |
| 7 | **Wiki and Issue Toggles** | Checks that GHEC's inability to disable pull requests is noted when GitLab had merge requests disabled. | `repo.merge_requests_enabled`, `repo.issues_enabled`, `repo.wiki_enabled` | ✅ Yes — Items 26–28 in Seamless table |
| 8 | **Submodule URL Rewriting** | Checks that `.gitmodules` URLs pointing to GitLab repositories are updated post-migration to point to the corresponding GHEC repository URLs. | `repo.submodules` | ✅ Yes — Item 13 in Seamless table |
| 9 | **User Identity Mapping** | Checks that Git author/committer emails in migrated commits are linked to GHEC user profiles only if the email matches a verified email on a GitHub account. | `repo.commits`, `repo.signed_commits`, `access.ssh_keys`, `access.gpg_keys` | ✅ Yes — Items 6, 14, 32, 33 in Seamless table |
| 10 | **GHEC Tier Assumption** | Checks that the target is confirmed as GitHub Enterprise Cloud with an active Enterprise account, and that GHAS is separately licensed for private/internal repos. | All items (platform-wide prerequisite) | ✅ Yes — Applies globally across all 178 items |
| 11 | **API Rate Limits** | Checks that migration operations respect GHEC API rate limits (5,000 req/hr for users, 15,000 for GitHub Apps) and implement pagination, retry, and backoff logic. | All API-migrated items (issues, PRs, labels, milestones, comments, reviews, releases, webhooks, etc.) | ✅ Yes — Applies to all API-based migration items |
| 12 | **Repository Size Limits** | Checks that repository sizes are within GHEC limits (recommended <5 GB, hard limit ~100 GB, push limit ~2 GB per push). | `repo.name` (size-related metadata) | ✅ Yes — Noted in conditions; size is an implicit attribute of repo migration |

---

### Part 2 — Conditions from 🟡 Migratable with Changes / Behavioral Differences

| # | Condition | What It Checks | Metadata / Attribute(s) | Available in Current Discovery |
|---|---|---|---|---|
| 13 | **User Identity Mapping is Critical** | Checks that a comprehensive `gitlab_username → ghec_username` mapping table exists before migrating any collaboration objects (issues, PRs, comments, reviews, approvals). Without it, author attribution is lost. | `pm.issues`, `pm.issue_comments`, `pm.issue_assignees`, `review.mr_core`, `review.comments`, `review.diff_comments`, `review.threads`, `review.approval_history`, `review.required_reviewers` | ✅ Yes — Items 26–33, 39–43 in Behavioral table |
| 14 | **CI/CD Rewrite is the Largest Single Effort** | Checks that GitLab CI/CD → GitHub Actions is treated as a full rewrite workstream, not a metadata copy. Covers syntax, execution model, runners, artifacts, caching, services, schedules, triggers, OIDC. | `cicd.pipeline_config`, `cicd.variables_project`, `cicd.variables_group`, `cicd.environments`, `cicd.deployment_approvals`, `cicd.schedules`, `cicd.runners_project`, `cicd.runners_group`, `cicd.runners_shared`, `cicd.artifacts`, `cicd.artifact_retention`, `cicd.cache`, `cicd.services`, `cicd.includes`, `cicd.parent_child`, `cicd.rules`, `cicd.oidc`, `cicd.triggers`, `cicd.matrix` | ✅ Yes — Items 56–74 in Behavioral table |
| 15 | **GitHub Advanced Security (GHAS) Licensing** | Checks that GHAS is purchased and enabled for private/internal repositories before migrating security configurations. Without GHAS: no CodeQL, no secret scanning for private repos, no push protection, no dependency review, no custom secret patterns. | `security.sast`, `security.dependency_scanning`, `security.secret_detection`, `security.secret_custom_patterns`, `security.container_scanning`, `security.dast`, `security.license_scanning` | ✅ Yes — Items 88–95 in Behavioral table |
| 16 | **Group-to-Organization Structural Mapping Must Be Planned First** | Checks that the group→org/team mapping strategy is finalized before migrating any group-scoped resources. This decision cascades to labels, milestones, variables, runners, webhooks, boards, policies. | `org.groups`, `org.subgroups`, `access.group_membership`, `labels.group`, `pm.milestones`, `pm.boards`, `cicd.variables_group`, `cicd.runners_group`, `integrations.webhooks_group`, `org.policies` | ✅ Yes — Items 7–9, 37, 44–46, 53, 58, 63, 103 in Behavioral table |
| 17 | **Package Registry Gaps** | Checks that GitLab's PyPI, Conan, Composer, and Generic package registries have no native GHEC equivalent and require alternative hosting solutions. | `packages.pypi`, `packages.conan`, `packages.composer`, `packages.generic` | ✅ Yes — Items 78–82 in Behavioral table (classified as 🟡 with explicit "no direct equivalent" notes) |
| 18 | **API-Based Timestamp Attribution** | Checks that original `created_at` timestamps for issues, PRs, and comments are preserved either via import-specific API behavior or by embedding original dates in body text as attribution metadata. | `pm.issues`, `pm.issue_comments`, `review.mr_core`, `review.comments`, `review.diff_comments` | ✅ Yes — Items 26, 27, 28, 39, 40 in Behavioral table |
| 19 | **Webhook Payload Breaking Changes** | Checks that all downstream systems consuming GitLab webhook events are updated to handle GHEC webhook payload formats, event names, and signature verification mechanisms. | `integrations.webhooks_project`, `integrations.webhooks_group`, `integrations.webhook_secrets` | ✅ Yes — Items 52–54 in Behavioral table |
| 20 | **Historical Data Preservation Pattern** | Checks that the migration approach distinguishes between content preservation (titles, bodies, comment text) and system metadata preservation (original timestamps, auto-generated events, internal IDs). Establishes the pattern of embedding original metadata as formatted text. | `pm.issues`, `pm.issue_comments`, `review.mr_core`, `review.comments`, `review.approval_history`, `cicd.pipeline_history`, `cicd.deployment_history` | ✅ Yes — Items 26–28, 32, 39–40 in Behavioral table; Items 10–12 in Blockers table |
| 21 | **Environment and Secret Scoping Model Change** | Checks that GitLab's "protected variable" concept is mapped to GHEC's environment-scoped secrets with deployment branch policies, requiring environment creation and branch restriction configuration. | `cicd.protected_variables`, `cicd.masked_variables`, `cicd.file_variables`, `cicd.environments` | ✅ Yes — Items 59, 98–100 in Behavioral table |
| 22 | **Container Registry URL Updates Are Pervasive** | Checks that every reference to `registry.gitlab.com` across Dockerfiles, docker-compose, Kubernetes manifests, Helm charts, CI/CD pipelines, and documentation is updated to `ghcr.io`. | `packages.container_registry` | ✅ Yes — Item 83 in Behavioral table |

---

### Part 3 — Conditions from 🔴 Hard Blockers / Cannot Be Migrated

| # | Condition | What It Checks | Metadata / Attribute(s) | Available in Current Discovery |
|---|---|---|---|---|
| 23 | **"Hard Blocker" is Contextual** | Checks that several items classified as blockers (merge trains, group boards, GitLab Pages, commit discussions, snippets) have functional GHEC equivalents for common cases and should be reclassified to 🟡 if the migration accepts the GHEC model. | `review.merge_trains`, `pm.group_boards`, `repo.pages`, `review.commit_discussions`, `repo.snippets_personal`, `repo.snippets_project` | ✅ Yes — Items 7, 14, 22, 28–29 in Blockers table with explicit reclassification notes |
| 24 | **GitLab Tier Prerequisites** | Checks whether the source GitLab instance is on Free, Premium, or Ultimate tier. Many blocker items (epics, iterations, requirements, test cases, multi-project pipelines, multi-rule approvals, roadmaps, insights, VSA, compliance frameworks) only exist on Premium/Ultimate. | `pm.epics`, `pm.iterations`, `pm.requirements`, `pm.test_cases`, `cicd.multi_project_pipelines`, `review.multi_rule_approvals`, `pm.roadmaps`, `pm.custom_insights`, `pm.value_stream_analytics`, `security.compliance_frameworks` | ✅ Yes — Items 1–4, 8, 15–17, 39–40 in Blockers table |
| 25 | **Historical Runtime Data Cannot Be Migrated** | Checks that pipeline runs, job logs, artifacts, deployment history, and vulnerability findings are runtime-generated data that GHEC does not accept as imports. External archival is the only preservation option. | `cicd.pipeline_history`, `cicd.job_logs_historical`, `cicd.artifacts` (historical), `cicd.deployment_history_full`, `security.vulnerability_mgmt` (historical findings) | ✅ Yes — Items 10–12, 93 in combined tables |
| 26 | **Structural Model Differences Are Not "Fixable"** | Checks that epics, scoped labels, requirements, iterations, and multi-rule approvals are absent from GHEC as first-class object types and can only be approximated via issues + labels + Projects (v2) custom fields. | `pm.epics`, `pm.iterations`, `pm.requirements`, `pm.test_cases`, `labels.scoped`, `review.multi_rule_approvals`, `review.mr_level_approvals` | ✅ Yes — Items 1–6, 39–40 in Blockers table |
| 27 | **Snippet Ownership Model** | Checks that GHEC has no enterprise-scoped snippet concept. Gists belong to individual users on github.com, not the enterprise. Enterprise-owned snippets on GitLab cannot become enterprise-owned assets on GHEC. | `repo.snippets_personal`, `repo.snippets_project`, `repo.snippets_group` | ✅ Yes — Items 19–21 in Blockers table |
| 28 | **Feature Flags, Error Tracking, Incident Management, Service Desk** | Checks that these operational features are absent from GHEC and require migration to dedicated third-party services (LaunchDarkly, Sentry, PagerDuty, Zendesk, etc.). | `cicd.feature_flags`, `integrations.error_tracking`, `integrations.incident_mgmt`, `integrations.service_desk` | ✅ Yes — Items 31–34 in Blockers table |
| 29 | **AI Product Boundaries** | Checks that GitLab Duo and GitHub Copilot are independent products with separate licensing. No AI configuration, prompts, or usage history migrates between them. | `integrations.ai` | ✅ Yes — Item 36 in Blockers table |
| 30 | **CI/CD Job Token Cross-Repository Access** | Checks that GitLab's `CI_JOB_TOKEN` project allowlist model (controlling which projects can access another project's registries/APIs from CI) has no GHEC equivalent. GHEC requires PATs or GitHub App tokens for cross-repo access. | `cicd.job_token_auth` | ✅ Yes — Item 38 in Blockers table |
| 31 | **Repository Mirroring Absence** | Checks that GHEC does not provide native inbound or outbound repository mirroring as a repo setting. All mirroring must be reimplemented via GitHub Actions workflows or third-party tools. | `repo.mirroring_push`, `repo.mirroring_pull`, `repo.mirroring_bidirectional` | ✅ Yes — Items 23–25 in Blockers table |
| 32 | **Instance Configuration (Self-Managed GitLab Source)** | Checks that instance-level settings from self-managed GitLab (LDAP, Kerberos, mail server, feature flags, custom hooks) have no relevance to GHEC as a hosted platform. | `org.instance_config` | ✅ Yes — Item 26 in Blockers table |
| 33 | **PAT and Secret Regeneration is Mandatory** | Checks that no token, secret, or credential migrates from GitLab to GHEC. Every PAT, deploy token, webhook secret, CI/CD secret variable, integration credential, and mirror credential must be regenerated. | `access.pat_migration`, `access.project_tokens`, `access.group_tokens`, `access.deploy_tokens`, `integrations.webhook_secrets`, `cicd.variables_project`, `cicd.variables_group` | ✅ Yes — Item 37 in Blockers table; cross-references Items 12–14, 54, 57–58 in Behavioral table |
| 34 | **User Attribution for Blocker Items** | Checks that workaround recreations of blocker items (epics as parent issues, scoped labels as flat labels, requirements as issues) follow the same user identity mapping challenges as behavioral difference items. | `pm.epics`, `pm.requirements`, `pm.test_cases`, `labels.scoped`, `pm.iterations` | ✅ Yes — Cross-references Condition #13 (User Identity Mapping) and Items 1–6 in Blockers table |

---

## Summary Statistics

| Metric | Count |
|---|---|
| Total Conditions & Assumptions Documented | **34** |
| From Seamless Section (Part 1) | 12 |
| From Behavioral Differences Section (Part 2) | 10 |
| From Hard Blockers Section (Part 3) | 12 |
| Conditions Mapped to Specific Metadata IDs | 34 / 34 (100%) |
| Conditions Available in Current Discovery | 34 / 34 (100%) |
| Unique Metadata/Attributes Referenced by Conditions | **~85 distinct capability IDs** |

---

### Key Takeaway

Every condition documented in the report is **directly traceable** to one or more specific metadata/capability items in the 178-item master inventory. There are **zero orphan conditions** (conditions that don't map to a discovered metadata item) and **zero unconditioned critical attributes** (critical attributes that lack an associated condition or assumption). The conditions collectively serve as the **risk register and prerequisite checklist** for the migration solution's engineering design.
