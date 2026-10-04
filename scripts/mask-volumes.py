#!/usr/bin/env python3
"""Mask volume (mL) and superior extent per Pincram result. Args: ROOT pincram_gen id..."""
import sys, numpy as np, nibabel as nib
root, gen, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
print("target_id\tparenchyma_mL\ticv_mL\tz_top_slice\tz_bottom_slice")
for i in ids:
    out = []
    for nm in ("parenchyma", "icv"):
        im = nib.load(f"{root}/pincram/{gen}/{i}-n100/{nm}.nii.gz"); a = np.squeeze(np.asarray(im.dataobj)) > 0
        out.append((a.sum()*np.prod(im.header.get_zooms()[:3])/1000, a))
    zs = np.nonzero(out[0][1].any((0, 1)))[0]
    print(f"{i}\t{out[0][0]:.0f}\t{out[1][0]:.0f}\t{zs.max()}\t{zs.min()}")
