#!/usr/bin/env python3
"""Numeric ICV estimate from HD-BET masks (runbook 12.3): ICV_est = FACTOR * HD-BET mask volume.

FACTOR defaults to the pooled ratio manual-ICV / HD-BET-mask volume, 1.0597, measured on two reference sets with HD-BET 1.1
(CPU, -mode accurate, -tta 0): klasson n=62 (1.0576, sd 1.7%) and the IXI Pincram atlas n=100 (1.0611, sd 2.2%); pooled sd 2.1%
(error per scan about 2%, ~30 mL). Not validated for populations that differ strongly in CSF space/atrophy from those sets.

usage: hdbet-icv-estimate.py [--factor F] "id<TAB>brain_mask.nii.gz" ...
Output TSV: target_id, hdbet_mL, icv_est_mL, margin_below_mask_mm (lowest mask slice to the FOV edge, canonical RAS),
mask_touches_fov (any mask voxel on the array border: brain probably clipped; do not trust the estimate). The absence of this flag
does not prove full coverage (a clipped cerebellum can leave a few mm of margin): check the margin and QC visually."""
import sys, numpy as np, nibabel as nib
FACTOR = 1.0597
args = sys.argv[1:]
if args and args[0] == "--factor": FACTOR = float(args[1]); args = args[2:]
print("target_id\thdbet_mL\ticv_est_mL\tmargin_below_mask_mm\tmask_touches_fov")
for tid, path in (a.split("\t") for a in args):
    im = nib.as_closest_canonical(nib.load(path)); m = np.squeeze(np.asarray(im.dataobj)) > 0; z = im.header.get_zooms()
    v = m.sum()*np.prod(z[:3])/1000; zs = np.nonzero(m.any((0, 1)))[0]
    border = any(m.take(0, axis=a).any() or m.take(m.shape[a]-1, axis=a).any() for a in range(3))
    print(f"{tid}\t{v:.0f}\t{v*FACTOR:.0f}\t{zs.min()*z[2]:.0f}\t{'yes' if border else 'no'}")
