# Platform Parity Frontend Implementation Plan v1.0

**Date:** 2026-08-31  
**Status:** Pre-Implementation (Ready to Execute)  
**Repository:** pace-git-lift-ui  
**Target Route:** `/platform-parity`  
**Technology Stack:** Angular 19 + TypeScript, Bootstrap 4.6, RxJS, @ng-bootstrap

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture & Design Principles](#architecture--design-principles)
3. [Backend Integration Context](#backend-integration-context)
4. [Component Hierarchy & Module Structure](#component-hierarchy--module-structure)
5. [Data Models & Interfaces](#data-models--interfaces)
6. [API Contract Definition](#api-contract-definition)
7. [Feature Breakdown - Phase by Phase](#feature-breakdown---phase-by-phase)
8. [Routing Configuration](#routing-configuration)
9. [Service Layer Design](#service-layer-design)
10. [Component Details](#component-details)
11. [Styling & Layout Patterns](#styling--layout-patterns)
12. [Testing Strategy](#testing-strategy)
13. [Implementation Checklist](#implementation-checklist)
14. [Deployment & Rollout](#deployment--rollout)
15. [Risk Mitigation](#risk-mitigation)

---

## Executive Summary

This plan defines the complete frontend implementation for **Platform Parity** within pace-git-lift-ui. Platform Parity enables users to analyze SCM migration compatibility by comparing source and target platforms (GitLab↔GitHub, Azure DevOps↔Bitbucket, etc.) and generates detailed parity reports.

### What Gets Built

1. **Analyzer Component** (`/platform-parity/analyzer`) - Platform selection + execution
2. **Report Viewer Component** (`/platform-parity/reports/:id`) - Detailed 5-section report display
3. **Report List Component** (`/platform-parity/reports`) - History of generated reports
4. **API Service** - Backend integration via RESTful endpoints
5. **Models & Data Structures** - TypeScript interfaces matching backend schemas

### What Gets Delivered

- **URL:** `http://localhost:4200/platform-parity/...`
- **Features:** Compare platforms, generate reports, view history, export data
- **Integration:** Temporal-based workflow execution (async backend processing)
- **Export Formats:** JSON, Markdown (rendered as HTML via Bootstrap)

### Key Assumptions

- Backend API endpoints exist (to be defined in §6)
- Workflow execution is async (reports generated via Temporal workers)
- User has appropriate permission to access platform comparison data
- Bootstrap 4.6 is sufficient for rendering (no Markdown library needed)

---

## Architecture & Design Principles

### 1.1 Design Patterns

| Pattern | Usage | Rationale |
|---------|-------|-----------|
| **Standalone Components** | All components are standalone (no shared module) | Aligns with Angular 19 best practices, simplifies lazy-loading |
| **Lazy Loading** | Platform-Parity module loads on-demand | Reduces initial bundle size |
| **Service-Oriented** | All HTTP logic in services, NOT in components | Separation of concerns, testability, reusability |
| **Reactive Forms** | FormBuilder for analyzer input | Type-safe, validation-friendly |
| **RxJS Observables** | Async data fetching, state management | Follows existing pace-git-lift-ui patterns |
| **Dependency Injection** | Services injected via Angular's DI container | Testable, mockable services |

### 1.2 Architectural Layers

```
┌────────────────────────────────────────────────────────┐
│                    ROUTING LAYER                        │
│          app.routes.ts (platform-parity routes)         │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│                  CONTAINER COMPONENT                    │
│      platform-parity.component (lazy-loaded)           │
│        Manages routing between sub-routes              │
└────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌──────────────────┐              ┌──────────────────┐
│  ANALYZER PAGE   │              │  REPORT PAGES    │
│  (Execution)     │              │  (Viewing)       │
│                  │              │                  │
│ - Selectors      │              │ - Report List    │
│ - Form           │              │ - Report Detail  │
│ - Execute BTN    │              │ - Export BTN     │
└──────────────────┘              └──────────────────┘
        ↓                                      ↓
        └──────────────┬───────────────────────┘
                       ↓
            ┌─────────────────────────┐
            │   SERVICE LAYER         │
            │                         │
            │ - PlatformParityService │
            │ - ReportService         │
            │ - ApiService            │
            └─────────────────────────┘
                       ↓
            ┌─────────────────────────┐
            │   HTTP CLIENT LAYER     │
            │   (HttpClient)          │
            └─────────────────────────┘
```

### 1.3 State Management Strategy

**NO NgRx/Global State Management Required**

State will be managed locally at component level using:
- Reactive Forms for analyzer form state
- Component @Input/@Output for parent-child communication
- RxJS observables for async operations
- LocalStorage for caching (optional: recent reports)

**Rationale:** Platform Parity is a self-contained feature with no complex inter-component state sharing. The existing pace-git-lift-ui codebase also avoids NgRx for similar components.

---

## Backend Integration Context

### 2.1 Platform Parity Backend Overview

The backend consists of three separate systems that work together:

| System | Location | Purpose |
|--------|----------|---------|
| **Script Executor** | pace-git-lift-api/src/scm_migration_tool/script_executor | Orchestrates script-based workflows via Temporal |
| **Platform Parity CLI** | pace-scm-migration-scripts/platform_parity | Local analysis engine with deterministic comparison + Bedrock formatting |
| **Platform Parity Worker** | pace-git-lift-api/src/scm_migration_tool/temporal/workers/activities/commons/platform_parity | Temporal activity that runs analysis and stores results |

### 2.2 Execution Flow

```
┌────────────────────────────────────────────────────────────┐
│  1. USER INITIATES ANALYSIS (Frontend)                     │
│     POST /api/v1/platform-parity/compare                   │
│     { source_platform, target_platform }                   │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│  2. API VALIDATES & DISPATCHES (Git-Lift API Pod)          │
│     - Validate platform values (GitLab, GitHub, etc.)      │
│     - Create workflow execution record (DB)                │
│     - Dispatch to Temporal queue via ScriptExecutor        │
│     - Return execution_id + status=PENDING                 │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│  3. WORKFLOW EXECUTES (Worker Pod)                         │
│     Multi-step script workflow:                            │
│     Step 1: platform_parity_init.py                        │
│       - Validates source/target                            │
│       - Passes params to next steps                        │
│     Step 2: platform_parity_load_kb.py                     │
│       - Loads capabilities from DB                         │
│     Step 3: platform_parity_parse_discovery.py             │
│       - [Optional] Parses discovery report                 │
│     Step 4: platform_parity_kb_updater.py                  │
│       - [Optional] Updates KB with live docs               │
│     Step 5: platform_parity_generate_report.py             │
│       - Calls AWS Bedrock to format report                 │
│       - Stores result in parity.parity_reports DB table    │
│     Step 6: platform_parity_export.py                      │
│       - Assembles final structured report                  │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│  4. FRONTEND POLLS STATUS (Optional)                       │
│     GET /api/v1/platform-parity/status/{execution_id}      │
│     Returns: { status, progress, error, report_id }        │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│  5. REPORT AVAILABLE (Frontend Fetches)                    │
│     GET /api/v1/platform-parity/reports/{report_id}        │
│     Returns full report: sections, gaps, coverage, etc.    │
└────────────────────────────────────────────────────────────┘
```

### 2.3 Report Structure (Backend Output)

The backend outputs a report with this structure:

```json
{
  "report_id": "gitlab_to_github_7895f1aba77c",
  "source_platform": "gitlab",
  "target_platform": "github",
  "generated_at": "2026-08-31T14:23:45Z",
  "overall_risk": "MEDIUM",
  "sections": {
    "executive_summary": {
      "title": "Executive Summary",
      "content": "Migrating from GitLab to GitHub...",
      "metrics": {
        "total_capabilities": 54,
        "supported": 48,
        "partial": 4,
        "unsupported": 2,
        "coverage_percentage": 88.9
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
          "source_behavior": "GitLab shared runners available",
          "target_behavior": "GitHub Actions requires self-hosted for equivalent",
          "migration_impact": "High effort remediation needed",
          "workaround": "Use GitHub Actions with self-hosted runners"
        }
      ]
    },
    "behavioral_differences": {
      "title": "🟡 Behavioral Differences",
      "items": [ /* similar structure */ ]
    },
    "seamless_migrations": {
      "title": "🟢 Seamless Migrations",
      "items": [ /* similar structure */ ]
    },
    "coverage_report": {
      "title": "📋 Coverage Report",
      "by_category": {
        "CI/CD": { "count": 15, "coverage": "86.7%" },
        "Access Control": { "count": 12, "coverage": "91.7%" },
        // ... more categories
      }
    }
  }
}
```

### 2.4 Database Schema (Backend)

The backend stores reports in `parity.parity_reports` table:

| Column | Type | Purpose |
|--------|------|---------|
| report_id | uuid | Primary key |
| source_platform | varchar | e.g., "gitlab" |
| target_platform | varchar | e.g., "github" |
| report_content | jsonb | Full report JSON |
| markdown_content | text | Markdown-formatted report |
| generated_at | timestamp | When analysis was run |
| generated_by | varchar | User ID |
| execution_id | uuid | Temporal execution ID (foreign key) |
| status | enum | PENDING, COMPLETED, FAILED |
| error_message | text | If status=FAILED |

---

## Component Hierarchy & Module Structure

### 3.1 File Structure

```
src/app/
└── script-box/
    └── platform-parity/                          ← NEW MODULE
        ├── platform-parity.component.ts          ← Container/Router
        ├── platform-parity.component.html        ← Placeholder for <router-outlet>
        ├── platform-parity.component.scss        ← Module-level styles
        │
        ├── analyzer/                             ← Feature: Run Analysis
        │   ├── analyzer.component.ts
        │   ├── analyzer.component.html
        │   ├── analyzer.component.scss
        │   └── analyzer.component.spec.ts
        │
        ├── report-list/                          ← Feature: View History
        │   ├── report-list.component.ts
        │   ├── report-list.component.html
        │   ├── report-list.component.scss
        │   └── report-list.component.spec.ts
        │
        ├── report-detail/                        ← Feature: View Report
        │   ├── report-detail.component.ts
        │   ├── report-detail.component.html
        │   ├── report-detail.component.scss
        │   ├── report-detail.component.spec.ts
        │   │
        │   └── report-sections/                  ← Sub-components
        │       ├── executive-summary-section.component.ts
        │       ├── hard-blockers-section.component.ts
        │       ├── behavioral-differences-section.component.ts
        │       ├── seamless-migrations-section.component.ts
        │       └── coverage-report-section.component.ts
        │
        └── shared/                               ← Module Shared Utils
            ├── models/
            │   └── parity-report.model.ts        ← Report interfaces
            │
            ├── services/
            │   ├── platform-parity-api.service.ts      ← HTTP calls
            │   ├── platform-parity-api.service.spec.ts
            │   ├── parity-state.service.ts       ← Local state mgmt
            │   └── parity-state.service.spec.ts
            │
            └── pipes/
                └── risk-level.pipe.ts            ← Display formatting

```

### 3.2 Component Hierarchy

```
PlatformParityComponent (standalone, lazy-loaded)
│
├── AnalyzerComponent (standalone)
│   ├── Platform selectors (dropdowns)
│   ├── Execute button
│   └── Loading/status indicator
│
├── ReportListComponent (standalone)
│   ├── Table of reports
│   ├── Filter/search
│   └── Delete functionality
│
└── ReportDetailComponent (standalone)
    ├── Report header (metadata)
    │
    ├── ExecutiveSummarySection (standalone)
    │   └── Metrics display
    │
    ├── HardBlockersSection (standalone)
    │   ├── Capability items
    │   └── Impact indicators
    │
    ├── BehavioralDifferencesSection (standalone)
    │   └── Difference cards
    │
    ├── SeamlessmigrationsSection (standalone)
    │   └── Success capability list
    │
    ├── CoverageReportSection (standalone)
    │   └── Category breakdown table
    │
    └── Actions
        ├── Export JSON
        ├── Export Markdown
        └── Delete report
```

---

## Data Models & Interfaces

### 4.1 Platform Parity Models

```typescript
// ── Core Report Models ─────────────────────────────────────

export enum Platform {
  GITLAB = 'gitlab',
  GITHUB = 'github',
  AZURE_DEVOPS = 'azure_devops',
  BITBUCKET = 'bitbucket',
}

export enum CapabilityGapType {
  HARD_BLOCKER = 'HARD_BLOCKER',
  BEHAVIORAL_DIFFERENCE = 'BEHAVIORAL_DIFFERENCE',
  SEAMLESS_MIGRATION = 'SEAMLESS_MIGRATION',
}

export enum RiskLevel {
  CRITICAL = 'CRITICAL',
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW',
  MINIMAL = 'MINIMAL',
}

export enum ReportStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

// ── Capability Gap Item ─────────────────────────────────────

export interface CapabilityGap {
  capability_id: string;
  capability_name: string;
  category: string;
  gap_type: CapabilityGapType;
  source_behavior: string;
  target_behavior: string;
  migration_impact?: string;
  workaround?: string;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW';
  last_verified?: string;
  verification_source?: string;
}

// ── Report Sections ─────────────────────────────────────────

export interface ExecutiveSummarySection {
  title: string;
  content: string;
  metrics: {
    total_capabilities: number;
    supported: number;
    partial: number;
    unsupported: number;
    coverage_percentage: number;
  };
}

export interface GapSection {
  title: string;
  items: CapabilityGap[];
}

export interface CoverageByCategory {
  [category: string]: {
    count: number;
    coverage: string; // e.g., "86.7%"
  };
}

export interface CoverageReportSection {
  title: string;
  by_category: CoverageByCategory;
}

// ── Full Report ─────────────────────────────────────────────

export interface PlatformParityReport {
  report_id: string;
  source_platform: Platform;
  target_platform: Platform;
  generated_at: string; // ISO timestamp
  generated_by?: string;
  overall_risk: RiskLevel;
  sections: {
    executive_summary: ExecutiveSummarySection;
    hard_blockers: GapSection;
    behavioral_differences: GapSection;
    seamless_migrations: GapSection;
    coverage_report: CoverageReportSection;
  };
  // Optional: Original markdown for export
  markdown_content?: string;
}

// ── Execution Status (Polling) ──────────────────────────────

export interface ExecutionStatus {
  execution_id: string;
  status: ReportStatus;
  progress?: number; // 0-100 for in-progress
  report_id?: string; // Populated when COMPLETED
  error_message?: string; // Populated when FAILED
  estimated_seconds_remaining?: number;
}

// ── Report Summary (for list) ───────────────────────────────

export interface ReportSummary {
  report_id: string;
  source_platform: Platform;
  target_platform: Platform;
  generated_at: string;
  generated_by: string;
  overall_risk: RiskLevel;
  coverage_percentage: number;
  blocker_count: number;
  difference_count: number;
  seamless_count: number;
}

// ── Create Request ──────────────────────────────────────────

export interface CreateReportRequest {
  source_platform: Platform;
  target_platform: Platform;
  include_kb_sync?: boolean; // Optional: sync KB with live docs
  output_format?: 'json' | 'markdown' | 'both'; // Default: 'both'
}

// ── List Response ───────────────────────────────────────────

export interface ReportListResponse {
  items: ReportSummary[];
  total: number;
  limit: number;
  offset: number;
}
```

### 4.2 Analyzer Form Model

```typescript
export interface AnalyzerFormValue {
  source_platform: Platform | null;
  target_platform: Platform | null;
  include_kb_sync: boolean;
  output_format: 'json' | 'markdown' | 'both';
}
```

---

## API Contract Definition

### 5.1 API Endpoints Required

The following endpoints must be implemented in `pace-git-lift-api`:

#### Endpoint 1: Create/Execute Analysis

```
POST /api/v1/platform-parity/compare
Content-Type: application/json

Request Body:
{
  "source_platform": "gitlab",
  "target_platform": "github",
  "include_kb_sync": false,
  "output_format": "both"
}

Response (202 Accepted):
{
  "execution_id": "uuid-here",
  "report_id": null,
  "status": "PENDING",
  "message": "Analysis queued. Poll status endpoint for progress."
}

Status Codes:
- 202: Accepted, execution queued
- 400: Invalid platform selection
- 422: Same source and target platform
- 429: Rate limited
- 500: Internal error
```

#### Endpoint 2: Get Execution Status

```
GET /api/v1/platform-parity/status/{execution_id}

Response (200 OK):
{
  "execution_id": "uuid-here",
  "status": "IN_PROGRESS",
  "progress": 45,
  "report_id": null,
  "error_message": null,
  "estimated_seconds_remaining": 30
}

Alternative responses:
- status = "COMPLETED" → report_id populated
- status = "FAILED" → error_message populated

Status Codes:
- 200: Status returned
- 404: Execution not found
- 500: Internal error
```

#### Endpoint 3: Get Report Detail

```
GET /api/v1/platform-parity/reports/{report_id}

Response (200 OK):
{
  "report_id": "gitlab_to_github_7895f1aba77c",
  "source_platform": "gitlab",
  "target_platform": "github",
  "generated_at": "2026-08-31T14:23:45Z",
  "generated_by": "user123",
  "overall_risk": "MEDIUM",
  "sections": {
    "executive_summary": { ... },
    "hard_blockers": { ... },
    "behavioral_differences": { ... },
    "seamless_migrations": { ... },
    "coverage_report": { ... }
  },
  "markdown_content": "# Report\n## 1. Executive Summary\n..."
}

Status Codes:
- 200: Report found and returned
- 404: Report not found
- 500: Internal error
```

#### Endpoint 4: List Reports (History)

```
GET /api/v1/platform-parity/reports?limit=20&offset=0&sort_by=generated_at&order=desc

Query Parameters:
- limit: int (default: 20, max: 100)
- offset: int (default: 0)
- sort_by: string (generated_at, overall_risk, source_platform)
- order: string (asc, desc)

Response (200 OK):
{
  "items": [
    {
      "report_id": "gitlab_to_github_7895f1aba77c",
      "source_platform": "gitlab",
      "target_platform": "github",
      "generated_at": "2026-08-31T14:23:45Z",
      "generated_by": "user123",
      "overall_risk": "MEDIUM",
      "coverage_percentage": 88.9,
      "blocker_count": 2,
      "difference_count": 4,
      "seamless_count": 48
    }
  ],
  "total": 127,
  "limit": 20,
  "offset": 0
}

Status Codes:
- 200: List returned
- 500: Internal error
```

#### Endpoint 5: Delete Report

```
DELETE /api/v1/platform-parity/reports/{report_id}

Response (204 No Content):
(empty)

Status Codes:
- 204: Successfully deleted
- 404: Report not found
- 403: Insufficient permission
- 500: Internal error
```

### 5.2 Backend Compatibility Notes

**Important:** The backend may route these through Script Executor or implement them directly. The frontend doesn't care about the implementation—just the contracts above.

Possible implementations:
1. **Direct FastAPI router** in a new `platform_parity_router.py` file
2. **Script Executor workflow** that dispatches to platform_parity scripts
3. **Hybrid** - Status/List via direct API, Analysis via Script Executor

**Frontend is implementation-agnostic** as long as the contracts are met.

---

## Feature Breakdown - Phase by Phase

### Phase 1: Core Analyzer (Weeks 1-2)

**Goal:** Users can execute platform comparisons

**Deliverables:**

1. **AnalyzerComponent**
   - [ ] Platform selector dropdowns (GitLab, GitHub, Azure DevOps, Bitbucket)
   - [ ] Form validation (both platforms selected, not identical)
   - [ ] Execute button (disabled while validation fails)
   - [ ] Loading spinner during analysis
   - [ ] Success toast with report_id
   - [ ] Error handling with toast notification
   - [ ] Auto-redirect to report detail on completion

2. **PlatformParityApiService**
   - [ ] `createAnalysis(request: CreateReportRequest): Observable<ExecutionStatus>`
   - [ ] `getExecutionStatus(execution_id): Observable<ExecutionStatus>`
   - [ ] Polling logic (retry with exponential backoff)

3. **Models & Interfaces**
   - [ ] All core interfaces in `parity-report.model.ts`
   - [ ] Enums for Platform, RiskLevel, ReportStatus, etc.

4. **Unit Tests**
   - [ ] Analyzer form validation tests
   - [ ] API service mocking tests
   - [ ] Error handling tests

**Acceptance Criteria:**
- ✅ User can select two different platforms
- ✅ Clicking "Analyze" sends request to backend
- ✅ Loading state shown while waiting
- ✅ On completion, auto-navigates to report view
- ✅ Errors show as toast notifications

---

### Phase 2: Report Detail Viewer (Weeks 2-3)

**Goal:** Users can view detailed analysis reports

**Deliverables:**

1. **ReportDetailComponent**
   - [ ] Header with metadata (platforms, risk level, timestamp)
   - [ ] Report sections container
   - [ ] Back navigation
   - [ ] Fetch report by ID on init

2. **Report Section Components** (5 sub-components)
   - [ ] ExecutiveSummarySectionComponent
     - Metrics display (total, supported, partial, unsupported, coverage %)
     - Content rendering
   - [ ] HardBlockersSectionComponent
     - Capability gap items
     - Risk badge styling (🔴 red)
     - Workaround display
   - [ ] BehavioralDifferencesSectionComponent
     - Capability gap items
     - Difference highlighting (🟡 yellow)
   - [ ] SeamlessMigrationsSectionComponent
     - Capability list (🟢 green)
     - Simple styling
   - [ ] CoverageReportSectionComponent
     - Category breakdown table
     - Coverage percentages

3. **Export Functionality**
   - [ ] Export JSON button
   - [ ] Export Markdown button (if available from backend)
   - [ ] Copy link to clipboard

4. **PlatformParityApiService Extensions**
   - [ ] `getReport(report_id): Observable<PlatformParityReport>`

5. **Unit Tests**
   - [ ] Report fetch and render tests
   - [ ] Section component rendering tests
   - [ ] Export functionality tests

**Acceptance Criteria:**
- ✅ Report displays all 5 sections correctly
- ✅ Risk badges and emojis render properly
- ✅ Export buttons work (downloads files)
- ✅ Responsive on mobile and desktop
- ✅ No layout shift during load

---

### Phase 3: Report History & Management (Weeks 3-4)

**Goal:** Users can browse and manage previous reports

**Deliverables:**

1. **ReportListComponent**
   - [ ] Table of past reports
   - [ ] Columns: Source, Target, Risk, Generated At, Coverage, Actions
   - [ ] Sorting (by date, platform, risk)
   - [ ] Pagination (20 per page)
   - [ ] Row click navigates to detail
   - [ ] Delete action with confirmation
   - [ ] Filter/search by platform pair (future enhancement)

2. **Report Status Indicators**
   - [ ] Badge styling for risk levels
   - [ ] Color coding (red/yellow/green)

3. **PlatformParityApiService Extensions**
   - [ ] `listReports(limit, offset, sort): Observable<ReportListResponse>`
   - [ ] `deleteReport(report_id): Observable<void>`

4. **Storage (Optional)**
   - [ ] LocalStorage caching of report summaries (for UX speed)
   - [ ] Cache invalidation on delete

5. **Unit Tests**
   - [ ] List fetch and render tests
   - [ ] Pagination tests
   - [ ] Delete confirmation tests

**Acceptance Criteria:**
- ✅ Report list loads and displays correctly
- ✅ Sorting and pagination work
- ✅ Delete with confirmation works
- ✅ Clicking report navigates to detail
- ✅ Empty state message when no reports

---

### Phase 4: Polish & Optimization (Week 4)

**Goal:** Production-ready UI with performance and accessibility

**Deliverables:**

1. **Performance**
   - [ ] Lazy-loaded module bundle
   - [ ] OnPush change detection where appropriate
   - [ ] Unsubscribe from observables properly (takeUntil)
   - [ ] Image/icon optimization

2. **UX Enhancements**
   - [ ] Loading skeletons (ngx-skeleton-loader)
   - [ ] Empty states for all pages
   - [ ] Keyboard navigation support
   - [ ] Mobile-responsive design

3. **Accessibility**
   - [ ] ARIA labels on buttons/icons
   - [ ] Color contrast compliance
   - [ ] Semantic HTML structure

4. **Error Handling**
   - [ ] Graceful 404 for missing reports
   - [ ] Network error recovery
   - [ ] Timeout handling for long-running analyses

5. **Documentation**
   - [ ] Component README files
   - [ ] API integration guide
   - [ ] Contributing guide

6. **E2E Tests** (Karma)
   - [ ] Full user flow tests
   - [ ] Report CRUD tests
   - [ ] Error scenario tests

---

## Routing Configuration

### 6.1 Route Structure

In `app.routes.ts`, add platform-parity routes:

```typescript
{
  path: 'orchestrator',
  loadComponent: () => import('./script-box/script-box.component').then(m => m.ScriptBoxComponent),
  children: [
    // ... existing routes ...
    
    {
      path: 'platform-parity',
      loadComponent: () =>
        import('./script-box/platform-parity/platform-parity.component').then(
          m => m.PlatformParityComponent
        ),
      children: [
        {
          path: '',
          pathMatch: 'full',
          redirectTo: 'analyzer',
        },
        {
          path: 'analyzer',
          loadComponent: () =>
            import('./script-box/platform-parity/analyzer/analyzer.component').then(
              m => m.AnalyzerComponent
            ),
        },
        {
          path: 'reports',
          loadComponent: () =>
            import('./script-box/platform-parity/report-list/report-list.component').then(
              m => m.ReportListComponent
            ),
        },
        {
          path: 'reports/:reportId',
          loadComponent: () =>
            import('./script-box/platform-parity/report-detail/report-detail.component').then(
              m => m.ReportDetailComponent
            ),
        },
      ],
    },
  ],
}
```

### 6.2 Navigation Flow

```
/platform-parity
  ↓
  /analyzer (default) → User selects platforms → Execute
                         ↓
                         Polling status
                         ↓
                         Auto-redirect to /reports/:reportId
                         
  /reports → List of all reports
              ↓
              Click row → Navigate to /reports/:reportId
              
  /reports/:reportId → View report detail
                       Actions: Export, Delete, Back
```

---

## Service Layer Design

### 7.1 PlatformParityApiService

**File:** `src/app/script-box/platform-parity/shared/services/platform-parity-api.service.ts`

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { catchError, retry, timeout } from 'rxjs/operators';
import { ENV_TOKEN } from '../../app.token';
import { Env } from '../../../environments/env.common';
import {
  CreateReportRequest,
  ExecutionStatus,
  PlatformParityReport,
  ReportListResponse,
  ReportSummary,
} from '../shared/models/parity-report.model';

@Injectable({ providedIn: 'root' })
export class PlatformParityApiService {
  private readonly http = inject(HttpClient);
  private readonly env: Env = inject(ENV_TOKEN);
  private readonly baseUrl = `${this.env.serviceUrl}/api/v1/platform-parity`;

  /**
   * Initiate platform parity analysis
   * Returns execution ID for polling
   */
  createAnalysis(request: CreateReportRequest): Observable<ExecutionStatus> {
    return this.http.post<ExecutionStatus>(`${this.baseUrl}/compare`, request).pipe(
      timeout(30000), // 30 second timeout
      retry({ count: 1, delay: 1000 }),
      catchError(err => this.handleError('Analysis creation failed', err))
    );
  }

  /**
   * Poll execution status
   * Used to track progress until report is ready
   */
  getExecutionStatus(execution_id: string): Observable<ExecutionStatus> {
    return this.http.get<ExecutionStatus>(`${this.baseUrl}/status/${execution_id}`).pipe(
      timeout(10000),
      catchError(err => this.handleError('Status fetch failed', err))
    );
  }

  /**
   * Get full report by ID
   * Call this when status.status === 'COMPLETED'
   */
  getReport(report_id: string): Observable<PlatformParityReport> {
    return this.http.get<PlatformParityReport>(`${this.baseUrl}/reports/${report_id}`).pipe(
      timeout(15000),
      retry({ count: 1, delay: 1000 }),
      catchError(err => this.handleError('Report fetch failed', err))
    );
  }

  /**
   * List all past reports with pagination & sorting
   */
  listReports(
    limit: number = 20,
    offset: number = 0,
    sortBy: string = 'generated_at',
    order: string = 'desc'
  ): Observable<ReportListResponse> {
    const params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString())
      .set('sort_by', sortBy)
      .set('order', order);

    return this.http.get<ReportListResponse>(`${this.baseUrl}/reports`, { params }).pipe(
      timeout(10000),
      catchError(err => this.handleError('Report list fetch failed', err))
    );
  }

  /**
   * Delete a specific report
   */
  deleteReport(report_id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/reports/${report_id}`).pipe(
      timeout(10000),
      catchError(err => this.handleError('Report deletion failed', err))
    );
  }

  /**
   * Helper: Handle HTTP errors with logging
   */
  private handleError(context: string, err: any): Observable<never> {
    console.error(`[PlatformParity] ${context}:`, err);
    return throwError(() => ({
      message: context,
      status: err.status,
      error: err.error,
    }));
  }
}
```

### 7.2 ParityStateService (Optional - Local State)

**File:** `src/app/script-box/platform-parity/shared/services/parity-state.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { ReportSummary } from '../models/parity-report.model';

/**
 * Local state management for platform parity
 * Manages UI state like selected report, list cache, etc.
 */
@Injectable({ providedIn: 'root' })
export class ParityStateService {
  private selectedReport$ = new BehaviorSubject<ReportSummary | null>(null);
  private recentReports$ = new BehaviorSubject<ReportSummary[]>([]);

  getSelectedReport(): Observable<ReportSummary | null> {
    return this.selectedReport$.asObservable();
  }

  setSelectedReport(report: ReportSummary | null): void {
    this.selectedReport$.next(report);
  }

  getRecentReports(): Observable<ReportSummary[]> {
    return this.recentReports$.asObservable();
  }

  setRecentReports(reports: ReportSummary[]): void {
    this.recentReports$.next(reports);
  }

  addRecentReport(report: ReportSummary): void {
    const current = this.recentReports$.value;
    this.recentReports$.next([report, ...current.slice(0, 19)]);
  }

  clear(): void {
    this.selectedReport$.next(null);
    this.recentReports$.next([]);
  }
}
```

---

## Component Details

### 8.1 PlatformParityComponent (Container)

**File:** `src/app/script-box/platform-parity/platform-parity.component.ts`

```typescript
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { UiKitModule } from '@dagility-ui/kit';

@Component({
  selector: 'app-platform-parity',
  standalone: true,
  imports: [CommonModule, RouterOutlet, UiKitModule],
  template: `
    <div class="platform-parity-container">
      <router-outlet></router-outlet>
    </div>
  `,
  styles: [`
    .platform-parity-container {
      padding: 1rem;
      background-color: #f8f9fa;
      min-height: 100vh;
    }
  `],
})
export class PlatformParityComponent {}
```

### 8.2 AnalyzerComponent

**File:** `src/app/script-box/platform-parity/analyzer/analyzer.component.ts`

```typescript
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, interval } from 'rxjs';
import { takeUntil, switchMap, finalize } from 'rxjs/operators';
import { ToasterService } from '@dagility-ui/shared-components';
import { UiKitModule } from '@dagility-ui/kit';
import { PlatformParityApiService } from '../shared/services/platform-parity-api.service';
import { Platform, ReportStatus, ExecutionStatus } from '../shared/models/parity-report.model';

@Component({
  selector: 'app-analyzer',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, UiKitModule],
  templateUrl: './analyzer.component.html',
  styleUrl: './analyzer.component.scss',
})
export class AnalyzerComponent implements OnInit, OnDestroy {
  private fb = inject(FormBuilder);
  private api = inject(PlatformParityApiService);
  private router = inject(Router);
  private toaster = inject(ToasterService);
  private destroy$ = new Subject<void>();

  form = this.fb.group({
    source_platform: [null as Platform | null, Validators.required],
    target_platform: [null as Platform | null, Validators.required],
    include_kb_sync: [false],
    output_format: ['both' as 'json' | 'markdown' | 'both'],
  });

  platforms = Object.values(Platform);
  isAnalyzing = false;
  analysisProgress = 0;
  currentExecutionId: string | null = null;

  ngOnInit(): void {
    this.form.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.validatePlatforms());
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  validatePlatforms(): void {
    const source = this.form.value.source_platform;
    const target = this.form.value.target_platform;

    if (source && target && source === target) {
      this.form.setErrors({ samePlatform: true });
    }
  }

  execute(): void {
    if (this.form.invalid) return;

    this.isAnalyzing = true;
    this.analysisProgress = 0;

    const request = {
      source_platform: this.form.value.source_platform!,
      target_platform: this.form.value.target_platform!,
      include_kb_sync: this.form.value.include_kb_sync || false,
      output_format: (this.form.value.output_format || 'both') as 'json' | 'markdown' | 'both',
    };

    this.api.createAnalysis(request)
      .pipe(
        switchMap((response: ExecutionStatus) => {
          this.currentExecutionId = response.execution_id;
          // Poll status every 2 seconds
          return interval(2000).pipe(
            switchMap(() => this.api.getExecutionStatus(response.execution_id)),
            takeUntil(
              new Subject<ExecutionStatus>().pipe(
                switchMap((status) => {
                  if (status.status === ReportStatus.COMPLETED) {
                    return of(status);
                  } else if (status.status === ReportStatus.FAILED) {
                    throw new Error(status.error_message || 'Analysis failed');
                  }
                  this.analysisProgress = status.progress || 0;
                  return EMPTY;
                })
              )
            )
          );
        }),
        finalize(() => (this.isAnalyzing = false)),
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (status: ExecutionStatus) => {
          this.toaster.successToast({
            title: 'Analysis Complete',
            content: 'Redirecting to report...',
          });
          this.router.navigate(['/orchestrator/platform-parity/reports', status.report_id]);
        },
        error: (err) => {
          this.toaster.errorToast({
            title: 'Analysis Failed',
            content: err.message || 'An error occurred during analysis.',
          });
        },
      });
  }

  getAnalyzeButtonText(): string {
    if (this.isAnalyzing) {
      return `Analyzing... ${this.analysisProgress}%`;
    }
    return 'Analyze';
  }
}
```

**Template:** `analyzer.component.html`

```html
<div class="analyzer-container">
  <div class="card">
    <div class="card-header">
      <h3>Platform Parity Analyzer</h3>
      <p class="text-muted mb-0">
        Compare source and target SCM platforms to identify migration gaps and compatibility issues.
      </p>
    </div>

    <div class="card-body">
      <form [formGroup]="form" class="analyzer-form">
        <!-- Source Platform -->
        <div class="form-group">
          <label for="source">Source Platform *</label>
          <select
            id="source"
            class="form-control"
            formControlName="source_platform"
            [disabled]="isAnalyzing"
          >
            <option [value]="null">Select source platform...</option>
            <option *ngFor="let platform of platforms" [value]="platform">
              {{ platform | uppercase }}
            </option>
          </select>
          <small class="form-text text-muted">The platform you're migrating FROM</small>
        </div>

        <!-- Target Platform -->
        <div class="form-group">
          <label for="target">Target Platform *</label>
          <select
            id="target"
            class="form-control"
            formControlName="target_platform"
            [disabled]="isAnalyzing"
          >
            <option [value]="null">Select target platform...</option>
            <option *ngFor="let platform of platforms" [value]="platform">
              {{ platform | uppercase }}
            </option>
          </select>
          <small class="form-text text-muted">The platform you're migrating TO</small>
        </div>

        <!-- Options -->
        <div class="form-group">
          <div class="form-check">
            <input
              type="checkbox"
              class="form-check-input"
              id="kb_sync"
              formControlName="include_kb_sync"
              [disabled]="isAnalyzing"
            />
            <label class="form-check-label" for="kb_sync">
              Sync with latest documentation (KB update)
            </label>
          </div>
        </div>

        <!-- Output Format -->
        <div class="form-group">
          <label for="format">Output Format</label>
          <select
            id="format"
            class="form-control"
            formControlName="output_format"
            [disabled]="isAnalyzing"
          >
            <option value="json">JSON</option>
            <option value="markdown">Markdown</option>
            <option value="both">Both (JSON + Markdown)</option>
          </select>
        </div>

        <!-- Progress Bar (while analyzing) -->
        <div *ngIf="isAnalyzing" class="progress mb-3">
          <div
            class="progress-bar progress-bar-striped progress-bar-animated"
            [style.width.%]="analysisProgress"
          >
            {{ analysisProgress }}%
          </div>
        </div>

        <!-- Error Message -->
        <div *ngIf="form.errors?.['samePlatform']" class="alert alert-warning" role="alert">
          Source and target platforms must be different.
        </div>

        <!-- Buttons -->
        <div class="d-flex gap-2">
          <button
            type="button"
            class="btn btn-primary"
            (click)="execute()"
            [disabled]="form.invalid || isAnalyzing"
          >
            <span *ngIf="!isAnalyzing">
              <fa-icon icon="startPlay" class="mr-2"></fa-icon>
              {{ getAnalyzeButtonText() }}
            </span>
            <span *ngIf="isAnalyzing">
              <span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>
              {{ getAnalyzeButtonText() }}
            </span>
          </button>

          <button
            type="button"
            class="btn btn-secondary"
            (click)="form.reset()"
            [disabled]="isAnalyzing"
          >
            Clear Form
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Info Card -->
  <div class="card mt-3">
    <div class="card-header bg-light">
      <h5>About Platform Parity Analysis</h5>
    </div>
    <div class="card-body small">
      <p>
        This tool analyzes the compatibility between source and target SCM platforms by comparing
        supported capabilities. The report identifies:
      </p>
      <ul>
        <li><strong>Hard Blockers (🔴)</strong> - Critical gaps requiring workarounds</li>
        <li><strong>Behavioral Differences (🟡)</strong> - Features that work differently</li>
        <li><strong>Seamless Migrations (🟢)</strong> - Features that migrate cleanly</li>
        <li><strong>Coverage Report</strong> - Overall compatibility metrics</li>
      </ul>
      <p class="mb-0 text-muted">
        Analysis typically takes 30-60 seconds. You'll be notified when the report is ready.
      </p>
    </div>
  </div>
</div>
```

### 8.3 ReportDetailComponent

**File:** `src/app/script-box/platform-parity/report-detail/report-detail.component.ts`

```typescript
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ToasterService } from '@dagility-ui/shared-components';
import { UiKitModule } from '@dagility-ui/kit';
import { PlatformParityApiService } from '../shared/services/platform-parity-api.service';
import { PlatformParityReport, RiskLevel } from '../shared/models/parity-report.model';
import { ExecutiveSummarySectionComponent } from './report-sections/executive-summary-section.component';
import { HardBlockersSectionComponent } from './report-sections/hard-blockers-section.component';
import { BehavioralDifferencesSectionComponent } from './report-sections/behavioral-differences-section.component';
import { SeamlessMigrationsSectionComponent } from './report-sections/seamless-migrations-section.component';
import { CoverageReportSectionComponent } from './report-sections/coverage-report-section.component';

@Component({
  selector: 'app-report-detail',
  standalone: true,
  imports: [
    CommonModule,
    UiKitModule,
    ExecutiveSummarySectionComponent,
    HardBlockersSectionComponent,
    BehavioralDifferencesSectionComponent,
    SeamlessMigrationsSectionComponent,
    CoverageReportSectionComponent,
  ],
  templateUrl: './report-detail.component.html',
  styleUrl: './report-detail.component.scss',
})
export class ReportDetailComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private api = inject(PlatformParityApiService);
  private toaster = inject(ToasterService);
  private destroy$ = new Subject<void>();

  report: PlatformParityReport | null = null;
  loading = true;
  error: string | null = null;

  ngOnInit(): void {
    const reportId = this.route.snapshot.paramMap.get('reportId');
    if (!reportId) {
      this.error = 'Report ID not found';
      this.loading = false;
      return;
    }

    this.api.getReport(reportId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (report) => {
          this.report = report;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load report. Please try again.';
          this.loading = false;
          this.toaster.errorToast({
            title: 'Load Error',
            content: this.error,
          });
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  goBack(): void {
    this.router.navigate(['/orchestrator/platform-parity/reports']);
  }

  exportJSON(): void {
    if (!this.report) return;

    const json = JSON.stringify(this.report, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    this.downloadBlob(blob, `${this.report.report_id}.json`);

    this.toaster.successToast({
      title: 'Export Successful',
      content: 'Report exported as JSON',
    });
  }

  exportMarkdown(): void {
    if (!this.report || !this.report.markdown_content) {
      this.toaster.warningToast({
        title: 'No Markdown',
        content: 'Markdown content not available for this report.',
      });
      return;
    }

    const blob = new Blob([this.report.markdown_content], { type: 'text/markdown' });
    this.downloadBlob(blob, `${this.report.report_id}.md`);

    this.toaster.successToast({
      title: 'Export Successful',
      content: 'Report exported as Markdown',
    });
  }

  deleteReport(): void {
    if (!this.report) return;

    const confirmed = confirm('Are you sure? This action cannot be undone.');
    if (!confirmed) return;

    this.api.deleteReport(this.report.report_id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.toaster.successToast({
            title: 'Deleted',
            content: 'Report has been deleted.',
          });
          this.goBack();
        },
        error: () => {
          this.toaster.errorToast({
            title: 'Delete Failed',
            content: 'Could not delete report. Please try again.',
          });
        },
      });
  }

  copyReportLink(): void {
    if (!this.report) return;

    const url = `${window.location.origin}/orchestrator/platform-parity/reports/${this.report.report_id}`;
    navigator.clipboard.writeText(url).then(() => {
      this.toaster.successToast({
        title: 'Copied',
        content: 'Report link copied to clipboard.',
      });
    });
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  }

  getRiskBadgeClass(): string {
    if (!this.report) return '';

    const riskMap: Record<RiskLevel, string> = {
      CRITICAL: 'badge-danger',
      HIGH: 'badge-warning',
      MEDIUM: 'badge-info',
      LOW: 'badge-success',
      MINIMAL: 'badge-light',
    };

    return riskMap[this.report.overall_risk] || 'badge-secondary';
  }
}
```

**Template:** `report-detail.component.html`

```html
<div class="report-detail-container">
  <!-- Loading State -->
  <div *ngIf="loading" class="text-center py-5">
    <div class="spinner-border text-primary mb-3"></div>
    <p>Loading report...</p>
  </div>

  <!-- Error State -->
  <div *ngIf="error && !loading" class="alert alert-danger" role="alert">
    {{ error }}
    <button type="button" class="btn btn-sm btn-primary mt-2" (click)="goBack()">
      Back to Reports
    </button>
  </div>

  <!-- Report Content -->
  <ng-container *ngIf="report && !loading && !error">
    <!-- Header -->
    <div class="report-header card mb-4">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start mb-3">
          <div>
            <h2>Platform Parity Report</h2>
            <p class="text-muted mb-0">
              {{ report.source_platform | uppercase }} → {{ report.target_platform | uppercase }}
            </p>
          </div>
          <div class="text-right">
            <span [ngClass]="'badge ' + getRiskBadgeClass()">
              Overall Risk: {{ report.overall_risk }}
            </span>
          </div>
        </div>

        <div class="row small text-muted">
          <div class="col-md-3">
            <strong>Generated:</strong> {{ report.generated_at | date: 'medium' }}
          </div>
          <div class="col-md-3">
            <strong>By:</strong> {{ report.generated_by || 'System' }}
          </div>
          <div class="col-md-6">
            <strong>Report ID:</strong> <code>{{ report.report_id }}</code>
          </div>
        </div>
      </div>
    </div>

    <!-- Report Sections -->
    <div class="report-sections">
      <app-executive-summary-section
        [section]="report.sections.executive_summary"
      ></app-executive-summary-section>

      <app-hard-blockers-section
        [section]="report.sections.hard_blockers"
      ></app-hard-blockers-section>

      <app-behavioral-differences-section
        [section]="report.sections.behavioral_differences"
      ></app-behavioral-differences-section>

      <app-seamless-migrations-section
        [section]="report.sections.seamless_migrations"
      ></app-seamless-migrations-section>

      <app-coverage-report-section
        [section]="report.sections.coverage_report"
      ></app-coverage-report-section>
    </div>

    <!-- Actions -->
    <div class="report-actions mt-4 d-flex gap-2">
      <button class="btn btn-primary" (click)="exportJSON()">
        <fa-icon icon="facDownload" class="mr-2"></fa-icon>Export JSON
      </button>

      <button class="btn btn-primary" (click)="exportMarkdown()" *ngIf="report.markdown_content">
        <fa-icon icon="facDownload" class="mr-2"></fa-icon>Export Markdown
      </button>

      <button class="btn btn-secondary" (click)="copyReportLink()">
        <fa-icon icon="link" class="mr-2"></fa-icon>Copy Link
      </button>

      <button class="btn btn-outline-danger ml-auto" (click)="deleteReport()">
        <fa-icon icon="trash" class="mr-2"></fa-icon>Delete
      </button>

      <button class="btn btn-secondary" (click)="goBack()">
        <fa-icon icon="chevronLeft" class="mr-2"></fa-icon>Back
      </button>
    </div>
  </ng-container>
</div>
```

### 8.4 Report Section Components

I'll provide one example; the others follow the same pattern.

**Hard Blockers Section:** `hard-blockers-section.component.ts`

```typescript
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GapSection } from '../../shared/models/parity-report.model';

@Component({
  selector: 'app-hard-blockers-section',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="section-card card mb-4">
      <div class="card-header bg-danger text-white">
        <h4 class="mb-0">{{ section.title }}</h4>
      </div>
      <div class="card-body">
        <div *ngIf="section.items.length === 0" class="text-muted">
          <p class="mb-0">No hard blockers identified! Migration should be straightforward.</p>
        </div>

        <div *ngFor="let gap of section.items" class="gap-item mb-3">
          <div class="d-flex align-items-start">
            <span class="badge badge-danger mr-2">{{ gap.category }}</span>
            <div class="flex-grow-1">
              <h6>{{ gap.capability_name }}</h6>
              <p class="small text-muted mb-1">
                <strong>{{ gap.source_behavior }}</strong>
              </p>
              <p class="small mb-1">
                ↓ Becomes ↓
              </p>
              <p class="small text-danger mb-2">
                <strong>{{ gap.target_behavior }}</strong>
              </p>
              <p class="small text-warning mb-1" *ngIf="gap.migration_impact">
                <strong>Impact:</strong> {{ gap.migration_impact }}
              </p>
              <p class="small mb-0" *ngIf="gap.workaround">
                <strong>Workaround:</strong> {{ gap.workaround }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .gap-item {
      border-left: 3px solid #dc3545;
      padding-left: 1rem;
    }
  `],
})
export class HardBlockersSectionComponent {
  @Input() section!: GapSection;
}
```

---

## Styling & Layout Patterns

### 9.1 Global Styling

**File:** Add to existing `src/styles.scss`

```scss
// Platform Parity Module Styles
.platform-parity-container {
  background-color: #f8f9fa;
  min-height: 100vh;
}

// Cards
.section-card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
  border: none;

  .card-header {
    padding: 1rem;
    font-weight: 600;
  }

  .card-body {
    padding: 1.5rem;
  }
}

// Risk Badge Colors
.badge-risk-critical {
  background-color: #dc3545;
}

.badge-risk-high {
  background-color: #fd7e14;
}

.badge-risk-medium {
  background-color: #ffc107;
  color: #333;
}

.badge-risk-low {
  background-color: #28a745;
}

.badge-risk-minimal {
  background-color: #e2e3e5;
  color: #333;
}

// Gap Items
.gap-item {
  padding: 1rem;
  border-radius: 0.25rem;
  background-color: #f8f9fa;
  margin-bottom: 1rem;

  &:last-child {
    margin-bottom: 0;
  }
}

// Report Actions
.report-actions {
  padding: 2rem 0;
  border-top: 1px solid #dee2e6;

  .btn {
    min-width: 140px;
  }
}

// Responsive Adjustments
@media (max-width: 768px) {
  .platform-parity-container {
    padding: 0.5rem;
  }

  .section-card {
    margin-bottom: 1rem;
  }

  .report-actions {
    flex-wrap: wrap;
    gap: 0.5rem !important;

    .btn {
      flex-grow: 1;
      min-width: auto;
    }
  }
}
```

### 9.2 Component-Level SCSS

**Analyzer Component:** `analyzer.component.scss`

```scss
.analyzer-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 1rem;

  .card {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .analyzer-form {
    .form-group {
      margin-bottom: 1.5rem;

      label {
        font-weight: 600;
        margin-bottom: 0.5rem;
      }

      select {
        cursor: pointer;

        &:disabled {
          background-color: #e9ecef;
        }
      }
    }

    .progress {
      height: 1.5rem;

      .progress-bar {
        line-height: 1.5rem;
        font-size: 0.875rem;
        font-weight: 600;
      }
    }
  }

  .btn {
    min-width: 120px;
  }
}
```

---

## Testing Strategy

### 10.1 Unit Tests

**Structure:**
- `.component.spec.ts` files for each component
- `.service.spec.ts` files for services
- Minimum 80% code coverage target

**Test Coverage:**

| Component | Tests |
|-----------|-------|
| AnalyzerComponent | Form validation, execution flow, error handling |
| ReportDetailComponent | Data fetching, export functionality, delete action |
| ReportListComponent | List rendering, pagination, sorting, delete |
| API Service | HTTP mocks, error handling, retry logic |

### 10.2 E2E Tests (Karma)

**User flows to test:**
1. Complete analysis execution (end-to-end)
2. Report viewing and navigation
3. Report deletion with confirmation
4. Export functionality
5. Error scenarios (network failure, 404, timeout)

---

## Implementation Checklist

### Phase 1: Core Analyzer
- [ ] Create `platform-parity` folder structure
- [ ] Create `parity-report.model.ts` with all interfaces
- [ ] Create `platform-parity-api.service.ts`
- [ ] Create `analyzer.component.ts` + template + styles
- [ ] Add routes to `app.routes.ts`
- [ ] Write unit tests for analyzer
- [ ] Test execution flow locally
- [ ] Code review & merge

### Phase 2: Report Viewer
- [ ] Create `report-detail.component.ts` + template + styles
- [ ] Create 5 section sub-components
- [ ] Implement export functionality
- [ ] Add delete functionality
- [ ] Write unit tests
- [ ] Test report display locally
- [ ] Code review & merge

### Phase 3: Report History
- [ ] Create `report-list.component.ts` + template + styles
- [ ] Implement pagination & sorting
- [ ] Add delete action with confirmation
- [ ] Write unit tests
- [ ] Test list view locally
- [ ] Code review & merge

### Phase 4: Polish
- [ ] Performance optimization (OnPush, lazy load)
- [ ] Accessibility audit
- [ ] Mobile responsiveness testing
- [ ] Error handling completeness
- [ ] Documentation
- [ ] Final QA testing
- [ ] Production deployment

---

## Deployment & Rollout

### 11.1 Deployment Steps

1. **Backend Readiness**
   - Verify all 5 API endpoints are implemented and tested
   - Confirm database schema and migrations are in place
   - Load test the endpoints

2. **Frontend Deployment**
   - Merge feature branch to main
   - Trigger CI/CD pipeline (build, test, deploy)
   - Deploy to staging environment
   - Smoke test all workflows

3. **Go-Live**
   - Deploy to production
   - Monitor error logs and performance metrics
   - User communication/documentation

### 11.2 Rollback Plan

If critical issues are found post-deployment:
- Feature flag to disable platform-parity route
- Revert to previous deployment version
- Root cause analysis and fix
- Re-deploy after verification

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Backend API delays** | Medium | High | Start implementation with mocked API responses; swap to real API when ready |
| **Report generation timeout** | Medium | Medium | Implement polling with exponential backoff; show estimated time remaining |
| **Large report rendering lag** | Low | Medium | Implement virtual scrolling for large lists; lazy-load sections |
| **Cross-browser issues** | Low | Low | Test in Chrome, Firefox, Safari; use standard Bootstrap classes |
| **Performance degradation** | Low | Medium | Profile with Chrome DevTools; optimize change detection; lazy-load modules |
| **Data consistency** | Low | High | Implement optimistic locking on delete; retry logic for failed API calls |

---

## Conclusion

This implementation plan provides a complete, phased approach to building the Platform Parity frontend. The architecture aligns with existing pace-git-lift-ui patterns, uses proven Angular techniques, and includes comprehensive testing strategy.

**Key Success Factors:**
1. ✅ Clean separation of concerns (services, components, models)
2. ✅ Follows existing code patterns and style
3. ✅ Comprehensive error handling and UX feedback
4. ✅ Testable architecture from the ground up
5. ✅ Performance-conscious design
6. ✅ Accessibility-first approach

**Estimated Timeline:** 4 weeks (with concurrent backend work)

**Success Criteria:**
- All 5 API endpoints integrated and working
- All user workflows functioning end-to-end
- 80%+ test coverage
- Mobile and desktop responsive
- <3 second load time for report list
- Zero blocking issues in production

---

**Document Version:** 1.0  
**Last Updated:** 2026-08-31  
**Ready for Implementation:** ✅ YES
