#!/bin/bash
# Test results summary script for GitHub Actions workflows
# Usage: ./test-results-summary.sh <package_names> <stage1> <stage2> <build_status> [failure_phase] [failure_stage] [failure_component]
# Example: ./test-results-summary.sh "vllm python" passed passed success

# Parse positional parameters
PACKAGES=""
STAGE1=""
STAGE2=""
BUILD_STATUS=""
FAILURE_PHASE=""
FAILURE_STAGE=""
FAILURE_COMPONENT=""

# Collect all arguments
args=("$@")

# First, try to identify where the status parameters start (they are predictable values)
for i in "${!args[@]}"; do
    arg="${args[$i]}"
    if [[ "$arg" == "passed" || "$arg" == "failed" || "$arg" == "success" ]]; then
        # Found the start of status parameters
        # Everything before this is packages
        PACKAGES="${args[@]:0:$i}"
        STAGE1="${args[$i]}"
        STAGE2="${args[$((i+1))]}"
        BUILD_STATUS="${args[$((i+2))]}"
        FAILURE_PHASE="${args[$((i+3))]}"
        FAILURE_STAGE="${args[$((i+4))]}"
        FAILURE_COMPONENT="${args[$((i+5))]}"
        break
    fi
done

# Fallback: if no status found, assume old single-package format
if [ -z "$STAGE1" ]; then
    PACKAGES="$1"
    STAGE1="$2"
    STAGE2="$3"
    BUILD_STATUS="$4"
    FAILURE_PHASE="$5"
    FAILURE_STAGE="$6"
    FAILURE_COMPONENT="$7"
fi

# Count packages
PACKAGE_COUNT=$(echo $PACKAGES | wc -w)

echo "=== Build Test Results Summary ==="
if [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
    echo "PR from: $GITHUB_HEAD_REF_REPO_FULL_NAME"
    echo "Branch: $GITHUB_HEAD_REF"
    echo "Commit: $GITHUB_SHA"
else
    echo "Manual run from: $GITHUB_REPOSITORY"
    echo "Branch: $GITHUB_REF_NAME"
    echo "Commit: $GITHUB_SHA"
fi
echo ""
echo "Hardware: Jetson Orin"
echo "Package Count: $PACKAGE_COUNT"
echo "Packages: $PACKAGES"
echo "Stage 1 (Package Listing): $STAGE1"
echo "Stage 2 (Package Build): $STAGE2"
echo "Overall Status: $BUILD_STATUS"

if [ "$BUILD_STATUS" = "success" ]; then
    if [ $PACKAGE_COUNT -eq 1 ]; then
        echo "🎉 RESULT: $PACKAGES package SUCCESS on Jetson Orin"
    else
        echo "🎉 RESULT: $PACKAGE_COUNT packages SUCCESS on Jetson Orin"
        echo "Successfully built packages:"
        for pkg in $PACKAGES; do
            echo "  ✅ $pkg"
        done
    fi
    exit 0
else
    if [ $PACKAGE_COUNT -eq 1 ]; then
        echo "💥 RESULT: $PACKAGES package FAILED on Jetson Orin"
    else
        echo "💥 RESULT: Package build FAILED on Jetson Orin ($PACKAGE_COUNT packages attempted)"
        echo "Attempted packages:"
        for pkg in $PACKAGES; do
            echo "  ❌ $pkg"
        done
    fi
    echo "Failure Phase: $FAILURE_PHASE"
    echo "Failure Stage: $FAILURE_STAGE"
    echo "Failure Component: $FAILURE_COMPONENT"
    echo ""
    echo "❌ Package Test (Orin) - FAILED in STAGE: $FAILURE_PHASE > $FAILURE_STAGE > $FAILURE_COMPONENT"
    echo "Check build logs above for detailed failure information"
    exit 1
fi
