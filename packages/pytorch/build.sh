#!/usr/bin/env bash
# Python builder
set -xuo pipefail
set -e

echo "Building PyTorch ${PYTORCH_BUILD_VERSION}"

echo "Installing gcc-12 due that gcc-13 is not supported by PyTorch"
UBUNTU_VERSION=$(lsb_release -r)
# if ubuntu_version is > 22.04 use gcc-12
if [[ "$UBUNTU_VERSION" == *"24.04"* ]]; then
  GCC_VERSION=12
  apt-get update
  apt-get install -y g++-$GCC_VERSION
  update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-"$GCC_VERSION" 50
  update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-"$GCC_VERSION" 50
  update-alternatives --install /usr/bin/gcov gcov /usr/bin/gcov-"$GCC_VERSION" 50
fi

# build from source

cd /opt/pytorch

# https://github.com/pytorch/pytorch/issues/138333
CPUINFO_PATCH=third_party/cpuinfo/src/arm/linux/aarch64-isa.c
sed -i 's|cpuinfo_log_error|cpuinfo_log_warning|' ${CPUINFO_PATCH}
grep 'PR_SVE_GET_VL' ${CPUINFO_PATCH} || echo "patched ${CPUINFO_PATCH}"
tail -20 ${CPUINFO_PATCH}

pip3 install -r requirements.txt
pip3 install scikit-build ninja
pip3 install 'cmake<4'

#TORCH_CXX_FLAGS="-D_GLIBCXX_USE_CXX11_ABI=0" \

export MAX_JOBS=14  # or whatever is appropriate for your system
export VERBOSE=1
export CMAKE_VERBOSE_MAKEFILE=1
export PYTORCH_BUILD_VERBOSE=1
export USE_NINJA=1  # Ensures ninja is used (usually default)
export NINJA_STATUS="[%r processes, %f/%t tasks, %es elapsed] "
export BUILD_TEST=0
export CMAKE_ARGS="-DBUILD_TEST=OFF -DBUILD_TESTS=OFF -DBUILD_CAFFE2_OPS=OFF -DUSE_GTEST=OFF"
export PYTORCH_BUILD_NUMBER=1

# Best practices for PyTorch build on Jetson Thor (Blackwell)

# 1. Print all environment variables and system info for debugging
printenv | sort
uname -a
cat /etc/os-release || true
free -h
nproc
lscpu || true

echo "/dev/shm size:"
df -h /dev/shm
if [ $(df --output=size /dev/shm | tail -1) -lt 8000000 ]; then
    echo "WARNING: /dev/shm is less than 8GB. Consider running your container with --shm-size=8g for PyTorch builds."
fi

# 2. Check CUDA arch flags for Jetson Thor (Blackwell, sm_101)
echo "TORCH_CUDA_ARCH_LIST=$TORCH_CUDA_ARCH_LIST"

# 3. Set CUB_HOME for PyTorch build
export CUB_HOME=/usr/local/cuda/include/
echo "CUB_HOME=$CUB_HOME"

# 4. Optionally enable ccache if available
if command -v ccache &> /dev/null; then
    export USE_CCACHE=1
    export CCACHE_DIR="/tmp/ccache"
    export CC="ccache /usr/bin/gcc-11"
    export CXX="ccache /usr/bin/g++-11"
    echo "Using ccache at $CCACHE_DIR"
    ccache -s
else
    export CC=/usr/bin/gcc-11
    export CXX=/usr/bin/g++-11
fi

PYTORCH_BUILD_NUMBER=1 \
USE_CUDNN=1 \
USE_CUSPARSELT=1 \
USE_CUDSS=1 \
USE_CUFILE=1 \
USE_NATIVE_ARCH=1 \
USE_DISTRIBUTED=1 \
USE_FLASH_ATTENTION=1 \
USE_MEM_EFF_ATTENTION=1 \
USE_TENSORRT=0 \
USE_BLAS="$USE_BLAS" \
BLAS="$BLAS" \
CUB_HOME=/usr/local/cuda/include/ \
python3 setup.py bdist_wheel --dist-dir /opt

python3 setup.py bdist_wheel --dist-dir /opt --verbose 2>&1 | tee /tmp/pytorch_build_$(date +%Y%m%d_%H%M%S).log

# install the compiled wheel
pip3 install /opt/torch*.whl
python3 -c 'import torch; print(f"PyTorch version: {torch.__version__}"); print(f"CUDA available:  {torch.cuda.is_available()}"); print(f"cuDNN version:   {torch.backends.cudnn.version()}"); print(torch.__config__.show());'
twine upload --verbose /opt/torch*.whl || echo "failed to upload wheel to ${TWINE_REPOSITORY_URL}"

echo "Installing gcc-13 for ubuntu 24.04 again"
if [[ "$UBUNTU_VERSION" == *"24.04"* ]]; then
  GCC_VERSION=13
  apt-get update
  apt-get install -y g++-$GCC_VERSION
  update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-"$GCC_VERSION" 50
  update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-"$GCC_VERSION" 50
  update-alternatives --install /usr/bin/gcov gcov /usr/bin/gcov-"$GCC_VERSION" 50
fi

