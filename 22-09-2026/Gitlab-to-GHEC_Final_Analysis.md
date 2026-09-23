# GitLab to GHEC Policy vs Current Discovery

The table below provides a complete comparison of the GitLab-to-GHEC policy against the current discovery data.

| Flag | Condition | What it checks | Metadata or attribute | Available in current discovery |
| --- | --- | --- | --- | --- |
| `repo_size_exceeds_ghec_recommendation` | `total_repo_size_bytes > 5368709120` | Checks whether repository size exceeds the recommended 5 GB GHEC limit. | `repository_size_bytes` | **Yes** |
| `repo_size_exceeds_ghec_hard_limit` | `total_repo_size_bytes > 10737418240` | Checks whether repository size exceeds the 10 GB GHEC hard limit. | `repository_size_bytes` | **Yes** |
| `lfs_storage_exceeds_default_quota` | `lfs_size_bytes > 1073741824` | Checks whether LFS storage exceeds the 1 GB default quota. | `lfs_objects_size_bytes` | **Yes** |
| `lfs_objects_present` | `lfs_file_count > 0` | Checks whether the repository contains LFS files. | `total_lfs_files` | **Yes** |
| `submodules_present` | `submodule_count > 0` | Checks whether the repository contains Git submodules. | `total_submodules` | **Yes** |
| `fork_lineage_review_required` | `is_fork = true` | Checks whether the repository is a fork requiring fork-lineage review. | `is_fork` | **No** Missing: `is_fork` |
| `archived_repo_review_required` | `is_archived = true` | Checks whether the repository is archived and therefore requires migration review. | `archived` | **Yes** |
| `private_repo_access_mapping_needed` | `is_private = true` | Checks whether the repository is private and may require access mapping. | `visibility` | **Yes** |
| `internal_visibility_translation_needed` | `visibility = "internal"` | Checks whether the repository has GitLab's internal visibility setting. | `visibility` | **Yes** |
| `no_branch_protection_governance_gap` | `protected_branch_count = 0` and `branch_count > 0` | Checks whether a repository has branches but no protected branches. | `total_protected_branches`, `total_branches` | **Yes** |
| `protected_tags_present` | `protected_tag_count > 0` | Checks whether the repository has protected tags. | `total_protected_tags` | **Yes** |
| `high_branch_count_complexity` | `branch_count > 500` | Checks whether the repository has more than 500 branches. | `total_branches` | **Yes** |
| `very_high_branch_count_risk` | `branch_count > 5000` | Checks whether the repository has more than 5,000 branches. | `total_branches` | **Yes** |
| `high_commit_volume_complexity` | `commit_count > 100000` | Checks whether the repository has more than 100,000 commits. | `total_commits` | **Yes** |
| `pr_volume_high_migration_effort` | `pr_count > 1000` | Checks whether the repository has more than 1,000 pull/merge requests. | `total_merge_requests` | **Yes** |
| `issue_volume_high_migration_effort` | `issue_count > 5000` | Checks whether the repository has more than 5,000 issues. | `total_issues` | **Yes** |
| `label_volume_high_migration_effort` | `label_count > 100` | Checks whether the repository has more than 100 labels. | `total_labels` | **Yes** |
| `release_metadata_present` | `release_count > 0` | Checks whether the repository contains release metadata. | `total_releases` | **Yes** |
| `open_pull_requests_present` | `inventory_pull_requests.state = "open"` | Checks whether the repository has at least one open pull request. | `state` | **No** Missing: `state` |
| `draft_pull_requests_present` | `inventory_pull_requests.is_draft = true` | Checks whether the repository has draft pull requests. | `mr_draft_count` | **Yes** |
| `codeowner_approval_rules_present` | `inventory_protected_branches.code_owner_approval_required = true` | Checks whether protected branches require code-owner approval. | `approval_rules_code_owner_required`, `total_protected_branches_with_code_owner_approval` | **Yes** |
| `force_push_allowed_on_protected_branch` | `inventory_protected_branches.allow_force_push = true` | Checks whether force-push is allowed on a protected branch. | `total_protected_branches_with_force_push` | **Yes** |
| `releases_with_binary_assets` | `inventory_releases.asset_count > 0` | Checks whether releases contain binary/file assets. | `asset_count` | **No** Missing: `asset_count` |
| `prerelease_usage_present` | `inventory_releases.is_prerelease = true` | Checks whether the repository uses prerelease releases. | `is_prerelease` | **No** Missing: `is_prerelease` |
| `open_milestones_present` | `inventory_milestones.state = "open"` and `count >= 1` | Checks whether the repository has at least one open milestone. | `milestones_active_count` | **Yes** |
| `external_collaborators_present` | `inventory_users.is_external = true` | Checks whether the repository has external collaborators/users. | `is_external` | **No** Missing: `is_external` |
| `bot_users_present` | `inventory_users.is_bot = true` | Checks whether the repository has bot users. | `bots_count` | **Yes** |
| `annotated_tags_present` | `inventory_tags.is_annotated = true` | Checks whether the repository contains annotated tags. | `is_annotated` | **No** Missing: `is_annotated` |
| `pr_comment_volume_high` | `pr_comment_count > 5000` | Checks whether the repository has more than 5,000 PR comments. | `pr_comment_count` | **No** Missing: `pr_comment_count` |
| `stale_repo_no_recent_push` | `pushed_at < "2024-01-01T00:00:00Z"` and `is_archived = false` | Checks for non-archived repositories that have not been pushed to since before 2024. | `last_activity_at`, `archived` | **No** Missing: `pushed_at` |
| `migration_risk_high` | `total_repo_size_bytes > 10737418240`, `lfs_size_bytes > 5368709120`, `branch_count > 5000`, `submodule_count > 10`, `pr_count > 10000`, `issue_count > 10000`, `is_archived = true` | Flags a repository as high migration risk when any defined high-risk condition is met. | `repository_size_bytes`, `lfs_objects_size_bytes`, `total_branches`, `total_submodules`, `total_merge_requests`, `total_issues`, `archived` | **Yes** |
| `migration_risk_medium` | `total_repo_size_bytes > 1073741824`, `total_repo_size_bytes <= 10737418240`, `branch_count <= 5000`, `is_archived = false` | Classifies repositories within the defined medium migration-risk range. | `repository_size_bytes`, `total_branches`, `archived` | **Yes** |
| `migration_risk_low` | `total_repo_size_bytes <= 1073741824`, `branch_count <= 500`, `lfs_file_count = 0`, `submodule_count = 0`, `is_fork = false`, `is_archived = false` | Classifies repositories as low migration risk when all defined low-risk conditions are satisfied. | `repository_size_bytes`, `total_branches`, `total_lfs_files`, `total_submodules`, `is_fork`, `archived` | **No** Missing: `is_fork` |

The CSV header confirms the corresponding discovery metadata such as `repository_size_bytes`, `lfs_objects_size_bytes`, `total_branches`, `total_commits`, `total_lfs_files`, `total_submodules`, `total_protected_branches`, `total_protected_tags`, `total_merge_requests`, `total_issues`, `total_milestones`, `milestones_active_count`, `total_releases`, `bots_count`, `total_labels`, `approval_rules_code_owner_required`, `total_protected_branches_with_force_push`, and `total_protected_branches_with_code_owner_approval`.

The policy flags and conditions are taken from `Gitlab-to-GHEC_policy3.json` in their original order.

## Reference: Gitlab-to-GHEC_policy.json

```json
{
  "categories": [
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
      "flag": "lfs_objects_present",
      "logic": "OR",
      "conditions": [
        { "field": "lfs_file_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "submodules_present",
      "logic": "OR",
      "conditions": [
        { "field": "submodule_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "fork_lineage_review_required",
      "logic": "OR",
      "conditions": [
        { "field": "is_fork", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "archived_repo_review_required",
      "logic": "OR",
      "conditions": [
        { "field": "is_archived", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "private_repo_access_mapping_needed",
      "logic": "OR",
      "conditions": [
        { "field": "is_private", "op": "eq", "value": true }
      ]
    },
    {
      "flag": "internal_visibility_translation_needed",
      "logic": "OR",
      "conditions": [
        { "field": "visibility", "op": "eq", "value": "internal" }
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
      "flag": "protected_tags_present",
      "logic": "OR",
      "conditions": [
        { "field": "protected_tag_count", "op": "gt", "value": 0 }
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
      "flag": "high_commit_volume_complexity",
      "logic": "OR",
      "conditions": [
        { "field": "commit_count", "op": "gt", "value": 100000 }
      ]
    },
    {
      "flag": "pr_volume_high_migration_effort",
      "logic": "OR",
      "conditions": [
        { "field": "pr_count", "op": "gt", "value": 1000 }
      ]
    },
    {
      "flag": "issue_volume_high_migration_effort",
      "logic": "OR",
      "conditions": [
        { "field": "issue_count", "op": "gt", "value": 5000 }
      ]
    },
    {
      "flag": "label_volume_high_migration_effort",
      "logic": "OR",
      "conditions": [
        { "field": "label_count", "op": "gt", "value": 100 }
      ]
    },
    {
      "flag": "release_metadata_present",
      "logic": "OR",
      "conditions": [
        { "field": "release_count", "op": "gt", "value": 0 }
      ]
    },
    {
      "flag": "open_pull_requests_present",
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
      "flag": "draft_pull_requests_present",
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
      "flag": "codeowner_approval_rules_present",
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
      "flag": "releases_with_binary_assets",
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
      "flag": "prerelease_usage_present",
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
      "flag": "open_milestones_present",
      "logic": "OR",
      "conditions": [
        {
          "op": "count",
          "table": "inventory_milestones",
          "join_key": "repo_id",
          "match": [
            { "field": "state", "op": "eq", "value": "open" }
          ],
          "result_op": "gte",
          "result_value": 1
        }
      ]
    },
    {
      "flag": "external_collaborators_present",
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
      "flag": "bot_users_present",
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
      "flag": "annotated_tags_present",
      "logic": "OR",
      "conditions": [
        {
          "op": "exists",
          "table": "inventory_tags",
          "join_key": "repo_id",
          "match": [
            { "field": "is_annotated", "op": "eq", "value": true }
          ]
        }
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
      "flag": "stale_repo_no_recent_push",
      "logic": "AND",
      "conditions": [
        { "field": "pushed_at", "op": "lt", "value": "2024-01-01T00:00:00Z" },
        { "field": "is_archived", "op": "eq", "value": false }
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
