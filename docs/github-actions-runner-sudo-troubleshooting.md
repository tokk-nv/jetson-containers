# GitHub Actions Runner Sudo Configuration Troubleshooting

> **Related Documentation:** [GitHub Actions Self-Hosted Runner Setup](./github-actions-self-hosted-runner-setup.md)
>
> This guide provides troubleshooting and fix scripts for sudo configuration issues on self-hosted runners.

## Problem

GitHub Actions self-hosted runners need passwordless `sudo` for specific commands to clean up root-owned files created during Docker builds. A typo in the sudoers configuration (`> home` instead of `/home`) breaks this functionality.

**Symptoms:**
- Checkout steps fail with "Permission denied" errors
- Logs show: `sudo: a password is required`
- Files in `data/` and `logs/` directories can't be deleted

## Solution

Three scripts are provided to diagnose and fix this issue:

### 1. `check_runner_sudo.sh` - Diagnostic Tool

**Safe, read-only check** - Makes no changes.

```bash
# Run locally on a runner
./check_runner_sudo.sh

# Or run remotely
ssh jetson@runner-hostname 'bash -s' < check_runner_sudo.sh
```

**Output:**
- ✅ `RUNNER IS PROPERLY CONFIGURED` - No action needed
- ❌ `RUNNER HAS TYPO IN CONFIGURATION` - Needs fix
- ❌ `RUNNER NOT CONFIGURED` - Needs initial setup

### 2. `fix_runner_sudo.sh` - Single Runner Fix

**Fixes one runner at a time.**

```bash
# Run locally on the runner
./fix_runner_sudo.sh

# Or run remotely
scp fix_runner_sudo.sh jetson@runner-hostname:/tmp/
ssh jetson@runner-hostname 'bash /tmp/fix_runner_sudo.sh'
```

**What it does:**
1. Backs up current configuration
2. Checks for typo and permission issues
3. Applies corrected configuration
4. Verifies the fix works
5. Reports success/failure

### 3. `fix_all_runners.sh` - Bulk Fix Tool

**Fixes multiple runners automatically.**

**Setup:**
Edit the script to list your runners:
```bash
DEFAULT_RUNNERS=(
    "jat04-iso0818"
    "jao512"
    "jao202-jp621"
    # Add all your runner hostnames
)
```

**Usage:**
```bash
# Fix all runners in DEFAULT_RUNNERS array
./fix_all_runners.sh

# Or specify runners as arguments
./fix_all_runners.sh jat04 jat05 jao512
```

**Requirements:**
- SSH access to all runners (passwordless SSH keys recommended)
- Ability to sudo on each runner

**Output:**
- Summary showing which runners succeeded, failed, or were unreachable

## The Correct Configuration

The sudoers file should contain:

```
jetson ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/ln, /bin/rm -rf /home/jetson/actions-runner/_work/*, /bin/chmod -R /home/jetson/actions-runner/_work/*, /bin/chown -R /home/jetson/actions-runner/_work/*
```

**Note:** No `> ` between `/` and `home`!

## Manual Fix

If you prefer to fix manually:

```bash
# Backup current config
sudo cp /etc/sudoers.d/jetson-actions /etc/sudoers.d/jetson-actions.backup

# Write correct config
echo 'jetson ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/ln, /bin/rm -rf /home/jetson/actions-runner/_work/*, /bin/chmod -R /home/jetson/actions-runner/_work/*, /bin/chown -R /home/jetson/actions-runner/_work/*' | sudo tee /etc/sudoers.d/jetson-actions

# Set correct permissions
sudo chmod 0440 /etc/sudoers.d/jetson-actions

# Verify syntax
sudo visudo -c -f /etc/sudoers.d/jetson-actions

# Test it works
sudo -k
sudo -n rm -rf /tmp/test
echo "Exit code: $?"  # Should be 0
```

## Verification

After applying the fix, verify with:

```bash
./check_runner_sudo.sh
```

Should show: ✅ `RUNNER IS PROPERLY CONFIGURED`

## Testing in Workflow

The workflows use this cleanup pattern:

```yaml
- name: Pre-checkout cleanup
  run: |
    echo "=== Pre-checkout Cleanup ==="
    sudo rm -rf /home/jetson/actions-runner/_work/jetson-containers/jetson-containers/data
    sudo rm -rf /home/jetson/actions-runner/_work/jetson-containers/jetson-containers/logs
    echo "Cleanup completed"
```

After fixing the runners, this should execute without password prompts.

## Quick Reference

| Task | Command |
|------|---------|
| Check single runner | `./check_runner_sudo.sh` |
| Fix single runner | `./fix_runner_sudo.sh` |
| Fix all runners | `./fix_all_runners.sh` |
| Manual check | `sudo -n rm -rf /tmp/test && echo OK` |

## Related Files

- `/etc/sudoers.d/jetson-actions` - Sudoers configuration file
- `docs/github-actions-self-hosted-runner-setup.md` - Full runner setup guide
- `.github/workflows/RUNNER_MAINTENANCE.md` - Workflow maintenance docs

## Impact

This issue affects **all runners** configured with the typo. Symptoms:
- ❌ Checkout failures in workflows
- ❌ Permission denied errors
- ❌ Builds fail before they even start

After fixing:
- ✅ Workflows run smoothly
- ✅ No password prompts
- ✅ Clean workspace every run

