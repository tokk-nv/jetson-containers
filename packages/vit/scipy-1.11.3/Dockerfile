#---
# name: scipy-1.11.3
# group: vit
# depends: [numpy]
# requires: '>=34.1.0'
# docs: docs.md
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
		  gcc g++ gfortran libopenblas-dev liblapack-dev pkg-config python3-pip python3-dev \
          git cmake \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN pip3 install meson-python ninja Cython pythran pybind11

RUN git clone -b v1.11.3 --single-branch https://github.com/scipy/scipy/ && \
    cd scipy && \
    git submodule update --init && \
    pip3 install . --no-build-isolation
