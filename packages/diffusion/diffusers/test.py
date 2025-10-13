#!/usr/bin/env python3
print('testing diffusers...')

from diffusers import DiffusionPipeline
import torch

pipe = DiffusionPipeline.from_pretrained(
    "segmind/tiny-sd",          # ~770 MB vs. ~4 GB for SD-1.5
    torch_dtype=torch.float16
).to("cuda")

with torch.inference_mode():
    image = pipe("a small cat").images[0]
    image.save("/data/images/tiny_cat.png")

print('diffusers OK\n')

