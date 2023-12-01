#---
# name: jetracer
# group: hardware
# depends: [jupyterlab, jetcam, torchvision, jupyter_clickable_image_widget]
# notes: https://github.com/NVIDIA-AI-IOT/jetracer
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt/

# Install jetcam
RUN echo "\e[42m Install jetracer \e[0m"
RUN git clone https://github.com/NVIDIA-AI-IOT/jetracer && \
    cd jetcam && \
    pip3 install .
