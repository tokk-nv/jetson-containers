
![](https://user-images.githubusercontent.com/25759564/67250039-b1c22e00-f41e-11e9-931f-98c1729550d0.jpg)

* Container for JetRacer from https://github.com/NVIDIA-AI-IOT/jetracer
* (Aiming to) support Jetson AGX Orin, Jetson Orin Nano, Jetson Xavier NX developer kits, and the original Jetson Nano Developer Kit.

To launch the container, run the command below, and then navigate your browser to `http://HOSTNAME:8888`

```bash
./run.sh $(./autotag jetracer)
```

### Hardware setup

We assume you set up your JetRacer hardware based on the original [hardware_setup](https://github.com/NVIDIA-AI-IOT/jetracer/blob/master/docs/tamiya/hardware_setup.md) instruction, but using a Jetson developer kit other than the original Jetson Nano Developer Kit.

### Examples

https://github.com/NVIDIA-AI-IOT/jetracer/blob/master/docs/examples.md