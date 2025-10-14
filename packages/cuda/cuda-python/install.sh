#!/usr/bin/env bash
set -ex

if [ "$FORCE_BUILD" == "on" ]; then
	echo "Forcing build of cuda-python ${CUDA_PYTHON_VERSION}"
	exit 1
fi

uv pip install --no-cache-dir cuda-python==${CUDA_PYTHON_VERSION} && ${PIP_APPEND_CONSTRAINT} cuda-python ||
uv pip install --no-cache-dir cuda_core cuda_bindings==${CUDA_PYTHON_VERSION} && ${PIP_APPEND_CONSTRAINT} cuda_core && ${PIP_APPEND_CONSTRAINT} cuda_bindings
