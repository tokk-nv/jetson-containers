#---
# name: jetbot
# group: hardware
# depends: [build-essential, tensorrt, pytorch, torchvision, jupyter_clickable_image_widget, oled, opencv]
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
    
    # ====================
    # From `build-essential` package
    # ====================
    # RUN apt-get update \
    #     && apt-get install -y --no-install-recommends \
    #         build-essential \
    #         software-properties-common \
    #         apt-transport-https \
    #         ca-certificates \
    #         lsb-release \
    #         pkg-config \
    #         gnupg \
    #         git \
    #         gdb \
    #         wget \
    #         curl \
    #         nano \
    #         zip \
    #         unzip \
    #         time \
    #         sshpass \
    #         ssh-client \
    #     && apt-get clean \
    #     && rm -rf /var/lib/apt/lists/*
    RUN gcc --version \
        && g++ --version
    
    # =================
    # INSTALL GSTREAMER
    # =================
    RUN apt-get update && \
        apt-get install -y \
        libwayland-egl1 \
        gstreamer1.0-plugins-bad \
        libgstreamer-plugins-bad1.0-0 \
        gstreamer1.0-plugins-good \
        python3-gst-1.0
    
    # ==============
    # INSTALL JETBOT
    # ==============
    ENV JETBOT_REPO_DIR=/opt/jetbot
    RUN cd /opt/ && git clone https://github.com/tokk-nv/jetbot/ && cat /opt/jetbot/jetbot/robot.py
    RUN cd ${JETBOT_REPO_DIR} && \
        git checkout dev-no-sparkfun && \
        python3 setup.py install
    
    RUN ls -la /
    
    ENV JUPYTER_ROOT=/opt/jetbot/notebooks
    
    CMD /start_jupyter && /start_oled_server && /bin/bash
    # CMD /bin/bash