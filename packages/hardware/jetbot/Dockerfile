#---
# name: jetbot
# group: hardware
# depends: [jupyter_clickable_image_widget, oled]
# notes: https://github.com/NVIDIA-AI-IOT/jetbot/
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# Avoid warnings by switching to noninteractive
ARG DEBIAN_FRONTEND=noninteractive

# ====================
# INSTALL COMMON TOOLS
# ====================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            net-tools vim cmake && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

WORKDIR /opt

# ==============
# INSTALL JETBOT
# ==============
ENV JETBOT_REPO_DIR=/opt/jetbot
RUN cd /opt/ && git clone https://github.com/tokk-nv/jetbot/
RUN cd ${JETBOT_REPO_DIR} && \
    git checkout dev-no-sparkfun && \
    python3 setup.py install

RUN ls -la /


CMD /start_jupyter && /start_oled_server && /bin/bash
# CMD /bin/bash