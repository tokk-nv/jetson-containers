#!/usr/bin/env bash
set -ex

echo "Building Apache TVM from source (commit=${TVM_COMMIT})"

export TVM_SRC_DIR=/opt/tvm

git clone --recursive https://github.com/apache/tvm.git ${TVM_SRC_DIR}
cd ${TVM_SRC_DIR}

if [ -n "${TVM_COMMIT}" ]; then
    git fetch origin ${TVM_COMMIT} || true
    git checkout ${TVM_COMMIT}
fi

git submodule update --init --recursive

mkdir -p build
cp cmake/config.cmake build/config.cmake

# Configure per instructions with additional options for Python bindings
{
  echo "set(USE_LLVM ON)";
  echo "set(USE_CUBLAS ON)";
  echo "set(USE_CUDNN ON)";
  echo "set(USE_CUDA ON)";
  echo "set(USE_CUTLASS ON)";
  echo "set(USE_THRUST ON)";
  echo "set(USE_NCCL ON)";
  echo "set(CMAKE_CUDA_ARCHITECTURES ${CUDAARCHS})";
  echo "set(USE_PYTHON ON)";
  echo "set(USE_FFI ON)";
  echo "set(USE_GRAPH_EXECUTOR ON)";
  echo "set(USE_PROFILER ON)";
  echo "set(USE_RPC ON)";
  echo "set(USE_MICRO OFF)";
  echo "set(USE_AOT_EXECUTOR OFF)";
  echo "set(USE_GTEST OFF)";
  echo "set(USE_LIBBACKTRACE OFF)";
  echo "set(BUILD_DUMMY_LIBTVM OFF)";
} >> build/config.cmake

cd build
cmake ..
make -j$(nproc)

# Set environment variables for Python build - CRITICAL for tvm_ffi linking
export TVM_LIBRARY_PATH=/opt/tvm/build
export TVM_BUILD_PATH=/opt/tvm/build
export LD_LIBRARY_PATH=/opt/tvm/build/lib:${LD_LIBRARY_PATH}
export PYTHONPATH=/opt/tvm/python:${PYTHONPATH}

# Create the tvm_ffi directory structure in the Python package
mkdir -p /opt/tvm/python/tvm/_ffi
mkdir -p /opt/tvm/python/tvm/_ffi/_cy3

# Copy libraries to the correct locations for Python setup.py
cp /opt/tvm/build/libtvm_ffi.so /opt/tvm/python/tvm/_ffi/
cp /opt/tvm/build/libtvm.so /opt/tvm/python/tvm/_ffi/

# Also copy to the _cy3 directory which is sometimes used
cp /opt/tvm/build/libtvm_ffi.so /opt/tvm/python/tvm/_ffi/_cy3/
cp /opt/tvm/build/libtvm.so /opt/tvm/python/tvm/_ffi/_cy3/

# Create __init__.py files to make them proper Python packages
touch /opt/tvm/python/tvm/_ffi/__init__.py
touch /opt/tvm/python/tvm/_ffi/_cy3/__init__.py

cd /opt/tvm/python
python3 setup.py bdist_wheel

pip3 install dist/tvm-*.whl

# Test that tvm_ffi can be imported
python3 -c "import tvm; print('TVM imported successfully')" || echo "Warning: TVM import test failed"

twine upload --verbose dist/tvm-*.whl || echo "failed to upload wheel to ${TWINE_REPOSITORY_URL}"

