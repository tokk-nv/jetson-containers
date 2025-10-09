#!/bin/bash
# Fix script for GitHub Actions self-hosted runner sudo configuration
# This fixes the typo in /etc/sudoers.d/jetson-actions that prevents
# passwordless sudo for workspace cleanup operations

set -e

SUDOERS_FILE="/etc/sudoers.d/jetson-actions"
BACKUP_FILE="/etc/sudoers.d/jetson-actions.backup.$(date +%Y%m%d-%H%M%S)"

echo "========================================"
echo "GitHub Actions Runner Sudo Fix Script"
echo "========================================"
echo "Runner: $(hostname)"
echo "User: $(whoami)"
echo ""

# Function to check if sudoers file has the typo
check_typo() {
    if [ ! -f "$SUDOERS_FILE" ]; then
        echo "⚠️  WARNING: $SUDOERS_FILE does not exist"
        return 2
    fi
    
    if sudo cat "$SUDOERS_FILE" 2>/dev/null | grep -q '> home'; then
        return 0  # Has typo
    else
        return 1  # No typo
    fi
}

# Function to test sudo permissions
test_sudo() {
    echo "Testing sudo permissions..."
    sudo -k  # Clear sudo cache
    
    # Test rm
    if sudo -n rm -rf /tmp/test_sudo_$$ 2>/dev/null; then
        echo "  ✅ sudo rm works without password"
        rm_works=1
    else
        echo "  ❌ sudo rm requires password"
        rm_works=0
    fi
    
    # Test chmod
    mkdir -p /tmp/test_chmod_$$
    if sudo -n chmod -R 755 /tmp/test_chmod_$$ 2>/dev/null; then
        echo "  ✅ sudo chmod works without password"
        chmod_works=1
        rm -rf /tmp/test_chmod_$$
    else
        echo "  ❌ sudo chmod requires password"
        chmod_works=0
    fi
    
    if [ $rm_works -eq 1 ] && [ $chmod_works -eq 1 ]; then
        return 0
    else
        return 1
    fi
}

# Step 1: Check current status
echo "Step 1: Checking current configuration"
echo "---------------------------------------"

if [ ! -f "$SUDOERS_FILE" ]; then
    echo "❌ CRITICAL: $SUDOERS_FILE does not exist!"
    echo ""
    echo "This runner has never been configured for GitHub Actions."
    echo "Creating new configuration..."
    CREATE_NEW=1
else
    echo "Current sudoers file content:"
    sudo cat "$SUDOERS_FILE" | sed 's/^/  /'
    echo ""
    CREATE_NEW=0
fi

# Step 2: Detect typo
echo "Step 2: Checking for typo"
echo "-------------------------"

if check_typo; then
    echo "❌ TYPO DETECTED: Found '> home' in sudoers config"
    echo "   This breaks chmod/chown permissions!"
    HAS_TYPO=1
elif [ $? -eq 2 ]; then
    echo "⚠️  File doesn't exist, will create new one"
    HAS_TYPO=0
else
    echo "✅ No typo found in sudoers file"
    HAS_TYPO=0
fi
echo ""

# Step 3: Test current permissions
if [ $CREATE_NEW -eq 0 ]; then
    echo "Step 3: Testing current sudo permissions"
    echo "----------------------------------------"
    if test_sudo; then
        echo "✅ Sudo permissions are working correctly"
        NEEDS_FIX=0
    else
        echo "❌ Sudo permissions are NOT working"
        NEEDS_FIX=1
    fi
    echo ""
else
    NEEDS_FIX=1
fi

# Step 4: Apply fix if needed
if [ $HAS_TYPO -eq 1 ] || [ $NEEDS_FIX -eq 1 ] || [ $CREATE_NEW -eq 1 ]; then
    echo "Step 4: Applying fix"
    echo "--------------------"
    
    # Backup existing file
    if [ -f "$SUDOERS_FILE" ]; then
        echo "Backing up current file to: $BACKUP_FILE"
        sudo cp "$SUDOERS_FILE" "$BACKUP_FILE"
    fi
    
    # Write corrected configuration
    echo "Writing corrected configuration..."
    CORRECT_CONFIG="$USER ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/ln, /bin/rm -rf /home/jetson/actions-runner/_work/*, /bin/chmod -R /home/jetson/actions-runner/_work/*, /bin/chown -R /home/jetson/actions-runner/_work/*"
    
    echo "$CORRECT_CONFIG" | sudo tee "$SUDOERS_FILE" >/dev/null
    sudo chmod 0440 "$SUDOERS_FILE"
    
    echo "✅ Configuration written"
    echo ""
    
    # Verify syntax
    echo "Verifying sudoers syntax..."
    if sudo visudo -c -f "$SUDOERS_FILE" 2>&1 | grep -q "parsed OK"; then
        echo "✅ Sudoers syntax is valid"
    else
        echo "❌ ERROR: Sudoers syntax validation failed!"
        echo "Restoring backup..."
        if [ -f "$BACKUP_FILE" ]; then
            sudo cp "$BACKUP_FILE" "$SUDOERS_FILE"
        fi
        exit 1
    fi
    echo ""
else
    echo "Step 4: No fix needed"
    echo "--------------------"
    echo "✅ Configuration is already correct"
    echo ""
fi

# Step 5: Final verification
echo "Step 5: Final verification"
echo "--------------------------"

echo "New sudoers file content:"
sudo cat "$SUDOERS_FILE" | sed 's/^/  /'
echo ""

# Check for typo again
if check_typo; then
    echo "❌ ERROR: Typo still present after fix!"
    exit 1
else
    echo "✅ No typo in configuration"
fi

# Test permissions
echo ""
if test_sudo; then
    echo ""
    echo "✅ All sudo permissions verified working"
else
    echo ""
    echo "❌ ERROR: Sudo permissions still not working!"
    echo "   Manual intervention may be required"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ SUCCESS: Runner is now properly configured"
echo "========================================"
echo ""
echo "The runner can now execute these commands without password:"
echo "  - sudo rm -rf /home/jetson/actions-runner/_work/*"
echo "  - sudo chmod -R /home/jetson/actions-runner/_work/*"
echo "  - sudo chown -R /home/jetson/actions-runner/_work/*"
echo "  - sudo apt-get ..."
echo "  - sudo ln ..."
echo ""
if [ -f "$BACKUP_FILE" ]; then
    echo "Backup of old config: $BACKUP_FILE"
fi
echo ""

