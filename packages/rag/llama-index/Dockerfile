#---
# name: llama-index
# group: rag
# depends: [pytorch, ollama, jupyterlab]
# requires: '>=34.1.0'
# docs: docs.md
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

RUN pip3 install --no-cache-dir --verbose \
        llama-index-core \
        llama-index-readers-file \
        llama-index-llms-ollama \
        llama-index-embeddings-huggingface

COPY samples/*.py /opt/llama-index/
COPY samples/*.ipynb /opt/llama-index/
COPY samples/L4T-README /opt/llama-index/L4T-README

CMD /start_ollama && \
    JUPYTER_ROOT=/opt/llama-index /start_jupyter && \
    /bin/bash
