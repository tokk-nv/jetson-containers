#---
# name: jetbot
# group: hardware
# depends: [oled, jupyterlab]
# notes: https://github.com/NVIDIA-AI-IOT/jetbot/
#---
ARG BASE_IMAGE
FROM ubuntu:22.04

# Avoid warnings by switching to noninteractive
ARG DEBIAN_FRONTEND=noninteractive












CMD /start_jupyter && /start_oled_server && /bin/bash
#CMD /bin/bash