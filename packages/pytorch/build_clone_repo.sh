#!/usr/bin/env bash
# Python builder
set -xuo pipefail

# Clone from GitHub repository
echo "Cloning PyTorch ${PYTORCH_BUILD_VERSION}"

RETRIES=5
SLEEP=10

# Retry function
retry() {
    local n=0
    until [ "$n" -ge "$RETRIES" ]; do
        "$@" && break
        n=$((n+1))
        echo "Command failed. Attempt $n/$RETRIES. Retrying in $SLEEP seconds..."
        sleep $SLEEP
    done
    if [ "$n" -eq "$RETRIES" ]; then
        echo "Command failed after $RETRIES attempts."
        exit 1
    fi
}

# Clone PyTorch repo with retries
retry bash -c \
    'rm -rf /opt/pytorch && \
    git clone --branch "v${PYTORCH_BUILD_VERSION}" --depth=1 --recursive https://github.com/pytorch/pytorch /opt/pytorch'

cd /opt/pytorch

# Retry submodule update
retry git submodule update --init --recursive