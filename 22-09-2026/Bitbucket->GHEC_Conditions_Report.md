# Conditions & Assumptions — Mapping to Discovery Inventory

Below is the complete extraction of every condition and assumption stated across all three responses, mapped to the specific metadata items they govern and whether the condition was already captured within the discovery tables.

---

## Legend for "Available in Current Discovery"

| Symbol | Meaning |
|---|---|
| ✅ Yes | Condition was explicitly noted in the relevant discovery table row (Notes/Conditions, Impact, Action Required, or Workaround column) |
| ⚠️ Partial | Condition was mentioned in a table row but the full scope of its impact spans more items than the row covers |
| ❌ No | Condition was stated in the Conditions section but was **not** explicitly surfaced in any discovery table row — represents a gap in the tabular discovery |

---

## Response 1 Conditions (Seamless / Direct)

| # | Condition | What It Checks | Metadata / Attribute(s) Affected | Available in Current Discovery |
|---|---|---|---|---|
| C1.1 | **GHEC Enterprise Policy Alignment** | Whether the GHEC enterprise or organization policy permits the equivalent repository visibility setting (e.g., public repos allowed or blocked) | `repo.visibility.public` | ✅ Yes — noted in Seamless row #4 Notes |
| C1.2 | **Git Protocol Fidelity** | Whether Git object data (commits, trees, blobs, tags, notes) transfers with byte-level integrity via `git push --mirror` | `repo.commits`, `repo.branches`, `repo.tags`, `repo.git_notes`, `repo.git_replace_refs` | ✅ Yes — noted in Seamless rows #10–13, #25, #30–31 |
| C1.3 | **LFS Storage Quotas** | Whether GHEC LFS storage quota (1 GiB base per org) is sufficient for migrated LFS objects | `repo.lfs` | ✅ Yes — noted in Seamless row #13 Notes |
| C1.4 | **Author Attribution on UI** | Whether commit author/committer email addresses match GitHub user accounts for UI avatar/linking | `repo.commit_authors` | ✅ Yes — noted in Seamless row #26 Notes |
| C1.5 | **Repository Naming Constraints** | Whether Bitbucket repo name length (≤128) and character set are compatible with GHEC limits (≤100, restricted chars) | `repo.name`, `repo.slug` | ✅ Yes — noted in Seamless rows #1–2 Notes |
| C1.6 | **Markdown Compatibility** | Whether Bitbucket-flavored Markdown in PR descriptions, comments, wiki, README is compatible with GitHub Flavored Markdown (GFM); checks @-mention syntax, internal link formats, rich-editor macros | `review.pr_description`, `review.pr_comments`, `review.pr_inline_comments`, `pm.issue_comments`, `repo.wiki_content`, `repo.readme` | ⚠️ Partial — noted in Seamless row #36 Notes for PR descriptions, but the broader impact across issues, wiki, and comments is not individually flagged in each of those rows |
| C1.7 | **Timestamps (Repository-Level)** | Whether `created_at` / `updated_at` on GHEC reflect original Bitbucket timestamps or migration time | `repo.created_on`, `repo.updated_on` | ✅ Yes — noted in Seamless rows #8–9 Notes |
| C1.8 | **Empty Repositories** | Whether empty Bitbucket repositories (no commits) can be created empty on GHEC and whether branch-protection settings require at least one branch | `repo.empty` | ✅ Yes — noted in Seamless row #28 Notes |
| C1.9 | **Scope of "Seamless" Definition** | Meta-condition: defines the classification threshold — no data-model transformation, no permission restructuring, no scope remapping, no behavioral adaptation | All 🟢-classified items | ❌ No — this is a classification rule, not a metadata-specific condition; not reflected in any table row |

---

## Response 2 Conditions (Migratable with Changes / Behavioral Differences)

| # | Condition | What It Checks | Metadata / Attribute(s) Affected | Available in Current Discovery |
|---|---|---|---|---|
| C2.1 | **User Identity Mapping** | Whether a comprehensive Bitbucket accountId → GitHub username (or EMU short-name) mapping exists before migration begins; foundational for all actor-attributed objects | `access.users`, `access.user_profile`, `review.pr_comments`, `review.pr_approvals`, `review.pr_reviewers`, `pm.issue_reporter`, `pm.issue_assignee`, `pm.issue_comments`, `meta.original_actor_attribution` | ✅ Yes — covered in Behavioral rows #16, #17 and Blocker rows #10–11 |
| C2.2 | **Target Enterprise & Organization Provisioning** | Whether GHEC enterprise, target organizations, SSO, SCIM, and enterprise policies are provisioned before repository migration begins | `workspace.metadata`, `enterprise.container`, `access.sso`, `access.scim`, `governance.enterprise_policies` | ✅ Yes — covered in Behavioral rows #1, #128–129, #132 |
| C2.3 | **GHAS Licensing** | Whether GitHub Advanced Security is licensed on the target GHEC org/enterprise; gates availability of secret scanning (private repos), code scanning (private repos), and dependency review | `security.secret_scanning`, `security.code_scanning`, `security.dependency_scanning` | ✅ Yes — covered in Behavioral rows #113–115 |
| C2.4 | **Actions Adoption** | Whether the migration strategy commits to translating Bitbucket Pipelines to GitHub Actions (vs. alternative CI approaches) | `cicd.pipelines`, `cicd.workflow_config`, all `cicd.*` items | ✅ Yes — covered in Behavioral row #68 |
| C2.5 | **API Rate Limits** | Whether GHEC API rate limits (5,000 req/hr authenticated; higher with GitHub Apps) are sufficient for bulk migration throughput of issues, PRs, comments, reviews | All API-migrated items: `review.pr_*`, `pm.issue_*`, `pm.issue_comments`, `review.pr_comments`, `review.pr_approvals` | ❌ No — this is an operational/engineering constraint not surfaced in any discovery table row; should be noted for migration tool design |
| C2.6 | **EMU vs Standard GHEC** | Whether the target GHEC uses Enterprise Managed Users (IdP-provisioned, namespaced usernames) or standard GitHub accounts; affects identity mapping strategy, invitation flow, and attribution | `access.emu`, `access.users`, `access.scim`, `access.sso` | ✅ Yes — covered in Behavioral row #129 |
| C2.7 | **Cross-Reference Rewriting** | Whether in-content cross-references (`#123`, `workspace/repo#456`) to Bitbucket issue/PR IDs are rewritten to new GHEC IDs using a mapping table; checks ID counter divergence due to GitHub's shared issue/PR counter | `pm.issue_id`, `pm.issue_links`, `review.pr_description`, `review.pr_comments`, `repo.commits` (commit messages) | ✅ Yes — covered in Behavioral rows #52, #67 |
| C2.8 | **Actor Attribution in Migrated Content** | Whether original author identity is preserved in native GHEC fields or only via body annotations; checks which attribution strategy is chosen (migration bot, per-user impersonation, ghost users) | `meta.original_actor_attribution`, `review.pr_approval_timestamps_native`, `pm.issue_reporter`, `review.pr_comments`, `pm.issue_comments` | ✅ Yes — covered in Blocker rows #10–11 |
| C2.9 | **Timestamp Fidelity** | Whether `created_at` / `updated_at` on migrated PRs, issues, comments reflect original Bitbucket timestamps or migration time; checks if GHEC import API or body-annotation approach is used | All historical items: `review.pr_*`, `pm.issue_*`, `pm.issue_comments`, `review.pr_comments`, `review.pr_approvals`, `cicd.deployment_history` | ⚠️ Partial — mentioned in Behavioral rows #34, #51, #61 Notes but the full cross-cutting impact is not flagged on every affected row |
| C2.10 | **Webhook Payload Structure** | Whether downstream webhook consumers are rewritten to parse GHEC's payload format (different field names, event catalog, HMAC-SHA-256 signature) instead of Bitbucket's | `integrations.webhooks.repo`, `integrations.webhooks.workspace`, `integrations.webhook_secrets` | ✅ Yes — covered in Behavioral rows #91–93 |
| C2.11 | **CI/CD Pipeline Rewrite** | Whether every `bitbucket-pipelines.yml` is translated to GitHub Actions workflow YAML; checks for converter tooling or manual rewrite | `cicd.pipelines`, `cicd.pipeline_steps`, `cicd.pipeline_parallel`, `cicd.pipeline_stages`, all `cicd.pipeline_triggers.*` | ✅ Yes — covered in Behavioral row #68 |
| C2.12 | **Historical Data Preservability Matrix** | Cross-cutting check: for each historical data type (Git history, PR content, comments, approvals, wiki, pipeline runs, deployments, audit logs, webhook deliveries, watchers), whether data is fully preservable, partially preservable, or not preservable natively | All items with historical data dimension | ⚠️ Partial — the matrix was presented in the Conditions section but individual rows in the tables do not all explicitly call out the historical preservability dimension |
| C2.13 | **Scope Mapping (Workspace → Org, Project → Team+Topic)** | Whether the organizational hierarchy mapping is correctly applied: Bitbucket Workspace → GHEC Org, Bitbucket Project → GHEC Team + Custom Property | `workspace.metadata`, `project.metadata`, `project.permissions`, `project.repositories` | ✅ Yes — covered in Behavioral rows #1–10 |

---

## Response 3 Conditions (Hard Blockers)

| # | Condition | What It Checks | Metadata / Attribute(s) Affected | Available in Current Discovery |
|---|---|---|---|---|
| C3.1 | **Historical vs. Ongoing Capability Distinction** | Whether the blocker applies to historical runtime data only (not injectable) while the ongoing capability is achievable via 🟡 reconfiguration | All 🔴 items: `cicd.pipeline_run_history`, `cicd.deployment_history_native`, `security.audit_log`, `integrations.webhook_delivery_history` | ✅ Yes — explicitly stated in Blocker section intro and per-row Impact columns |
| C3.2 | **External Cold Storage as Standard Compromise** | Whether an external archive (S3, SIEM, archive DB) is provisioned to store blocker-class historical data that cannot be natively imported into GHEC | `cicd.pipeline_run_history`, `cicd.pipeline_step_logs`, `cicd.test_reports`, `cicd.deployment_history_native`, `security.audit_log`, `security.user_access_log`, `integrations.webhook_delivery_history` | ✅ Yes — covered in Workaround column of Blocker rows #1–3, #8, #13, #15 |
| C3.3 | **Actor Attribution Fidelity is a Fundamental Public-API Limitation** | Whether the GHEC public REST/GraphQL API permits setting arbitrary author identity and historical timestamps on created objects (it does not — API records the acting principal) | `meta.original_actor_attribution`, `review.pr_approval_timestamps_native` | ✅ Yes — covered in Blocker rows #10–11 |
| C3.4 | **Bitbucket Pipes Ecosystem Requires Case-by-Case Mapping** | Whether each `pipe:` reference in `bitbucket-pipelines.yml` has been individually evaluated and mapped to an equivalent GitHub Action | `cicd.pipes` | ✅ Yes — covered in Blocker row #5 |
| C3.5 | **Jira Historical Links Are a Cross-Platform Blocker** | Whether historical Jira Development Panel entries referencing Bitbucket branches/commits/PRs are rewritten to GHEC URLs via Jira-side automation | `integrations.jira_dev_panel_history` | ✅ Yes — covered in Blocker row #17 |
| C3.6 | **Downloads URL Consumer Impact Requires Migration Communication** | Whether external consumers of Bitbucket Downloads URLs (installers, package managers, Homebrew formulas, deployment scripts) are identified and notified of URL change | `repo.downloads_urls` | ✅ Yes — covered in Blocker row #16 |
| C3.7 | **Redirect / URL Rewriting Requires External Infrastructure** | Whether a durable redirect service or CDN is deployed to translate Bitbucket URL patterns to GHEC equivalents post-decommissioning | All URL-dependent items: `repo.https_url`, `repo.ssh_url`, `repo.downloads_urls`, `review.pr_*` (PR page URLs), `pm.issue_*` (issue page URLs), `repo.wiki_content` (wiki page URLs), `cicd.pipeline_run_history` (pipeline run URLs) | ❌ No — this is a cross-cutting infrastructure requirement not surfaced as a specific row or note in any discovery table |

---

## Summary of Gaps (Conditions Not Fully Reflected in Discovery Tables)

| Gap # | Condition | Why It's a Gap | Recommendation |
|---|---|---|---|
| G1 | **C1.6 — Markdown Compatibility** | Only flagged on `review.pr_description`; the same @-mention syntax and link-format transformation applies to `pm.issue_comments`, `pm.issue_description`, `review.pr_comments`, `repo.wiki_content`, `repo.readme` | Add a note to each affected Behavioral row that markdown content requires @-mention and link rewriting |
| G2 | **C2.5 — API Rate Limits** | Operational constraint affecting all API-migrated items but not surfaced in any table row | Add to migration tool design requirements; not a metadata parity issue per se but a migration feasibility constraint |
| G3 | **C2.9 — Timestamp Fidelity** | Mentioned on a few rows but the cross-cutting nature (affects every historical object) is not uniformly flagged | Consider adding a "Historical Timestamp" column to the Behavioral table or a global note |
| G4 | **C2.12 — Historical Data Preservability Matrix** | Presented as a summary table in Conditions but not embedded in the discovery tables | The matrix should be treated as a cross-reference overlay on the discovery tables |
| G5 | **C3.7 — Redirect / URL Rewriting Infrastructure** | Cross-cutting infrastructure requirement not tied to any single metadata row | Should be captured as a migration-project-level infrastructure prerequisite, not a per-metadata condition |
| G6 | **C1.9 — Scope of "Seamless" Definition** | Classification meta-rule, not a metadata condition | No action needed; this is a report methodology note, not a discovery gap |

---

## Quick-Reference: Condition → Discovery Row Cross-Index

| Condition ID | Primary Discovery Rows |
|---|---|
| C1.1 | 🟢 #4 |
| C1.2 | 🟢 #10–13, #25, #30–31 |
| C1.3 | 🟢 #13 |
| C1.4 | 🟢 #26 |
| C1.5 | 🟢 #1–2 |
| C1.6 | 🟢 #36; also 🟡 #34, #51, #61, #103 |
| C1.7 | 🟢 #8–9 |
| C1.8 | 🟢 #28 |
| C2.1 | 🟡 #16–17; 🔴 #10–11 |
| C2.2 | 🟡 #1, #128–129, #132 |
| C2.3 | 🟡 #113–115 |
| C2.4 | 🟡 #68 |
| C2.5 | *(no row — operational)* |
| C2.6 | 🟡 #129 |
| C2.7 | 🟡 #52, #67 |
| C2.8 | 🔴 #10–11 |
| C2.9 | 🟡 #34, #51, #61; 🔴 #10 |
| C2.10 | 🟡 #91–93 |
| C2.11 | 🟡 #68 |
| C2.12 | *(cross-cutting — all rows with historical data)* |
| C2.13 | 🟡 #1–10 |
| C3.1 | 🔴 all rows |
| C3.2 | 🔴 #1–3, #8, #13, #15 |
| C3.3 | 🔴 #10–11 |
| C3.4 | 🔴 #5 |
| C3.5 | 🔴 #17 |
| C3.6 | 🔴 #16 |
| C3.7 | *(cross-cutting — all URL-dependent items)* |
