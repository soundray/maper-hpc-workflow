#!/usr/bin/env python3
"""HD-BET mask volumes and grid check vs the prepared T1 (ROOT/hdbet/<id>/brain_mask.nii.gz vs ROOT/prepared/<gen>/<id>/T1.nii.gz). Args: ROOT GEN id..."""
import sys, numpy as np, nibabel as nib
root, gen, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
print("target_id\thdbet_mL\tz_top_slice\tz_bottom_slice\tgrid_ok\tn_components_est")
for i in ids:
    h = nib.load(f"{root}/hdbet/{i}/brain_mask.nii.gz"); t = nib.load(f"{root}/prepared/{gen}/{i}/T1.nii.gz")
    m = np.squeeze(np.asarray(h.dataobj)) > 0; zs = np.nonzero(m.any((0, 1)))[0]
    ok = h.shape[:3] == t.shape and np.allclose(h.affine, t.affine, atol=1e-3)
    print(f"{i}\t{m.sum()*np.prod(t.header.get_zooms()[:3])/1000:.0f}\t{zs.max()}\t{zs.min()}\t{ok}\t-")
