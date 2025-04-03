#!/bin/bash

LSB_RELEASE=24.04
LOG_DIR="./logs/test/"
REPEAT=1  # default number of times to repeat each combination
TARGET="lerobot"  # default target

# Allow override with --repeat=N
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --repeat=*) REPEAT="${1#*=}"; shift ;;
        --target=*) TARGET="${1#*=}"; shift ;;
        *) echo "Unknown parameter: $1" && exit 1 ;;
    esac
done

SUMMARY_FILE="${LOG_DIR}/test_${TARGET}_$(date +%Y%m%d_%H%M%S).txt"

mkdir -p "$LOG_DIR"

BUILD_NETWORKS=("host" "bridge")
TEST_NETWORKS=("host" "bridge")

SUMMARY=()
TOTAL_RUNS=0
PASS_COUNT=0
FAIL_COUNT=0

for build_net in "${BUILD_NETWORKS[@]}"; do
    for test_net in "${TEST_NETWORKS[@]}"; do
        for ((i=1; i<=REPEAT; i++)); do
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            COMBO="build=$build_net test=$test_net run=$i"
            LOG_FILE="$LOG_DIR/${TARGET}_${build_net}_${test_net}_${TIMESTAMP}_run${i}.log"

            echo "=========================================" | tee -a "$LOG_FILE"
            echo "Running: $COMBO" | tee -a "$LOG_FILE"
            echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
            echo "=========================================" | tee -a "$LOG_FILE"

            LSB_RELEASE=$LSB_RELEASE \
            jetson-containers build \
                --build-network="$build_net" \
                --test-network="$test_net" \
                "$TARGET" 2>&1 | ts '[%H:%M:%S]' >> "$LOG_FILE"

            BUILD_EXIT_CODE=${PIPESTATUS[0]}  # Capture actual return code
            ((TOTAL_RUNS++))

            if [ $BUILD_EXIT_CODE  -eq 0 ]; then
                RESULT="✅ PASS"
                ((PASS_COUNT++))
            else
                RESULT="❌ FAIL"
                ((FAIL_COUNT++))
            fi

            SUMMARY+=("$COMBO -> $RESULT")
            echo "$COMBO -> $RESULT" >> "$SUMMARY_FILE"
            echo -e "\n$COMBO -> $RESULT\n" | tee -a "$LOG_FILE"

            # Clean up
            echo "Cleaning up Docker system..."
            docker system prune -f -a > /dev/null 2>&1

        done
    done
done

# Summary report
{
  echo ""
  echo "==========================="
  echo "Total runs:   $TOTAL_RUNS"
  echo "✅ Passes:     $PASS_COUNT"
  echo "❌ Failures:   $FAIL_COUNT"
  echo "==========================="
  echo ""
} | tee -a "$SUMMARY_FILE"