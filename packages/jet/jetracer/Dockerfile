#---
# name: jetracer
# group: jet
# depends: [jupyter_clickable_image_widget]
# test: 
# notes: https://github.com/NVIDIA-AI-IOT/jetracer/
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}


# ============================
# Enable OLED display
# ============================
RUN apt-get update && apt-get install -y supervisor unzip
RUN apt install -y python3-smbus python3-pil

RUN pip3 install pillow flask Adafruit_SSD1306

# oled_display_server.py
# utils.py

WORKDIR /root

RUN mkdir jetracer && \
    cd jetracer && \
    wget https://raw.githubusercontent.com/NVIDIA-AI-IOT/jetcard/852475be56ab220283b273f7c320e74b764a3b43/jetcard/display_server.py -O oled_display_server.py && \
    sed -i 's|\.utils|utils|' oled_display_server.py && \
    wget https://raw.githubusercontent.com/NVIDIA-AI-IOT/jetcard/852475be56ab220283b273f7c320e74b764a3b43/jetcard/utils.py && \
    touch __init__.py 

