# Platform Parity Reporting Guide

## Purpose
This folder contains the scripts and knowledge-base files to compare source control platforms and generate migration parity reports.

It supports two report-generation modes:
- Deterministic mode: fast, no Bedrock call, useful for validation and CI checks.
- Bedrock mode: deterministic comparison plus LLM-generated narrative report sections.

The output is a pair of files per run:
- Markdown report for humans
- JSON payload for automation and downstream tooling

## Who This Is For
This guide is written for users with no prior context. If you can run shell commands and have access credentials, you can generate and validate reports end to end.

## What Is In This Folder
- test_bedrock_e2e.py: single source-to-target report run
- run_parity_matrix.py: batch run across all known migration pairs
- capability_kb/: taxonomy, platform capability maps, known gaps
- prompts/: Bedrock prompt templates
- test_output/: generated markdown and json artifacts
- aws-ca-bundle.pem: optional custom CA bundle for corporate TLS environments

## Prerequisites
### Required
- Python 3.10 or newer
- pip
- Network access to AWS STS and AWS Bedrock (for Bedrock mode)

### Python Packages
Install required packages from your environment:

    pip install pyyaml boto3

## Quick Start
### 1) Open a terminal in the repository root
Repository root is the folder containing platform_parity.

### 2) Move into this folder

    cd platform_parity

### 3) Run a deterministic single-pair report
This does not call Bedrock.

    python test_bedrock_e2e.py --source-platform gitlab --target-platform github --skip-bedrock

### 4) Review output
Generated files appear in test_output with names like:
- gitlab_to_github_<hash>.md
- gitlab_to_github_<hash>.json

## Bedrock Mode Setup
Use this only when you want LLM narrative reports.

### 1) Set AWS credentials
PowerShell example:

    $Env:AWS_ACCESS_KEY_ID = "<your_key>"
    $Env:AWS_SECRET_ACCESS_KEY = "<your_secret>"
    $Env:AWS_SESSION_TOKEN = "<your_session_token>"   # required for temporary credentials
    $Env:AWS_DEFAULT_REGION = "us-east-1"

### 2) Set Bedrock model and inference profile
In this environment, the Sonnet model requires an inference profile.

    $Env:BEDROCK_MODEL_ID = "anthropic.claude-sonnet-4-6"
    $Env:BEDROCK_INFERENCE_PROFILE_ID = "us.anthropic.claude-sonnet-4-6"

### 3) Optional timeout and retry tuning

    $Env:BEDROCK_MAX_TOKENS = "2048"
    $Env:BEDROCK_CONNECT_TIMEOUT_SECONDS = "20"
    $Env:BEDROCK_READ_TIMEOUT_SECONDS = "300"
    $Env:BEDROCK_MAX_ATTEMPTS = "5"

### 4) Optional corporate TLS CA bundle
If your organization requires a custom CA trust chain, set:

    $Env:AWS_CA_BUNDLE = "<absolute_path_to_repo>\platform_parity\aws-ca-bundle.pem"
    $Env:REQUESTS_CA_BUNDLE = "<absolute_path_to_repo>\platform_parity\aws-ca-bundle.pem"

### 5) Run Bedrock single-pair report

    python test_bedrock_e2e.py --source-platform gitlab --target-platform github

## Run All Pairs (Matrix)
### Deterministic matrix

    python run_parity_matrix.py

### Bedrock matrix

    python run_parity_matrix.py --with-bedrock

### Run selected pairs only

    python run_parity_matrix.py --with-bedrock --pairs gitlab_to_github,github_to_gitlab

## Command Reference
### test_bedrock_e2e.py
Useful options:
- --source-platform
- --target-platform
- --skip-bedrock
- --aws-region
- --bedrock-model-id
- --bedrock-inference-profile-id
- --bedrock-max-tokens
- --bedrock-connect-timeout-seconds
- --bedrock-read-timeout-seconds
- --bedrock-max-attempts
- --kb-base-path
- --output-dir
- --preview-chars

Show all options:

    python test_bedrock_e2e.py --help

### run_parity_matrix.py
Useful options:
- --pairs all or comma-separated list
- --with-bedrock
- all Bedrock tuning options above

Show all options:

    python run_parity_matrix.py --help

## How To Check Everything Is Working
Use this checklist after a run.

### A) Script execution checks
- Command exits with success code.
- Console shows: All 5 required sections present - PASS.
- Console shows markdown and json output paths.

### B) Output file checks
- For each pair run, both .md and .json files are created.
- File names include source_to_target hash pattern.

PowerShell quick check:

    Get-ChildItem .\test_output | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name, LastWriteTime

### C) Report structure checks
Each markdown report must contain all sections:
- 1. Executive Summary
- 2. Hard Blockers
- 3. Behavioral Differences
- 4. Seamless Migrations
- 5. Coverage Report

PowerShell quick check for section headers:

    $f = ".\test_output\gitlab_to_github_<hash>.md"
    Select-String -Path $f -Pattern "## 1\. Executive Summary|## 2\. 🔴 Hard Blockers|## 3\. 🟡 Behavioral Differences|## 4\. 🟢 Seamless Migrations|## 5\. 📋 Coverage Report"

### D) Behavioral Differences content checks
Section 3 is expected to contain per-item details with:
- Source item or behavior
- Target item or behavior
- Brief behavioral difference

PowerShell quick check across all reports:

    Get-ChildItem .\test_output -Filter *.md | ForEach-Object {
      $c = Get-Content $_.FullName -Raw
      $items = ([regex]::Matches($c, "Item / Behavior:\*\*")).Count
      $brief = ([regex]::Matches($c, "Behavioral Difference \(Brief\):\*\*")).Count
      "{0} | item_fields={1} | brief_fields={2}" -f $_.Name, $items, $brief
    }

## Keep Only Latest Report Per Pair
If you run the same pair multiple times, test_output can contain older hash versions.

Use this PowerShell cleanup to keep only the latest md and json per pair:

    $outDir = ".\test_output"
    $files = Get-ChildItem -Path $outDir -File | Where-Object { $_.Name -match '^[a-z_]+_to_[a-z_]+_[0-9a-f]{12}\.(md|json)$' }
    $parsed = foreach ($f in $files) {
      if ($f.Name -match '^([a-z_]+_to_[a-z_]+)_[0-9a-f]{12}\.(md|json)$') {
        [PSCustomObject]@{ File=$f; Pair=$matches[1]; Ext=$matches[2] }
      }
    }
    $toDelete = @()
    foreach ($g in ($parsed | Group-Object Pair,Ext)) {
      $sorted = $g.Group | Sort-Object { $_.File.LastWriteTimeUtc } -Descending
      $toDelete += ($sorted | Select-Object -Skip 1)
    }
    foreach ($d in $toDelete) { Remove-Item -Path $d.File.FullName -Force }

## Common Issues And Fixes
### Missing dependencies
Symptom:
- PyYAML not installed
- boto3 not installed

Fix:

    pip install pyyaml boto3

### Missing AWS credentials
Symptom:
- Missing environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

Fix:
- Set AWS credential environment variables in your shell before Bedrock runs.

### Bedrock inference profile required
Symptom:
- ValidationException mentioning on-demand throughput or inference profile

Fix:
- Set BEDROCK_INFERENCE_PROFILE_ID and rerun.

### SSL certificate verify failed
Symptom:
- TLS/SSL verification errors to AWS endpoints

Fix:
- Set AWS_CA_BUNDLE and REQUESTS_CA_BUNDLE to aws-ca-bundle.pem path.

### Command appears to stall on Bedrock call
Possible causes:
- Large model response time
- Network latency
- Retry backoff from transient errors

Fixes:
- Increase read timeout and max attempts.
- Retry pair-by-pair first, then run matrix.

## Recommended Operating Sequence
For reliable production runs:
1. Run one deterministic single pair.
2. Validate output files and section structure.
3. Run one Bedrock single pair.
4. Validate section quality, especially Section 3.
5. Run full Bedrock matrix.
6. Prune old outputs and keep latest artifacts only.

## Security Notes
- Never hardcode secrets in scripts.
- Prefer short-lived credentials and role-based access.
- Keep token and credential scope minimal.

## Support Notes
If a run fails, capture:
- Full command used
- Full terminal output
- Pair name
- Whether deterministic or Bedrock mode
- Current environment variable settings (without secret values)

This information is usually enough to triage quickly.
