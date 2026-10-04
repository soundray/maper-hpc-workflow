#!/usr/bin/env python3
"""Host PIL: stack mask-QC rows (1280x256 each) from {dir}/*.rgb into one PNG with ID labels. Args: dir out.png label..."""
import sys
from PIL import Image, ImageDraw
d, outp, labels = sys.argv[1], sys.argv[2], sys.argv[3:]
sh = Image.new("RGB", (1280, 256*len(labels))); dr = ImageDraw.Draw(sh)
for k, l in enumerate(labels):
    sh.paste(Image.frombytes("RGB", (1280, 256), open(f"{d}/{l}.rgb", "rb").read()), (0, 256*k)); dr.rectangle([0, 256*k, 150, 256*k+11], fill=0); dr.text((3, 256*k), l, fill=(255, 255, 255))
sh.save(outp); print(outp, sh.size)
