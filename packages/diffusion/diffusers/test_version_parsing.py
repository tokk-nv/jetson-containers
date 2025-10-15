#!/usr/bin/env python3
"""
Test script for version pinning functionality.
This demonstrates how different version formats are parsed and used.
"""

def _is_commit_hash(s):
    """Check if string looks like a git commit hash (7-40 hex characters)."""
    if not s:
        return False
    return len(s) >= 7 and len(s) <= 40 and all(c in '0123456789abcdef' for c in s.lower())


def _is_version_number(s):
    """Check if string looks like a version number (e.g., '0.35.1', '1.2.3')."""
    if not s:
        return False
    return s[0].isdigit() and '.' in s


def parse_version(version):
    """Parse version string into base_version and commit_hash."""
    base_version = None
    commit_hash = None

    if '+' in version:
        # Format: version+commit (e.g., '0.35.1+a4bc845')
        base_version, commit_hash = version.split('+', 1)
    elif _is_commit_hash(version):
        # Pure commit hash
        commit_hash = version
    else:
        # Branch name or version tag
        base_version = version

    return base_version, commit_hash


def test_version_parsing():
    """Test parsing of different version formats"""

    test_cases = [
        # (input, expected_base_version, expected_commit, expected_git_version, description)
        ('main', 'main', None, None, 'Branch name'),
        ('release-tests', 'release-tests', None, 'release-tests', 'Custom branch name'),
        ('0.35.1', '0.35.1', None, 'v0.35.1', 'Version tag (v added automatically)'),
        ('0.36.0', '0.36.0', None, 'v0.36.0', 'Another version tag'),
        ('3eb4078', None, '3eb4078', None, 'Short commit hash'),
        ('a4bc8454783dbae3be9cf840f074b961a558aba5', None, 'a4bc8454783dbae3be9cf840f074b961a558aba5', None, 'Full commit hash'),
        ('0.35.1+0f252be', '0.35.1', '0f252be', 'v0.35.1', 'Version + commit'),
        ('0.36.0+abc123def456', '0.36.0', 'abc123def456', 'v0.36.0', 'Version + longer commit'),
    ]

    print("Testing version parsing logic:\n")
    print("=" * 80)

    all_passed = True

    for version, expected_base, expected_commit, expected_git_version, description in test_cases:
        base_version, commit_hash = parse_version(version)

        # Verify results
        success = (base_version == expected_base and commit_hash == expected_commit)
        status = "✓" if success else "✗"
        all_passed = all_passed and success

        print(f"\n{status} {description}: '{version}'")
        print(f"  Parsed base:   {base_version!r} (expected: {expected_base!r})")
        print(f"  Parsed commit: {commit_hash!r} (expected: {expected_commit!r})")

        # Show what build args would be generated (following jetson-containers convention)
        build_args = {}
        if base_version and base_version != 'main':
            # Add 'v' prefix for version numbers
            if _is_version_number(base_version):
                build_args['DIFFUSERS_VERSION'] = f'v{base_version}'
            else:
                build_args['DIFFUSERS_VERSION'] = base_version
        if commit_hash:
            build_args['DIFFUSERS_COMMIT'] = commit_hash
        print(f"  Build args:    {build_args}")
        if expected_git_version:
            print(f"  Git version:   {build_args.get('DIFFUSERS_VERSION', 'N/A')} (expected: {expected_git_version})")

        if not success:
            print(f"  ❌ FAILED!")

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == '__main__':
    exit(test_version_parsing())

