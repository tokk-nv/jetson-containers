# torchvision

<details open>
<summary><b>CONTAINERS</b></summary>
<br>

| **`torchvision`** | |
| :-- | :-- |
| &nbsp;&nbsp;&nbsp;Builds | [![`torchvision_jp51`](https://img.shields.io/github/actions/workflow/status/dusty-nv/jetson-containers/torchvision_jp51.yml?label=torchvision_jp51)](https://github.com/dusty-nv/jetson-containers/actions/workflows/torchvision_jp51.yml) [![`torchvision_jp46`](https://img.shields.io/github/actions/workflow/status/dusty-nv/jetson-containers/torchvision_jp46.yml?label=torchvision_jp46)](https://github.com/dusty-nv/jetson-containers/actions/workflows/torchvision_jp46.yml) |
| &nbsp;&nbsp;&nbsp;Requires | `L4T >=32.6` |
| &nbsp;&nbsp;&nbsp;Dependencies | [`build-essential`](/packages/build-essential) [`python`](/packages/python) [`cmake`](/packages/cmake/cmake_pip) [`numpy`](/packages/numpy) [`onnx`](/packages/onnx) [`pytorch`](/packages/pytorch) |
| &nbsp;&nbsp;&nbsp;Dependants | [`auto-gptq`](/packages/llm/auto-gptq) [`awq`](/packages/llm/awq) [`gptq-for-llama`](/packages/llm/gptq-for-llama) [`l4t-diffusion`](/packages/l4t/l4t-diffusion) [`l4t-ml`](/packages/l4t/l4t-ml) [`l4t-pytorch`](/packages/l4t/l4t-pytorch) [`l4t-text-generation`](/packages/l4t/l4t-text-generation) [`nemo`](/packages/nemo) [`optimum`](/packages/llm/optimum) [`stable-diffusion`](/packages/diffusion/stable-diffusion) [`stable-diffusion-webui`](/packages/diffusion/stable-diffusion-webui) [`text-generation-inference`](/packages/llm/text-generation-inference) [`text-generation-webui`](/packages/llm/text-generation-webui) [`torch2trt`](/packages/pytorch/torch2trt) [`torch_tensorrt`](/packages/pytorch/torch_tensorrt) [`transformers`](/packages/llm/transformers) |
| &nbsp;&nbsp;&nbsp;Dockerfile | [`Dockerfile`](Dockerfile) |

</details>

<details open>
<summary><b>CONTAINER IMAGES</b></summary>
<br>

| Repository/Tag | Date | Arch | Size |
| :-- | :--: | :--: | :--: |
| &nbsp;&nbsp;[`dustynv/torchvision:r32.7.1`](https://hub.docker.com/r/dustynv/torchvision/tags) | `2023-07-29` | `arm64` | `1.1GB` |

> <sub>Container images are compatible with other minor versions of JetPack/L4T:</sub><br>
> <sub>&nbsp;&nbsp;&nbsp;&nbsp;• L4T R32.7 containers can run on other versions of L4T R32.7 (JetPack 4.6+)</sub><br>
> <sub>&nbsp;&nbsp;&nbsp;&nbsp;• L4T R35.x containers can run on other versions of L4T R35.x (JetPack 5.1+)</sub><br>
</details>

<details open>
<summary><b>RUN CONTAINER</b></summary>
<br>

To start the container, you can use the [`run.sh`](/run.sh)/[`autotag`](/autotag) helpers or manually put together a [`docker run`](https://docs.docker.com/engine/reference/commandline/run/) command:
```bash
# automatically pull or build a compatible container image
./run.sh $(./autotag torchvision)

# or explicitly specify one of the container images above
./run.sh dustynv/torchvision:r32.7.1

# or if using 'docker run' (specify image and mounts/ect)
sudo docker run --runtime nvidia -it --rm --network=host dustynv/torchvision:r32.7.1
```
> <sup>[`run.sh`](/run.sh) forwards arguments to [`docker run`](https://docs.docker.com/engine/reference/commandline/run/) with some defaults added (like `--runtime nvidia`, mounts a `/data` cache, and detects devices)</sup><br>
> <sup>[`autotag`](/autotag) finds a container image that's compatible with your version of JetPack/L4T - either locally, pulled from a registry, or by building it.</sup>

To mount your own directories into the container, use the [`-v`](https://docs.docker.com/engine/reference/commandline/run/#volume) or [`--volume`](https://docs.docker.com/engine/reference/commandline/run/#volume) flags:
```bash
./run.sh -v /path/on/host:/path/in/container $(./autotag torchvision)
```
To launch the container running a command, as opposed to an interactive shell:
```bash
./run.sh $(./autotag torchvision) my_app --abc xyz
```
You can pass any options to `run.sh` that you would to [`docker run`](https://docs.docker.com/engine/reference/commandline/run/), and it'll print out the full command that it constructs before executing it.
</details>
<details open>
<summary><b>BUILD CONTAINER</b></summary>
<br>

If you use [`autotag`](/autotag) as shown above, it'll ask to build the container for you if needed.  To manually build it, first do this System Setup, then run:
```bash
./build.sh torchvision
```
The dependencies from above will be built into the container, and it'll be tested during.  See [`./build.sh --help`](/jetson_containers/build.py) for build options.
</details>