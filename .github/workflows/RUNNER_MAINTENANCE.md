# Self-Hosted Runner Maintenance Guide

## ⚠️ CRITICAL: Be Careful With `sudo` in Workflow Steps

### Why We Avoid `sudo`

Self-hosted GitHub Actions runners run as a regular user (typically `jetson`). When a workflow step uses `sudo` for commands not configured for passwordless execution, it will:
1. **Prompt for password** on the runner console
2. **Hang indefinitely** waiting for user input
3. **Block the entire workflow** and potentially other jobs
4. **Cannot be killed** remotely without manual intervention

### History

We encountered this issue early in development when attempting to use `sudo` commands that required password prompts. This led to runner hangs and blocked workflows.

To address this, we implemented two solutions:
1. **Passwordless sudo** for specific cleanup commands in the workspace directory (see [GitHub Actions Self-Hosted Runner Setup](https://github.com/NVIDIA-AI-IOT/jetson-containers/blob/dev/docs/github-actions-self-hosted-runner-setup.md))
2. **Sudo-less cleanup strategy** using git and Docker's built-in mechanisms

The sudoers configuration allows these commands **when prefixed with `sudo`** to run **without password prompt**:
```
$USER ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/ln, /bin/rm -rf /home/jetson/actions-runner/_work/*, /bin/chmod -R /home/jetson/actions-runner/_work/*, /bin/chown -R /home/jetson/actions-runner/_work/*
```

**Important**: This means `sudo rm -rf /path` won't prompt for password, but you still NEED the `sudo` prefix. It doesn't make commands work without `sudo`.

**However**, testing revealed that `git clean -ffdx` **cannot** remove root-owned files (permission denied). Therefore, we **DO use sudo** with these requirements:
- **Full absolute paths**: Must match the NOPASSWD rule `/home/jetson/actions-runner/_work/*`
- **Use `$GITHUB_WORKSPACE`** or full paths, NOT relative paths
- **Configured NOPASSWD**: Relies on sudoers configuration being present

Look for comments like this in workflows:
```yaml
- name: Pre-clean workspace
  run: |
    # Use sudo with full paths - NOPASSWD is configured for workspace paths
    sudo rm -rf ${{ github.workspace }}/data/ || true
```

### Solution

Our cleanup strategy uses:
1. **Sudo with full paths** for removing root-owned files (relies on NOPASSWD configuration)
2. **Checkout with `clean: true`** as additional safety layer
3. **Docker cleanup** with proper user permissions
4. **`|| true`** to fail gracefully if sudo somehow fails

The key requirement: **Always use full absolute paths with sudo** to match the NOPASSWD rule.

### Understanding the Passwordless Sudo Configuration

The sudoers NOPASSWD configuration means these **commands WITH `sudo`** won't prompt for password:

```bash
# ✅ WORKS - Full absolute path matches NOPASSWD rule:
sudo rm -rf /home/jetson/actions-runner/_work/jetson-containers/jetson-containers/data
sudo rm -rf $PWD/data/                  # $PWD expands to full path
sudo rm -rf $GITHUB_WORKSPACE/data/     # In workflows

# ❌ FAILS - Relative path doesn't match NOPASSWD rule:
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers
sudo rm -rf data/                       # Will prompt! (relative path)

# ❌ FAILS - Wrong path (not in allowed list):
sudo rm -rf /tmp/some-file              # Will prompt! (not in workspace)

# ❌ FAILS - Wrong command (not in allowed list):
sudo systemctl restart docker            # Will prompt! (systemctl not allowed)
sudo docker system prune                 # Will prompt! (docker not allowed)

# ⚠️ WON'T WORK - Without sudo, root-owned files remain:
rm -rf /home/jetson/actions-runner/_work/.../data/audio/
# No password prompt, but permission denied on root-owned files
# Exit code 0 with || true (appears to succeed but files remain)
```

**Critical Requirements**:
1. **Must use `sudo`** - without it, root-owned files cannot be deleted
2. **Must use full absolute paths** - relative paths don't match the NOPASSWD rule
3. **Must be in workspace** - `/home/jetson/actions-runner/_work/*`
4. **Must use allowed commands** - `rm`, `chmod`, `chown` from the NOPASSWD list

**Best Practice for Workflows**:
- **DO** use `sudo rm -rf ${{ github.workspace }}/data/` with full paths
- **DON'T** use `sudo rm -rf data/` with relative paths (will prompt and hang)
- **DO** rely on NOPASSWD configuration being present on all runners
- **DO** keep `|| true` to fail gracefully if something unexpected happens

---

## Workspace Cleanup Strategy

### Discover Job Cleanup
```yaml
- name: Pre-clean workspace (discover)
  run: |
    # Use sudo with FULL PATHS to match NOPASSWD rule
    sudo rm -rf ${{ github.workspace }}/data/ || true
    sudo rm -rf ${{ github.workspace }}/logs/ || true
    sudo rm -rf ${{ github.workspace }}/build/ || true
    sudo rm -rf ${{ github.workspace }}/test/ || true
    rm -f results.json || true

- name: Checkout
  uses: actions/checkout@v4
  with:
    clean: true  # Additional safety layer
```

### Run-Chunks Job Cleanup
```yaml
- name: Pre-clean workspace
  run: |
    # Use sudo with FULL PATHS to match NOPASSWD rule
    ROOT="${RUNNER_WORKSPACE}/jetson-containers/jetson-containers"
    sudo rm -rf "${ROOT}/data" "${ROOT}/logs" || true
    sudo rm -rf ${{ github.workspace }}/data/ || true
    sudo rm -rf ${{ github.workspace }}/logs/ || true
    sudo rm -rf ${{ github.workspace }}/build/ || true
    sudo rm -rf ${{ github.workspace }}/test/ || true
    rm -f results.json || true
    mkdir -p logs
    # Docker cleanup with flock to prevent race conditions
    docker system prune -af  # or -f for cache-friendly
```

**Key Points:**
- ✅ Uses `sudo` with `${{ github.workspace }}` (full path)
- ✅ Won't prompt because path matches NOPASSWD rule
- ✅ Actually removes root-owned files (unlike `git clean`)
- ✅ `|| true` ensures workflow continues even if sudo fails

---

## Permission Issues from Docker Builds

### Problem
Docker containers often run as root and create directories/files owned by root in the workspace:
- `data/` directories (e.g., `data/audio/`)
- Build artifacts
- Log files

When git checkout tries to work with these directories, it fails with:
```
fatal: cannot create directory at 'data/audio': Permission denied
```

**Key insight**: The error is misleading - git isn't trying to CREATE the directory (it already exists), it's trying to WRITE FILES into a root-owned directory, which fails.

```bash
mkdir -p data/audio          # ✅ Succeeds (directory exists)
touch data/audio/file.txt    # ❌ Fails (permission denied - can't write)
```

### Why This Became an Issue
- **Orin runners**: Long-running, accumulated root-owned directories over multiple builds
- **Thor runners**: Newer, less accumulated cruft, or different packages that don't create problematic directories
- **`clean: false`**: Workspace persisted between runs, root-owned directories prevented git checkout from writing files

### Solution
1. **Use sudo with full paths** in pre-clean steps (primary fix) - actually removes root-owned directories
2. **Set `clean: true`** in checkout action (additional safety layer)
3. **Rely on NOPASSWD configuration** - allows sudo without password prompts in workspace paths

**Important**: Testing proved that `git clean -ffdx` **cannot** remove root-owned files (permission denied). Therefore, sudo is required.

---

## Testing Cleanup on Runners

### Before Making Changes

SSH into the runner and check current state:
```bash
# Check workspace directory
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers
ls -la

# Look for root-owned files
ls -la data/ 2>/dev/null || echo "No data directory"
find . -user root 2>/dev/null | head -20

# Check disk usage
du -sh data/ logs/ build/ test/ 2>/dev/null
```

### Test Cleanup Commands

Simulate what the workflow does:
```bash
# Navigate to workspace
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers

# Test pre-clean (without sudo)
rm -rf data/ logs/ build/ test/ || true
rm -f results.json || true

# Check what's left
ls -la
find . -user root 2>/dev/null | head -20

# Test git clean (what checkout action does)
git clean -ffdx
git status

# Final check
ls -la
find . -user root 2>/dev/null | head -20
```

### Expected Results
- `rm -rf` commands: May fail on root-owned files (expected, that's OK)
- `git clean -ffdx`: Should remove remaining files including root-owned ones
- Final state: Clean workspace ready for next build

---

## Manual Cleanup (If Needed)

If a runner gets stuck with permission issues:

### Option 1: Use the Runner Service Account
```bash
# The runner service might have sudo privileges configured
# Check /etc/sudoers.d/ for runner configuration

# If available:
sudo rm -rf /home/jetson/actions-runner/_work/jetson-containers/jetson-containers/data
```

### Option 2: Docker Cleanup
```bash
# Remove Docker containers and volumes (they might hold references)
docker system prune -af --volumes

# Then try regular cleanup again
cd /home/jetson/actions-runner/_work/jetson-containers/jetson-containers
rm -rf data/ logs/ build/ test/ || true
```

### Option 3: Restart Runner
```bash
cd /home/jetson/actions-runner
./svc.sh stop
# Manually clean workspace with appropriate permissions
./svc.sh start
```

---

## Monitoring

### Check for Stuck Jobs
```bash
# On the runner
ps aux | grep actions-runner

# Check for hanging processes waiting for input
ps aux | grep -E "sudo|password"
```

### Workflow Indicators
- Job runs for >5 minutes without output: Likely hanging on sudo
- Pre-clean step never completes: Permission or sudo issue
- Checkout fails with "Permission denied": Root-owned files preventing cleanup

---

## Best Practices

1. ✅ **Always use `clean: true`** in checkout actions for self-hosted runners
2. ✅ **Never use `sudo`** in workflow steps
3. ✅ **Use `|| true`** for cleanup commands to fail gracefully
4. ✅ **Use `docker system prune`** with appropriate flags for cache management
5. ✅ **Use `flock`** to prevent concurrent Docker operations
6. ❌ **Don't assume** workspace is clean between runs
7. ❌ **Don't use** `clean: false` unless you have a specific reason

---

## Troubleshooting Guide

### Symptom: Checkout fails with "Permission denied"
**Cause**: Root-owned files from previous Docker builds
**Fix**: Ensure `clean: true` in checkout action

### Symptom: Job hangs at pre-clean step
**Cause**: Accidental use of `sudo` in cleanup commands
**Fix**: Remove all `sudo` commands, use `|| true` for resilience

### Symptom: "data/audio" permission denied
**Cause**: Previous build created root-owned `data/audio` directory
**Fix**: `clean: true` will handle this automatically

### Symptom: Runner disk full
**Cause**: Docker images accumulating over time
**Fix**: Ensure `docker system prune -af` runs regularly (or `-f` for cache mode)

---

## Configuration Reference

### Checkout Action Settings
```yaml
uses: actions/checkout@v4
with:
  fetch-depth: 1          # Shallow clone for speed
  clean: true             # REQUIRED: Clean workspace before checkout
  submodules: false       # Set based on your needs
```

### Docker Cleanup Settings
```yaml
# Fresh build (no cache)
docker system prune -af

# Cache-friendly build (keeps images)
docker system prune -f
```

---

## Questions?

If you're unsure whether to use `sudo`:
- **DON'T use it** in GitHub Actions workflow steps
- **DO** rely on git and Docker's built-in cleanup mechanisms
- **ASK** if you think you need elevated permissions - there's usually a better way

Last Updated: 2025-10-09

