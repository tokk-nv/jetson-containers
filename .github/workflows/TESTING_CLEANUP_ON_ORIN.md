# Testing Cleanup on Orin Runners

## Quick Test Guide

This guide shows you how to test the cleanup commands from `sweep-build-matrix.yml` on an Orin runner to verify they work correctly without hanging.

### Step 1: SSH into Orin Runner

```bash
ssh jetson@<orin-runner-hostname>
```

### Step 2: Run the Test Script

```bash
# Navigate to the actions runner workspace
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers

# Run the test script
bash .github/workflows/scripts/test_runner_cleanup.sh --verbose
```

The script will:
1. ✅ Check current workspace state (root-owned files, sizes)
2. ✅ Test pre-clean commands without sudo
3. ✅ Test with sudo (if passwordless sudo is configured)
4. ✅ Simulate git clean (dry run first, asks before actual clean)
5. ✅ Report final state and results

### Step 3: Manual Testing (Alternative)

If you prefer to test manually:

```bash
# Navigate to workspace
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers

# Check current state
echo "=== Current State ==="
ls -la data/ logs/ 2>/dev/null
find . -user root 2>/dev/null | head -20

# Test the pre-clean commands (what the workflow does)
echo "=== Testing Pre-clean (no sudo) ==="
rm -rf data/ logs/ build/ test/ || true
rm -f results.json || true
echo "Exit code: $?"

# Check what's left
echo "=== After Pre-clean ==="
find . -user root 2>/dev/null | wc -l

# Test git clean (dry run)
echo "=== Testing Git Clean (dry run) ==="
git clean -ffdxn

# Optional: Test with sudo (if configured)
echo "=== Testing With Sudo (optional) ==="
sudo -n rm -rf data/ logs/ build/ test/
echo "Exit code: $?"

# Check if it hangs (should return immediately)
echo "✅ No hang detected!"
```

### Expected Results

#### ✅ Good (No Hang)
```
Testing Pre-clean (no sudo)
Exit code: 0
After Pre-clean: 5 root-owned files remaining
Testing Git Clean (dry run)
Would remove data/audio/
Would remove logs/build_001/
...
✅ No hang detected!
```

#### ❌ Bad (Hangs)
```
Testing With Sudo (optional)
[sudo] password for jetson:
<HANGS HERE - no further output>
```

If you see the password prompt, the sudo command is NOT configured for passwordless execution!

### Verification Checklist

- [ ] Pre-clean commands complete without hanging
- [ ] Root-owned files are handled gracefully (no errors, just skipped)
- [ ] Git clean removes remaining files
- [ ] No password prompts appear
- [ ] Exit codes are 0 (or ignored with `|| true`)

### Passwordless Sudo Configuration Check

To verify your sudoers configuration:

```bash
# Check if passwordless sudo is configured
sudo -n -l | grep "NOPASSWD"

# Expected output should include:
# /usr/bin/apt-get
# /usr/bin/ln
# /bin/rm -rf /home/jetson/actions-runner/_work/*
# /bin/chmod -R /home/jetson/actions-runner/_work/*
# /bin/chown -R /home/jetson/actions-runner/_work/*
```

If you see the above, passwordless sudo IS configured correctly.

### Testing Specific Problem Directories

To specifically test the `data/audio` issue that caused the original error:

```bash
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers

# Create a root-owned test directory to simulate the issue
sudo mkdir -p data/audio/test
sudo touch data/audio/test/root-owned-file.txt
ls -la data/audio/test/

echo "=== Test 1: Without sudo (should fail silently) ==="
rm -rf data/ || true
echo "Exit code: $?"  # Should be 0 (due to || true)

# Check if directory still exists
if [ -d data/audio/test/ ]; then
    echo "❌ Directory still exists (expected - permission denied)"
    ls -la data/audio/test/
else
    echo "✅ Directory removed (unexpected - no root-owned files were present?)"
fi

echo ""
echo "=== Test 2: With sudo (should succeed) ==="
sudo rm -rf data/
echo "Exit code: $?"

if [ -d data/audio/test/ ]; then
    echo "❌ Directory still exists (unexpected!)"
else
    echo "✅ Directory removed (expected with sudo)"
fi

echo ""
echo "=== Test 3: Git clean (should also remove root-owned files) ==="
# Recreate for git clean test
sudo mkdir -p data/audio/test
sudo touch data/audio/test/root-owned-file.txt

git clean -ffdx data/

if [ -d data/audio/test/ ]; then
    echo "❌ Directory still exists (git clean failed)"
else
    echo "✅ Directory removed by git clean (expected)"
fi
```

**Key Insight**: The difference isn't in "prompting" - neither prompts. The difference is:
- `rm -rf` without sudo → Exits 0 (with `|| true`), but **leaves root-owned files**
- `sudo rm -rf` → Exits 0, **actually deletes** root-owned files
- `git clean -ffdx` → Exits 0, **actually deletes** root-owned files

### Troubleshooting

#### Problem: Script not found
```bash
# If the script isn't in the workspace yet, copy it:
git fetch origin
git checkout origin/dev -- .github/workflows/scripts/test_runner_cleanup.sh
chmod +x .github/workflows/scripts/test_runner_cleanup.sh
```

#### Problem: Not in a git repository
```bash
# Make sure you're in the workspace:
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers
git status
```

#### Problem: Permission denied on script execution
```bash
chmod +x .github/workflows/scripts/test_runner_cleanup.sh
```

### What to Look For

1. **No Password Prompts**: Commands should complete immediately without asking for passwords
2. **Graceful Failures**: `rm -rf` may fail on root files, but with `|| true` it continues
3. **Git Clean Success**: `git clean` should remove remaining root-owned files
4. **Fast Completion**: All commands should complete in < 5 seconds

### Reporting Results

After testing, report:
- ✅ Did any commands hang? (yes/no)
- ✅ Were root-owned files removed? (by pre-clean, git clean, or neither)
- ✅ Any password prompts? (yes/no)
- ✅ Final workspace state (clean/has root files)

### Quick One-Liner Test

For a quick sanity check:

```bash
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers && time (rm -rf data/ logs/ || true; git clean -ffdxn | head -20) && echo "✅ No hang"
```

This should complete in < 2 seconds and show what would be removed.

---

## See Also

- [RUNNER_MAINTENANCE.md](./RUNNER_MAINTENANCE.md) - Full maintenance guide
- [GitHub Actions Self-Hosted Runner Setup](https://github.com/NVIDIA-AI-IOT/jetson-containers/blob/dev/docs/github-actions-self-hosted-runner-setup.md) - Sudoers configuration

