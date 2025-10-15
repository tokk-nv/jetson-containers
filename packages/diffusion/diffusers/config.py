def diffusers(version, requires=None, default=False):
    pkg = package.copy()

    if requires:
        pkg['requires'] = requires

    pkg['name'] = f'diffusers:{version}'

    # Parse version format - supports:
    #  1. Branch name: "main", "release-tests", etc.
    #  2. Version tag: "0.35.1", "0.36.0" (will add 'v' prefix for git)
    #  3. Commit ID: "3eb4078", "a4bc8454783dbae3be9cf840f074b961a558aba5"
    #  4. Version + commit: "0.35.1+a4bc845" (version for context, commit for pinning) ⭐ RECOMMENDED

    base_version = None
    commit_hash = None

    if '+' in version:
        # Format: version+commit (e.g., '0.35.1+a4bc845')
        base_version, commit_hash = version.split('+', 1)
    elif _is_commit_hash(version):
        # Pure commit hash (7-40 hex chars)
        commit_hash = version
    else:
        # Branch name or version tag
        base_version = version

    # Build the build_args
    pkg['build_args'] = {}

    if base_version and base_version != 'main':
        # For version tags, add 'v' prefix for git operations (e.g., '0.35.1' -> 'v0.35.1')
        # For branch names, use as-is
        # Strip 'v' prefix if accidentally included (to be more forgiving)
        if base_version.startswith('v') and _is_version_number(base_version[1:]):
            # User passed 'v0.35.1' - strip the v and re-add it
            pkg['build_args']['DIFFUSERS_VERSION'] = base_version
        elif _is_version_number(base_version):
            # User passed '0.35.1' - add the v prefix
            pkg['build_args']['DIFFUSERS_VERSION'] = f'v{base_version}'
        else:
            # Branch name - use as-is
            pkg['build_args']['DIFFUSERS_VERSION'] = base_version

    if commit_hash:
        # Set commit hash when specified (either standalone or after '+')
        pkg['build_args']['DIFFUSERS_COMMIT'] = commit_hash

    builder = pkg.copy()

    builder['name'] = f'diffusers:{version}-builder'
    builder['build_args'] = {**pkg['build_args'], **{'FORCE_BUILD': 'on'}}

    if default:
        pkg['alias'] = 'diffusers'
        builder['alias'] = 'diffusers:builder'

    return pkg, builder


def _is_commit_hash(s):
    """Check if string looks like a git commit hash (7-40 hex characters)."""
    if not s:
        return False
    # Check if it's hex and reasonable length for a git hash
    return len(s) >= 7 and len(s) <= 40 and all(c in '0123456789abcdef' for c in s.lower())


def _is_version_number(s):
    """Check if string looks like a version number (e.g., '0.35.1', '1.2.3')."""
    if not s:
        return False
    # Simple check: starts with digit and contains dots
    return s[0].isdigit() and '.' in s

package = [
    # Version format examples (WITHOUT 'v' prefix - added automatically):
    #  - Branch:         'main', 'release-tests', 'nightly-fix'
    #  - Version tag:    '0.35.1' (automatically becomes 'v0.35.1' for git)
    #                    ⚠️  Only use tags that exist! Non-existent tags will FAIL (no silent fallback)
    #  - Commit hash:    '3eb4078', 'a4bc8454783dbae3be9cf840f074b961a558aba5'
    #  - Version+commit: '0.35.1+a4bc845' (version for context, commit for stability) ⭐ RECOMMENDED

    #diffusers('0.35.1', default=False),
    #diffusers('main', default=True), # we force build main until the next diffusers release

    # Example with commit pinning (uncomment when ready to use):
    diffusers('0.35.1+3eb4078', default=True),   # Pin to known-good commit
    diffusers('main', default=False),            # Track upstream main (non-default) to catch breakages early
]

