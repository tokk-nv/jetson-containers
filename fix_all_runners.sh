#!/bin/bash
# Script to fix sudo configuration on multiple runners at once
# Usage: ./fix_all_runners.sh [runner1] [runner2] ... or reads from RUNNERS array

set -e

# Define your runners here (or pass as arguments)
DEFAULT_RUNNERS=(
    "jat04-iso0818"
    "jao512"
    "jao202-jp621"
    # Add more runner hostnames here
)

# Use provided arguments or default list
if [ $# -gt 0 ]; then
    RUNNERS=("$@")
else
    RUNNERS=("${DEFAULT_RUNNERS[@]}")
fi

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fix_runner_sudo.sh"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ ERROR: fix_runner_sudo.sh not found at: $SCRIPT_PATH"
    exit 1
fi

echo "========================================"
echo "Multi-Runner Sudo Fix Script"
echo "========================================"
echo "Will fix ${#RUNNERS[@]} runners"
echo ""

# Summary tracking
declare -a SUCCESS_RUNNERS
declare -a FAILED_RUNNERS
declare -a UNREACHABLE_RUNNERS

for runner in "${RUNNERS[@]}"; do
    echo ""
    echo "========================================"
    echo "Processing: $runner"
    echo "========================================"

    # Test connectivity
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "jetson@$runner" "echo 'Connected'" >/dev/null 2>&1; then
        echo "❌ Cannot connect to $runner (check SSH access)"
        UNREACHABLE_RUNNERS+=("$runner")
        continue
    fi

    # Copy script to runner
    echo "Copying fix script to $runner..."
    if ! scp -q "$SCRIPT_PATH" "jetson@$runner:/tmp/fix_runner_sudo.sh"; then
        echo "❌ Failed to copy script to $runner"
        FAILED_RUNNERS+=("$runner")
        continue
    fi

    # Execute fix script
    echo "Executing fix script on $runner..."
    if ssh "jetson@$runner" "bash /tmp/fix_runner_sudo.sh"; then
        echo "✅ Successfully fixed $runner"
        SUCCESS_RUNNERS+=("$runner")
        # Clean up
        ssh "jetson@$runner" "rm -f /tmp/fix_runner_sudo.sh" 2>/dev/null || true
    else
        echo "❌ Fix script failed on $runner"
        FAILED_RUNNERS+=("$runner")
    fi
done

# Print summary
echo ""
echo ""
echo "========================================"
echo "SUMMARY"
echo "========================================"
echo "Total runners: ${#RUNNERS[@]}"
echo ""

if [ ${#SUCCESS_RUNNERS[@]} -gt 0 ]; then
    echo "✅ Successfully fixed (${#SUCCESS_RUNNERS[@]}):"
    for runner in "${SUCCESS_RUNNERS[@]}"; do
        echo "   - $runner"
    done
    echo ""
fi

if [ ${#FAILED_RUNNERS[@]} -gt 0 ]; then
    echo "❌ Failed (${#FAILED_RUNNERS[@]}):"
    for runner in "${FAILED_RUNNERS[@]}"; do
        echo "   - $runner"
    done
    echo ""
fi

if [ ${#UNREACHABLE_RUNNERS[@]} -gt 0 ]; then
    echo "⚠️  Unreachable (${#UNREACHABLE_RUNNERS[@]}):"
    for runner in "${UNREACHABLE_RUNNERS[@]}"; do
        echo "   - $runner"
    done
    echo ""
fi

if [ ${#FAILED_RUNNERS[@]} -eq 0 ] && [ ${#UNREACHABLE_RUNNERS[@]} -eq 0 ]; then
    echo "🎉 All runners successfully fixed!"
    exit 0
else
    echo "⚠️  Some runners need manual attention"
    exit 1
fi

