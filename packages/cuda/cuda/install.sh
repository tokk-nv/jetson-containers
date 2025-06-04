#!/usr/bin/env bash
set -ex

ARCH=$(uname -m)
ARCH_TYPE=$ARCH
IS_SBSA=$([ -z "$(nvidia-smi --query-gpu=name --format=csv,noheader | grep nvgpu)" ] && echo 1 || echo 0)

echo "Detected architecture: ${ARCH_TYPE}"
echo "IS_SBSA: ${IS_SBSA}"

apt-get update
apt-get install -y --no-install-recommends \
        binutils \
        xz-utils
rm -rf /var/lib/apt/lists/*
apt-get clean

echo "Setting up CUDA installation"
mkdir -p /tmp/cuda
cd /tmp/cuda

if [[ -z $IS_SBSA ]]; then
    # Jetson (Tegra)
    wget $WGET_FLAGS \
        https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/arm64/cuda-${DISTRO}.pin \
        -O /etc/apt/preferences.d/cuda-repository-pin-600
else
    echo "Downloading ${CUDA_DEB} from ${CUDA_URL}"
    # Download from URL as before
    if [[ "$ARCH_TYPE" == "tegra-aarch64" ]]; then
        # Jetson (Tegra)
        wget $WGET_FLAGS \
            https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/arm64/cuda-${DISTRO}.pin \
            -O /etc/apt/preferences.d/cuda-repository-pin-600
    else
        # ARM64 SBSA (Grace)
        wget $WGET_FLAGS \
            https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/sbsa/cuda-${DISTRO}.pin \
            -O /etc/apt/preferences.d/cuda-repository-pin-600
    fi

    wget $WGET_FLAGS ${CUDA_URL}
fi

dpkg -i *.deb
cp /var/cuda-*-local/cuda-*-keyring.gpg /usr/share/keyrings/

# Tegra (Jetson)
if [[ -z $IS_SBSA ]]; then
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