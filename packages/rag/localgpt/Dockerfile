#---
# name: localgpt
# group: rag
# depends: [langchain, huggingface_hub, transformers, auto_awq, auto_gptq, protobuf, bitsandbytes, llama_cpp]
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
    sed 's|^chromadb.*|chromadb|' -i requirements.txt && \
    sed 's|^sentence-transformers.*|sentence-transformers|' -i requirements.txt && \
    sed 's|^urllib3.*|urllib3|' -i requirements.txt && \
    sed 's|^huggingface_hub.*||' -i requirements.txt && \
    sed 's|^transformers.*||' -i requirements.txt && \
    sed 's|^autoawq.*||' -i requirements.txt && \
    sed 's|^auto-gptq.*||' -i requirements.txt && \
    sed 's|^protobuf.*||' -i requirements.txt && \
    sed 's|^bitsandbytes.*||' -i requirements.txt && \
    cat requirements.txt
RUN pip3 list
# RUN cd /opt/localGPT && \
#     pip3 install --ignore-installed -r requirements.txt  && \
#     pip3 list
# RUN cd /opt/localGPT && \ 
#     pip3 install -e .

CMD /bin/bash
# CMD python3 run_localGPT.py --show_sources
