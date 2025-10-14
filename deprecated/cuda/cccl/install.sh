#!/usr/bin/env bash
set -ex

if [ "$FORCE_BUILD" == "on" ]; then
	echo "Forcing build of cuda_cccl ${CCCL_VERSION}"
	exit 1
fi

pip3 install cuda-cccl==${CCCL_VERSION} || \
pip3 install cuda-cccl==${CCCL_VERSION_SPEC}

pip3 show cudnn && python3 -c 'import cudnn'

${PIP_APPEND_CONSTRAINT} cuda-cccl