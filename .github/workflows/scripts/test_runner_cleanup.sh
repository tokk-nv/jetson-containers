#!/bin/bash
#
# Test Runner Cleanup Script
# Tests the cleanup commands used in sweep-build-matrix.yml to ensure they work safely
# without sudo and can handle permission issues gracefully.
#
# Usage:
#   ./test_runner_cleanup.sh [--verbose]
#

set -e

VERBOSE=false
if [[ "$1" == "--verbose" ]]; then
    VERBOSE=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_info() {
    echo -e "ℹ️  $1"
}

# Determine workspace directory
if [[ -n "${RUNNER_WORKSPACE}" ]]; then
    WORKSPACE="${RUNNER_WORKSPACE}/jetson-containers/jetson-containers"
elif [[ -d "/home/jetson/actions-runner/_work/jetson-containers/jetson-containers" ]]; then
    WORKSPACE="/home/jetson/actions-runner/_work/jetson-containers/jetson-containers"
else
    log_error "Cannot find workspace directory"
    log_info "Set RUNNER_WORKSPACE or run from standard GitHub Actions path"
    exit 1
fi

log_section "Runner Cleanup Test"
log_info "Workspace: $WORKSPACE"
log_info "Current user: $(whoami)"
log_info "Hostname: $(hostname)"

# Check if passwordless sudo is configured for workspace cleanup
SUDO_AVAILABLE=false
if sudo -n rm --version >/dev/null 2>&1; then
    # Test if we can sudo rm in the workspace without password
    TEST_DIR="/tmp/test_sudo_$$"
    mkdir -p "$TEST_DIR"
    if sudo -n rm -rf "$TEST_DIR" 2>/dev/null; then
        SUDO_AVAILABLE=true
        log_info "Passwordless sudo: ✅ Available for workspace cleanup"
    else
        log_info "Passwordless sudo: ❌ Not configured"
    fi
else
    log_info "Passwordless sudo: ❌ Not configured"
fi
echo ""

# Check if we're in the right place
if [[ ! -d "$WORKSPACE" ]]; then
    log_error "Workspace directory does not exist: $WORKSPACE"
    exit 1
fi

cd "$WORKSPACE" || exit 1
log_success "Changed to workspace directory"

# ============================================================================
# Step 1: Analyze Current State
# ============================================================================
log_section "Step 1: Analyzing Current Workspace State"

# Check for root-owned files
ROOT_FILES=$(find . -user root 2>/dev/null | wc -l)
if [[ $ROOT_FILES -gt 0 ]]; then
    log_warning "Found $ROOT_FILES root-owned files/directories"
    if $VERBOSE; then
        echo "Sample root-owned files (first 20):"
        find . -user root 2>/dev/null | head -20 | sed 's/^/  /'
    fi
else
    log_info "No root-owned files found (good!)"
fi

# Check directories we typically clean
for dir in data logs build test; do
    if [[ -d "$dir" ]]; then
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        OWNER=$(stat -c "%U" "$dir" 2>/dev/null || echo "unknown")
        PERMS=$(stat -c "%A" "$dir" 2>/dev/null || echo "unknown")
        log_info "$dir/: exists (${SIZE}, owner: ${OWNER}, perms: ${PERMS})"

        # Check for root-owned files in this directory
        if [[ -d "$dir" ]]; then
            ROOT_IN_DIR=$(find "$dir" -user root 2>/dev/null | wc -l)
            if [[ $ROOT_IN_DIR -gt 0 ]]; then
                log_warning "  └─ Contains $ROOT_IN_DIR root-owned files"
            fi
        fi
    else
        log_info "$dir/: does not exist"
    fi
done

# Check for results.json
if [[ -f "results.json" ]]; then
    SIZE=$(du -h results.json 2>/dev/null | cut -f1)
    log_info "results.json: exists (${SIZE})"
else
    log_info "results.json: does not exist"
fi

# ============================================================================
# Step 2: Test Pre-clean Commands (without sudo)
# ============================================================================
log_section "Step 2: Testing Pre-clean Commands (no sudo)"

echo "Running: rm -rf data/ logs/ build/ test/ || true"
rm -rf data/ logs/ build/ test/ || true
log_success "Command completed (may have skipped some files)"

echo "Running: rm -f results.json || true"
rm -f results.json || true
log_success "Command completed"

# Check what's left after pre-clean
ROOT_FILES_AFTER=$(find . -user root 2>/dev/null | wc -l)
if [[ $ROOT_FILES_AFTER -gt 0 ]]; then
    log_warning "Still have $ROOT_FILES_AFTER root-owned files after pre-clean"
    log_info "This is expected - git clean will handle these"
    if $VERBOSE; then
        echo "Remaining root-owned files (first 20):"
        find . -user root 2>/dev/null | head -20 | sed 's/^/  /'
    fi
else
    log_success "All files removed successfully (no root files)"
fi

# ============================================================================
# Step 2.5: Test With Sudo (if available and configured)
# ============================================================================
if $SUDO_AVAILABLE; then
    log_section "Step 2.5: Testing Pre-clean With Sudo (optional)"
    log_info "Passwordless sudo is available, testing sudo cleanup..."

    echo "Running: sudo rm -rf data/ logs/ build/ test/ || true"
    sudo rm -rf data/ logs/ build/ test/ || true
    log_success "Sudo cleanup completed"

    ROOT_FILES_AFTER_SUDO=$(find . -user root 2>/dev/null | wc -l)
    log_info "Root-owned files after sudo cleanup: $ROOT_FILES_AFTER_SUDO"

    if [[ $ROOT_FILES_AFTER_SUDO -eq 0 ]]; then
        log_success "All root-owned files removed with sudo"
    fi
fi

# ============================================================================
# Step 3: Test Git Clean (what checkout action does)
# ============================================================================
log_section "Step 3: Testing Git Clean (checkout action simulation)"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_warning "Not a git repository - skipping git clean test"
    log_info "In actual workflow, this would be after checkout"
else
    # Save current state
    log_info "Checking git status before clean..."
    if $VERBOSE; then
        git status --short
    fi

    # Test git clean (dry run first)
    log_info "Running git clean -ffdxn (dry run)..."
    WOULD_REMOVE=$(git clean -ffdxn 2>/dev/null | wc -l)
    if [[ $WOULD_REMOVE -gt 0 ]]; then
        log_info "Would remove $WOULD_REMOVE items"
        if $VERBOSE; then
            git clean -ffdxn | head -20 | sed 's/^/  /'
        fi

        # Ask before actual clean
        read -p "Run actual git clean? This will remove untracked files! (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Running git clean -ffdx..."
            if git clean -ffdx 2>&1; then
                log_success "Git clean completed successfully"
            else
                log_error "Git clean failed (exit code: $?)"
            fi
        else
            log_info "Skipped actual git clean (dry run only)"
        fi
    else
        log_success "Git clean would not remove anything (workspace is clean)"
    fi
fi

# ============================================================================
# Step 4: Final State Check
# ============================================================================
log_section "Step 4: Final State Check"

# Check for remaining root-owned files
ROOT_FILES_FINAL=$(find . -user root 2>/dev/null | wc -l)
if [[ $ROOT_FILES_FINAL -gt 0 ]]; then
    log_warning "Still have $ROOT_FILES_FINAL root-owned files"
    log_info "These would be handled by checkout action's clean: true"
    if $VERBOSE; then
        echo "Remaining root-owned files:"
        find . -user root 2>/dev/null | sed 's/^/  /'
    fi
else
    log_success "No root-owned files remaining"
fi

# Check directories
for dir in data logs build test; do
    if [[ -d "$dir" ]]; then
        log_warning "$dir/ still exists"
    else
        log_success "$dir/ removed"
    fi
done

# Check results.json
if [[ -f "results.json" ]]; then
    log_warning "results.json still exists"
else
    log_success "results.json removed"
fi

# ============================================================================
# Summary
# ============================================================================
log_section "Summary"

echo "Initial state:"
echo "  - Root-owned files: $ROOT_FILES"
echo ""
echo "After pre-clean (no sudo):"
echo "  - Root-owned files: $ROOT_FILES_AFTER"
echo "  - Reduction: $((ROOT_FILES - ROOT_FILES_AFTER))"
echo ""
echo "After git clean:"
echo "  - Root-owned files: $ROOT_FILES_FINAL"
echo "  - Total reduction: $((ROOT_FILES - ROOT_FILES_FINAL))"
echo ""

if [[ $ROOT_FILES_FINAL -eq 0 ]]; then
    log_success "Cleanup test PASSED - workspace is clean"
    echo ""
    log_info "The workflow cleanup strategy works correctly:"
    if $SUDO_AVAILABLE; then
        log_info "  1. Pre-clean removes what it can (with passwordless sudo available)"
        log_info "  2. Git clean handles any remaining files"
    else
        log_info "  1. Pre-clean removes what it can (no sudo needed)"
        log_info "  2. Git clean handles remaining files (including root-owned)"
    fi
    echo ""
    exit 0
else
    log_warning "Cleanup test PARTIAL - some root files remain"
    echo ""
    log_info "In the actual workflow:"
    log_info "  - 'clean: true' in checkout action would handle these"
    log_info "  - This is expected behavior and safe"
    echo ""
    if $SUDO_AVAILABLE; then
        log_info "You have passwordless sudo configured. You could optionally use:"
        log_info "  sudo rm -rf $WORKSPACE/data $WORKSPACE/logs"
        log_info "But the current sudo-less approach is preferred for portability."
    else
        log_info "If you want to fully clean now, you can manually run:"
        log_info "  sudo rm -rf $WORKSPACE/data $WORKSPACE/logs"
        log_info "Or configure passwordless sudo (see RUNNER_MAINTENANCE.md)"
    fi
    echo ""
    exit 0
fi

