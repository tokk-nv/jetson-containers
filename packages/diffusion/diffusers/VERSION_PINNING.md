# Diffusers Version Pinning

This document explains how to pin diffusers to specific versions or commits.

## Version Format

The `diffusers()` function in `config.py` supports four version formats:

### 1. Branch Name (e.g., `'main'`, `'release-tests'`)
```python
diffusers('main', default=True)
diffusers('release-tests', default=False)
```
- Clones the latest code from the specified branch
- **Risk**: Upstream changes can break your build
- **Use case**: Tracking bleeding-edge development or testing branches

### 2. Tag Name (e.g., `'0.35.1'`)
```python
diffusers('0.35.1', default=True)  # Recommended - follows jetson-containers convention
# diffusers('v0.35.1', default=True)  # Also works but not recommended
```
- Checks out a specific release tag from the upstream repo
- **Convention**: Specify WITHOUT 'v' prefix (e.g., `'0.35.1'` not `'v0.35.1'`)
  - Matches PyPI version format: `pip install diffusers==0.35.1`
  - Consistent with other jetson-containers packages (vllm, habitat-sim)
  - Config automatically adds 'v' for git operations
- Stable and reproducible
- **Use case**: Building from a stable release

### 3. Commit Hash (e.g., `'3eb4078'` or full hash)
```python
diffusers('3eb4078', default=True)
diffusers('a4bc8454783dbae3be9cf840f074b961a558aba5', default=True)
```
- Checks out a specific commit by its hash (short or full)
- Most stable: guaranteed not to change
- **Use case**: When you need a specific state of the codebase

### 4. Tag + Commit Hash (e.g., `'0.35.1+0f252be'`) ⭐ **RECOMMENDED**
```python
diffusers('0.35.1+0f252be', default=True)  # Recommended format
# diffusers('v0.35.1+0f252be', default=True)  # Also works
```
- Checks out the specific commit, with tag providing context
- Best of both worlds: reference a version for context + pin to exact commit
- **Convention**: Use version WITHOUT 'v' prefix (e.g., `'0.35.1+abc1234'`)
- **Use case**: When you need features/fixes that came after a release but before the next one
- **Recommended**: This is the safest way to track post-release commits while documenting context

## Finding Branches, Tags, and Commits

### Branches
View all branches at: https://github.com/huggingface/diffusers/branches
- Common branches: `main`, `release-tests`

### Tags (Releases)
View all releases at: https://github.com/huggingface/diffusers/releases
- GitHub tags include the 'v' prefix: `v0.35.1`, `v0.36.0`, etc.
- **In config.py, specify WITHOUT 'v'**: `diffusers('0.35.1')` not `diffusers('v0.35.1')`
- The latest stable release is shown at the top

### Commit Hashes

#### Option 1: GitHub Web Interface
1. Go to https://github.com/huggingface/diffusers
2. Click on "Commits" to see commit history
3. Navigate to the commit you want (or view a specific PR's commits)
4. Copy the short hash (7 characters, shown in the UI) or full hash (40 characters)

#### Option 2: Command Line
```bash
# Clone the repo
git clone https://github.com/huggingface/diffusers
cd diffusers

# List recent commits with short hashes
git log --oneline -n 10

# Find commits after a specific tag
git log v0.35.1..HEAD --oneline

# Get the commit hash of a tag
git rev-list -n 1 v0.35.1

# Get full hash of a specific commit
git rev-parse 3eb4078
```

#### Option 3: GitHub Releases Page
- Each release at https://github.com/huggingface/diffusers/releases shows the commit hash
- Click on the commit hash to see what code state that release represents

## Example Configuration

```python
package = [
    # Released version - stable but may be missing features
    diffusers('0.35.1', default=False),

    # Pinned to specific commit after v0.35.1 with needed fixes (RECOMMENDED)
    diffusers('0.35.1+0f252be', default=True),

    # Direct commit hash - most explicit, no version context
    diffusers('3eb4078', default=False),

    # Track main branch - useful for testing but risky for production
    diffusers('main', default=False),

    # Custom branch for testing specific features
    diffusers('release-tests', default=False),
]
```

## Migration Guide

If you're currently using:
```python
diffusers('main', default=True)
```

To migrate to commit pinning:

1. Find the current HEAD commit hash of main:
   ```bash
   git clone https://github.com/huggingface/diffusers
   cd diffusers
   git checkout main
   git log -1 --format=%h  # Get short hash like: 3eb4078
   ```

2. Find the nearest tag (for context):
   ```bash
   git describe --tags --abbrev=0  # e.g., v0.35.1
   ```

3. Choose your approach:

   **Option A: Tag + Commit (Recommended)**
   ```python
   diffusers('0.35.1+3eb4078', default=True)  # Provides version context
   ```

   **Option B: Pure Commit**
   ```python
   diffusers('3eb4078', default=True)  # Most explicit, no version context
   ```

## Benefits of Commit Pinning

1. **Reproducibility**: Builds are deterministic and won't break due to upstream changes
2. **Context**: The version number provides context about what release you're near
3. **Flexibility**: Access post-release fixes without waiting for next release
4. **Testability**: Can test main branch separately while using stable pinned version

## Updating to a New Commit

When you want to update to a newer commit:

1. Test the new commit first:
   ```python
   package = [
       diffusers('0.35.1+old_hash', default=True),
       diffusers('0.35.1+new_hash', default=False),  # Test this first
   ]
   ```

2. After validation, swap the default:
   ```python
   package = [
       diffusers('0.35.1+old_hash', default=False),
       diffusers('0.35.1+new_hash', default=True),   # Now the default
   ]
   ```

3. Eventually remove the old version:
   ```python
   package = [
       diffusers('0.35.1+new_hash', default=True),
   ]
   ```

## Version Detection Logic

The system automatically detects which format you're using:

1. **Contains '+'** → Split into tag+commit: `'0.35.1+0f252be'` → version=`0.35.1`, commit=`0f252be`
2. **Is hex (7-40 chars)** → Treat as commit: `'3eb4078'` → commit=`3eb4078`
3. **Otherwise** → Treat as branch/tag name: `'main'` or `'0.35.1'` → use as branch/tag

This means:
- `'0.35.1'` → Adds 'v' prefix → Checks out tag v0.35.1
- `'v0.35.1'` → Forgiving, also works → Checks out tag v0.35.1
- `'0f252be'` → Checks out commit 0f252be (detected as hex)
- `'main'` → Checks out main branch (not hex)
- `'0.35.1+0f252be'` → Checks out commit 0f252be (with 0.35.1 for context)

