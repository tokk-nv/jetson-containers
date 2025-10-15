# Version Pinning Implementation Summary

This document summarizes the implementation of flexible version pinning for jetson-containers packages.

## What Was Implemented

A flexible version pinning system that supports four version formats:

1. **Branch names**: `'main'`, `'release-tests'`, `'nightly-fix'`
2. **Tag names**: `'v0.35.1'`, `'v0.36.0'`
3. **Commit hashes**: `'3eb4078'`, `'a4bc8454783dbae3be9cf840f074b961a558aba5'`
4. **Tag + commit**: `'v0.35.1+0f252be'` (RECOMMENDED for stability)

## Files Modified

### 1. `config.py`
**Changes:**
- Added `_is_commit_hash()` helper function to detect if a string is a git commit hash
- Updated `diffusers()` function to parse all four version formats
- Added intelligent version parsing logic that:
  - Splits tag+commit format on '+'
  - Detects pure commit hashes (7-40 hex characters, no 'v' prefix)
  - Treats everything else as branch/tag names
- Sets appropriate `DIFFUSERS_VERSION` and `DIFFUSERS_COMMIT` build args

### 2. `Dockerfile`
**Changes:**
- Added `DIFFUSERS_COMMIT` ARG to support commit-based builds

### 3. `build.sh`
**Changes:**
- Completely refactored git clone logic to handle all version formats
- Priority order:
  1. If `DIFFUSERS_COMMIT` is set → clone full repo, checkout specific commit
  2. If `DIFFUSERS_VERSION` is set → use `git clone --branch` (works for both branches and tags)
  3. If neither is set → clone main branch
- Added informative echo messages to show what's being built

### 4. New Files Created

- **`VERSION_PINNING.md`**: Comprehensive user documentation
- **`test_version_parsing.py`**: Test script to verify version parsing logic
- **`IMPLEMENTATION_SUMMARY.md`**: This file

## How It Works

### Version Detection Logic

```
Input: 'v0.35.1+0f252be'
├─ Contains '+'? YES
├─ Split: base='v0.35.1', commit='0f252be'
└─ Result: DIFFUSERS_VERSION=v0.35.1, DIFFUSERS_COMMIT=0f252be

Input: '3eb4078'
├─ Contains '+'? NO
├─ Is hex (7-40 chars)? YES
└─ Result: DIFFUSERS_COMMIT=3eb4078

Input: 'v0.35.1'
├─ Contains '+'? NO
├─ Is hex (7-40 chars)? NO (has 'v' prefix)
└─ Result: DIFFUSERS_VERSION=v0.35.1

Input: 'main'
├─ Contains '+'? NO
├─ Is hex (7-40 chars)? NO (has 'i' and 'n')
└─ Result: No build args (special case for 'main')
```

### Build Process

The `build.sh` script receives the build args and:

```bash
if [ -n "${DIFFUSERS_COMMIT}" ]; then
    # Clone full repo (no --depth=1) and checkout specific commit
    git clone --recursive https://github.com/huggingface/diffusers /opt/diffusers
    git checkout ${DIFFUSERS_COMMIT}

elif [ -n "${DIFFUSERS_VERSION}" ]; then
    # Clone specific branch or tag
    git clone --branch=${DIFFUSERS_VERSION} --depth=1 --recursive ...

else
    # Clone main branch (default)
    git clone --recursive ...
fi
```

## Example Usage

```python
package = [
    # Stable release
    diffusers('v0.35.1', default=False),

    # RECOMMENDED: Pinned to specific commit with context
    diffusers('v0.35.1+0f252be', default=True),

    # Direct commit (no version context)
    diffusers('a4bc845', default=False),

    # Track main (for testing)
    diffusers('main', default=False),
]
```

## Benefits

1. **Reproducibility**: Commit pinning ensures builds are deterministic
2. **Stability**: Won't break due to upstream changes
3. **Flexibility**: Can use unreleased features/fixes
4. **Context**: Tag+commit format documents what release you're near
5. **Backward Compatibility**: Existing configs continue to work

## Testing

Run the test script to verify version parsing:

```bash
cd packages/diffusion/diffusers
python3 test_version_parsing.py
```

Expected output shows parsing results for all format types.

## Migration Path

For users currently on `main`:

1. Find current commit: `git log -1 --format=%h`
2. Find nearest tag: `git describe --tags --abbrev=0`
3. Use format: `diffusers('v0.35.1+abc1234', default=True)`

## Applicability to Other Packages

This pattern can be applied to any package that builds from a git repository:

1. Add version parsing logic to the package's `config.py`
2. Pass `PACKAGE_VERSION` and `PACKAGE_COMMIT` as build args
3. Update `build.sh` to handle both args appropriately

Examples of other packages that could benefit:
- `transformers`
- `pytorch` (if building from source)
- `torchvision`
- Any package built from a git checkout

## Future Enhancements

Possible improvements:
- Add commit hash validation (check if commit exists before building)
- Auto-fetch latest commit hash for a given tag
- Support for git refs like `refs/pull/1234/head` for testing PRs
- Cache cloned repos to speed up builds with different commits

