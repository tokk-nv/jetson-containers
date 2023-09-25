#---
# name: mmcv
# group: vit
# depends: [pytorch]
# requires: '>=34.1.0'
# docs: docs.md
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt

RUN git clone https://github.com/open-mmlab/mmcv.git && \
    cd mmcv && \
    pip3 install -r requirements/optional.txt && \
    nvcc --version && \
    gcc --version && \
    export SYNC_BN_PY_FILE=${PWD}/mmcv/ops/sync_bn.py && \
    ls -lh ${SYNC_BN_PY_FILE} && \
    sed "s|^import torch.distributed as dist|# import torch.distributed as dist|" -i ${SYNC_BN_PY_FILE} && \
    MMCV_WITH_OPS=1 pip3 install . -v && \
    python3 .dev_scripts/check_installation.py


