# Platform Parity API Contract Specification

**Date:** 2026-08-31  
**Status:** Specification Ready  
**Integration Type:** RESTful HTTP  
**Base Path:** `/api/v1/platform-parity`

---

## Overview

This document defines the REST API contract required by the Platform Parity frontend module. The backend can implement these endpoints using any method (direct FastAPI, Script Executor workflow, database queries, etc.), as long as the request/response contracts are met.

---

## 1. Create/Execute Analysis

### 1.1 Request

**Endpoint:** `POST /api/v1/platform-parity/compare`

**HTTP Status:** 202 Accepted

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {token}  (if required)
```

**Request Body:**
```json
{
  "source_platform": "gitlab",
  "target_platform": "github",
  "include_kb_sync": false,
  "output_format": "both"
}
```

**Field Definitions:**

| Field | Type | Required | Values | Notes |
|-------|------|----------|--------|-------|
| source_platform | string | Yes | gitlab, github, azure_devops, bitbucket | Platform migrating FROM |
| target_platform | string | Yes | gitlab, github, azure_devops, bitbucket | Platform migrating TO |
| include_kb_sync | boolean | No | true, false | Optional KB refresh from live docs (default: false) |
| output_format | string | No | json, markdown, both | Report format (default: both) |

**Validation Rules:**
- source_platform and target_platform must be different
- Both platforms must be in the allowed values list
- Invalid platforms → return 400
- Same source/target → return 422

### 1.2 Response

**Success Response (202 Accepted):**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_id": null,
  "status": "PENDING",
  "progress": 0,
  "message": "Analysis queued. Poll status endpoint for progress."
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "bad_request",
  "message": "Invalid platform: 'invalid_platform'",
  "details": {
    "field": "target_platform",
    "allowed_values": ["gitlab", "github", "azure_devops", "bitbucket"]
  }
}
```

**Error Response (422 Unprocessable Entity):**
```json
{
  "error": "validation_error",
  "message": "Source and target platforms cannot be the same",
  "details": {
    "source_platform": "gitlab",
    "target_platform": "gitlab"
  }
}
```

**Error Response (429 Too Many Requests):**
```json
{
  "error": "rate_limited",
  "message": "Too many analysis requests. Please try again later.",
  "retry_after": 60
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": "internal_error",
  "message": "Failed to queue analysis",
  "details": {
    "trace_id": "xyz-123"
  }
}
```

### 1.3 Response Fields

| Field | Type | Always Present | Description |
|-------|------|-----------------|-------------|
| execution_id | string (uuid) | Yes | Unique execution identifier for polling |
| report_id | string or null | Yes | Report ID (null until completion) |
| status | string | Yes | PENDING, IN_PROGRESS, COMPLETED, FAILED |
| progress | integer | No | 0-100, progress percentage (if IN_PROGRESS) |
| message | string | No | Human-readable status message |

---

## 2. Get Execution Status

### 2.1 Request

**Endpoint:** `GET /api/v1/platform-parity/status/{execution_id}`

**HTTP Status:** 200 OK

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| execution_id | string (uuid) | Yes | UUID from create analysis response |

**Query Parameters:** None

### 2.2 Response

**Success Response (200 OK) - Pending:**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "progress": 0,
  "report_id": null,
  "error_message": null,
  "estimated_seconds_remaining": 120
}
```

**Success Response (200 OK) - In Progress:**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "IN_PROGRESS",
  "progress": 45,
  "report_id": null,
  "error_message": null,
  "estimated_seconds_remaining": 60
}
```

**Success Response (200 OK) - Completed:**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "progress": 100,
  "report_id": "gitlab_to_github_7895f1aba77c",
  "error_message": null,
  "estimated_seconds_remaining": 0
}
```

**Success Response (200 OK) - Failed:**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FAILED",
  "progress": 50,
  "report_id": null,
  "error_message": "AWS Bedrock timeout after 600 seconds",
  "estimated_seconds_remaining": null
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "not_found",
  "message": "Execution not found",
  "details": {
    "execution_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": "internal_error",
  "message": "Failed to retrieve execution status"
}
```

### 2.3 Response Fields

| Field | Type | Always Present | Notes |
|-------|------|-----------------|-------|
| execution_id | string (uuid) | Yes | Echo back request parameter |
| status | string | Yes | PENDING, IN_PROGRESS, COMPLETED, FAILED |
| progress | integer | Yes | 0-100, always present (0 for pending, 100 for completed) |
| report_id | string or null | Yes | Report ID (populated when COMPLETED) |
| error_message | string or null | Yes | Error details (populated when FAILED) |
| estimated_seconds_remaining | integer or null | Yes | Estimated seconds to completion (null when FAILED) |

---

## 3. Get Report Detail

### 3.1 Request

**Endpoint:** `GET /api/v1/platform-parity/reports/{report_id}`

**HTTP Status:** 200 OK

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| report_id | string | Yes | Report ID from execution status or list |

**Query Parameters:** None

### 3.2 Response

**Success Response (200 OK):**
```json
{
  "report_id": "gitlab_to_github_7895f1aba77c",
  "source_platform": "gitlab",
  "target_platform": "github",
  "generated_at": "2026-08-31T14:23:45.123456Z",
  "generated_by": "user@example.com",
  "overall_risk": "MEDIUM",
  "sections": {
    "executive_summary": {
      "title": "Executive Summary",
      "content": "Migrating from GitLab to GitHub requires...",
      "metrics": {
        "total_capabilities": 54,
        "supported": 48,
        "partial": 4,
        "unsupported": 2,
        "coverage_percentage": 88.89
      }
    },
    "hard_blockers": {
      "title": "🔴 Hard Blockers",
      "items": [
        {
          "capability_id": "cap_shared_runners",
          "capability_name": "Shared Runners",
          "category": "CI/CD",
          "gap_type": "HARD_BLOCKER",
          "source_behavior": "GitLab provides shared runners on demand",
          "target_behavior": "GitHub Actions requires self-hosted runners for equivalent functionality",
          "migration_impact": "High effort: must provision and maintain self-hosted runner infrastructure",
          "workaround": "Use GitHub Actions with self-hosted runners or GitHub-hosted runners with limitations",
          "confidence": "HIGH",
          "last_verified": "2026-08-20",
          "verification_source": "GitHub Actions documentation v2024.08"
        }
      ]
    },
    "behavioral_differences": {
      "title": "🟡 Behavioral Differences",
      "items": [
        {
          "capability_id": "cap_mr_approval_rules",
          "capability_name": "Merge Request Approval Rules",
          "category": "Code Review",
          "gap_type": "BEHAVIORAL_DIFFERENCE",
          "source_behavior": "GitLab MR rules: named rules, complex conditions, per-project settings",
          "target_behavior": "GitHub PR rules: branch protection rules, simpler conditions, org/repo level",
          "migration_impact": "Medium effort: rules need redesign to match GitHub model",
          "workaround": "Use GitHub branch protection rules with Actions for complex logic",
          "confidence": "HIGH",
          "last_verified": "2026-08-20",
          "verification_source": "GitHub branch protection API v2024.08"
        }
      ]
    },
    "seamless_migrations": {
      "title": "🟢 Seamless Migrations",
      "items": [
        {
          "capability_id": "cap_ssh_keys",
          "capability_name": "SSH Key Authentication",
          "category": "Authentication",
          "gap_type": "SEAMLESS_MIGRATION",
          "source_behavior": "SSH keys supported for repository access",
          "target_behavior": "SSH keys supported for repository access",
          "migration_impact": null,
          "workaround": null,
          "confidence": "HIGH",
          "last_verified": "2026-08-20",
          "verification_source": "GitHub SSH documentation v2024.08"
        }
      ]
    },
    "coverage_report": {
      "title": "📋 Coverage Report",
      "by_category": {
        "CI/CD": {
          "count": 15,
          "coverage": "86.67"
        },
        "Code Review": {
          "count": 12,
          "coverage": "91.67"
        },
        "Authentication": {
          "count": 8,
          "coverage": "100.00"
        },
        "Access Control": {
          "count": 9,
          "coverage": "88.89"
        },
        "Webhooks": {
          "count": 10,
          "coverage": "90.00"
        }
      }
    }
  },
  "markdown_content": "# Platform Parity Report: GitLab → GitHub\n\n## 1. Executive Summary\n\n..."
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "not_found",
  "message": "Report not found",
  "details": {
    "report_id": "gitlab_to_github_7895f1aba77c"
  }
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": "internal_error",
  "message": "Failed to retrieve report"
}
```

### 3.3 Response Fields

**Top Level:**

| Field | Type | Always Present | Notes |
|-------|------|-----------------|-------|
| report_id | string | Yes | Unique report identifier |
| source_platform | string | Yes | Source SCM platform |
| target_platform | string | Yes | Target SCM platform |
| generated_at | string (ISO 8601) | Yes | Timestamp of report generation |
| generated_by | string | No | User ID or system identifier |
| overall_risk | string | Yes | CRITICAL, HIGH, MEDIUM, LOW, MINIMAL |
| sections | object | Yes | Five report sections (see below) |
| markdown_content | string | No | Markdown-formatted report (may be null if not generated) |

**Sections Object:**

| Field | Type | Description |
|-------|------|-------------|
| executive_summary | ExecutiveSummarySection | High-level summary and metrics |
| hard_blockers | GapSection | HARD_BLOCKER items |
| behavioral_differences | GapSection | BEHAVIORAL_DIFFERENCE items |
| seamless_migrations | GapSection | SEAMLESS_MIGRATION items |
| coverage_report | CoverageReportSection | Category-by-category breakdown |

**ExecutiveSummarySection:**

| Field | Type | Notes |
|-------|------|-------|
| title | string | Section title (e.g., "Executive Summary") |
| content | string | Narrative summary of migration complexity |
| metrics.total_capabilities | integer | Total capabilities analyzed |
| metrics.supported | integer | Fully supported capabilities |
| metrics.partial | integer | Partially supported (differences) |
| metrics.unsupported | integer | Unsupported (blockers) |
| metrics.coverage_percentage | number | (supported / total) * 100 |

**GapSection:**

| Field | Type | Notes |
|-------|------|-------|
| title | string | Section title with emoji (e.g., "🔴 Hard Blockers") |
| items | array | Array of CapabilityGap objects |

**CapabilityGap:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| capability_id | string | Yes | Unique ID (e.g., "cap_shared_runners") |
| capability_name | string | Yes | Human-readable name |
| category | string | Yes | Category (CI/CD, Code Review, etc.) |
| gap_type | string | Yes | HARD_BLOCKER, BEHAVIORAL_DIFFERENCE, SEAMLESS_MIGRATION |
| source_behavior | string | Yes | How feature works in source platform |
| target_behavior | string | Yes | How feature works in target platform |
| migration_impact | string | No | Impact description (null for seamless) |
| workaround | string | No | Suggested workaround (null if none) |
| confidence | string | No | HIGH, MEDIUM, LOW (default: HIGH) |
| last_verified | string | No | Date of last verification (YYYY-MM-DD) |
| verification_source | string | No | Source of verification (e.g., API docs version) |

**CoverageReportSection:**

| Field | Type | Notes |
|-------|------|-------|
| title | string | Section title |
| by_category | object | Keys are category names, values are coverage objects |

**Coverage Object (values in by_category):**

| Field | Type | Notes |
|-------|------|-------|
| count | integer | Number of capabilities in this category |
| coverage | string | Percentage as string (e.g., "86.67") |

---

## 4. List Reports (History)

### 4.1 Request

**Endpoint:** `GET /api/v1/platform-parity/reports`

**HTTP Status:** 200 OK

**Query Parameters:**

| Parameter | Type | Required | Default | Max | Description |
|-----------|------|----------|---------|-----|-------------|
| limit | integer | No | 20 | 100 | Results per page |
| offset | integer | No | 0 | N/A | Pagination offset |
| sort_by | string | No | generated_at | N/A | Field to sort by: generated_at, overall_risk, source_platform, target_platform |
| order | string | No | desc | N/A | Sort order: asc or desc |

**Example URL:**
```
GET /api/v1/platform-parity/reports?limit=20&offset=0&sort_by=generated_at&order=desc
```

### 4.2 Response

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "report_id": "gitlab_to_github_7895f1aba77c",
      "source_platform": "gitlab",
      "target_platform": "github",
      "generated_at": "2026-08-31T14:23:45.123456Z",
      "generated_by": "user@example.com",
      "overall_risk": "MEDIUM",
      "coverage_percentage": 88.89,
      "blocker_count": 2,
      "difference_count": 4,
      "seamless_count": 48
    },
    {
      "report_id": "azure_devops_to_github_abc123def456",
      "source_platform": "azure_devops",
      "target_platform": "github",
      "generated_at": "2026-08-30T09:15:20.654321Z",
      "generated_by": "system",
      "overall_risk": "HIGH",
      "coverage_percentage": 78.50,
      "blocker_count": 5,
      "difference_count": 8,
      "seamless_count": 41
    }
  ],
  "total": 127,
  "limit": 20,
  "offset": 0
}
```

**Error Response (400 Bad Request - Invalid Query):**
```json
{
  "error": "bad_request",
  "message": "Invalid sort_by parameter",
  "details": {
    "allowed_values": ["generated_at", "overall_risk", "source_platform", "target_platform"],
    "provided": "invalid_sort"
  }
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": "internal_error",
  "message": "Failed to retrieve report list"
}
```

### 4.3 Response Fields

**Top Level:**

| Field | Type | Notes |
|-------|------|-------|
| items | array | Array of ReportSummary objects |
| total | integer | Total number of reports (across all pages) |
| limit | integer | Results per page (echoed) |
| offset | integer | Pagination offset (echoed) |

**ReportSummary:**

| Field | Type | Notes |
|-------|------|-------|
| report_id | string | Unique report identifier |
| source_platform | string | Source platform |
| target_platform | string | Target platform |
| generated_at | string (ISO 8601) | When report was generated |
| generated_by | string | User or system identifier |
| overall_risk | string | CRITICAL, HIGH, MEDIUM, LOW, MINIMAL |
| coverage_percentage | number | Capability coverage percentage |
| blocker_count | integer | Number of hard blockers |
| difference_count | integer | Number of behavioral differences |
| seamless_count | integer | Number of seamless migrations |

---

## 5. Delete Report

### 5.1 Request

**Endpoint:** `DELETE /api/v1/platform-parity/reports/{report_id}`

**HTTP Status:** 204 No Content

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| report_id | string | Yes | Report ID to delete |

**Query Parameters:** None

### 5.2 Response

**Success Response (204 No Content):**
```
(empty body)
```

**Error Response (404 Not Found):**
```json
{
  "error": "not_found",
  "message": "Report not found",
  "details": {
    "report_id": "gitlab_to_github_7895f1aba77c"
  }
}
```

**Error Response (403 Forbidden - Insufficient Permission):**
```json
{
  "error": "forbidden",
  "message": "You do not have permission to delete this report",
  "details": {
    "report_id": "gitlab_to_github_7895f1aba77c",
    "generated_by": "other_user@example.com"
  }
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": "internal_error",
  "message": "Failed to delete report"
}
```

---

## 6. Error Handling

### 6.1 Error Response Format

All error responses follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "value",
    "other_context": "value"
  },
  "trace_id": "optional-trace-id-for-debugging"
}
```

### 6.2 Standard HTTP Status Codes

| Code | Meaning | When to Use |
|------|---------|------------|
| 200 | OK | Successful read operation |
| 202 | Accepted | Analysis queued successfully |
| 204 | No Content | Successful delete |
| 400 | Bad Request | Invalid request parameters |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Semantic validation failed |
| 429 | Too Many Requests | Rate limited |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Backend service down |

### 6.3 Common Error Codes

| Code | HTTP Status | Scenario |
|------|------------|----------|
| bad_request | 400 | Invalid platform, missing fields |
| validation_error | 422 | Same source/target, invalid combination |
| rate_limited | 429 | Too many requests in short time |
| not_found | 404 | Report/execution not found |
| forbidden | 403 | User lacks delete permission |
| internal_error | 500 | Unexpected server error |
| service_unavailable | 503 | Bedrock/database down |

---

## 7. Rate Limiting

**Recommended Limits:**

| Endpoint | Limit | Window | Notes |
|----------|-------|--------|-------|
| POST /compare | 10 | 1 hour | Prevent analysis overload |
| GET /status | Unlimited | N/A | Status polling should be unrestricted |
| GET /reports | 100 | 1 minute | Prevent list bombing |
| DELETE | 50 | 1 hour | Prevent accidental bulk deletes |

**Rate Limit Headers** (recommended):

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1693413600
```

---

## 8. Security Considerations

### 8.1 Authentication

All endpoints should require:
- Valid JWT token or session cookie
- Token must be verified and user identified

### 8.2 Authorization

- **List/View:** Users can see their own and shared reports
- **Delete:** Only report owner (generated_by) or admin can delete
- **Create:** Any authenticated user can create analysis

### 8.3 Data Sensitivity

Reports may contain:
- Platform configuration details
- Capability/gap information
- Analysis results

**Recommendation:** Mark reports as internal-only data (not for external sharing).

### 8.4 SQL Injection Prevention

If using direct SQL:
- Always use parameterized queries
- Never concatenate user input into SQL

### 8.5 Input Validation

- Validate platform values against whitelist
- Validate report_id format (alphanumeric, dashes, underscores only)
- Validate execution_id is valid UUID
- Limit string fields (report metadata, etc.) to reasonable lengths

---

## 9. Implementation Notes

### 9.1 Database Considerations

**Required Tables:**

```sql
-- Execution tracking
CREATE TABLE parity.parity_executions (
  execution_id UUID PRIMARY KEY,
  source_platform VARCHAR(50),
  target_platform VARCHAR(50),
  status VARCHAR(50),
  progress INTEGER,
  report_id UUID,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  created_by VARCHAR(255)
);

-- Report storage
CREATE TABLE parity.parity_reports (
  report_id VARCHAR(100) PRIMARY KEY,
  source_platform VARCHAR(50),
  target_platform VARCHAR(50),
  report_content JSONB,  -- Full report JSON
  markdown_content TEXT,
  generated_at TIMESTAMP,
  generated_by VARCHAR(255),
  execution_id UUID REFERENCES parity.parity_executions(execution_id),
  status VARCHAR(50),
  error_message TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_executions_user ON parity.parity_executions(created_by);
CREATE INDEX idx_executions_status ON parity.parity_executions(status);
CREATE INDEX idx_reports_platform_pair ON parity.parity_reports(source_platform, target_platform);
CREATE INDEX idx_reports_generated_at ON parity.parity_reports(generated_at DESC);
```

### 9.2 Async Execution Pattern

Recommended flow:

1. POST /compare → Validate → Queue to Temporal → Return execution_id (202)
2. Frontend polls GET /status/{execution_id} every 2-5 seconds
3. When status = COMPLETED, GET /reports/{report_id} to fetch full data
4. Workflow writes final report to database via RabbitMQ consumer

### 9.3 Caching Strategy

- Cache report list for 5 minutes per user
- Cache individual reports indefinitely (invalidate on delete)
- Don't cache execution status (always fresh from DB)

### 9.4 Timeout Handling

- Analysis timeout: 600 seconds (10 minutes)
- API request timeout: 30 seconds
- Polling timeout: After 15 minutes, stop polling and show error

---

## 10. Example Frontend Integration

```typescript
// Create analysis
this.api.createAnalysis({
  source_platform: 'gitlab',
  target_platform: 'github',
  include_kb_sync: false,
  output_format: 'both'
}).subscribe(response => {
  console.log('Analysis queued:', response.execution_id);
  
  // Poll status
  const pollInterval = setInterval(() => {
    this.api.getExecutionStatus(response.execution_id)
      .subscribe(status => {
        if (status.status === 'COMPLETED') {
          clearInterval(pollInterval);
          // Fetch report
          this.api.getReport(status.report_id).subscribe(...);
        }
      });
  }, 2000);
});
```

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-31 | Initial specification |

---

**API Contract Finalized:** ✅ Ready for Backend Implementation
