#!/bin/bash

safe_apt_install() {
    local command="$1"
    local max_retries="${2:-3}"
    local attempt=1

    while [ $attempt -le $max_retries ]; do
        echo "Attempt $attempt/$max_retries: $command"

        if eval "$command"; then
            echo "✅ Success: $command"
            return 0
        else
            echo "❌ Failed: $command (attempt $attempt/$max_retries)"

            if [ $attempt -lt $max_retries ]; then
                echo "Waiting before retry..."
                sleep $((attempt * 2))  # Exponential backoff
                attempt=$((attempt + 1))
            else
                echo "❌ All attempts failed for: $command"
                return 1
            fi
        fi
    done
}

safe_apt_install "sudo apt-get install -y curl" 5
sudo systemctl stop docker 2>/dev/null || true
sudo systemctl stop containerd 2>/dev/null || true

# Remove old docker packages
echo Remove conflicting packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove -qq -y $pkg || true; done
for pkg in docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras; do sudo apt-get remove -qq -y $pkg || true; done

# Add Docker's official GPG key:
sudo apt-get update
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
safe_apt_install "sudo apt-get update" 5
safe_apt_install "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin" 5

echo Docker service installed

# on you host PC, first download the following Debian packages and SCP transfer them to the Jetson
# $ cd ~/Downloads/nvidia/sdkm_downloads
# $ scp libnvidia-container1_1.18.0~rc.1-1_arm64.deb \
#       libnvidia-container-tools_1.18.0~rc.1-1_arm64.deb \
#       nvidia-container-toolkit_1.18.0~rc.1-1_arm64.deb \
#       nvidia-container-toolkit-base_1.18.0~rc.1-1_arm64.deb \
#       jetson@10.110.51.116:/home/jetson/Downloads/

cd ~/Downloads && sudo dpkg -i libnvidia-container1_1.18.0~rc.1-1_arm64.deb libnvidia-container-tools_1.18.0~rc.1-1_arm64.deb nvidia-container-toolkit_1.18.0~rc.1-1_arm64.deb nvidia-container-toolkit-base_1.18.0~rc.1-1_arm64.deb