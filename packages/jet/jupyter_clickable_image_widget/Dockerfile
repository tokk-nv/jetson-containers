#---
# name: jupyter_clickable_image_widget
# group: jet
# depends: [jupyterlab]
# notes: https://github.com/jaybdub/jupyter_clickable_image_widget
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# Reference:
# https://github.com/NVIDIA-AI-IOT/jetbot/blob/master/docker/base/Dockerfile

# # Uninstall JupyterLab for now
# RUN echo -e "\e[48;5;172m Uninstall JupyterLab for now \e[0m"
# RUN python3 -m pip uninstall -y jupyter jupyter_core jupyter-client jupyter-console jupyterlab_pygments qtconsole notebook nbconvert nbformat nbclassic nbclient jupyterlab-widgets jupyter-events jupyter-server jupyter-server-terminals 


# Install traitlets (master, to support the unlink() method)
RUN echo -e "\e[48;5;172m Install traitlets \e[0m"
RUN python3 -m pip install git+https://github.com/ipython/traitlets@main
# Install dependencies for jupyter_clickable_image_widget
RUN echo "\e[42m Install dependencies \e[0m"
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            libssl-dev \
            nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# # Install JupyterLab 2.2.6
# RUN echo -e "\e[48;5;172m Install JupyterLab 2.2.6 \e[0m"
# RUN pip3 install jupyter jupyterlab==2.2.6
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager

WORKDIR /

# Install jupyter_clickable_image_widget
RUN echo "\e[42m Install jupyter_clickable_image_widget \e[0m"
RUN git clone https://github.com/jaybdub/jupyter_clickable_image_widget && \
    cd jupyter_clickable_image_widget && \
    git checkout tags/v0.1 && \
    pip3 install -e . && \
    jupyter labextension install js && \
    jupyter lab build