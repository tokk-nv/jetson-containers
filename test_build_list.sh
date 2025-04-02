#!/bin/bash

runs=10
success=0
fail=0
LOG_DIR="./logs"
LOG_FILE="$LOG_DIR/build_list_test_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

echo "Testing 'jetson-containers build --list' $runs times..." | tee -a "$LOG_FILE"
echo | tee -a "$LOG_FILE"

for i in $(seq 1 $runs); do
    echo "[$i/$runs] Running at $(date)" | tee -a "$LOG_FILE"

    if jetson-containers build --list &>> "$LOG_FILE"; then
        echo "[$i] ✅ SUCCESS" | tee -a "$LOG_FILE"
        ((success++))
    else
        echo "[$i] ❌ FAIL" | tee -a "$LOG_FILE"
        ((fail++))
    fi

    echo | tee -a "$LOG_FILE"
    sleep 1
done

echo "=== Summary ===" | tee -a "$LOG_FILE"
echo "Successes: $success"
