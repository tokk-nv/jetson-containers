# Testing Results Summary - Orin Runner Cleanup Issue

**Date**: October 8, 2025
**Runner Tested**: jao512-jp62 (Orin)
**Issue**: Checkout fails with "Permission denied" on `data/audio`

---

## Problem Statement

Build Matrix workflow started failing on Orin runners with:
```
fatal: cannot create directory at 'data/audio': Permission denied
Error: The process '/usr/bin/git' failed with exit code 128
```

---

## Root Cause Analysis

### What We Discovered

1. **The Error Was Misleading**
   - Git error says "cannot create directory"
   - Reality: Directory already exists (owned by root)
   - Actual problem: Can't write FILES into root-owned directory

2. **Proof**
   ```bash
   $ mkdir -p data/audio       # ✅ Succeeds (directory exists)
   $ touch data/audio/test.txt # ❌ Fails (permission denied)
   ```

3. **Docker Creates Root-Owned Directories**
   - Docker containers run as root
   - Create `data/audio/` and other directories owned by root:root
   - Git checkout can't write into these directories

4. **Why Only Orin Runners?**
   - Orin: Long-running, accumulated root-owned directories over time
   - Thor: Newer runners, less accumulated cruft
   - Specific packages that create `data/` were built on Orin, not Thor yet

---

## Testing Process

### Test 1: Can we delete without sudo?
```bash
$ sudo mkdir -p data/audio/test
$ sudo touch data/audio/test/root-file.txt
$ rm -rf data/
$ ls data/   # ✅ Directory STILL EXISTS
```
**Result**: ❌ Cannot delete root-owned files without sudo

### Test 2: Does git clean work?
```bash
$ git clean -ffdx data/
warning: failed to remove data/audio/test/root-file.txt: Permission denied
Exit code: 1
```
**Result**: ❌ Git clean also cannot remove root-owned files

### Test 3: Does sudo work with NOPASSWD?

**First attempt (wrong path):**
```bash
$ sudo -k  # Clear cache
$ sudo -n rm -rf /tmp/test
sudo: a password is required
```
**Result**: ❌ NOPASSWD doesn't apply to /tmp

**Second attempt (relative path):**
```bash
$ sudo -k
$ sudo -n rm -rf data/
sudo: a password is required
```
**Result**: ❌ NOPASSWD requires absolute path

**Third attempt (full path):**
```bash
$ sudo -k
$ sudo -n rm -rf $PWD/data/
Exit code: 0
$ ls data/  # Directory gone
```
**Result**: ✅ Works with full absolute path!

---

## Solution

### NOPASSWD Configuration Requirements

The sudoers rule requires **exact matching**:
```
/bin/rm -rf /home/jetson/actions-runner/_work/*
```

This means:
- ✅ `sudo rm -rf /home/jetson/actions-runner/_work/.../data/` → Works
- ✅ `sudo rm -rf $PWD/data/` → Works (expands to full path)
- ✅ `sudo rm -rf ${{ github.workspace }}/data/` → Works in workflows
- ❌ `sudo rm -rf data/` → Fails (relative path doesn't match rule)
- ❌ `sudo rm -rf /tmp/test` → Fails (path not in workspace)

### Workflow Changes

**Before (didn't work):**
```yaml
- name: Pre-clean (no sudo; avoid hangs)
  run: |
    rm -rf data/ logs/ || true  # Can't remove root-owned files

- name: Checkout
  uses: actions/checkout@v4
  with:
    clean: false  # Doesn't clean workspace
```

**After (works):**
```yaml
- name: Pre-clean workspace
  run: |
    # Use sudo with FULL PATHS to match NOPASSWD rule
    sudo rm -rf ${{ github.workspace }}/data/ || true
    sudo rm -rf ${{ github.workspace }}/logs/ || true

- name: Checkout
  uses: actions/checkout@v4
  with:
    clean: true  # Additional safety
```

---

## Key Learnings

### 1. NOPASSWD Requires Absolute Paths
- Sudoers rules match against the **full absolute path**
- Relative paths like `data/` don't match the rule
- Always use `${{ github.workspace }}` or `$PWD` in workflows

### 2. Git Clean Cannot Remove Root-Owned Files
- Common misconception: git clean can remove anything
- Reality: Fails with "Permission denied" on root-owned files
- Not reliable for Docker-based workflows

### 3. Sudo Cache Can Hide Issues
- Sudo remembers credentials for ~15 minutes
- Must use `sudo -k` to clear cache before testing
- Use `sudo -n` to test non-interactive behavior

### 4. Exit Code 0 Doesn't Mean Success
```bash
$ rm -rf data/ || true
$ echo $?  # Shows 0
$ ls data/ # Files still exist!
```
- With `|| true`, command always exits 0
- Must check if files actually deleted

### 5. Error Messages Can Be Misleading
- Git says "cannot create directory"
- Really means "can't write files into directory"
- Always test the actual scenario

---

## Verification Checklist

Before running workflows, verify on each runner:

```bash
# 1. Create root-owned test directory
sudo mkdir -p $PWD/data/test
sudo touch $PWD/data/test/root-file.txt
ls -la $PWD/data/test/

# 2. Clear sudo cache
sudo -k

# 3. Test sudo with full path (should work without prompt)
sudo -n rm -rf $PWD/data/
echo "Exit code: $?"

# 4. Verify actually deleted
ls $PWD/data/ 2>&1  # Should show "No such file or directory"
```

Expected result:
- ✅ Exit code 0
- ✅ No password prompt
- ✅ Directory actually deleted

---

## Files Modified

1. `.github/workflows/sweep-build-matrix.yml`
   - Added sudo with full paths to pre-clean steps
   - Changed `clean: false` → `clean: true`

2. `.github/workflows/RUNNER_MAINTENANCE.md`
   - Documented NOPASSWD requirements
   - Explained why sudo is necessary
   - Provided testing procedures

3. `.github/workflows/scripts/test_runner_cleanup.sh`
   - Created automated testing script
   - Detects NOPASSWD configuration
   - Tests both approaches

4. `.github/workflows/TESTING_CLEANUP_ON_ORIN.md`
   - Step-by-step testing guide
   - Manual testing procedures
   - Troubleshooting tips

---

## References

- [GitHub Actions Self-Hosted Runner Setup](https://github.com/NVIDIA-AI-IOT/jetson-containers/blob/dev/docs/github-actions-self-hosted-runner-setup.md) - NOPASSWD configuration
- [RUNNER_MAINTENANCE.md](./RUNNER_MAINTENANCE.md) - Ongoing maintenance guide
- [TESTING_CLEANUP_ON_ORIN.md](./TESTING_CLEANUP_ON_ORIN.md) - Testing procedures

---

## Next Steps

1. ✅ Test changes on one Orin runner first
2. ⏳ Run Build Matrix workflow with new changes
3. ⏳ Verify checkout succeeds without permission errors
4. ⏳ Monitor for any sudo-related hangs (shouldn't happen with full paths)
5. ⏳ Document any additional findings

---

**Tested By**: User
**Reviewed By**: AI Assistant
**Status**: Ready for deployment

