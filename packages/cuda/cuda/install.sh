#!/usr/bin/env bash
set -ex

ARCH=$(uname -m)
ARCH_TYPE=$ARCH
# Use the IS_SBSA build argument if provided, otherwise try to detect
if [[ -n "${IS_SBSA:-}" ]]; then
    IS_SBSA=${IS_SBSA}
else
    # Fallback detection (this won't work in containers without nvidia-smi)
    IS_SBSA=$([ -z "$(nvidia-smi --query-gpu=name --format=csv,noheader | grep nvgpu 2>/dev/null || echo '')" ] && echo 1 || echo 0)
fi

echo "Detected architecture: ${ARCH_TYPE}"
echo "IS_SBSA: ${IS_SBSA}"

apt-get update
apt-get install -y --no-install-recommends \
        binutils \
        xz-utils \
        sshpass \
        openssh-client
rm -rf /var/lib/apt/lists/*
apt-get clean

echo "Setting up CUDA installation"
mkdir -p /tmp/cuda
cd /tmp/cuda

# Set up repository pin based on architecture (needed for both local and remote deb files)
if [[ "$IS_SBSA" == "1" || "$IS_SBSA" == "true" || "$IS_SBSA" == "True" ]]; then
    # ARM64 SBSA (Grace)
    wget $WGET_FLAGS \
        https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/sbsa/cuda-${DISTRO}.pin \
        -O /etc/apt/preferences.d/cuda-repository-pin-600
else
    # Jetson (Tegra) ( <= r36.x)
    wget $WGET_FLAGS \
        https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/arm64/cuda-${DISTRO}.pin \
        -O /etc/apt/preferences.d/cuda-repository-pin-600
fi

# Debug: Print environment variables
echo "DEBUG: USE_LOCAL_DEB='${USE_LOCAL_DEB:-}'"
echo "DEBUG: CUDA_LOCAL_DEB='${CUDA_LOCAL_DEB:-}'"
echo "DEBUG: CUDA_URL='${CUDA_URL:-}'"
echo "DEBUG: USE_SCP_DOWNLOAD='${USE_SCP_DOWNLOAD:-}'"
echo "DEBUG: CUDA_SCP_PATH='${CUDA_SCP_PATH:-}'"

# Check if we're using SCP download
if [[ "${USE_SCP_DOWNLOAD:-false}" == "true" && -n "${CUDA_SCP_PATH:-}" ]]; then
    echo "Using SCP to download CUDA deb file from: ${CUDA_SCP_PATH}"
    # Extract filename from SCP path
    filename=$(basename "${CUDA_SCP_PATH}")
    # Use sshpass for password authentication if needed
    # Format: user@host:path or user:pass@host:path
    if [[ "${CUDA_SCP_PATH}" == *"@"* ]]; then
        # Parse user, password, host, and path
        if [[ "${CUDA_SCP_PATH}" == *":"*"@"* ]]; then
            # Format: user:pass@host:path
            user_pass="${CUDA_SCP_PATH%%@*}"
            host_path="${CUDA_SCP_PATH#*@}"
            user="${user_pass%%:*}"
            password="${user_pass#*:}"
            host="${host_path%%:*}"
            remote_path="${host_path#*:}"
            echo "SCP with password: user=${user}, host=${host}, path=${remote_path}"
            sshpass -p "${password}" scp -o StrictHostKeyChecking=no "${user}@${host}:${remote_path}" "/tmp/cuda/${filename}"
        else
            # Format: user@host:path
            user="${CUDA_SCP_PATH%%@*}"
            host_path="${CUDA_SCP_PATH#*@}"
            host="${host_path%%:*}"
            remote_path="${host_path#*:}"
            echo "SCP without password: user=${user}, host=${host}, path=${remote_path}"
            scp -o StrictHostKeyChecking=no "${user}@${host}:${remote_path}" "/tmp/cuda/${filename}"
        fi
    else
        echo "Invalid SCP path format: ${CUDA_SCP_PATH}"
        exit 1
    fi
# Check if we're using a local deb file
elif [[ "${USE_LOCAL_DEB:-false}" == "true" && -n "${CUDA_LOCAL_DEB:-}" ]]; then
    echo "Using local CUDA deb file: ${CUDA_LOCAL_DEB}"
    # Copy the local deb file to the container
    cp "${CUDA_LOCAL_DEB}" /tmp/cuda/
else
    echo "Downloading ${CUDA_DEB} from ${CUDA_URL}"
    wget $WGET_FLAGS ${CUDA_URL}
fi

dpkg -i *.deb
cp /var/cuda-*-local/cuda-*-keyring.gpg /usr/share/keyrings/

# Tegra (Jetson) - only needed for Tegra systems, not SBSA
if [[ "$IS_SBSA" != "1" && "$IS_SBSA" != "true" && "$IS_SBSA" != "True" ]]; then
    ar x /var/cuda-tegra-repo-ubuntu*-local/cuda-compat-*.deb
    tar xvf data.tar.xz -C /
fi

apt-get update
apt-get install -y --no-install-recommends ${CUDA_PACKAGES}
# ARM64 SBSA (Grace) NVIDIA Performance Libraries (NVPL)
# NVPL allows you to easily port HPC applications to NVIDIA Grace™ CPU platforms to achieve industry-leading performance and efficiency.
if [[ "$ARCH_TYPE" == "aarch64" ]]; then
    wget $WGET_FLAGS https://developer.download.nvidia.com/compute/nvpl/25.5/local_installers/nvpl-local-repo-ubuntu2404-25.5_1.0-1_arm64.deb
    dpkg -i nvpl-*_arm64.deb
    cp /var/nvpl-*/nvpl-*-keyring.gpg /usr/share/keyrings/
    apt-get update
    apt-get -y install nvpl
fi
rm -rf /var/lib/apt/lists/*
apt-get clean

dpkg --list | grep cuda
dpkg -P ${CUDA_DEB}
rm -rf /tmp/cuda