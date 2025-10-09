#!/bin/bash
# Quick diagnostic script to check runner sudo configuration status
# Safe to run - makes NO changes, only reports status

SUDOERS_FILE="/etc/sudoers.d/jetson-actions"

echo "========================================"
echo "Runner Sudo Configuration Check"
echo "========================================"
echo "Runner: $(hostname)"
echo "User: $(whoami)"
echo "Date: $(date)"
echo ""

# Check 1: File exists
echo "Check 1: Sudoers file exists"
echo "----------------------------"
if [ -f "$SUDOERS_FILE" ]; then
    echo "✅ File exists: $SUDOERS_FILE"
else
    echo "❌ File missing: $SUDOERS_FILE"
    echo ""
    echo "VERDICT: ❌ RUNNER NOT CONFIGURED"
    exit 1
fi
echo ""

# Check 2: File content
echo "Check 2: Sudoers file content"
echo "-----------------------------"
sudo cat "$SUDOERS_FILE" | sed 's/^/  /'
echo ""

# Check 3: Typo detection
echo "Check 3: Typo detection"
echo "-----------------------"
if sudo cat "$SUDOERS_FILE" 2>/dev/null | grep -q '> home'; then
    echo "❌ TYPO FOUND: Contains '> home' (should be '/home')"
    echo "   This breaks chmod and chown permissions!"
    HAS_TYPO=1
else
    echo "✅ No typo detected"
    HAS_TYPO=0
fi
echo ""

# Check 4: Permission tests
echo "Check 4: Testing actual permissions"
echo "------------------------------------"
sudo -k  # Clear cache

# Test rm
echo -n "  rm test: "
if sudo -n rm -rf /tmp/test_sudo_$$ 2>/dev/null; then
    echo "✅ PASS"
    RM_OK=1
else
    echo "❌ FAIL (requires password)"
    RM_OK=0
fi

# Test chmod
echo -n "  chmod test: "
mkdir -p /tmp/test_chmod_$$
if sudo -n chmod -R 755 /tmp/test_chmod_$$ 2>/dev/null; then
    echo "✅ PASS"
    CHMOD_OK=1
    rm -rf /tmp/test_chmod_$$
else
    echo "❌ FAIL (requires password)"
    CHMOD_OK=0
fi

# Test chown
echo -n "  chown test: "
mkdir -p /tmp/test_chown_$$
if sudo -n chown -R $USER:$USER /tmp/test_chown_$$ 2>/dev/null; then
    echo "✅ PASS"
    CHOWN_OK=1
    rm -rf /tmp/test_chown_$$
else
    echo "❌ FAIL (requires password)"
    CHOWN_OK=0
fi

echo ""

# Final verdict
echo "========================================"
echo "VERDICT"
echo "========================================"

if [ $HAS_TYPO -eq 0 ] && [ $RM_OK -eq 1 ] && [ $CHMOD_OK -eq 1 ] && [ $CHOWN_OK -eq 1 ]; then
    echo "✅ RUNNER IS PROPERLY CONFIGURED"
    echo ""
    echo "This runner can execute GitHub Actions workflows"
    echo "with sudo cleanup steps without password prompts."
    exit 0
elif [ $HAS_TYPO -eq 1 ]; then
    echo "❌ RUNNER HAS TYPO IN CONFIGURATION"
    echo ""
    echo "The sudoers file contains a typo that breaks chmod/chown."
    echo "Run fix_runner_sudo.sh to fix this issue."
    exit 1
elif [ $RM_OK -eq 0 ] || [ $CHMOD_OK -eq 0 ] || [ $CHOWN_OK -eq 0 ]; then
    echo "❌ RUNNER CONFIGURATION NOT WORKING"
    echo ""
    echo "The sudoers file exists but permissions don't work."
    echo "Run fix_runner_sudo.sh to fix this issue."
    exit 1
else
    echo "⚠️  UNKNOWN STATE"
    exit 2
fi

