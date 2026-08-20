# Platform Parity

Platform Parity compares source-control-management platforms and generates migration parity reports. It is designed to answer questions such as:

- What breaks when moving from GitLab to GitHub?
- Which capabilities migrate cleanly?
- Which capabilities need manual remediation, tooling, or redesign?
- What should migration teams review before starting execution?

The implementation in this folder is self-contained. It must work even if `v_1.0` and `v_2.0` are deleted. Those folders are historical/reference material only and are not used at runtime.

## What This Project Does

Platform Parity performs three main steps:

1. Loads the local capability knowledge base from `platform_parity/capability_kb`.
2. Runs a deterministic comparison between a source SCM platform and a target SCM platform.
3. Uses AWS Bedrock Claude only to explain and format the deterministic results into a formal report.

The deterministic engine is the source of truth. Bedrock does not decide gaps, counts, risks, or capability classifications. It only writes a human-readable report from precomputed JSON.

## Supported Platforms

The currently supported SCM platforms are:

- `gitlab`
- `github`
- `azure_devops`
- `bitbucket`

Every source-target pair is supported as long as source and target are different. With four platforms, there are 12 possible migration combinations.

## Key Files And Folders

```text
platform_parity/
  parity_agent.py                     # Main CLI entrypoint
  requirements.txt                    # Python dependencies
  prompts/bedrock_prompts.yaml        # Bedrock report prompt
  capability_kb/
    capability_taxonomy.yaml          # Canonical capability list
    known_gaps.yaml                   # Curated known migration gaps
    platforms/*.yaml                  # Per-platform capability data
    kb_update_log.yaml                # KB freshness activity log
  kb_doc_sync/
    doc_sources.yaml                  # Official documentation source URLs
    doc_fetcher.py                    # Fetch/cache official docs
    kb_updater.py                     # KB freshness orchestration
  test_output/                        # Generated Markdown and JSON reports
  tests/                              # Automated tests
```

## Output Files

Each run writes two files to `platform_parity/test_output`:

```text
<source>_to_<target>_<hash>.md
<source>_to_<target>_<hash>.json
```

Example:

```text
gitlab_to_github_7895f1aba77c.md
gitlab_to_github_7895f1aba77c.json
```

The Markdown report follows a formal v1-style report layout:

1. Executive Summary
2. Hard Blockers
3. Behavioral Differences
4. Seamless Migrations
5. Coverage Report

The JSON file contains the deterministic analysis payload and metadata such as overall risk, gap count, blocker count, behavioral differences, and partial support items.

## Prerequisites

You need:

- Windows PowerShell
- Python virtual environment already present at `.venv`
- AWS temporary credentials with permission to call Bedrock Runtime Converse
- Access to Bedrock model/profile `us.anthropic.claude-sonnet-4-6` in `us-east-1`
- Network access to official SCM documentation sites for KB freshness checks

No AWS CLI is required.

## Step 1: Open PowerShell At Repo Root

```powershell
Set-Location "C:\Users\307519\OneDrive - UST\Desktop\pace-scm-migration-scripts"
& ".\.venv\Scripts\Activate.ps1"
```

## Step 2: Configure Console Encoding

This prevents Markdown symbols such as arrows and status icons from displaying incorrectly in PowerShell.

```powershell
chcp 65001
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

## Step 3: Set AWS Credentials

Use your temporary AWS credentials. Do not store these values in code or commit them to the repository.

```powershell
$Env:AWS_ACCESS_KEY_ID = "<your-temporary-access-key-id>"
$Env:AWS_SECRET_ACCESS_KEY = "<your-temporary-secret-access-key>"
$Env:AWS_SESSION_TOKEN = "<your-temporary-session-token>"
```

If your environment already has these variables set, you do not need to set them again.

## Step 4: Set Bedrock And TLS Environment Variables

```powershell
$Env:AWS_DEFAULT_REGION = "us-east-1"
$Env:AWS_CA_BUNDLE = "C:\Users\307519\OneDrive - UST\Desktop\pace-scm-migration-scripts\platform_parity\aws-ca-bundle.pem"
$Env:REQUESTS_CA_BUNDLE = $Env:AWS_CA_BUNDLE

$Env:BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
$Env:BEDROCK_INFERENCE_PROFILE_ID = "us.anthropic.claude-sonnet-4-6"
$Env:BEDROCK_MODEL_CANDIDATES = "us.anthropic.claude-sonnet-4-6"
```

## Step 5: Set Bedrock Timeout Settings

Full reports can produce large prompts and responses. These timeout settings prevent Bedrock Converse from failing too early.

```powershell
$Env:BEDROCK_CONNECT_TIMEOUT_SECONDS = "30"
$Env:BEDROCK_READ_TIMEOUT_SECONDS = "600"
$Env:BEDROCK_MAX_ATTEMPTS = "5"
```

## Step 6: Validate Syntax

```powershell
& ".\.venv\Scripts\python.exe" -m py_compile `
  "platform_parity\parity_agent.py" `
  "platform_parity\kb_doc_sync\kb_updater.py" `
  "platform_parity\kb_doc_sync\doc_fetcher.py"
```

Expected result: no output and no error.

## Step 7: Run Tests

```powershell
& ".\.venv\Scripts\python.exe" -m pytest "platform_parity\tests" -q
```

Expected result:

```text
15 passed
```

A warning about `langchain-community` deprecation may appear. It is non-blocking for the current implementation.

## Step 8: Run A Deterministic Baseline Report

This checks the local deterministic engine and report export without Bedrock or KB sync.

```powershell
& ".\.venv\Scripts\python.exe" "platform_parity\parity_agent.py" `
  --source-platform gitlab `
  --target-platform github `
  --skip-bedrock `
  --skip-kb-sync
```

Expected result:

```text
Markdown report: ...platform_parity\test_output\gitlab_to_github_<hash>.md
JSON report: ...platform_parity\test_output\gitlab_to_github_<hash>.json
```

## Step 9: Run A Bedrock Report Without KB Sync

This checks deterministic comparison plus Bedrock report writing. It skips KB freshness so it is faster.

```powershell
& ".\.venv\Scripts\python.exe" "platform_parity\parity_agent.py" `
  --source-platform gitlab `
  --target-platform github `
  --skip-kb-sync
```

Expected result:

```text
Attempting Bedrock report generation with model_id=us.anthropic.claude-sonnet-4-6
Markdown report: ...platform_parity\test_output\gitlab_to_github_<hash>.md
JSON report: ...platform_parity\test_output\gitlab_to_github_<hash>.json
```

## Step 10: Run Full End-To-End

This checks the full flow: KB freshness, deterministic comparison, Bedrock report, and file export.

```powershell
& ".\.venv\Scripts\python.exe" "platform_parity\parity_agent.py" `
  --source-platform gitlab `
  --target-platform github
```

Expected result:

```text
Checking KB freshness...
Capabilities checked : 162
Docs changed         : 0
Auto-updates applied : 0
Staged for review    : 0
Attempting Bedrock report generation with model_id=us.anthropic.claude-sonnet-4-6
Markdown report: ...platform_parity\test_output\gitlab_to_github_<hash>.md
JSON report: ...platform_parity\test_output\gitlab_to_github_<hash>.json
```

`Docs changed` may be greater than zero if official documentation changed or cache state is different.

## Step 11: Verify The Latest Report

```powershell
Get-ChildItem "platform_parity\test_output" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 8 Name, LastWriteTime, Length

$latestJson = Get-ChildItem "platform_parity\test_output\gitlab_to_github_*.json" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$latestMd = Get-ChildItem "platform_parity\test_output\gitlab_to_github_*.md" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$latestJson.FullName
$latestMd.FullName
Get-Content $latestMd.FullName -TotalCount 80
```

Validate JSON metrics:

```powershell
& ".\.venv\Scripts\python.exe" -c "import json; p=r'$($latestJson.FullName)'; d=json.load(open(p,encoding='utf-8')); print('overall_risk=',d['metadata']['overall_risk']); print('gap_count=',d['metadata']['gap_count']); print('hard_blockers=',len(d['hard_blockers'])); print('behavioral_diffs=',len(d['behavioral_diffs'])); print('partial_support=',len(d['partial_support']))"
```

## Generate Reports For All Source-Target Combinations

There are 12 combinations:

- gitlab -> github
- gitlab -> azure_devops
- gitlab -> bitbucket
- github -> gitlab
- github -> azure_devops
- github -> bitbucket
- azure_devops -> gitlab
- azure_devops -> github
- azure_devops -> bitbucket
- bitbucket -> gitlab
- bitbucket -> github
- bitbucket -> azure_devops

### Recommended First: Generate All Reports Without KB Sync

This validates all deterministic and Bedrock report paths more quickly.

```powershell
Set-Location "C:\Users\307519\OneDrive - UST\Desktop\pace-scm-migration-scripts"
& ".\.venv\Scripts\Activate.ps1"

$platforms = @("gitlab", "github", "azure_devops", "bitbucket")
$py = ".\.venv\Scripts\python.exe"
$script = "platform_parity\parity_agent.py"
$failed = @()

foreach ($src in $platforms) {
  foreach ($tgt in $platforms) {
    if ($src -ne $tgt) {
      Write-Host ""
      Write-Host "=== RUN: $src -> $tgt (skip-kb-sync) ===" -ForegroundColor Cyan
      & $py $script --source-platform $src --target-platform $tgt --skip-kb-sync
      if ($LASTEXITCODE -ne 0) {
        $failed += "$src -> $tgt"
      }
    }
  }
}

if ($failed.Count -eq 0) {
  Write-Host "All skip-kb-sync report runs completed successfully." -ForegroundColor Green
} else {
  Write-Host "Failed combinations:" -ForegroundColor Red
  $failed | ForEach-Object { Write-Host $_ -ForegroundColor Red }
}
```

### Full End-To-End For All Combinations

This runs KB freshness for every combination, so it is slower.

```powershell
Set-Location "C:\Users\307519\OneDrive - UST\Desktop\pace-scm-migration-scripts"
& ".\.venv\Scripts\Activate.ps1"

$platforms = @("gitlab", "github", "azure_devops", "bitbucket")
$py = ".\.venv\Scripts\python.exe"
$script = "platform_parity\parity_agent.py"
$failed = @()

foreach ($src in $platforms) {
  foreach ($tgt in $platforms) {
    if ($src -ne $tgt) {
      Write-Host ""
      Write-Host "=== FULL RUN: $src -> $tgt ===" -ForegroundColor Yellow
      & $py $script --source-platform $src --target-platform $tgt
      if ($LASTEXITCODE -ne 0) {
        $failed += "$src -> $tgt"
      }
    }
  }
}

if ($failed.Count -eq 0) {
  Write-Host "All full end-to-end report runs completed successfully." -ForegroundColor Green
} else {
  Write-Host "Failed combinations:" -ForegroundColor Red
  $failed | ForEach-Object { Write-Host $_ -ForegroundColor Red }
}
```

## Verify All Generated Reports

Count Markdown and JSON files:

```powershell
Get-ChildItem "platform_parity\test_output\*.md" | Sort-Object Name | Select-Object Name, Length, LastWriteTime
Get-ChildItem "platform_parity\test_output\*.json" | Sort-Object Name | Select-Object Name, Length, LastWriteTime
```

Validate each Markdown report has all required sections:

```powershell
$required = @(
  "## 1. Executive Summary",
  "## 2. 🔴 Hard Blockers",
  "## 3. 🟡 Behavioral Differences",
  "## 4. 🟢 Seamless Migrations",
  "## 5. 📋 Coverage Report"
)

$bad = @()
Get-ChildItem "platform_parity\test_output\*.md" | ForEach-Object {
  $content = Get-Content $_.FullName -Raw -Encoding UTF8
  foreach ($section in $required) {
    if ($content -notlike "*$section*") {
      $bad += "$($_.Name): missing $section"
    }
  }
}

if ($bad.Count -eq 0) {
  Write-Host "All Markdown reports contain required sections." -ForegroundColor Green
} else {
  $bad | ForEach-Object { Write-Host $_ -ForegroundColor Red }
}
```

Validate each JSON report is readable and has summary metrics:

```powershell
& ".\.venv\Scripts\python.exe" -c "import json, pathlib; files=sorted(pathlib.Path('platform_parity/test_output').glob('*.json')); bad=[]; print('json_files=',len(files));
for p in files:
    d=json.load(open(p,encoding='utf-8'))
    m=d.get('metadata',{})
    if 'overall_risk' not in m or 'gap_count' not in m:
        bad.append(str(p))
    else:
        print(p.name, 'risk=', m['overall_risk'], 'gaps=', m['gap_count'])
print('bad=', bad)"
```

## Troubleshooting

### Bedrock Read Timeout

If Bedrock times out, keep these timeout variables set and rerun:

```powershell
$Env:BEDROCK_CONNECT_TIMEOUT_SECONDS = "30"
$Env:BEDROCK_READ_TIMEOUT_SECONDS = "600"
$Env:BEDROCK_MAX_ATTEMPTS = "5"
```

If a full report still times out, first confirm the fast path works:

```powershell
& ".\.venv\Scripts\python.exe" "platform_parity\parity_agent.py" --source-platform gitlab --target-platform github --skip-kb-sync
```

### Expired Temporary Credentials

If you see an AWS credential error, replace the temporary credential environment variables:

```powershell
$Env:AWS_ACCESS_KEY_ID = "<new-temporary-access-key-id>"
$Env:AWS_SECRET_ACCESS_KEY = "<new-temporary-secret-access-key>"
$Env:AWS_SESSION_TOKEN = "<new-temporary-session-token>"
```

Do not hardcode credentials in project files.

### Markdown Icons Look Corrupted In Terminal

Set the PowerShell code page and output encoding:

```powershell
chcp 65001
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

### KB Freshness Fetch Warnings

Occasional SSL/network warnings can happen while fetching official documentation. If a cached copy exists, the fetcher uses the cache. If no cache exists, that capability is reported in the KB freshness error list for review.

## Success Checklist

A full successful validation means:

- Syntax check passes.
- Tests show `15 passed`.
- Deterministic baseline generates Markdown and JSON.
- Bedrock run with `--skip-kb-sync` generates Markdown and JSON.
- Full end-to-end run checks KB freshness and generates Markdown and JSON.
- All 12 source-target combinations generate both `.md` and `.json` files.
- Markdown reports contain the five required sections.
- JSON files contain `overall_risk` and `gap_count` metadata.

## Design Constraints

- `platform_parity` is self-contained.
- No runtime imports, reads, or dependencies on `v_1.0` or `v_2.0`.
- Deterministic comparison is the authority.
- Bedrock is used only to explain and format deterministic results.
- Credentials are supplied through environment variables and are never stored in code.
