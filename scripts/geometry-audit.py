#!/usr/bin/env python3
"""Header geometry audit of target images: qform/sform, orientation, voxel size, centring."""
import sys, numpy as np, nibabel as nib
cols = ["target_id","dim","voxel_mm","dtype","qform_code","sform_code","q_eq_s_maxdiff",
        "axcodes_q","det_sign","grid_centre_mm","centre_dist_mm","fov_mm","size_MB_uncomp"]
print("\t".join(cols))
for tid, path in (l.split("\t") for l in sys.argv[1:]):
    img = nib.load(path); h = img.header
    q, qc = img.get_qform(coded=True); s, sc = img.get_sform(coded=True)
    qa = img.get_qform(); sa = img.get_sform()
    shp = np.array(img.shape[:3]); zooms = np.array(h.get_zooms()[:3])
    ctr = qa @ np.r_[(shp - 1) / 2, 1]
    print("\t".join(map(str, [tid, "x".join(map(str, img.shape)),
        "x".join(f"{z:.4g}" for z in zooms), h.get_data_dtype(), int(qc), int(sc),
        f"{np.abs(qa - sa).max():.3g}", "".join(nib.aff2axcodes(qa)),
        "+" if np.linalg.det(qa[:3, :3]) > 0 else "-",
        ",".join(f"{c:.1f}" for c in ctr[:3]), f"{np.linalg.norm(ctr[:3]):.1f}",
        "x".join(f"{f:.0f}" for f in shp * zooms),
        f"{np.prod(img.shape) * h.get_data_dtype().itemsize / 1e6:.1f}"])))
