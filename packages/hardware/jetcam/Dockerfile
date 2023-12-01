#---
# name: jetcam
# group: hardware
# depends: [jupyterlab]
# notes: https://github.com/NVIDIA-AI-IOT/jetcam
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt/

# Install jetcam
RUN echo "\e[42m Install jetcam \e[0m"
RUN git clone https://github.com/NVIDIA-AI-IOT/jetcam && \
    cd jetcam && \
    pip3 install .
