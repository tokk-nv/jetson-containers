#!/usr/bin/env bash
set -ex
echo "Detected architecture: ${CUDA_ARCH}"

ARCH_DEB_SUFFIX="amd64"
if [[ "$CUDA_ARCH" == "aarch64" || "$CUDA_ARCH" == "tegra-aarch64" ]]; then
  ARCH_DEB_SUFFIX="arm64"
fi

BASE_URL="https://developer.download.nvidia.com/compute/cusparselt/${CUSPARSELT_VERSION}/local_installers"
GENERIC_DEB="cusparselt-local-repo-${DISTRO}-${CUSPARSELT_VERSION}_1.0-1_${ARCH_DEB_SUFFIX}.deb"
TEGRA_DEB="cusparselt-local-tegra-repo-${DISTRO}-${CUSPARSELT_VERSION}_1.0-1_arm64.deb"

# Download order:
#  - On tegra-aarch64: try tegra-specific DEB first, then fall back to generic arm64 if unavailable
#  - On aarch64 (SBSA): generic arm64 DEB
#  - On x86_64: generic amd64 DEB
if [[ "$CUDA_ARCH" == "tegra-aarch64" ]]; then
  set +e
  wget $WGET_FLAGS "${BASE_URL}/${TEGRA_DEB}"
  WGET_STATUS=$?
  set -e
  if [[ $WGET_STATUS -ne 0 ]]; then
    echo "[warn] tegra-specific package not found, falling back to generic: ${GENERIC_DEB}"
    wget $WGET_FLAGS "${BASE_URL}/${GENERIC_DEB}"
  fi
elif [[ "$CUDA_ARCH" == "aarch64" ]]; then
  wget $WGET_FLAGS "${BASE_URL}/${GENERIC_DEB}"
else
  wget $WGET_FLAGS "${BASE_URL}/${GENERIC_DEB}"
fi
dpkg -i cusparselt-local-*.deb
cp /var/cusparselt-local-*/cusparselt-*-keyring.gpg /usr/share/keyrings/
apt-get update
apt-get -y install libcusparselt0 libcusparselt-dev
rm -rf /var/lib/apt/lists/*
apt-get clean
