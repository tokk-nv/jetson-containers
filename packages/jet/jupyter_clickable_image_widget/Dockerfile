#---
# name: jupyter_clickable_image_widget
# group: jet
# depends: [python]
# test: test.py
# notes: https://github.com/jaybdub/jupyter_clickable_image_widget
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            node-gyp \
            libssl-dev \
            nmp && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && \
    apt-get install -y nodejs

RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager

WORKDIR /

RUN git clone https://github.com/jaybdub/jupyter_clickable_image_widget && \
    cd jupyter_clickable_image_widget && \
    pip3 install -e . && \
    jupyter labextension install js