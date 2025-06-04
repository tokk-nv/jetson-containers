#!/usr/bin/env bash
set -ex

: "${CUDA_SAMPLES_ROOT:=/opt/cuda-samples}"

cd $CUDA_SAMPLES_ROOT/bin/$(uname -m)/linux/release

# Get CUDA version
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep -o ".*release [0-9]*\.[0-9]*" | grep -o "[0-9]*\.[0-9]*")
else
    CUDA_VERSION=""
fi

./deviceQuery

# Only run bandwidthTest if CUDA version is less than 12.9
if [[ -z "$CUDA_VERSION" ]] || awk 'BEGIN{exit ARGV[1]>=12.9?1:0}' "$CUDA_VERSION"; then
    ./bandwidthTest
else
    echo "Skipping ./bandwidthTest for CUDA version >= 12.9 ($CUDA_VERSION)"
fi

# NVBandwidth utility is to replace the CUDA Sample's bandwidthTest.
# https://github.com/nvidia/nvbandwidth
/opt/nvbandwidth/nvbandwidth -j

./vectorAdd
./matrixMul