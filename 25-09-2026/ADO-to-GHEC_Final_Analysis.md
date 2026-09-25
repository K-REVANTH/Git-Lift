# ADO to GHEC Policy Analysis

The table below provides a complete extraction and documentation of every policy flag from `ADO-to-GHEC_policy.json`, preserving the exact original order, conditions, thresholds, and metadata references as defined in the policy JSON. No discovery availability is assessed, as there is no Discovery CSV for the ADO → GHEC migration path.

**Policy source:** `ADO-to-GHEC_policy.json`
**Total flags:** 96
**Migration path:** Azure DevOps Services (ADO) → GitHub Enterprise Cloud (GHEC)

---

| Flag | Conditions | What it checks | Metadata or Attribute |
| --- | --- | --- | --- |
| `sizeS` | `total_repo_size_bytes < 1048576` | Classifies repositories with total size under 1 MB into the small size bucket. | `total_repo_size_bytes` |
| `sizeM` | `total_repo_size_bytes >= 1048576`<br>`total_repo_size_bytes < 1073741824` | Classifies repositories with total size between 1 MB and 1 GB into the medium size bucket. | `total_repo_size_bytes` |
| `sizeL` | `total_repo_size_bytes >= 1073741824`<br>`total_repo_size_bytes < 5368709120` | Classifies repositories with total size between 1 GB and 5 GB into the large size bucket. | `total_repo_size_bytes` |
| `sizeXL` | `total_repo_size_bytes >= 5368709120` | Classifies repositories with total size 5 GB or above into the extra-large size bucket. | `total_repo_size_bytes` |
| `repo_size_exceeds_ghec_recommendation` | `total_repo_size_bytes > 5368709120` | Checks whether the repository total size exceeds the 5 GB GHEC recommended limit. | `total_repo_size_bytes` |
| `repo_size_exceeds_ghec_hard_limit` | `total_repo_size_bytes > 10737418240` | Checks whether the repository total size exceeds the 10 GB GHEC hard limit. | `total_repo_size_bytes` |
| `lfs_storage_exceeds_default_quota` | `lfs_size_bytes > 1073741824` | Checks whether LFS storage exceeds the 1 GB default GHEC quota. | `lfs_size_bytes` |
| `lfs_storage_large` | `lfs_size_bytes > 5368709120` | Checks whether LFS storage exceeds 5 GB. | `lfs_size_bytes` |
| `lfs_objects_present` | `lfs_file_count > 0` | Checks whether the repository contains any LFS-tracked files. | `lfs_file_count` |
| `lfs_object_exceeds_ghec_file_limit` | `exists in inventory_lfs`<br>`join repo_id`<br>`match size > 2147483648` | Checks whether any individual LFS object exceeds the 2 GB GHEC per-file LFS limit. | `inventory_lfs`<br>`repo_id`<br>`size` |
| `lfs_object_exceeds_100mb_non_lfs_limit` | `exists in inventory_lfs`<br>`join repo_id`<br>`match size > 104857600` | Checks whether any individual LFS object exceeds the 100 MB non-LFS file push limit. | `inventory_lfs`<br>`repo_id`<br>`size` |
| `has_submodules_url_remap_needed` | `submodule_count > 0` | Checks whether the repository contains submodules that may require URL remapping. | `submodule_count` |
| `high_submodule_count` | `submodule_count > 10` | Checks whether the repository has more than 10 submodules. | `submodule_count` |
| `submodule_references_ado_url` | `exists in inventory_submodules`<br>`join repo_id`<br>`match url contains "dev.azure.com"` | Checks whether any submodule URL references dev.azure.com and requires remapping. | `inventory_submodules`<br>`repo_id`<br>`url` |
| `submodule_references_visualstudio_url` | `exists in inventory_submodules`<br>`join repo_id`<br>`match url contains "visualstudio.com"` | Checks whether any submodule URL references visualstudio.com and requires remapping. | `inventory_submodules`<br>`repo_id`<br>`url` |
| `is_fork_requires_lineage_setup` | `is_fork = true` | Checks whether the repository is a fork requiring fork-lineage setup on GHEC. | `is_fork` |
| `is_archived_migration_candidate` | `is_archived = true` | Checks whether the repository is archived. | `is_archived` |
| `is_empty_repo` | `is_empty = true` | Checks whether the repository is empty (contains no commits or content). | `is_empty` |
| `private_repo_identity_mapping_required` | `is_private = true` | Checks whether the repository is private and requires identity mapping for access. | `is_private` |
| `public_repo_enterprise_policy_check` | `is_private = false` | Checks whether the repository is public and requires enterprise policy verification. | `is_private` |
| `no_branch_protection_governance_gap` | `protected_branch_count = 0`<br>`branch_count > 0` | Checks whether a repository has branches but no branch protection configured. | `protected_branch_count`<br>`branch_count` |
| `has_branch_protection_ruleset_migration` | `protected_branch_count > 0` | Checks whether the repository has protected branches requiring ruleset migration. | `protected_branch_count` |
| `multiple_protected_branches_ruleset_migration` | `protected_branch_count > 1` | Checks whether the repository has more than one protected branch requiring multi-ruleset migration. | `protected_branch_count` |
| `high_branch_count_complexity` | `branch_count > 500` | Checks whether the repository has more than 500 branches. | `branch_count` |
| `very_high_branch_count_risk` | `branch_count > 5000` | Checks whether the repository has more than 5,000 branches. | `branch_count` |
| `has_protected_tags` | `protected_tag_count > 0` | Checks whether the repository has protected tags. | `protected_tag_count` |
| `has_codeowner_approval_required` | `exists in inventory_protected_branches`<br>`join repo_id`<br>`match code_owner_approval_required = true` | Checks whether any protected branch requires code-owner approval. | `inventory_protected_branches`<br>`repo_id`<br>`code_owner_approval_required` |
| `force_push_allowed_on_protected_branch` | `exists in inventory_protected_branches`<br>`join repo_id`<br>`match allow_force_push = true` | Checks whether force-push is allowed on any protected branch. | `inventory_protected_branches`<br>`repo_id`<br>`allow_force_push` |
| `has_open_prs_requiring_migration` | `exists in inventory_pull_requests`<br>`join repo_id`<br>`match state = "open"` | Checks whether the repository has at least one open pull request. | `inventory_pull_requests`<br>`repo_id`<br>`state` |
| `has_draft_prs` | `exists in inventory_pull_requests`<br>`join repo_id`<br>`match is_draft = true` | Checks whether the repository has draft pull requests. | `inventory_pull_requests`<br>`repo_id`<br>`is_draft` |
| `pr_volume_high` | `pr_count > 1000` | Checks whether the repository has more than 1,000 pull requests. | `pr_count` |
| `pr_volume_very_high` | `pr_count > 10000` | Checks whether the repository has more than 10,000 pull requests. | `pr_count` |
| `pr_comment_volume_high` | `pr_comment_count > 5000` | Checks whether the repository has more than 5,000 PR comments. | `pr_comment_count` |
| `has_large_diff_prs` | `exists in inventory_pull_requests`<br>`join repo_id`<br>`match changed_files > 500` | Checks whether any pull request has more than 500 changed files. | `inventory_pull_requests`<br>`repo_id`<br>`changed_files` |
| `has_unresolved_pr_review_comments` | `exists in inventory_pr_comments`<br>`join repo_id`<br>`match is_resolved = false` | Checks whether the repository has unresolved PR review comments. | `inventory_pr_comments`<br>`repo_id`<br>`is_resolved` |
| `issue_volume_high` | `issue_count > 5000` | Checks whether the repository has more than 5,000 issues. | `issue_count` |
| `issue_volume_very_high` | `issue_count > 50000` | Checks whether the repository has more than 50,000 issues. | `issue_count` |
| `has_open_issues_requiring_migration` | `exists in inventory_issues`<br>`join repo_id`<br>`match state = "open"` | Checks whether the repository has at least one open issue. | `inventory_issues`<br>`repo_id`<br>`state` |
| `has_open_milestones` | `exists in inventory_milestones`<br>`join repo_id`<br>`match state = "open"` | Checks whether the repository has at least one open milestone. | `inventory_milestones`<br>`repo_id`<br>`state` |
| `has_overdue_milestones` | `exists in inventory_milestones`<br>`join repo_id`<br>`match state = "open"`<br>`match due_date < "2026-01-01T00:00:00Z"` | Checks whether the repository has open milestones with a due date before 2026-01-01. | `inventory_milestones`<br>`repo_id`<br>`state`<br>`due_date` |
| `high_label_count_migration_effort` | `label_count > 50` | Checks whether the repository has more than 50 labels. | `label_count` |
| `has_releases_with_assets` | `exists in inventory_releases`<br>`join repo_id`<br>`match asset_count > 0` | Checks whether any release has binary/file assets attached. | `inventory_releases`<br>`repo_id`<br>`asset_count` |
| `has_prerelease_releases` | `exists in inventory_releases`<br>`join repo_id`<br>`match is_prerelease = true` | Checks whether the repository has prerelease releases. | `inventory_releases`<br>`repo_id`<br>`is_prerelease` |
| `has_draft_releases` | `exists in inventory_releases`<br>`join repo_id`<br>`match is_draft = true` | Checks whether the repository has draft releases. | `inventory_releases`<br>`repo_id`<br>`is_draft` |
| `high_release_count` | `release_count > 100` | Checks whether the repository has more than 100 releases. | `release_count` |
| `has_external_collaborators` | `exists in inventory_users`<br>`join repo_id`<br>`match is_external = true` | Checks whether the repository has external collaborators. | `inventory_users`<br>`repo_id`<br>`is_external` |
| `has_bot_users` | `exists in inventory_users`<br>`join repo_id`<br>`match is_bot = true` | Checks whether the repository has bot users. | `inventory_users`<br>`repo_id`<br>`is_bot` |
| `high_commit_count` | `commit_count > 50000` | Checks whether the repository has more than 50,000 commits. | `commit_count` |
| `very_high_commit_count` | `commit_count > 500000` | Checks whether the repository has more than 500,000 commits. | `commit_count` |
| `stale_repo_no_recent_push` | `pushed_at < "2024-01-01T00:00:00Z"`<br>`is_archived = false` | Checks for non-archived repositories that have not been pushed to since before 2024-01-01. | `pushed_at`<br>`is_archived` |
| `recently_active_repo` | `pushed_at >= "2025-01-01T00:00:00Z"`<br>`is_archived = false` | Checks for non-archived repositories with a push on or after 2025-01-01. | `pushed_at`<br>`is_archived` |
| `never_pushed` | `pushed_at is_null` | Checks whether the repository has never been pushed to. | `pushed_at` |
| `belongs_to_large_namespace` | `exists in inventory_namespaces`<br>`join repo_id`<br>`match repo_count > 100` | Checks whether the repository belongs to a namespace with more than 100 repositories. | `inventory_namespaces`<br>`repo_id`<br>`repo_count` |
| `belongs_to_very_large_namespace` | `exists in inventory_namespaces`<br>`join repo_id`<br>`match repo_count > 500` | Checks whether the repository belongs to a namespace with more than 500 repositories. | `inventory_namespaces`<br>`repo_id`<br>`repo_count` |
| `tfvc_repo_requires_git_conversion` | `source_vcs_type = "Tfvc"` | Checks whether the repository uses TFVC version control and requires conversion to Git. | `source_vcs_type` |
| `has_yaml_pipelines` | `yaml_pipeline_count > 0` | Checks whether the repository has YAML-based Azure Pipelines. | `yaml_pipeline_count` |
| `has_classic_build_pipelines` | `classic_build_pipeline_count > 0` | Checks whether the repository has classic build pipelines. | `classic_build_pipeline_count` |
| `has_classic_release_pipelines` | `classic_release_pipeline_count > 0` | Checks whether the repository has classic release pipelines. | `classic_release_pipeline_count` |
| `high_pipeline_count` | `pipeline_count > 20` | Checks whether the repository has more than 20 pipelines. | `pipeline_count` |
| `has_service_connections` | `service_connection_count > 0` | Checks whether the repository/project has service connections. | `service_connection_count` |
| `has_variable_groups` | `variable_group_count > 0` | Checks whether the repository/project has variable groups. | `variable_group_count` |
| `has_secure_files` | `secure_file_count > 0` | Checks whether the repository/project has secure files. | `secure_file_count` |
| `has_pipeline_environments` | `environment_count > 0` | Checks whether the repository/project has pipeline environments. | `environment_count` |
| `has_deployment_groups` | `deployment_group_count > 0` | Checks whether the repository/project has deployment groups. | `deployment_group_count` |
| `has_work_items` | `work_item_count > 0` | Checks whether the project has work items. | `work_item_count` |
| `high_work_item_count` | `work_item_count > 10000` | Checks whether the project has more than 10,000 work items. | `work_item_count` |
| `very_high_work_item_count` | `work_item_count > 100000` | Checks whether the project has more than 100,000 work items. | `work_item_count` |
| `has_custom_work_item_types` | `custom_work_item_type_count > 0` | Checks whether the project has custom work item types. | `custom_work_item_type_count` |
| `has_area_paths` | `area_path_count > 1` | Checks whether the project has more than one area path. | `area_path_count` |
| `has_deep_area_path_hierarchy` | `area_path_depth > 3` | Checks whether the project has area path hierarchy deeper than 3 levels. | `area_path_depth` |
| `has_iteration_paths` | `iteration_path_count > 1` | Checks whether the project has more than one iteration path. | `iteration_path_count` |
| `has_test_plans` | `test_plan_count > 0` | Checks whether the project has Azure Test Plans. | `test_plan_count` |
| `has_test_suites` | `test_suite_count > 0` | Checks whether the project has test suites. | `test_suite_count` |
| `has_manual_test_cases` | `manual_test_case_count > 0` | Checks whether the project has manual test cases. | `manual_test_case_count` |
| `has_artifact_feeds` | `artifact_feed_count > 0` | Checks whether the project/organization has Azure Artifacts feeds. | `artifact_feed_count` |
| `has_npm_packages` | `npm_package_count > 0` | Checks whether the project has npm packages in artifact feeds. | `npm_package_count` |
| `has_nuget_packages` | `nuget_package_count > 0` | Checks whether the project has NuGet packages in artifact feeds. | `nuget_package_count` |
| `has_maven_packages` | `maven_package_count > 0` | Checks whether the project has Maven packages in artifact feeds. | `maven_package_count` |
| `has_python_packages_no_ghec_native_support` | `python_package_count > 0` | Checks whether the project has Python packages (GHEC does not natively support PyPI). | `python_package_count` |
| `has_universal_packages_no_ghec_native_support` | `universal_package_count > 0` | Checks whether the project has Universal Packages (GHEC has no native support). | `universal_package_count` |
| `has_container_images` | `container_image_count > 0` | Checks whether the project has container images. | `container_image_count` |
| `has_wiki` | `wiki_count > 0` | Checks whether the project has wikis. | `wiki_count` |
| `has_code_wiki` | `code_wiki_count > 0` | Checks whether the project has code wikis (published from code repo folder). | `code_wiki_count` |
| `has_dashboards` | `dashboard_count > 0` | Checks whether the project has dashboards. | `dashboard_count` |
| `has_extensions_installed` | `extension_count > 0` | Checks whether the organization has extensions installed. | `extension_count` |
| `has_service_hooks` | `service_hook_count > 0` | Checks whether the project has service hooks configured. | `service_hook_count` |
| `has_custom_process_template` | `process_template_type != "Basic"` | Checks whether the project uses a non-Basic process template (Agile, Scrum, CMMI, or custom inherited). | `process_template_type` |
| `has_inherited_process_customizations` | `inherited_process_customization_count > 0` | Checks whether the project's inherited process has customizations (custom fields, states, rules, WITs). | `inherited_process_customization_count` |
| `has_ghas_enabled` | `ghas_enabled = true` | Checks whether GitHub Advanced Security for Azure DevOps (GHAzDO) is enabled. | `ghas_enabled` |
| `has_keyvault_linked_variable_groups` | `keyvault_linked_variable_group_count > 0` | Checks whether the project has variable groups linked to Azure Key Vault. | `keyvault_linked_variable_group_count` |
| `has_path_based_permissions` | `path_scoped_permission_count > 0` | Checks whether the repository has path-scoped (sub-folder) permissions. | `path_scoped_permission_count` |
| `has_deny_permissions` | `deny_permission_count > 0` | Checks whether the repository/project uses explicit deny permissions. | `deny_permission_count` |
| `has_custom_security_groups` | `custom_security_group_count > 0` | Checks whether the project has custom security groups. | `custom_security_group_count` |
| `migration_risk_high` | `total_repo_size_bytes > 10737418240`<br>`lfs_size_bytes > 5368709120`<br>`branch_count > 5000`<br>`submodule_count > 10`<br>`pr_count > 10000`<br>`issue_count > 10000`<br>`commit_count > 500000`<br>`is_archived = true` | Flags repositories as high migration risk if any one of the defined high-risk conditions is met (OR logic). | `total_repo_size_bytes`<br>`lfs_size_bytes`<br>`branch_count`<br>`submodule_count`<br>`pr_count`<br>`issue_count`<br>`commit_count`<br>`is_archived` |
| `migration_risk_medium` | `total_repo_size_bytes > 1073741824`<br>`total_repo_size_bytes <= 10737418240`<br>`branch_count <= 5000`<br>`is_archived = false` | Classifies repositories within the medium migration-risk range when all bounded conditions are satisfied (AND logic). | `total_repo_size_bytes`<br>`branch_count`<br>`is_archived` |
| `migration_risk_low` | `total_repo_size_bytes <= 1073741824`<br>`branch_count <= 500`<br>`lfs_file_count = 0`<br>`submodule_count = 0`<br>`is_fork = false`<br>`is_archived = false` | Classifies repositories as low migration risk when all defined low-risk conditions are satisfied (AND logic). | `total_repo_size_bytes`<br>`branch_count`<br>`lfs_file_count`<br>`submodule_count`<br>`is_fork`<br>`is_archived` |

---

## Metadata Summary

The policy references the following distinct metadata fields and inventory tables:

### Repository-Level Fields

| Field | Type | Used By |
| --- | --- | --- |
| `total_repo_size_bytes` | BIGINT | `sizeS`, `sizeM`, `sizeL`, `sizeXL`, `repo_size_exceeds_ghec_recommendation`, `repo_size_exceeds_ghec_hard_limit`, `migration_risk_high`, `migration_risk_medium`, `migration_risk_low` |
| `lfs_size_bytes` | BIGINT | `lfs_storage_exceeds_default_quota`, `lfs_storage_large`, `migration_risk_high` |
| `lfs_file_count` | INTEGER | `lfs_objects_present`, `migration_risk_low` |
| `submodule_count` | INTEGER | `has_submodules_url_remap_needed`, `high_submodule_count`, `migration_risk_high`, `migration_risk_low` |
| `is_fork` | BOOLEAN | `is_fork_requires_lineage_setup`, `migration_risk_low` |
| `is_archived` | BOOLEAN | `is_archived_migration_candidate`, `stale_repo_no_recent_push`, `recently_active_repo`, `migration_risk_high`, `migration_risk_medium`, `migration_risk_low` |
| `is_empty` | BOOLEAN | `is_empty_repo` |
| `is_private` | BOOLEAN | `private_repo_identity_mapping_required`, `public_repo_enterprise_policy_check` |
| `protected_branch_count` | INTEGER | `no_branch_protection_governance_gap`, `has_branch_protection_ruleset_migration`, `multiple_protected_branches_ruleset_migration` |
| `branch_count` | INTEGER | `no_branch_protection_governance_gap`, `high_branch_count_complexity`, `very_high_branch_count_risk`, `migration_risk_high`, `migration_risk_medium`, `migration_risk_low` |
| `protected_tag_count` | INTEGER | `has_protected_tags` |
| `pr_count` | INTEGER | `pr_volume_high`, `pr_volume_very_high`, `migration_risk_high` |
| `pr_comment_count` | INTEGER | `pr_comment_volume_high` |
| `issue_count` | INTEGER | `issue_volume_high`, `issue_volume_very_high`, `migration_risk_high` |
| `label_count` | INTEGER | `high_label_count_migration_effort` |
| `release_count` | INTEGER | `high_release_count` |
| `commit_count` | INTEGER | `high_commit_count`, `very_high_commit_count`, `migration_risk_high` |
| `pushed_at` | TIMESTAMPTZ | `stale_repo_no_recent_push`, `recently_active_repo`, `never_pushed` |

### ADO-Specific Generated Fields

| Field | Type | Used By |
| --- | --- | --- |
| `source_vcs_type` | TEXT | `tfvc_repo_requires_git_conversion` |
| `yaml_pipeline_count` | INTEGER | `has_yaml_pipelines` |
| `classic_build_pipeline_count` | INTEGER | `has_classic_build_pipelines` |
| `classic_release_pipeline_count` | INTEGER | `has_classic_release_pipelines` |
| `pipeline_count` | INTEGER | `high_pipeline_count` |
| `service_connection_count` | INTEGER | `has_service_connections` |
| `variable_group_count` | INTEGER | `has_variable_groups` |
| `secure_file_count` | INTEGER | `has_secure_files` |
| `environment_count` | INTEGER | `has_pipeline_environments` |
| `deployment_group_count` | INTEGER | `has_deployment_groups` |
| `work_item_count` | INTEGER | `has_work_items`, `high_work_item_count`, `very_high_work_item_count` |
| `custom_work_item_type_count` | INTEGER | `has_custom_work_item_types` |
| `area_path_count` | INTEGER | `has_area_paths` |
| `area_path_depth` | INTEGER | `has_deep_area_path_hierarchy` |
| `iteration_path_count` | INTEGER | `has_iteration_paths` |
| `test_plan_count` | INTEGER | `has_test_plans` |
| `test_suite_count` | INTEGER | `has_test_suites` |
| `manual_test_case_count` | INTEGER | `has_manual_test_cases` |
| `artifact_feed_count` | INTEGER | `has_artifact_feeds` |
| `npm_package_count` | INTEGER | `has_npm_packages` |
| `nuget_package_count` | INTEGER | `has_nuget_packages` |
| `maven_package_count` | INTEGER | `has_maven_packages` |
| `python_package_count` | INTEGER | `has_python_packages_no_ghec_native_support` |
| `universal_package_count` | INTEGER | `has_universal_packages_no_ghec_native_support` |
| `container_image_count` | INTEGER | `has_container_images` |
| `wiki_count` | INTEGER | `has_wiki` |
| `code_wiki_count` | INTEGER | `has_code_wiki` |
| `dashboard_count` | INTEGER | `has_dashboards` |
| `extension_count` | INTEGER | `has_extensions_installed` |
| `service_hook_count` | INTEGER | `has_service_hooks` |
| `process_template_type` | TEXT | `has_custom_process_template` |
| `inherited_process_customization_count` | INTEGER | `has_inherited_process_customizations` |
| `ghas_enabled` | BOOLEAN | `has_ghas_enabled` |
| `keyvault_linked_variable_group_count` | INTEGER | `has_keyvault_linked_variable_groups` |
| `path_scoped_permission_count` | INTEGER | `has_path_based_permissions` |
| `deny_permission_count` | INTEGER | `has_deny_permissions` |
| `custom_security_group_count` | INTEGER | `has_custom_security_groups` |

### Inventory / Subquery Tables

| Table | Join Key | Fields Referenced | Used By |
| --- | --- | --- | --- |
| `inventory_lfs` | `repo_id` | `size` | `lfs_object_exceeds_ghec_file_limit`, `lfs_object_exceeds_100mb_non_lfs_limit` |
| `inventory_submodules` | `repo_id` | `url` | `submodule_references_ado_url`, `submodule_references_visualstudio_url` |
| `inventory_protected_branches` | `repo_id` | `code_owner_approval_required`, `allow_force_push` | `has_codeowner_approval_required`, `force_push_allowed_on_protected_branch` |
| `inventory_pull_requests` | `repo_id` | `state`, `is_draft`, `changed_files` | `has_open_prs_requiring_migration`, `has_draft_prs`, `has_large_diff_prs` |
| `inventory_pr_comments` | `repo_id` | `is_resolved` | `has_unresolved_pr_review_comments` |
| `inventory_issues` | `repo_id` | `state` | `has_open_issues_requiring_migration` |
| `inventory_milestones` | `repo_id` | `state`, `due_date` | `has_open_milestones`, `has_overdue_milestones` |
| `inventory_releases` | `repo_id` | `asset_count`, `is_prerelease`, `is_draft` | `has_releases_with_assets`, `has_prerelease_releases`, `has_draft_releases` |
| `inventory_users` | `repo_id` | `is_external`, `is_bot` | `has_external_collaborators`, `has_bot_users` |
| `inventory_namespaces` | `repo_id` | `repo_count` | `belongs_to_large_namespace`, `belongs_to_very_large_namespace` |

---

## Policy Statistics

| Metric | Value |
| --- | --- |
| Total policy flags | 96 |
| Flags using standard repository fields | 55 |
| Flags using ADO-specific generated fields | 30 |
| Flags using inventory subqueries | 21 |
| Flags with single condition | 82 |
| Flags with multiple conditions (AND logic) | 10 |
| Flags with multiple conditions (OR logic) | 4 |
| Distinct standard repository fields referenced | 17 |
| Distinct ADO-specific generated fields referenced | 37 |
| Distinct inventory tables referenced | 10 |
| Distinct inventory match fields referenced | 12 |

---

## Reference: ADO-to-GHEC_policy.json

```json
{
  "categories": [
    {
      "flag": "sizeS",
      "logic": "AND",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "lt", "value": 1048576 }
      ]
    },
    {
      "flag": "sizeM",
      "logic": "AND",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "gte", "value": 1048576 },
        { "field": "total_repo_size_bytes", "op": "lt", "value": 1073741824 }
      ]
    },
    {
      "flag": "sizeL",
      "logic": "AND",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "gte", "value": 1073741824 },
        { "field": "total_repo_size_bytes", "op": "lt", "value": 5368709120 }
      ]
    },
    {
      "flag": "sizeXL",
      "logic": "AND",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "gte", "value": 5368709120 }
      ]
    },
    {
      "flag": "repo_size_exceeds_ghec_recommendation",
      "logic": "OR",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "gt", "value": 5368709120 }
      ]
    },
    {
      "flag": "repo_size_exceeds_ghec_hard_limit",
      "logic": "OR",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "gt", "value": 10737418240 }
      ]
    },
    {
      "flag": "lfs_storage_exceeds_default_quota",
      "logic": "OR",
      "conditions": [
        { "field": "lfs_size_bytes", "op": "gt", "value": 1073741824 }
      ]
    },
    {
      "flag": "lfs_storage_large",
      "logic": "OR",
      "conditions": [
        { "field": "lfs_size_bytes", "op": "gt", "value": 5368709120 }
      ]
    },
    {
      "flag": "lfs_objects_present",
      "logic": "OR",
      "conditions": [
        { "field": "lfs_file_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "lfs_object_exceeds_ghec_file_limit",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_lfs",
          "join_key": "repo_id",
          "match": [
            { "field": "size", "op": "gt", "value": 2147483648 }
          ]
        }
      ]
    },
    {
      "flag": "lfs_object_exceeds_100mb_non_lfs_limit",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_lfs",
          "join_key": "repo_id",
          "match": [
            { "field": "size", "op": "gt", "value": 104857600 }
          ]
        }
      ]
    },
    {
      "flag": "has_submodules_url_remap_needed",
      "logic": "OR",
      "conditions": [
        { "field": "submodule_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "high_submodule_count",
      "logic": "OR",
      "conditions": [
        { "field": "submodule_count", "op": "gt", "value": 10 }
      ]
    },
    {
      "flag": "submodule_references_ado_url",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_submodules",
          "join_key": "repo_id",
          "match": [
            { "field": "url", "op": "contains", "value": "dev.azure.com" }
          ]
        }
      ]
    },
    {
      "flag": "submodule_references_visualstudio_url",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_submodules",
          "join_key": "repo_id",
          "match": [
            { "field": "url", "op": "contains", "value": "visualstudio.com" }
          ]
        }
      ]
    },
    {
      "flag": "is_fork_requires_lineage_setup",
      "logic": "OR",
      "conditions": [
        { "field": "is_fork", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "is_archived_migration_candidate",
      "logic": "OR",
      "conditions": [
        { "field": "is_archived", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "is_empty_repo",
      "logic": "OR",
      "conditions": [
        { "field": "is_empty", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "private_repo_identity_mapping_required",
      "logic": "OR",
      "conditions": [
        { "field": "is_private", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "public_repo_enterprise_policy_check",
      "logic": "OR",
      "conditions": [
        { "field": "is_private", "op": "eq", "value": false }
      ]
    },
    {
      "flag": "no_branch_protection_governance_gap",
      "logic": "AND",
      "conditions": [
        { "field": "protected_branch_count", "op": "eq", "value": 0 },
        { "field": "branch_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_branch_protection_ruleset_migration",
      "logic": "OR",
      "conditions": [
        { "field": "protected_branch_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "multiple_protected_branches_ruleset_migration",
      "logic": "OR",
      "conditions": [
        { "field": "protected_branch_count", "op": "gt", "value": 1 }
      ]
    },
    {
      "flag": "high_branch_count_complexity",
      "logic": "OR",
      "conditions": [
        { "field": "branch_count", "op": "gt", "value": 500 }
      ]
    },
    {
      "flag": "very_high_branch_count_risk",
      "logic": "OR",
      "conditions": [
        { "field": "branch_count", "op": "gt", "value": 5000 }
      ]
    },
    {
      "flag": "has_protected_tags",
      "logic": "OR",
      "conditions": [
        { "field": "protected_tag_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_codeowner_approval_required",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_protected_branches",
          "join_key": "repo_id",
          "match": [
            { "field": "code_owner_approval_required", "op": "eq", "value": true }
          ]
        }
      ]
    },
    {
      "flag": "force_push_allowed_on_protected_branch",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_protected_branches",
          "join_key": "repo_id",
          "match": [
            { "field": "allow_force_push", "op": "eq", "value": true }
          ]
        }
      ]
    },
    {
      "flag": "has_open_prs_requiring_migration",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_pull_requests",
          "join_key": "repo_id",
          "match": [
            { "field": "state", "op": "eq", "value": "open" }
          ]
        }
      ]
    },
    {
      "flag": "has_draft_prs",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_pull_requests",
          "join_key": "repo_id",
          "match": [
            { "field": "is_draft", "op": "eq", "value": true }
          ]
        }
      ]
    },
    {
      "flag": "pr_volume_high",
      "logic": "OR",
      "conditions": [
        { "field": "pr_count", "op": "gt", "value": 1000 }
      ]
    },
    {
      "flag": "pr_volume_very_high",
      "logic": "OR",
      "conditions": [
        { "field": "pr_count", "op": "gt", "value": 10000 }
      ]
    },
    {
      "flag": "pr_comment_volume_high",
      "logic": "OR",
      "conditions": [
        { "field": "pr_comment_count", "op": "gt", "value": 5000 }
      ]
    },
    {
      "flag": "has_large_diff_prs",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_pull_requests",
          "join_key": "repo_id",
          "match": [
            { "field": "changed_files", "op": "gt", "value": 500 }
          ]
        }
      ]
    },
    {
      "flag": "has_unresolved_pr_review_comments",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_pr_comments",
          "join_key": "repo_id",
          "match": [
            { "field": "is_resolved", "op": "eq", "value": false }
          ]
        }
      ]
    },
    {
      "flag": "issue_volume_high",
      "logic": "OR",
      "conditions": [
        { "field": "issue_count", "op": "gt", "value": 5000 }
      ]
    },
    {
      "flag": "issue_volume_very_high",
      "logic": "OR",
      "conditions": [
        { "field": "issue_count", "op": "gt", "value": 50000 }
      ]
    },
    {
      "flag": "has_open_issues_requiring_migration",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_issues",
          "join_key": "repo_id",
          "match": [
            { "field": "state", "op": "eq", "value": "open" }
          ]
        }
      ]
    },
    {
      "flag": "has_open_milestones",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_milestones",
          "join_key": "repo_id",
          "match": [
            { "field": "state", "op": "eq", "value": "open" }
          ]
        }
      ]
    },
    {
      "flag": "has_overdue_milestones",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_milestones",
          "join_key": "repo_id",
          "match": [
            { "field": "state", "op": "eq", "value": "open" },
            { "field": "due_date", "op": "lt", "value": "2026-01-01T00:00:00Z" }
          ]
        }
      ]
    },
    {
      "flag": "high_label_count_migration_effort",
      "logic": "OR",
      "conditions": [
        { "field": "label_count", "op": "gt", "value": 50 }
      ]
    },
    {
      "flag": "has_releases_with_assets",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_releases",
          "join_key": "repo_id",
          "match": [
            { "field": "asset_count", "op": "gt", "value": 0 }
          ]
        }
      ]
    },
    {
      "flag": "has_prerelease_releases",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_releases",
          "join_key": "repo_id",
          "match": [
            { "field": "is_prerelease", "op": "eq", "value": true }
          ]
        }
      ]
    },
    {
      "flag": "has_draft_releases",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_releases",
          "join_key": "repo_id",
          "match": [
            { "field": "is_draft", "op": "eq", "value": true }
          ]
        }
      ]
    },
    {
      "flag": "high_release_count",
      "logic": "OR",
      "conditions": [
        { "field": "release_count", "op": "gt", "value": 100 }
      ]
    },
    {
      "flag": "has_external_collaborators",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_users",
          "join_key": "repo_id",
          "match": [
            { "field": "is_external", "op": "eq", "value": true }
          ]
        }
      ]
    },
    {
      "flag": "has_bot_users",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_users",
          "join_key": "repo_id",
          "match": [
            { "field": "is_bot", "op": "eq", "value": true }
          ]
        }
      ]
    },
    {
      "flag": "high_commit_count",
      "logic": "OR",
      "conditions": [
        { "field": "commit_count", "op": "gt", "value": 50000 }
      ]
    },
    {
      "flag": "very_high_commit_count",
      "logic": "OR",
      "conditions": [
        { "field": "commit_count", "op": "gt", "value": 500000 }
      ]
    },
    {
      "flag": "stale_repo_no_recent_push",
      "logic": "AND",
      "conditions": [
        { "field": "pushed_at", "op": "lt", "value": "2024-01-01T00:00:00Z" },
        { "field": "is_archived", "op": "eq", "value": false }
      ]
    },
    {
      "flag": "recently_active_repo",
      "logic": "AND",
      "conditions": [
        { "field": "pushed_at", "op": "gte", "value": "2025-01-01T00:00:00Z" },
        { "field": "is_archived", "op": "eq", "value": false }
      ]
    },
    {
      "flag": "never_pushed",
      "logic": "OR",
      "conditions": [
        { "field": "pushed_at", "op": "is_null" }
      ]
    },
    {
      "flag": "belongs_to_large_namespace",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_namespaces",
          "join_key": "repo_id",
          "match": [
            { "field": "repo_count", "op": "gt", "value": 100 }
          ]
        }
      ]
    },
    {
      "flag": "belongs_to_very_large_namespace",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_namespaces",
          "join_key": "repo_id",
          "match": [
            { "field": "repo_count", "op": "gt", "value": 500 }
          ]
        }
      ]
    },
    {
      "flag": "tfvc_repo_requires_git_conversion",
      "logic": "OR",
      "conditions": [
        { "field": "source_vcs_type", "op": "eq", "value": "Tfvc" }
      ]
    },
    {
      "flag": "has_yaml_pipelines",
      "logic": "OR",
      "conditions": [
        { "field": "yaml_pipeline_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_classic_build_pipelines",
      "logic": "OR",
      "conditions": [
        { "field": "classic_build_pipeline_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_classic_release_pipelines",
      "logic": "OR",
      "conditions": [
        { "field": "classic_release_pipeline_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "high_pipeline_count",
      "logic": "OR",
      "conditions": [
        { "field": "pipeline_count", "op": "gt", "value": 20 }
      ]
    },
    {
      "flag": "has_service_connections",
      "logic": "OR",
      "conditions": [
        { "field": "service_connection_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_variable_groups",
      "logic": "OR",
      "conditions": [
        { "field": "variable_group_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_secure_files",
      "logic": "OR",
      "conditions": [
        { "field": "secure_file_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_pipeline_environments",
      "logic": "OR",
      "conditions": [
        { "field": "environment_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_deployment_groups",
      "logic": "OR",
      "conditions": [
        { "field": "deployment_group_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_work_items",
      "logic": "OR",
      "conditions": [
        { "field": "work_item_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "high_work_item_count",
      "logic": "OR",
      "conditions": [
        { "field": "work_item_count", "op": "gt", "value": 10000 }
      ]
    },
    {
      "flag": "very_high_work_item_count",
      "logic": "OR",
      "conditions": [
        { "field": "work_item_count", "op": "gt", "value": 100000 }
      ]
    },
    {
      "flag": "has_custom_work_item_types",
      "logic": "OR",
      "conditions": [
        { "field": "custom_work_item_type_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_area_paths",
      "logic": "OR",
      "conditions": [
        { "field": "area_path_count", "op": "gt", "value": 1 }
      ]
    },
    {
      "flag": "has_deep_area_path_hierarchy",
      "logic": "OR",
      "conditions": [
        { "field": "area_path_depth", "op": "gt", "value": 3 }
      ]
    },
    {
      "flag": "has_iteration_paths",
      "logic": "OR",
      "conditions": [
        { "field": "iteration_path_count", "op": "gt", "value": 1 }
      ]
    },
    {
      "flag": "has_test_plans",
      "logic": "OR",
      "conditions": [
        { "field": "test_plan_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_test_suites",
      "logic": "OR",
      "conditions": [
        { "field": "test_suite_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_manual_test_cases",
      "logic": "OR",
      "conditions": [
        { "field": "manual_test_case_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_artifact_feeds",
      "logic": "OR",
      "conditions": [
        { "field": "artifact_feed_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_npm_packages",
      "logic": "OR",
      "conditions": [
        { "field": "npm_package_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_nuget_packages",
      "logic": "OR",
      "conditions": [
        { "field": "nuget_package_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_maven_packages",
      "logic": "OR",
      "conditions": [
        { "field": "maven_package_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_python_packages_no_ghec_native_support",
      "logic": "OR",
      "conditions": [
        { "field": "python_package_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_universal_packages_no_ghec_native_support",
      "logic": "OR",
      "conditions": [
        { "field": "universal_package_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_container_images",
      "logic": "OR",
      "conditions": [
        { "field": "container_image_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_wiki",
      "logic": "OR",
      "conditions": [
        { "field": "wiki_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_code_wiki",
      "logic": "OR",
      "conditions": [
        { "field": "code_wiki_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_dashboards",
      "logic": "OR",
      "conditions": [
        { "field": "dashboard_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_extensions_installed",
      "logic": "OR",
      "conditions": [
        { "field": "extension_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_service_hooks",
      "logic": "OR",
      "conditions": [
        { "field": "service_hook_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_custom_process_template",
      "logic": "OR",
      "conditions": [
        { "field": "process_template_type", "op": "neq", "value": "Basic" }
      ]
    },
    {
      "flag": "has_inherited_process_customizations",
      "logic": "OR",
      "conditions": [
        { "field": "inherited_process_customization_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_ghas_enabled",
      "logic": "OR",
      "conditions": [
        { "field": "ghas_enabled", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "has_keyvault_linked_variable_groups",
      "logic": "OR",
      "conditions": [
        { "field": "keyvault_linked_variable_group_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_path_based_permissions",
      "logic": "OR",
      "conditions": [
        { "field": "path_scoped_permission_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_deny_permissions",
      "logic": "OR",
      "conditions": [
        { "field": "deny_permission_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "has_custom_security_groups",
      "logic": "OR",
      "conditions": [
        { "field": "custom_security_group_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "migration_risk_high",
      "logic": "OR",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "gt", "value": 10737418240 },
        { "field": "lfs_size_bytes", "op": "gt", "value": 5368709120 },
        { "field": "branch_count", "op": "gt", "value": 5000 },
        { "field": "submodule_count", "op": "gt", "value": 10 },
        { "field": "pr_count", "op": "gt", "value": 10000 },
        { "field": "issue_count", "op": "gt", "value": 10000 },
        { "field": "commit_count", "op": "gt", "value": 500000 },
        { "field": "is_archived", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "migration_risk_medium",
      "logic": "AND",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "gt", "value": 1073741824 },
        { "field": "total_repo_size_bytes", "op": "lte", "value": 10737418240 },
        { "field": "branch_count", "op": "lte", "value": 5000 },
        { "field": "is_archived", "op": "eq", "value": false }
      ]
    },
    {
      "flag": "migration_risk_low",
      "logic": "AND",
      "conditions": [
        { "field": "total_repo_size_bytes", "op": "lte", "value": 1073741824 },
        { "field": "branch_count", "op": "lte", "value": 500 },
        { "field": "lfs_file_count", "op": "eq", "value": 0 },
        { "field": "submodule_count", "op": "eq", "value": 0 },
        { "field": "is_fork", "op": "eq", "value": false },
        { "field": "is_archived", "op": "eq", "value": false }
      ]
    }
  ]
}
```
