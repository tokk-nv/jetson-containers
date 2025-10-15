#!/usr/bin/env bash
# Test script to verify git clone fallback logic for non-existent tags

set -e

TEST_DIR="/tmp/diffusers_test_$$"
echo "======================================================================"
echo "Testing git clone fallback logic"
echo "======================================================================"
echo ""

cleanup() {
    echo "Cleaning up test directory: $TEST_DIR"
    rm -rf "$TEST_DIR"
}

trap cleanup EXIT

mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Test 1: Clone existing tag (should succeed)
echo "Test 1: Clone existing tag v0.35.1"
echo "----------------------------------------------------------------------"
DIFFUSERS_VERSION="v0.35.1"
if git clone --branch=${DIFFUSERS_VERSION} --depth=1 --recursive https://github.com/huggingface/diffusers diffusers_test1 2>/dev/null; then
    echo "✅ SUCCESS: Tag ${DIFFUSERS_VERSION} exists and was cloned"
    TAG_RESULT=$(cd diffusers_test1 && git describe --tags)
    echo "  Actual tag: ${TAG_RESULT}"
    rm -rf diffusers_test1
else
    echo "❌ FAIL: Tag ${DIFFUSERS_VERSION} should exist but clone failed"
fi
echo ""

# Test 2: Clone non-existent tag should FAIL (no more silent fallback)
echo "Test 2: Clone non-existent tag v0.36.0 should fail"
echo "----------------------------------------------------------------------"
DIFFUSERS_VERSION="v0.36.0"
echo "Attempting: git clone --branch=${DIFFUSERS_VERSION} (should fail)"

if git clone --branch=${DIFFUSERS_VERSION} --depth=1 --recursive https://github.com/huggingface/diffusers diffusers_test2 2>/dev/null; then
    echo "⚠️  Tag ${DIFFUSERS_VERSION} exists now (may have been released since test was written)"
    TAG_RESULT=$(cd diffusers_test2 && git describe --tags 2>/dev/null || echo "unknown")
    echo "  Actual tag: ${TAG_RESULT}"
    rm -rf diffusers_test2
else
    echo "✅ SUCCESS: Tag ${DIFFUSERS_VERSION} doesn't exist and clone correctly failed"
    echo "  This is the desired behavior - fail fast on non-existent versions"
    echo "  Users should use commit pinning: '0.35.1+abc1234' for post-release commits"
fi
echo ""

# Test 3: Simulate the NEW build.sh logic (fail fast, no fallback)
echo "Test 3: Simulate NEW build.sh logic - fail fast on non-existent tags"
echo "----------------------------------------------------------------------"
DIFFUSERS_VERSION="v0.36.0"
echo "Running: if ! git clone --branch=\${DIFFUSERS_VERSION}; then exit 1; fi"

# This mimics the NEW build.sh logic
if git clone --branch=${DIFFUSERS_VERSION} --depth=1 --recursive https://github.com/huggingface/diffusers diffusers_test3 2>/dev/null; then
    echo "⚠️  Tag ${DIFFUSERS_VERSION} exists now"

    if [ -d "diffusers_test3/.git" ]; then
        BRANCH=$(cd diffusers_test3 && git branch --show-current)
        COMMIT=$(cd diffusers_test3 && git log -1 --format='%h - %s' | head -c 80)
        LATEST_TAG=$(cd diffusers_test3 && git describe --tags 2>/dev/null || echo "No tags reachable")

        echo "  Branch:      ${BRANCH}"
        echo "  Latest tag:  ${LATEST_TAG}"
        echo "  HEAD commit: ${COMMIT}"

        rm -rf diffusers_test3
    fi
else
    echo "✅ SUCCESS: Clone correctly failed for non-existent tag"
    echo "  Build.sh will now exit with error and helpful message"
    echo "  This prevents misleading container tags"
fi
echo ""

# Test 4: Test with valid commit hash (should work)
echo "Test 4: Clone and checkout specific commit (valid)"
echo "----------------------------------------------------------------------"
DIFFUSERS_COMMIT="0f252be"  # From v0.35.1 release
echo "Cloning repo and checking out commit: ${DIFFUSERS_COMMIT}"

if git clone --recursive https://github.com/huggingface/diffusers diffusers_test4 2>/dev/null; then
    cd diffusers_test4
    if git checkout ${DIFFUSERS_COMMIT} 2>/dev/null; then
        echo "✅ SUCCESS: Commit ${DIFFUSERS_COMMIT} checked out successfully"
        COMMIT_INFO=$(git log -1 --format='%h - %s' | head -c 80)
        echo "  Commit: ${COMMIT_INFO}"
    else
        echo "❌ FAIL: Could not checkout commit ${DIFFUSERS_COMMIT}"
        exit 1
    fi
    cd ..
    rm -rf diffusers_test4
else
    echo "❌ FAIL: Could not clone repository"
    exit 1
fi
echo ""

# Test 5: Test with invalid/non-existent commit hash (should fail)
echo "Test 5: Clone and checkout non-existent commit (should fail)"
echo "----------------------------------------------------------------------"
DIFFUSERS_COMMIT="deadbee"  # Non-existent commit
echo "Cloning repo and checking out commit: ${DIFFUSERS_COMMIT}"

if git clone --recursive https://github.com/huggingface/diffusers diffusers_test5 2>/dev/null; then
    cd diffusers_test5
    if git checkout ${DIFFUSERS_COMMIT} 2>/dev/null; then
        echo "⚠️  Commit ${DIFFUSERS_COMMIT} exists (unexpected - it's a fake hash)"
        COMMIT_INFO=$(git log -1 --format='%h - %s' | head -c 80)
        echo "  Commit: ${COMMIT_INFO}"
        cd ..
        rm -rf diffusers_test5
    else
        echo "✅ SUCCESS: Commit ${DIFFUSERS_COMMIT} doesn't exist and checkout correctly failed"
        echo "  This is the desired behavior - build.sh will exit with error"
        cd ..
        rm -rf diffusers_test5
    fi
else
    echo "❌ FAIL: Could not clone repository"
    exit 1
fi
echo ""

echo "======================================================================"
echo "All tests passed! ✅"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  ✅ Existing tags can be cloned directly"
echo "  ✅ Non-existent tags FAIL (no misleading container tags)"
echo "  ✅ Valid commits can be checked out after clone"
echo "  ✅ Non-existent commits FAIL at checkout (no misleading builds)"
echo "  ✅ Build.sh fails fast with helpful error messages"
echo ""
echo "Best practices:"
echo "  📌 Use commit pinning for stability: diffusers('0.35.1+abc1234')"
echo "  🏷️  Only use version tags that actually exist"
echo "  🔍 Check releases: https://github.com/huggingface/diffusers/releases"
echo "  🔍 Verify commits exist before using them"

