#!/bin/bash

# Script to create a test branch for GitHub Actions testing
# Usage: ./scripts/create-gha-test-branch.sh [branch-suffix]

set -e

# Get branch suffix from argument or generate one
if [ $# -eq 0 ]; then
    # Generate a random 3-digit number
    BRANCH_SUFFIX=$(shuf -i 100-999 -n 1)
else
    BRANCH_SUFFIX="$1"
fi

BRANCH_NAME="dev-gha-test-${BRANCH_SUFFIX}"
TEST_FILE="gha-test-${BRANCH_SUFFIX}"

echo "Creating GitHub Actions test branch: ${BRANCH_NAME}"

# Switch to dev branch and pull latest
echo "Switching to dev branch..."
git checkout dev
git pull origin dev

# Create and switch to new test branch
echo "Creating test branch: ${BRANCH_NAME}"
git checkout -b "${BRANCH_NAME}"

# Create a small change to trigger workflows
echo "Creating test file: ${TEST_FILE}"
touch "${TEST_FILE}"

# Add, commit and push
echo "Committing changes..."
git add .
git commit -m "Small change to trigger GitHub Actions workflows"

echo "Pushing to remote..."
git push --set-upstream tokknv "${BRANCH_NAME}"

# Show status
echo "Current status:"
git status

# Generate PR URL
echo ""
echo "PR URL:"
echo "https://github.com/chitoku/jetson-containers/compare/dev...tokk-nv:jetson-containers:${BRANCH_NAME}"

echo ""
echo "Test branch created successfully: ${BRANCH_NAME}"
echo "You can now create a PR using the URL above."
