# GitHub Actions Workflow Scripts

This directory contains Python scripts extracted from the GitHub Actions workflows for better maintainability and testing.

## Scripts Overview

All scripts use prefixes to indicate which workflow they belong to:
- `dashboard_*` - Scripts from `sweep-publish-dashboard.yml`
- `build_*` - Scripts from `sweep-build-matrix.yml` (future)

### 1. `dashboard_download_current_artifacts.py`
Downloads artifacts from the current workflow run, including:
- Merged results (`sweep-results-{sha}-{attempt}`)
- Chunk artifacts containing log files
- Organizes logs with unique platform-specific names

**Environment Variables Required:**
- `DASHBOARD_PAT` or `GITHUB_TOKEN` - Authentication
- `CURRENT_RUN_ID` - Current workflow run ID
- `CURRENT_SHA` - Current commit SHA
- `CURRENT_ATTEMPT` - Current run attempt number
- `REPO` - Repository name (default: NVIDIA-AI-IOT/jetson-containers)

### 2. `dashboard_download_historical_runs.py`
Fetches recent workflow runs for dashboard timeline:
- Tests repository access with PAT/token
- Downloads up to 10 recent completed runs
- Extracts and organizes results.json files

**Environment Variables Required:**
- `DASHBOARD_PAT` or `GITHUB_TOKEN` - Authentication
- `REPO` - Repository name
- `GITHUB_EVENT_NAME`, `GITHUB_ACTOR` - Context info

### 3. `dashboard_process_log_files.py`
Processes log files from historical runs:
- Downloads chunk artifacts containing logs
- Extracts and renames log files with platform suffixes
- Organizes logs in `logs/run-{id}/` directories

**Environment Variables Required:**
- `DASHBOARD_PAT` or `GITHUB_TOKEN` - Authentication
- `REPO` - Repository name

### 4. `dashboard_generate_html.py`
Generates the interactive HTML dashboard:
- Creates comprehensive dashboard with historical timeline
- Implements filtering, search, and detailed log access
- Supports run comparison and navigation

**Environment Variables Required:**
- None (reads from ./results-data/results.json and ./runs/)

### 5. `dashboard_generate_report.py`
Generates markdown build reports:
- Creates detailed markdown report with statistics
- Includes platform breakdown and results table
- Provides summary statistics and success rates

**Environment Variables Required:**
- None (reads from ./results-data/results.json)

## Usage in Workflows

Scripts are designed to be called from GitHub Actions workflows:

```yaml
- name: Download Current Artifacts
  env:
    DASHBOARD_PAT: ${{ secrets.DASHBOARD_PAT }}
    CURRENT_RUN_ID: ${{ github.event.workflow_run.id }}
    CURRENT_SHA: ${{ github.event.workflow_run.head_sha }}
    CURRENT_ATTEMPT: ${{ github.event.workflow_run.run_attempt }}
  run: |
    python3 .github/workflows/scripts/dashboard_download_current_artifacts.py
```

## Dependencies

See `requirements.txt` for dependencies. Most scripts use only standard library modules plus `requests`.

## Development

For local testing, set required environment variables:
```bash
export GITHUB_TOKEN="your_token"
export CURRENT_RUN_ID="12345"
export CURRENT_SHA="abc123"
# ... etc
```
