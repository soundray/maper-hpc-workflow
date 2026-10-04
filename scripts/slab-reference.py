#!/usr/bin/env python3
"""Reference brain-signal profile vs depth below vertex from UNAFFECTED images (canonical RAS; central ROI x+-40, y+-50
around the grid centre; P75 of head-mask voxels per slice, 2 mm bins), each normalised by its own median over 36-60 mm
depth. Output: depth_mm, median, p25, p75, n. Args: outfile "id<TAB>path" ..."""
import sys, numpy as np, nibabel as nib
out = sys.argv[1]; P = {}
for tid, path in (l.split("\t") for l in sys.argv[2:]):
    im = nib.as_closest_canonical(nib.load(path)); dz = abs(im.header.get_zooms()[2]); d = np.asarray(im.dataobj, dtype=np.float32)
    m = d > 0.15*np.percentile(d, 99); vtx = int(np.nonzero(m.sum((0,1)) >= 500)[0].max()); cx, cy = d.shape[0]//2, d.shape[1]//2
    v = {}
    for z in range(max(0, vtx-int(70/dz)), vtx+1):
        s = d[cx-40:cx+40, cy-50:cy+50, z]; ms = m[cx-40:cx+40, cy-50:cy+50, z]
        if ms.sum() > 100: v[(vtx-z)*dz] = np.percentile(s[ms], 75)
    ref = np.median([x for k, x in v.items() if 36 <= k <= 60])
    for k, x in v.items(): P.setdefault(int(k//2)*2, []).append(x/ref)
with open(out, "w") as f:
    f.write("depth_mm\tmedian\tp25\tp75\tn\n")
    for k in sorted(P): a = np.array(P[k]); f.write(f"{k}\t{np.median(a):.3f}\t{np.percentile(a,25):.3f}\t{np.percentile(a,75):.3f}\t{len(a)}\n")
