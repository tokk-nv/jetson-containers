#---
# name: pytorch
# alias: torch
# group: pytorch
# config: config.py
# depends: [cuda, cudnn, numpy, onnx]
# test: [test.sh, test.py]
# docs: |
#  Containers for PyTorch with CUDA support.
#  Note that the [`l4t-pytorch`](/packages/l4t/l4t-pytorch) containers also include PyTorch, `torchvision`, and `torchaudio`.
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# set the CUDA architectures that PyTorch extensions get built for
# set the torch hub model cache directory to mounted /data volume
ARG TORCH_CUDA_ARCH_LIST \
    TORCH_VERSION \
    PYTORCH_BUILD_VERSION \
    PIP_EXTRA_INDEX_URL \
    USE_NCCL=1 \
    USE_GLOO=1 \
    USE_MPI=0 \
    USE_FBGEMM=0 \
    USE_NNPACK=1 \
    USE_XNNPACK=1 \
    USE_PYTORCH_QNNPACK=1 \
    FORCE_BUILD=off

ENV TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCH_LIST} \
    PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL} \
    TORCH_HOME=/data/models/torch


# attempt to install from pip, and fall back to building it
#COPY install.sh build.sh build_clone_repo.sh /tmp/pytorch/
#RUN /tmp/pytorch/install.sh || bash -c "/tmp/pytorch/build_clone_repo.sh && /tmp/pytorch/build.sh"

### Skip trying to install for now, as we know we don't have pre-built wheel yet.
COPY build_clone_repo.sh /tmp/pytorch/
RUN /tmp/pytorch/build_clone_repo.sh

# 1. Install GCC-11 and G++-11
RUN apt-get update && \
    apt-get install -y gcc-11 g++-11

# 1b. Install OpenBLAS
RUN apt-get update && \
    apt-get install -y libopenblas-dev liblapack-dev

# 2. Set environment variables so all subsequent RUN commands use GCC-11
ENV CC=gcc-11
ENV CXX=g++-11
COPY build.sh /tmp/pytorch/
RUN /tmp/pytorch/build.sh
RUN ls -lh /opt/torch*.whl

# 3. Install pip and setuptools
RUN apt-get update && \
    apt-get install -y python3-pip python3-setuptools

# 4. Install PyTorch dependencies
RUN pip3 install setuptools wheel

# 5. Install PyTorch
RUN pip3 install /opt/torch*.whl

# 6. Verify PyTorch installation
# RUN python3 -c 'import torch; print(f"PyTorch version: {torch.__version__}"); print(f"CUDA available:  {torch.cuda.is_available()}"); print(f"cuDNN version:   {torch.backends.cudnn.version()}"); print(torch.__config__.show());'
