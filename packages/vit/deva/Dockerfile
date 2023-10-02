#---
# name: deva
# group: vit
# depends: [pytorch, torchvision, onnxruntime, onnx]
# requires: '>=34.1.0'
# docs: docs.md
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt

RUN git clone https://github.com/cheind/py-thin-plate-spline && \
    cd py-thin-plate-spline && \
    sed "s|^numpy.*||" -i requirements.txt && \
    sed "s|^torch.*||" -i requirements.txt && \
    pip3 install .

RUN git clone https://github.com/hkchengrex/Tracking-Anything-with-DEVA.git && \
    cd Tracking-Anything-with-DEVA && \
    sed "s|^.*thinplate.*||" -i pyproject.toml && \
    sed "s|^.*numpy.*||" -i pyproject.toml && \
    sed "s|^.*Pillow.*||" -i pyproject.toml && \
    sed "s|^.*scipy.*|  'scipy', |" -i pyproject.toml && \
    cat pyproject.toml && \
    pip3 install .

RUN git https://github.com/hkchengrex/Grounded-Segment-Anything && \
    cd Grounded-Segment-Anything && \
    export AM_I_DOCKER=False && \
    export BUILD_WITH_CUDA=True && \
    export CUDA_HOME=/usr/local/cuda-11.4/ && \
    python3 -m pip install -e segment_anything && \
    python3 -m pip install -e GroundingDINO && \
    pip3 install --upgrade diffusers[torch] && \
    git submodule update --init --recursive && \
    cd grounded-sam-osx && bash install.sh && \
    cd ../Tag2Text && pip install -r requirements.txt && \
    pip install opencv-python pycocotools matplotlib ipykernel
