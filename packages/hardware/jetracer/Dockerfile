#---
# name: jetracer
# group: hardware
# depends: [jupyterlab, jetcam, torchvision, jupyter_clickable_image_widget]
# notes: https://github.com/NVIDIA-AI-IOT/jetracer
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt/

# Install jetracer
RUN echo "\e[42m Install jetracer \e[0m"
RUN git clone https://github.com/NVIDIA-AI-IOT/jetracer && \
    cd jetracer && \
    pip3 install .