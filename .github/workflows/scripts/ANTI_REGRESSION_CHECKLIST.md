# Dashboard Anti-Regression Checklist

## ⚠️ CRITICAL: READ BEFORE SYNCING OR MODIFYING DASHBOARD CODE

This document tracks known regressions and critical design decisions to prevent them from being reintroduced.

---

## 🐛 Known Regressions (DO NOT REINTRODUCE)

### 1. ❌ "For Efficiency" - Only Processing Triggering Run

**What happened**: Code was added to only process logs for the triggering run "for efficiency", skipping all historical runs.

**Why it's wrong**:
- Breaks Enhanced Log links for all previous runs (they return 404)
- Dashboard shows historical runs but logs are not accessible
- Contradicts the workflow's purpose of maintaining historical data

**Fix**: ALWAYS process logs for ALL runs in `./runs` directory

**Location**: `.github/workflows/scripts/dashboard_process_log_files.py` lines 207-217

**Regression commits**:
- Introduced in: `276711ae` (Sync workflows from main to dev)
- Fixed in: (current fix)

**Code pattern to avoid**:
```python
# ❌ WRONG - This breaks historical logs
if triggering_run_id:
    # Only process the triggering run for efficiency
    process_run_logs(triggering_run_id, ...)
else:
    # Process all runs
    for filename in os.listdir(runs_dir):
        ...
```

**Correct pattern**:
```python
# ✅ CORRECT - Always process all historical runs
print(f"📋 Processing logs for all runs in {runs_dir}")
for filename in os.listdir(runs_dir):
    if filename.startswith('results-') and filename.endswith('.json'):
        run_id = filename.replace('results-', '').replace('.json', '')
        process_run_logs(run_id, headers, repo)
```

---

### 2. ❌ Log Path Mismatch in HTML Conversion

**What happened**: Workflow checked for logs at `./logs/*.log` but logs are saved to `./logs/run-{id}/*.log`

**Why it's wrong**:
- HTML conversion never runs (finds "no log files to convert")
- Users can't view Enhanced Logs in the web interface
- Raw .log files work but .html viewer links fail

**Fix**: Use `find ./logs -type f -name '*.log'` to search recursively

**Location**: `.github/workflows/sweep-publish-dashboard.yml` line 97

**Code pattern to avoid**:
```bash
# ❌ WRONG - Only checks flat directory
if [ -d "./logs" ] && [ "$(ls -A ./logs/*.log 2>/dev/null | wc -l)" -gt 0 ]; then
```

**Correct pattern**:
```bash
# ✅ CORRECT - Recursively finds all .log files
if [ -d "./logs" ] && [ "$(find ./logs -type f -name '*.log' 2>/dev/null | wc -l)" -gt 0 ]; then
```

---

## 📋 Design Decisions (DO NOT CHANGE WITHOUT DISCUSSION)

### 1. Log Directory Structure

**Decision**: Logs are organized by run: `./logs/run-{run_id}/*.log`

**Rationale**:
- Prevents filename conflicts across runs
- Easy to clean up old runs
- Clear separation for debugging

**Impact on code**:
- Must use recursive search when looking for logs
- Log URLs must include run ID: `/logs/run-{run_id}/{logfile}`

---

### 2. Process ALL Historical Runs

**Decision**: Always download and process logs for ALL runs in `./runs` directory

**Rationale**:
- Users expect historical Enhanced Log links to work
- Dashboard shows historical data, logs must match
- GitHub Pages deployment preserves old logs across publishes
- "Efficiency" optimization saves minutes but breaks user experience

**Performance notes**:
- Typical run: 10-20 historical runs
- Per-run processing: ~30-60 seconds
- Total time: 5-10 minutes (acceptable for deployment workflow)
- Artifacts expire after 90 days, so max ~90 runs to process

---

### 3. Log Filename Convention - Use Actual Runner Names

**Decision**: Log files include the actual runner name: `{basename}_{runner_label}.log`

**Example**: `index_000_gdrcopy_jat07-iso382.html`

**Rationale**:
- More informative - see exactly which runner ran each job
- Can distinguish between multiple runners of the same platform type
- Filename matches what's shown in the dashboard table
- Easier debugging when investigating runner-specific issues

**Implementation**:
- `dashboard_process_log_files.py` loads results JSON for each run
- Creates mapping from log basename to runner_label
- Uses actual runner name in filename (sanitized: `re.sub(r'[^a-zA-Z0-9]', '-', runner_label)`)
- Dashboard JavaScript uses the same sanitization to construct URLs

**Code locations**:
- Log file creation: `dashboard_process_log_files.py` lines 190-194
- URL generation: `dashboard_generate_html.py` lines 1378-1382

**DO NOT revert to generic platform suffixes** like "_thor" or "_orin" - they lose important information about which specific runner was used.

---

### 4. Preserve Existing Logs on Deployment

**Decision**: Download existing logs from GitHub Pages before deploying

**Rationale**:
- Artifacts expire after 90 days
- Logs on GitHub Pages persist indefinitely
- Merge old + new logs to maintain complete history

**Location**: `.github/workflows/sweep-publish-dashboard.yml` lines 128-151

---

## ✅ Pre-Sync Checklist

Before syncing from main or making major changes:

- [ ] Verify `dashboard_process_log_files.py` processes ALL runs (not just triggering run)
- [ ] Verify log files use actual runner names, not generic platform suffixes
- [ ] Verify log conversion uses `find` to search recursively
- [ ] Test that Enhanced Log links work for historical runs
- [ ] Check that logs are saved to `./logs/run-{id}/` structure
- [ ] Confirm existing logs are downloaded and merged during deployment

---

## 🔍 How to Test

### Test Log Processing

```bash
# Create test runs directory
mkdir -p ./runs
echo '{"run_id": "12345"}' > ./runs/results-12345.json
echo '{"run_id": "67890"}' > ./runs/results-67890.json

# Set environment (use actual PAT)
export DASHBOARD_PAT="your_token"
export REPO="NVIDIA-AI-IOT/jetson-containers"

# Run script
python3 .github/workflows/scripts/dashboard_process_log_files.py

# Should output:
# 📋 Processing logs for all runs in ./runs
# Processing logs for run 12345
# Processing logs for run 67890
# ✅ Completed processing log files for 2 run(s)
```

### Test Log Conversion

```bash
# Create test log structure
mkdir -p ./logs/run-12345
echo "test log" > ./logs/run-12345/test.log

# Run conversion check
if [ -d "./logs" ] && [ "$(find ./logs -type f -name '*.log' 2>/dev/null | wc -l)" -gt 0 ]; then
    echo "✅ Found logs correctly"
else
    echo "❌ Log detection failed"
fi
```

---

## 📚 Related Documentation

- [Dashboard Testing Guide](./tests/DASHBOARD_TESTING.md)
- [Dashboard Scripts README](./README.md)
- Original simplification: Commit `560211ad` - "Simplify dashboard workflow by treating all runs as historical"

---

## 🚨 If You See a Regression

1. **Document it** - Add to this file immediately
2. **Add a test** - Create a test case in `tests/test_dashboard_local.py`
3. **Comment the fix** - Add explanatory comments to prevent reintroduction
4. **Update checklist** - Add to the pre-sync checklist above

---

*Last updated: October 8, 2025*
*Maintainer: Review this document before ANY dashboard changes*

