#---
# name: stable-diffusion-trt
# group: diffusion
# depends: [pytorch, torchvision, onnx, onnxruntime, transformers]
# requires: '>=34.1.0'
# docs: docs.md
# notes: disabled on JetPack 4
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt

# Clone the TensorRT OSS repository
RUN git clone https://github.com/NVIDIA/TensorRT -b release/8.5 --single-branch && \
	cd TensorRT && \
	git submodule update --init --recursive

ENV TRT_OSSPATH=/opt/TensorRT
ENV LIBRARY_PATH=$LIBRARY_PATH:/usr/local/cuda-11.4/targets/aarch64-linux/lib/
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/.local/cuda/lib64
ENV CPLUS_INCLUDE_PATH=$CPLUS_INCLUDE_PATH:$HOME/.local/cuda/include
RUN echo "### LIBRARY_PATH       : ${LIBRARY_PATH}" && \
    echo "### LD_LIBRARY_PATH    : ${LD_LIBRARY_PATH}" && \
	echo "### CPLUS_INCLUDE_PATH : ${CPLUS_INCLUDE_PATH}"

# Build TensorRT plugins library
RUN cd ${TRT_OSSPATH} && \
	mkdir -p build && cd build && \
	pwd && \
	cmake .. \
		-DCMAKE_TOOLCHAIN_FILE=$TRT_OSSPATH/cmake/toolchains/cmake_aarch64.toolchain \
		-DCUDA_VERSION=11.4 \
		-DCUBLAS_LIB=/usr/local/cuda-11.4/targets/aarch64-linux/lib/stubs/libcublas.so \
		-DCUBLASLT_LIB=/usr/local/cuda-11.4/targets/aarch64-linux/lib/stubs/libcublasLt.so \
		-DCUDNN_LIB=/usr/lib/aarch64-linux-gnu/libcudnn.so \
		-DTRT_LIB_DIR=/usr/lib/aarch64-linux-gnu/ \
		-DTRT_LIBPATH=/usr/lib/aarch64-linux-gnu/ \
		-DTRT_OUT_DIR=$PWD/out \
		-DGPU_ARCHS="87" && \
	cd plugin && \
	sed 's|/usr/aarch64-linux-gnu/lib/librt.so|/usr/lib/aarch64-linux-gnu/librt.so|' -i ${TRT_OSSPATH}/cmake/toolchains/cmake_aarch64.toolchain && \
	make -j$(nproc) && \
	export PLUGIN_LIBS="${TRT_OSSPATH}/build/out/libnvinfer_plugin.so"

ENV PLUGIN_LIBS="${TRT_OSSPATH}/build/out/libnvinfer_plugin.so"

# Install required packages
RUN cd $TRT_OSSPATH/demo/Diffusion && \
	sed 's|^onnx.*||' -i requirements.txt && \
	sed 's|^onnx.*||' -i requirements.txt && \
	sed 's|^torch.*||' -i requirements.txt && \
	sed 's|^transformers.*||' -i requirements.txt && \
	cat requirements.txt && \
	pip3 install -r requirements.txt && \
	mkdir -p onnx engine output

RUN python3 -m pip install onnx_graphsurgeon==0.3.26 --index-url https://pypi.ngc.nvidia.com

WORKDIR ${TRT_OSSPATH}/demo/Diffusion
