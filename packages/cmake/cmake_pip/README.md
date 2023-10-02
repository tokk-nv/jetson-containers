# cmake_pip

> [`CONTAINERS`](#user-content-containers) [`IMAGES`](#user-content-images) [`RUN`](#user-content-run) [`BUILD`](#user-content-build)

<details open>
<summary><b><a id="containers">CONTAINERS</a></b></summary>
<br>

| **`cmake:pip`** | |
| :-- | :-- |
| &nbsp;&nbsp;&nbsp;Aliases | `cmake` |
| &nbsp;&nbsp;&nbsp;Builds | [![`cmake-pip_jp51`](https://img.shields.io/github/actions/workflow/status/dusty-nv/jetson-containers/cmake-pip_jp51.yml?label=cmake-pip:jp51)](https://github.com/dusty-nv/jetson-containers/actions/workflows/cmake-pip_jp51.yml) [![`cmake-pip_jp46`](https://img.shields.io/github/actions/workflow/status/dusty-nv/jetson-containers/cmake-pip_jp46.yml?label=cmake-pip:jp46)](https://github.com/dusty-nv/jetson-containers/actions/workflows/cmake-pip_jp46.yml) |
| &nbsp;&nbsp;&nbsp;Requires | `L4T >=32.6` |
| &nbsp;&nbsp;&nbsp;Dependencies | [`build-essential`](/packages/build-essential) [`python`](/packages/python) |
| &nbsp;&nbsp;&nbsp;Dependants | [`auto_gptq`](/packages/llm/auto_gptq) [`awq`](/packages/llm/awq) [`awq:dev`](/packages/llm/awq) [`bitsandbytes`](/packages/llm/bitsandbytes) [`cudf`](/packages/rapids/cudf) [`cuml`](/packages/rapids/cuml) [`deepstream`](/packages/deepstream) [`exllama`](/packages/llm/exllama) [`exllama:v2`](/packages/llm/exllama) [`faiss`](/packages/vectordb/faiss) [`faiss:lite`](/packages/vectordb/faiss_lite) [`gptq-for-llama`](/packages/llm/gptq-for-llama) [`l4t-diffusion`](/packages/l4t/l4t-diffusion) [`l4t-ml`](/packages/l4t/l4t-ml) [`l4t-pytorch`](/packages/l4t/l4t-pytorch) [`l4t-text-generation`](/packages/l4t/l4t-text-generation) [`langchain`](/packages/llm/langchain) [`langchain:samples`](/packages/llm/langchain) [`llama_cpp:ggml`](/packages/llm/llama_cpp) [`llama_cpp:gguf`](/packages/llm/llama_cpp) [`llava`](/packages/llm/llava) [`local_llm`](/packages/llm/local_llm) [`minigpt4`](/packages/llm/minigpt4) [`mlc`](/packages/llm/mlc) [`mlc:dev`](/packages/llm/mlc) [`nanodb`](/packages/vectordb/nanodb) [`nanosam`](/packages/vit/nanosam) [`nemo`](/packages/nemo) [`onnx`](/packages/onnx) [`onnxruntime`](/packages/onnxruntime) [`opencv_builder`](/packages/opencv/opencv_builder) [`optimum`](/packages/llm/optimum) [`pytorch:1.10`](/packages/pytorch) [`pytorch:1.11`](/packages/pytorch) [`pytorch:1.12`](/packages/pytorch) [`pytorch:1.13`](/packages/pytorch) [`pytorch:1.9`](/packages/pytorch) [`pytorch:2.0`](/packages/pytorch) [`pytorch:2.0_use_distributed`](/packages/pytorch) [`pytorch:2.1`](/packages/pytorch) [`raft`](/packages/rapids/raft) [`realsense`](/packages/realsense) [`ros:foxy-desktop`](/packages/ros) [`ros:foxy-ros-base`](/packages/ros) [`ros:foxy-ros-core`](/packages/ros) [`ros:galactic-desktop`](/packages/ros) [`ros:galactic-ros-base`](/packages/ros) [`ros:galactic-ros-core`](/packages/ros) [`ros:humble-desktop`](/packages/ros) [`ros:humble-ros-base`](/packages/ros) [`ros:humble-ros-core`](/packages/ros) [`ros:iron-desktop`](/packages/ros) [`ros:iron-ros-base`](/packages/ros) [`ros:iron-ros-core`](/packages/ros) [`ros:noetic-desktop`](/packages/ros) [`ros:noetic-ros-base`](/packages/ros) [`ros:noetic-ros-core`](/packages/ros) [`sam`](/packages/vit/sam) [`stable-diffusion`](/packages/diffusion/stable-diffusion) [`stable-diffusion-webui`](/packages/diffusion/stable-diffusion-webui) [`tam`](/packages/vit/tam) [`text-generation-inference`](/packages/llm/text-generation-inference) [`text-generation-webui`](/packages/llm/text-generation-webui) [`torch2trt`](/packages/pytorch/torch2trt) [`torch_tensorrt`](/packages/pytorch/torch_tensorrt) [`torchaudio`](/packages/pytorch/torchaudio) [`torchvision`](/packages/pytorch/torchvision) [`transformers`](/packages/llm/transformers) [`transformers:git`](/packages/llm/transformers) [`transformers:nvgpt`](/packages/llm/transformers) [`tvm`](/packages/tvm) [`xformers`](/packages/llm/xformers) |
| &nbsp;&nbsp;&nbsp;Dockerfile | [`Dockerfile`](Dockerfile) |
| &nbsp;&nbsp;&nbsp;Images | [`dustynv/cmake:pip-r32.7.1`](https://hub.docker.com/r/dustynv/cmake/tags) `(2023-09-07, 0.4GB)`<br>[`dustynv/cmake:pip-r35.2.1`](https://hub.docker.com/r/dustynv/cmake/tags) `(2023-09-07, 5.0GB)`<br>[`dustynv/cmake:pip-r35.3.1`](https://hub.docker.com/r/dustynv/cmake/tags) `(2023-08-29, 5.0GB)`<br>[`dustynv/cmake:pip-r35.4.1`](https://hub.docker.com/r/dustynv/cmake/tags) `(2023-08-29, 5.0GB)` |
| &nbsp;&nbsp;&nbsp;Notes | upgrade cmake with pip |

</details>

<details open>
<summary><b><a id="run">RUN CONTAINER</a></b></summary>
<br>

To start the container, you can use the [`run.sh`](/docs/run.md)/[`autotag`](/docs/run.md#autotag) helpers or manually put together a [`docker run`](https://docs.docker.com/engine/reference/commandline/run/) command:
```bash
# automatically pull or build a compatible container image
./run.sh $(./autotag cmake_pip)

# or if using 'docker run' (specify image and mounts/ect)
sudo docker run --runtime nvidia -it --rm --network=host cmake_pip:35.2.1

```
> <sup>[`run.sh`](/docs/run.md) forwards arguments to [`docker run`](https://docs.docker.com/engine/reference/commandline/run/) with some defaults added (like `--runtime nvidia`, mounts a `/data` cache, and detects devices)</sup><br>
> <sup>[`autotag`](/docs/run.md#autotag) finds a container image that's compatible with your version of JetPack/L4T - either locally, pulled from a registry, or by building it.</sup>

To mount your own directories into the container, use the [`-v`](https://docs.docker.com/engine/reference/commandline/run/#volume) or [`--volume`](https://docs.docker.com/engine/reference/commandline/run/#volume) flags:
```bash
./run.sh -v /path/on/host:/path/in/container $(./autotag cmake_pip)
```
To launch the container running a command, as opposed to an interactive shell:
```bash
./run.sh $(./autotag cmake_pip) my_app --abc xyz
```
You can pass any options to [`run.sh`](/docs/run.md) that you would to [`docker run`](https://docs.docker.com/engine/reference/commandline/run/), and it'll print out the full command that it constructs before executing it.
</details>
<details open>
<summary><b><a id="build">BUILD CONTAINER</b></summary>
<br>

If you use [`autotag`](/docs/run.md#autotag) as shown above, it'll ask to build the container for you if needed.  To manually build it, first do the [system setup](/docs/setup.md), then run:
```bash
./build.sh cmake_pip
```
The dependencies from above will be built into the container, and it'll be tested during.  See [`./build.sh --help`](/jetson_containers/build.py) for build options.
</details>
