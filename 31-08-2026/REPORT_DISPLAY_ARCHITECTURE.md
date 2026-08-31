# Report Display Architecture - Comprehensive Analysis

## Executive Summary

The PACE codebase uses a **Component-Based Report Display Pattern** built on Angular 19, Bootstrap 4.6, and direct HTML/CSS rendering. **No Markdown rendering library is currently installed** — reports are displayed using structured Bootstrap components (cards, tables, badges) with Angular directives.

---

## 1. Frontend Report Components

### 1.1 Core Report Display Components

#### **ValidationReportComponent** 
- **Location**: `pace-git-lift-ui/src/app/pages/migration-wrapper/migration-edit/migration/validation-report/`
- **Purpose**: Display migration validation results
- **Key Features**:
  - Fetches data from: `/api/v1/validation_es/{jobId}`
  - Displays summary metrics in card grid (Total Repos, Successful, Partial, Failed)
  - Table view with repository status, source/target URLs, branch counts
  - CSV download button (blob-based download)
  - Refresh functionality with loading states
- **Data Displayed**:
  - `report.job_id`, `report.last_updated`
  - `report.migration_summary`: {total_repositories, successful, partial, failed}
  - `report.repositories[]`: {repo_name, repo_id, status, source, target, branches}

#### **MigrationReportViewerComponent**
- **Location**: `pace-git-lift-ui/src/app/pages/migration-wrapper/migration-edit/migration/migration-report-viewer/`
- **Purpose**: Reusable component for displaying structured validation data
- **Key Features**:
  - Input-based: `@Input() reportData` + `@Input() activeNode`
  - Displays: Header with timestamps, plan ID, migration job ID
  - Summary cards: Overall Status, Validation Score, Issues, Warnings
  - Uses `UiKitModule` for UI components
  - Color-coded status badges (success/warning/danger)
- **Template Pattern**:
  ```html
  <!-- Header with metadata -->
  <!-- 4-column summary grid -->
  <!-- Detailed sections below -->
  ```

#### **DiscoveryReportComponent**
- **Location**: `pace-git-lift-ui/src/app/pages/migration-wrapper/migration-edit/discovery/discovery-report/`
- **Purpose**: Display discovered repositories in tree view
- **Key Features**:
  - Fetches: `/api/v1/planning-phase/tree/{jobId}` (discovery data)
  - Split-pane layout: Repository sidebar + Details pane
  - Search/filter on repository name
  - Buttons: Refresh, Download Report (CSV), Run Detailed Discovery, Plan Migration
  - Auto-navigates to first repo if none selected
- **Download Flow**:
  - Calls: `api.downloadReport(jobId, 'discovery')` → returns Blob
  - Creates filename: `discovery_report_{formatted_timestamp}.csv`
  - Triggers blob download via document.createElement('a')

#### **RepoReportComponent**
- **Location**: `pace-git-lift-ui/src/app/pages/migration-wrapper/migration-edit/discovery/discovery-report/repo-report/`
- **Purpose**: Display detailed discovery data for a single repository
- **Key Features**:
  - Version selector dropdown (displays previous discovery runs)
  - Fetches: `/api/v1/discovery/reports/{jobId}/{repoId}/versions`
  - Renders DepotViewerComponent with detailed repository metadata
  - Nested ItemDetailsComponent for expandable details (commits, files, etc.)
  - Supports path-based on-demand data loading

#### **ExecutiveSummaryComponent**
- **Location**: `pace-git-lift-ui/src/app/pages/migration-wrapper/migration-edit/discovery/executive-summary/`
- **Purpose**: Generate professional executive summary reports
- **Key Features**:
  - Uses: `ExecutiveSummaryDocxService` for DOCX generation
  - Export Data Interface: 50+ statistics fields
  - Generates styled Word document with:
    - Cover page (title, subtitle, project info)
    - Table of contents
    - Content sections with tables
  - Uses `docx` library (already in package.json)
  - Download as: `.docx` file

---

## 2. Report Data Structures

### 2.1 Core Data Models

```typescript
// Validation Report
interface ValidationReport {
  job_id: string;
  last_updated: string;  // ISO timestamp
  migration_summary: {
    total_repositories: number;
    successful: number;
    partial: number;
    failed: number;
  };
  repositories: Repository[];
}

// Repository in Validation Report
interface Repository {
  repo_name: string;
  repo_id: string;
  status: 'MATCH' | 'NOMATCH' | 'PARTIAL';
  source: {
    url: string;
    total_branches: number;
  };
  target: {
    url: string;
    total_branches: number;
  };
  branches: {
    matched: number;
    mismatched: number;
    missing_in_target: number;
  };
}

// Discovery Report Version
interface DiscoveryReportVersion {
  label: string;
  version_str: string;  // e.g., "d1", "dd1"
  type: string;         // phase type (DISCOVERY, DELTA_DISCOVERY, etc.)
}

// Executive Summary Export Data
interface ExecutiveSummaryExportData {
  projectName: string;
  timestamp: string;
  source?: string;
  target?: string;
  total_repository: number;
  total_branches: number;
  total_commits: number;
  // + 50+ additional fields
}

// Planning Phase Tree Response
interface PlanningPhaseResponse {
  repos: Repository[];
  csv_reports: any[];
}
```

### 2.2 Report Status/State Enums

- **Validation Status**: `MATCH`, `NOMATCH`, `PARTIAL`
- **Overall Status**: `PASSED`, `WARNING`, `FAILED`
- **Repository Status**: `DISCOVERY_COMPLETED`, `IN_DISCOVERY`, etc.

---

## 3. API Integration Points

### 3.1 Backend API Endpoints (FastAPI)

**Discovery Endpoints:**
```
POST   /discovery/reports/{job_id}                          → Start report generation
GET    /discovery/reports/{job_id}/{repo_id}                → Get report for repo
GET    /discovery/reports/{job_id}/{repo_id}/versions       → Get version history
GET    /discovery/ondemand/{job_id}/{repo_id}/{version_str} → Get metadata by path
GET    /download-report/{job_id}?report-type=discovery      → CSV export (Blob)
GET    /planning-phase/tree/{job_id}                        → Discovery tree structure
```

**Validation Endpoints:**
```
GET    /validation_reports/{job_id}/{plan_id}               → Validation report
GET    /validation_plans/{job_id}                           → List validation plans
GET    /validation_es/{job_id}                              → New ES-backed report
GET    /scm-validation/compare/{job_id}/{repo_id}           → Comparison data
GET    /validated-repos/{job_id}                            → List of validated repos
```

### 3.2 API Service Layer (Angular)

**APIService** (`pace-git-lift-ui/src/app/shared/services/api.service.ts`):

```typescript
class APIService {
  // Discovery Methods
  prepareDiscoveryReport(jobId, payload): Observable<any>
  getDiscoveryReportVersions(jobId, repoId): Observable<DiscoveryReportVersion[]>
  getDiscoveryReportForRepo(jobId, repoId, version?): Observable<any>
  
  // Validation Methods
  getMigrationSummary(jobId, reportId): Observable<any>
  getValidationPlans(jobId): Observable<any>
  getValidationReport(jobId, reportId): Observable<any>
  getNewValidationReport(jobId): Observable<any>
  getScmComparisonData(jobId, repoId): Observable<any>
  
  // Planning/Tree
  getPlanningPhaseTree(jobId, isPlanning): Observable<any>
  
  // Export
  downloadReport(jobId, type: 'discovery' | 'validation'): Observable<Blob>
}
```

---

## 4. Styling & Rendering Patterns

### 4.1 CSS Framework & Patterns

**Base Framework**: Bootstrap 4.6 + SCSS
- Utility classes: `d-flex`, `mb-3`, `p-0`, `text-center`, etc.
- Grid system: `col-md-3`, `row`, `col-sm-3`
- Cards: `.card`, `.card-header`, `.card-body`
- Tables: `.table`, `.table-sm`, `.table-responsive`
- Badges: `.badge`, `.badge-success`, `.badge-danger`, `.badge-warning`
- Alerts: `.alert`, `.alert-info`, `.alert-warning`

**Component Scoping**: Each component has own `.scss` file
- Example: `validation-report.component.scss`
- Global styles in: `src/styles.scss`

### 4.2 Angular Template Patterns

**Conditional Rendering**:
```html
<!-- Angular 19 @if syntax -->
@if (loading) {
  <div>Loading...</div>
} @else {
  <div>Content</div>
}

<!-- Or legacy *ngIf -->
<div *ngIf="condition">...</div>
```

**Data Binding**:
```html
<!-- Interpolation -->
{{ reportData.validation_timestamp | date: 'medium' }}

<!-- Property binding -->
[disabled]="downloadingReport"
[class.active]="router.url.includes(repoId)"

<!-- Event binding -->
(click)="downloadReport()"
(change)="onVersionChange($event)"
```

**Directives**:
```html
<!-- Tooltips -->
[ngbTooltip]="'Download executive summary as .docx'"
container="body"

<!-- Class binding -->
[ngClass]="{'text-success': status === 'PASSED'}"

<!-- Template loops -->
<div *ngFor="let repo of repositories">
  {{ repo.repo_name }}
</div>
```

### 4.3 Status Display Examples

```html
<!-- Summary Card Grid -->
<div class="col-md-3 mb-2">
  <div class="card h-100 border-0 shadow-sm">
    <div class="card-body py-3">
      <div class="text-uppercase text-muted small mb-1">Overall Status</div>
      <div class="h5 mb-0 font-weight-bold" 
           [ngClass]="{
             'text-success': overall_status === 'PASSED',
             'text-warning': overall_status?.includes('WARNING'),
             'text-danger': overall_status?.includes('FAILED')
           }">
        {{ overall_status || 'N/A' }}
      </div>
    </div>
  </div>
</div>

<!-- Table with Status Badges -->
<span class="badge status-badge" 
      [ngClass]="{
        'status-match': repo.status === 'MATCH',
        'status-nomatch': repo.status === 'NOMATCH',
        'status-partial': repo.status === 'PARTIAL'
      }">
  {{ repo.status }}
</span>
```

---

## 5. Export/Download Patterns

### 5.1 Blob-Based Download Pattern

**Universal Pattern** (used across all exports):

```typescript
// 1. Create blob with content
const blob = new Blob([content], { type: 'application/json;charset=utf-8;' });

// 2. Generate object URL
const url = URL.createObjectURL(blob);

// 3. Create anchor element
const anchor = document.createElement('a');
anchor.href = url;
anchor.download = filename;

// 4. Trigger download
anchor.click();

// 5. Clean up
URL.revokeObjectURL(url);
```

**Services Implementing This**:
- `WorkflowExportService`: JSON exports with sanitized filenames
- `ExecutiveSummaryDocxService`: DOCX exports using `docx` library
- API Service: CSV exports via `downloadReport()` returning Blob

### 5.2 File Format Support

| Format | Library | Service | Use Case |
|--------|---------|---------|----------|
| JSON | None | WorkflowExportService | Workflow definitions |
| CSV | Native (string) | Discovery/Validation APIs | Report exports |
| DOCX | `docx` library | ExecutiveSummaryDocxService | Executive summaries |
| Blob | HTTP | APIService | Generic binary downloads |

### 5.3 Filename Patterns

```typescript
// Discovery Report
`discovery_report_${formatted_timestamp}.csv`
// → discovery_report_Aug_31_2026_14_30_45.csv

// Executive Summary
`GitLift_Discovery_Executive_Summary_${projectName}.docx`

// Workflow Export
`${sanitized_workflow_name}.workflow.json`
// Sanitization: replace([^\w\s-]/g, ''), trim, lowercase, spaces→underscores
```

---

## 6. Key UI Components & Libraries

### 6.1 Third-Party Libraries Used

From `package.json`:
- **@dagility-ui/kit**: Custom UI components (lib-stream-wrapper, lib-dropdown, lib-info-box, lib-search)
- **@ng-bootstrap/ng-bootstrap**: Bootstrap integration (ngbTooltip, modal services)
- **@fortawesome/angular-fontawesome**: Font Awesome icons (fa-icon)
- **@ag-grid-community/angular**: Data tables (in other modules)
- **ngx-toastr**: Toast notifications (success/error messages)
- **perfect-scrollbar**: Smooth scrolling
- **docx**: Word document generation
- **papaparse**: CSV parsing (optional, for imports)
- **file-saver**: File download utilities

### 6.2 Custom UI Wrappers

**lib-stream-wrapper**: Async data rendering wrapper
```html
<lib-stream-wrapper [dataStream$]="repos$">
  <ng-template let-repositories="data" contentTemplate>
    <!-- Content rendered when data loads -->
  </ng-template>
</lib-stream-wrapper>
```

**lib-dropdown**: Styled dropdown selector
```html
<lib-dropdown
  [items]="versions"
  labelKey="label"
  valueKey="version_str"
  placeholder="Select Version"
  [(ngModel)]="selectedVersionId"
  (change)="onVersionChange($event)">
</lib-dropdown>
```

---

## 7. Data Flow Architecture

### 7.1 Discovery Report Data Flow

```
User Action (Click "Discovery Report" tab)
    ↓
DiscoveryReportComponent.getData()
    ↓
APIService.getPlanningPhaseTree(jobId) 
    ↓ (HTTP GET /planning-phase/tree/{jobId})
Backend FastAPI → Database Query
    ↓
Response: { repos: [], csv_reports: [] }
    ↓
Template renders via lib-stream-wrapper
    ↓
User selects repo → RepoReportComponent loads
    ↓
APIService.getDiscoveryReportVersions(jobId, repoId)
    ↓
Shows version dropdown + renders DepotViewerComponent
```

### 7.2 Validation Report Data Flow

```
User Action (Click "Validation Report" tab)
    ↓
ValidationReportComponent.getData()
    ↓
APIService.getNewValidationReport(jobId)
    ↓ (HTTP GET /validation_es/{jobId})
Backend (ElasticSearch-backed endpoint)
    ↓
Response: ValidationReport object
    ↓
Template renders summary cards + repository table
    ↓
User can: Download CSV, Refresh, or drill-down to details
```

### 7.3 Export Flow

```
User clicks "Download Report" button
    ↓
DiscoveryReportComponent.downloadReport()
    ↓
APIService.downloadReport(jobId, 'discovery')
    ↓ (HTTP GET /download-report/{jobId}?report-type=discovery)
Backend generates CSV and streams as Blob
    ↓
Client receives Blob
    ↓
WorkflowExportService.triggerDownload(blob, filename)
    ↓
Browser downloads file to default download folder
```

---

## 8. Missing Pieces / NOT Currently Implemented

### 🔴 No Markdown Support
- **Observation**: No `marked`, `markdown-it`, or `ngx-markdown` library installed
- **Current Approach**: All report rendering uses HTML/Bootstrap directly
- **For Platform Parity Reports**: Would need to either:
  1. Install markdown library + sanitizer (ngx-markdown)
  2. Keep using HTML/Bootstrap structure (recommended for consistency)

### 🔴 No HTML Sanitization Library
- Basic input validation only
- No `DomSanitizer.sanitize()` calls for user-generated HTML
- Could be risk if reports contain untrusted content

### 🔴 No Report Comparison
- No side-by-side diff views
- No change highlighting between versions

### 🔴 No Report Templates
- All styling hardcoded in components
- No reusable report theme system

### 🔴 No Live Progress Indicators
- No streaming progress updates during report generation
- No WebSocket or Server-Sent Events integration

---

## 9. Best Practices Observed

✅ **Service Layer Abstraction**: All API calls through APIService
✅ **Observable Patterns**: RxJS observables for async operations
✅ **Component Reusability**: MigrationReportViewerComponent as input-driven component
✅ **Error Handling**: Toast notifications for errors (ngx-toastr)
✅ **Loading States**: lib-stream-wrapper for async loading
✅ **Type Safety**: TypeScript interfaces for data models
✅ **Responsive Design**: Bootstrap grid system for mobile support
✅ **Accessibility**: Tooltips, aria-labels, semantic HTML

---

## 10. Implementation Recommendations for Platform Parity Reports

### Report Display Strategy
```
1. Use existing DiscoveryReportComponent pattern as template
2. Create PlatformParityReportComponent similar to ValidationReportComponent
3. Display 5 report sections in card/section layout (no Markdown needed)
4. Use Bootstrap alerts for colored sections (🔴 Hard Blockers, 🟡 Differences, etc.)
```

### Component Structure
```
PlatformParityModule/
├── platform-parity.component.ts          (main route)
├── analyzer/                             (select source/target)
├── report-display/
│   ├── report-display.component.ts       (main report viewer)
│   ├── executive-summary.component.ts    (section 1)
│   ├── blockers-section.component.ts     (section 2)
│   ├── differences-section.component.ts  (section 3)
│   └── coverage-report.component.ts      (section 5)
├── report-history.component.ts           (list previous reports)
└── services/
    ├── platform-parity-api.service.ts    (API calls)
    └── platform-parity-export.service.ts (DOCX/JSON export)
```

### Data Model Example
```typescript
interface PlatformParityReport {
  id: string;
  timestamp: string;
  source_platform: string;
  target_platform: string;
  executive_summary: {
    total_capabilities: number;
    seamless_migrations: number;
    hard_blockers: number;
    behavioral_differences: number;
  };
  hard_blockers: Blocker[];
  behavioral_differences: Difference[];
  seamless_migrations: Capability[];
  coverage_report: CoverageStats;
}
```

### Export Strategy
- **JSON**: Use WorkflowExportService pattern
- **Markdown**: Generate markdown string, provide download as `.md` file
- **DOCX**: Use ExecutiveSummaryDocxService pattern

---

## 11. File Structure Reference

### Frontend Report Files
```
pace-git-lift-ui/src/app/
├── pages/migration-wrapper/migration-edit/
│   ├── discovery/
│   │   ├── discovery-report/
│   │   │   ├── discovery-report.component.ts
│   │   │   ├── discovery-report.component.html
│   │   │   ├── discovery-report.component.scss
│   │   │   ├── repo-report/repo-report.component.ts
│   │   │   └── run-detailed-discovery/
│   │   ├── executive-summary/
│   │   │   ├── executive-summary.component.ts
│   │   │   ├── executive-summary.component.html
│   │   │   └── executive-summary-docx.service.ts
│   │   └── depot-viewer/
│   │       └── depot-viewer.component.ts
│   └── migration/
│       ├── validation-report/
│       │   ├── validation-report.component.ts
│       │   ├── validation-report.component.html
│       │   └── validation-report.component.scss
│       └── migration-report-viewer/
│           └── migration-report-viewer.component.ts
└── shared/services/
    ├── api.service.ts
    ├── workflow-export.service.ts
    └── workflow-import.service.ts
```

### Backend Report Files
```
pace-git-lift-api/src/scm_migration_tool/
├── routers/
│   ├── discovery.py       (discovery report endpoints)
│   └── validation.py      (validation report endpoints)
├── download/discovery/
│   └── discovery_csv_export.py
├── core/services/
│   ├── document_service.py
│   ├── discovery_report_json_operations.py
│   ├── validation_services.py
│   └── validation_plans.py
└── temporal/workers/models/
    ├── discovery_documents.py
    ├── discovery_activity_data.py
    └── validation_version.py
```

---

## Summary

The PACE UI uses a **well-structured Angular component pattern** for report display with:
- **No Markdown rendering** (direct HTML/Bootstrap)
- **Blob-based file exports** for all formats
- **Async data loading** via RxJS observables
- **Consistent styling** with Bootstrap cards, tables, badges
- **Service-layer abstraction** for all API calls
- **Responsive design** with mobile support

For Platform Parity reports, follow the ValidationReportComponent pattern for quick integration with minimal changes to existing architecture.
