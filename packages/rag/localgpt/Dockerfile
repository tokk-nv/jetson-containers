#---
# name: localgpt
# group: rag
# depends: [langchain, huggingface_hub, transformers, autoawq, protobuf, bitsandbytes, llama_cpp]
# requires: '>=34.1.0'
# docs: docs.md
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt
RUN cd /opt && \
    git clone https://github.com/PromtEngineer/localGPT/ && \
    cd localGPT && \
    sed 's|^langchain.*||' -i requirements.txt && \
    sed 's|^huggingface_hub.*||' -i requirements.txt && \
    sed 's|^transformers.*||' -i requirements.txt && \
    sed 's|^autoawq.*||' -i requirements.txt && \
    sed 's|^protobuf.*||' -i requirements.txt && \
    sed 's|^bitsandbytes.*||' -i requirements.txt && \
    cat requirements.txt && \
    pip3 install -e .

CMD /bin/bash
# CMD python3 run_localGPT.py --show_sources
