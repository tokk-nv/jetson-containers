# Using Local CUDA Deb Files

This document explains how to use local CUDA deb files instead of downloading them from NVIDIA's servers. This is useful for:

- Testing unreleased CUDA versions
- Using custom CUDA builds
- Working offline
- Using deb files that aren't publicly available

## Method: Direct Local File Path

You can directly specify a local deb file path in the configuration:

```python
# In packages/cuda/cuda/config.py
cuda_local_package('13.0', '/path/to/your/cuda-tegra-repo-ubuntu2404-13-0-local_13.0.0-1_arm64.deb', requires='>=36'),
cuda_samples('13.0', requires='>=36'),
```

## Usage Example

### Step 1: Prepare Your Local Deb File

Place your CUDA deb file in a known location, for example:
```bash
/home/jetson/Downloads/cuda-tegra-repo-ubuntu2404-13-0-local_13.0.0-1_arm64.deb
```

### Step 2: Modify the Configuration

In `packages/cuda/cuda/config.py`, find the CUDA 13.0 section and replace the existing line:

```python
# Replace this line:
cuda_package('13.0', 'https://developer.download.nvidia.com/compute/cuda/13.0.0/local_installers/cuda-tegra-repo-ubuntu2404-13-0-local_13.0.0-1_arm64.deb', requires='>=36'),

# With this line:
cuda_local_package('13.0', '/home/jetson/Downloads/cuda-tegra-repo-ubuntu2404-13-0-local_13.0.0-1_arm64.deb', requires='>=36'),
```

### Step 3: Build the Container

Build the CUDA container with your local deb file:
```bash
python3 jetson_containers/build.py --file packages/cuda/cuda/Dockerfile
```

## How It Works

1. **Function**: `cuda_local_package()` creates a container configuration that uses a local deb file
2. **Build Args**: Sets `USE_LOCAL_DEB=true` and `CUDA_LOCAL_DEB=/path/to/file.deb`
3. **Install Script**: The install script checks for these variables and copies the local file instead of downloading

## File Requirements

The local deb file should be:
- A valid CUDA deb package
- Compatible with your target architecture (arm64 for Jetson)
- Compatible with your Ubuntu version
- Accessible from the host system

## Troubleshooting

### File Not Found
- Ensure the file path is correct and absolute
- Check that the file exists and is readable
- Verify the file permissions

### Architecture Mismatch
- Ensure the deb file is for the correct architecture (arm64 for Jetson devices)

### Permission Issues
- Make sure the deb file is readable by the user running the build process

## Notes

- The local deb file is copied into the container during build
- The original file remains unchanged
- This approach works with all CUDA versions supported by jetson-containers
- You can use local deb files for different CUDA versions simultaneously