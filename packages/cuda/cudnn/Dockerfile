#---
# name: cudnn
# group: cuda
# depends: cuda
# config: config.py
# test: test.sh
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG CUDNN_URL
ARG CUDNN_DEB
ARG CUDNN_PACKAGES
ARG CUDNN_SCP_PATH
ARG USE_SCP_DOWNLOAD

RUN echo $CUDNN_PACKAGES

# First, remove any existing cuDNN packages to avoid conflicts
RUN apt-get update && \
    apt-get remove -y --purge libcudnn* && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN ls /etc/apt/sources.list.d/ && \
    apt-get update && \
    apt-cache search cudnn

# Install sshpass and openssh-client for SCP downloads
RUN apt-get update && \
    apt-get install -y --no-install-recommends sshpass openssh-client && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN echo "Downloading ${CUDNN_DEB}" && \
    rm -rf /tmp/cudnn && mkdir /tmp/cudnn && cd /tmp/cudnn && \
    if [ "${USE_SCP_DOWNLOAD:-false}" = "true" ] && [ -n "${CUDNN_SCP_PATH:-}" ]; then \
        echo "Using SCP to download from: ${CUDNN_SCP_PATH}" && \
        filename=$(basename "${CUDNN_SCP_PATH}") && \
        if echo "${CUDNN_SCP_PATH}" | grep -q ":" && echo "${CUDNN_SCP_PATH}" | grep -q "@"; then \
            if echo "${CUDNN_SCP_PATH}" | grep -q ":" && echo "${CUDNN_SCP_PATH}" | grep -q ":" && echo "${CUDNN_SCP_PATH}" | grep -q "@"; then \
                user_pass="${CUDNN_SCP_PATH%%@*}" && \
                host_path="${CUDNN_SCP_PATH#*@}" && \
                user="${user_pass%%:*}" && \
                password="${user_pass#*:}" && \
                host="${host_path%%:*}" && \
                remote_path="${host_path#*:}" && \
                echo "SCP with password: user=${user}, host=${host}, path=${remote_path}" && \
                sshpass -p "${password}" scp -o StrictHostKeyChecking=no "${user}@${host}:${remote_path}" "/tmp/cudnn/${filename}"; \
            else \
                user="${CUDNN_SCP_PATH%%@*}" && \
                host_path="${CUDNN_SCP_PATH#*@}" && \
                host="${host_path%%:*}" && \
                remote_path="${host_path#*:}" && \
                echo "SCP without password: user=${user}, host=${host}, path=${remote_path}" && \
                scp -o StrictHostKeyChecking=no "${user}@${host}:${remote_path}" "/tmp/cudnn/${filename}"; \
            fi; \
        else \
            echo "Invalid SCP path format: ${CUDNN_SCP_PATH}" && exit 1; \
        fi; \
    else \
        echo "Using wget to download from: ${CUDNN_URL}" && \
        wget ${WGET_FLAGS} ${CUDNN_URL}; \
    fi && \
    dpkg -i *.deb && \
    cp /var/cudnn-*-repo-*/cudnn-*-keyring.gpg /usr/share/keyrings/ && \
    apt-get update && \
    apt-cache search cudnn && \
    apt list --installed | grep 'cuda\|cudnn\|cublas' && \
    apt-get install -y --no-install-recommends ${CUDNN_PACKAGES} file && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    dpkg --list | grep cudnn && \
    dpkg -P ${CUDNN_DEB} && \
    rm -rf /tmp/cudnn

RUN cd /usr/src/cudnn_samples_v*/conv_sample/ && \
    make -j$(nproc)