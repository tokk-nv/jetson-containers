#!/usr/bin/env python3
"""
Integration test for diffusers config.py
Tests the actual functions with real package object and edge cases.
"""

import sys
import os
import importlib.util

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))

def create_mock_package():
    """Create a mock package dict similar to what jetson-containers provides."""
    # This mimics what jetson-containers passes as the base package dict
    # Based on jetson_containers/packages.py line 118-124
    return {
        'path': os.path.dirname(os.path.abspath(__file__)),
        'name': 'diffusers',
        'group': 'diffusion',
        'depends': ['pytorch', 'torchvision', 'transformers', 'onnx'],
        'requires': '>=34.1.0',
        'postfix': '',
        'config': [],
        'test': [],
        'build_args': {},
    }

# Load config.py as a module without executing the package list at the bottom
config_path = os.path.join(os.path.dirname(__file__), 'config.py')

# Read the config file and inject our mock package
with open(config_path, 'r') as f:
    config_source = f.read()

# Find where the 'package = [' list definition starts and exclude it
# We only want to execute the function definitions, not the package list
lines = config_source.split('\n')
code_lines = []
for i, line in enumerate(lines):
    # Stop before the final 'package = [' list
    if line.startswith('package = ['):
        break
    code_lines.append(line)

config_code = '\n'.join(code_lines)

# Create a module namespace with our mock package
namespace = {'package': create_mock_package()}

# Execute only the function definitions in our namespace
exec(config_code, namespace)

# Extract the functions we need
diffusers = namespace['diffusers']
_is_commit_hash = namespace['_is_commit_hash']
_is_version_number = namespace['_is_version_number']

def test_helper_functions():
    """Test the helper functions."""
    print("Testing helper functions:")
    print("-" * 80)

    # Test _is_commit_hash
    test_cases = [
        ('3eb4078', True, 'Short commit hash'),
        ('a4bc8454783dbae3be9cf840f074b961a558aba5', True, 'Full commit hash'),
        ('0.35.1', False, 'Version number (has dots)'),
        ('main', False, 'Branch name'),
        ('v0.35.1', False, 'Version with v (has v and dots)'),
        ('release-tests', False, 'Branch with dash'),
    ]

    all_passed = True
    for value, expected, desc in test_cases:
        result = _is_commit_hash(value)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"  {status} _is_commit_hash('{value}') = {result} (expected {expected}) - {desc}")

    print()

    # Test _is_version_number
    test_cases = [
        ('0.35.1', True, 'Version number'),
        ('1.2.3', True, 'Simple version'),
        ('v0.35.1', False, 'Version with v prefix'),
        ('main', False, 'Branch name'),
        ('3eb4078', False, 'Commit hash (no dots)'),
    ]

    for value, expected, desc in test_cases:
        result = _is_version_number(value)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"  {status} _is_version_number('{value}') = {result} (expected {expected}) - {desc}")

    print()
    return all_passed


def test_diffusers_function():
    """Test the actual diffusers() function with various inputs."""
    print("Testing diffusers() function:")
    print("=" * 80)
    print("NOTE: This tests config.py parsing logic, not whether versions exist")
    print("      ✅ = Parsing succeeded as expected")
    print("      ⚠️  = Parsing OK, but version doesn't exist (will fail at build)")
    print("      See test_git_fallback.sh for build-time validation")
    print("=" * 80)

    test_cases = [
        # (version, expected_VERSION, expected_COMMIT, exists_in_repo, description)
        # exists_in_repo: True=version exists, False=will fail at build time
        ('main', None, None, True, 'Branch: main'),
        ('release-tests', 'release-tests', None, True, 'Branch: release-tests'),
        ('0.35.1', 'v0.35.1', None, True, 'Version tag (auto-add v)'),
        ('0.36.0', 'v0.36.0', None, False, 'Version tag (DOESN\'T EXIST YET)'),
        ('v0.35.1', 'v0.35.1', None, True, 'Version tag WITH v (forgiving)'),
        ('v0.36.0', 'v0.36.0', None, False, 'Version tag WITH v (DOESN\'T EXIST YET)'),
        ('3eb4078', None, '3eb4078', True, 'Commit hash (short)'),
        ('deadbee', None, 'deadbee', False, 'Commit hash (DOESN\'T EXIST)'),
        ('a4bc8454783dbae3be9cf840f074b961a558aba5', None, 'a4bc8454783dbae3be9cf840f074b961a558aba5', True, 'Commit hash (full)'),
        ('0.35.1+0f252be', 'v0.35.1', '0f252be', True, 'Version+commit (RECOMMENDED)'),
        ('v0.35.1+0f252be', 'v0.35.1', '0f252be', True, 'Version+commit WITH v (forgiving)'),
    ]

    all_passed = True

    for version, expected_ver, expected_commit, exists_in_repo, desc in test_cases:
        try:
            pkg, builder = diffusers(version)

            actual_ver = pkg['build_args'].get('DIFFUSERS_VERSION')
            actual_commit = pkg['build_args'].get('DIFFUSERS_COMMIT')

            ver_match = actual_ver == expected_ver
            commit_match = actual_commit == expected_commit
            success = ver_match and commit_match

            # Status for parsing (separate from build-time existence)
            status = "✅" if success else "❌"
            if not success:
                all_passed = False

            # Show warning for versions that don't exist
            if not exists_in_repo:
                status = "⚠️ "
                desc = f"{desc} [PARSE OK, BUILD WILL FAIL]"

            print(f"\n{status} {desc}: '{version}'")
            print(f"  Package name:        {pkg['name']}")
            print(f"  DIFFUSERS_VERSION:   {actual_ver!r} (expected: {expected_ver!r}) {'✅' if ver_match else '❌'}")
            print(f"  DIFFUSERS_COMMIT:    {actual_commit!r} (expected: {expected_commit!r}) {'✅' if commit_match else '❌'}")
            print(f"  Builder name:        {builder['name']}")
            print(f"  FORCE_BUILD:         {builder['build_args'].get('FORCE_BUILD', 'off')}")

            if not exists_in_repo:
                print(f"  ⚠️  WARNING: This version doesn't exist in upstream repo!")
                print(f"      build.sh will fail with helpful error message")
                print(f"      See test_git_fallback.sh for validation")

        except Exception as e:
            print(f"\n❌ {desc}: '{version}'")
            print(f"  ERROR: {e}")
            all_passed = False

    print("\n" + "=" * 80)
    return all_passed


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\nTesting edge cases:")
    print("-" * 80)

    all_passed = True

    # Test with default=True
    try:
        pkg, builder = diffusers('0.35.1', default=True)
        has_alias = pkg.get('alias') == 'diffusers'
        has_builder_alias = builder.get('alias') == 'diffusers:builder'

        status = "✅" if has_alias and has_builder_alias else "❌"
        if not (has_alias and has_builder_alias):
            all_passed = False

        print(f"  {status} default=True sets aliases correctly")
        print(f"      pkg alias:     {pkg.get('alias')!r}")
        print(f"      builder alias: {builder.get('alias')!r}")
    except Exception as e:
        print(f"  ❌ default=True test failed: {e}")
        all_passed = False

    # Test with requires
    try:
        pkg, builder = diffusers('0.35.1', requires='>=36')
        has_requires = pkg.get('requires') == '>=36'

        status = "✅" if has_requires else "❌"
        if not has_requires:
            all_passed = False

        print(f"  {status} requires parameter works")
        print(f"      requires: {pkg.get('requires')!r}")
    except Exception as e:
        print(f"  ❌ requires test failed: {e}")
        all_passed = False

    # Test that package name reflects the input version (not the git version)
    try:
        pkg, builder = diffusers('0.35.1')
        name_correct = pkg['name'] == 'diffusers:0.35.1'
        builder_name_correct = builder['name'] == 'diffusers:0.35.1-builder'

        status = "✅" if name_correct and builder_name_correct else "❌"
        if not (name_correct and builder_name_correct):
            all_passed = False

        print(f"  {status} Package names use input version (not git version)")
        print(f"      pkg name:     {pkg['name']!r}")
        print(f"      builder name: {builder['name']!r}")
    except Exception as e:
        print(f"  ❌ Package name test failed: {e}")
        all_passed = False

    # Test with 'v' prefix (should be forgiving)
    try:
        pkg1, _ = diffusers('0.35.1')
        pkg2, _ = diffusers('v0.35.1')

        same_version = pkg1['build_args'].get('DIFFUSERS_VERSION') == pkg2['build_args'].get('DIFFUSERS_VERSION')

        status = "✅" if same_version else "❌"
        if not same_version:
            all_passed = False

        print(f"  {status} Handles 'v' prefix gracefully (forgiving)")
        print(f"      '0.35.1'  -> {pkg1['build_args'].get('DIFFUSERS_VERSION')!r}")
        print(f"      'v0.35.1' -> {pkg2['build_args'].get('DIFFUSERS_VERSION')!r}")
    except Exception as e:
        print(f"  ❌ 'v' prefix test failed: {e}")
        all_passed = False

    print()
    return all_passed


def main():
    """Run all tests."""
    print("=" * 80)
    print("DIFFUSERS CONFIG.PY INTEGRATION TEST")
    print("=" * 80)
    print()

    results = []

    # Run tests
    results.append(("Helper Functions", test_helper_functions()))
    results.append(("diffusers() Function", test_diffusers_function()))
    results.append(("Edge Cases", test_edge_cases()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n✅ All tests passed!\n")
        return 0
    else:
        print("\n❌ Some tests failed!\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())

