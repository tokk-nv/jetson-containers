# Quick Reference: Version Pinning

## Version Format Cheat Sheet

| Format | Example | When to Use |
|--------|---------|-------------|
| **Branch** | `'main'` | Testing bleeding edge (⚠️ can break) |
| **Tag** | `'0.35.1'` | Stable release (NO 'v' prefix) |
| **Commit** | `'3eb4078'` | Pin to specific state |
| **Tag+Commit** | `'0.35.1+0f252be'` | ⭐ **RECOMMENDED**: Stable + needed fixes |

## Common Workflows

### Finding the Right Commit

```bash
# Clone and explore
git clone https://github.com/huggingface/diffusers
cd diffusers

# See latest commits
git log --oneline -n 20

# Find commits after a release
git log v0.35.1..HEAD --oneline

# Get current main HEAD
git log -1 --format=%h main
```

### Config Examples

#### Production (Stable + Safe)
```python
package = [
    diffusers('0.35.1+0f252be', default=True),  # Pinned to known good commit
]
```

#### Development (Testing + Stable Fallback)
```python
package = [
    diffusers('0.35.1+0f252be', default=True),  # Stable default
    diffusers('main', default=False),            # Test main separately
]
```

#### Multi-Version Testing
```python
package = [
    diffusers('0.35.1', default=False),          # Previous release
    diffusers('0.35.1+abc1234', default=True),   # Stable with fixes
    diffusers('0.36.0', default=False),          # Next release (when available)
    diffusers('main', default=False),            # Bleeding edge
]
```

## Build Args Generated

| Version String | DIFFUSERS_VERSION | DIFFUSERS_COMMIT |
|----------------|-------------------|------------------|
| `'main'` | *(not set)* | *(not set)* |
| `'0.35.1'` | `v0.35.1` | *(not set)* |
| `'3eb4078'` | *(not set)* | `3eb4078` |
| `'0.35.1+3eb4078'` | `v0.35.1` | `3eb4078` |

## What Gets Checked Out

| Build Args | Git Command |
|------------|-------------|
| None | `git clone` → main branch |
| `VERSION=v0.35.1` | `git clone --branch=v0.35.1` (auto-adds 'v') |
| `COMMIT=3eb4078` | `git clone && git checkout 3eb4078` |
| Both | `git clone && git checkout 3eb4078` (commit wins) |

## Migration Checklist

- [ ] Find current commit you're using (if on `main`)
- [ ] Find nearest release tag for context
- [ ] Test new pinned version builds successfully
- [ ] Update config.py with `tag+commit` format
- [ ] Document why this commit was chosen (in comments)
- [ ] Keep `main` as a non-default option for future testing

## Pro Tips

💡 **Use tag+commit format**: Provides both stability (commit pin) and context (which release)

💡 **Test before defaulting**: Add new version with `default=False`, test it, then flip to `True`

💡 **Document your commits**: Add inline comments explaining why a specific commit was chosen

💡 **Keep a test version**: Always have `main` or latest as a non-default option to catch breakages early

## Examples with Context

```python
package = [
    # Pinned to commit after v0.35.1 that adds Qwen-Image-Edit improvements
    # See: https://github.com/huggingface/diffusers/pull/12188
    diffusers('0.35.1+0f252be', default=True),

    # Track main for CI testing
    diffusers('main', default=False),
]
```

## Version Format Convention

**✅ Recommended** (NO 'v' prefix):
```python
diffusers('0.35.1')           # Version tag
diffusers('0.35.1+abc1234')   # Version + commit
```

**⚠️ Accepted but NOT recommended** ('v' prefix):
```python
diffusers('v0.35.1')          # Works, but inconsistent with JC convention
diffusers('v0.35.1+abc1234')  # Works, but inconsistent with JC convention
```

**Why no 'v'?**
- Matches PyPI: `pip install diffusers==0.35.1`
- Consistent with other JC packages (vllm, habitat-sim)
- Config.py adds 'v' automatically for git operations

## Common Patterns

### "I need a feature from main, but main keeps breaking"
→ Find the commit with the feature, pin to it:
```python
diffusers('v0.35.1+abc1234', default=True)  # abc1234 has the feature
```

### "I want to track a release but it has a critical bug"
→ Find the commit that fixes it, use tag+commit:
```python
diffusers('v0.35.1+def5678', default=True)  # def5678 fixes the bug
```

### "I want to test if upgrading to v0.36.0 will work"
→ Add both versions:
```python
diffusers('v0.35.1+current', default=True),   # Current stable
diffusers('v0.36.0', default=False),          # Test this
```

