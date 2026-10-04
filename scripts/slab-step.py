#!/usr/bin/env python3
"""Locate the superior slab boundary and test an affine (contrast-compression) model.
Per image (canonical RAS, z=S): edge-bg(z) = mean of 10 outermost AP columns each side over central 60 x. Boundary z_r =
slice with the largest rise of (mean edge-bg of 4 slices above) / (mean of 4 below), searched in z >= 60% of FOV. Then
quantile-quantile map of slice-stack [z_r..z_r+3] onto [z_r-4..z_r-1] (same head-ish mask, 2nd..98th percentile of voxels
above a low threshold) and a linear fit out = a*in + b (a<1: compression toward fixed point b/(1-a)).
Args: "id<TAB>path" ..."""
import sys, numpy as np, nibabel as nib
print("\t".join(["target_id","z_r","vertex","step_ratio","edge_below","edge_above","qq_a","qq_b","qq_fixed_pt","qq_r2","slab_mm"]))
for tid, path in (l.split("\t") for l in sys.argv[1:]):
    d = np.asarray(nib.as_closest_canonical(nib.load(path)).dataobj, dtype=np.float32); nz = d.shape[2]
    cx = d.shape[0]//2; e = np.concatenate([d[cx-30:cx+30, :10], d[cx-30:cx+30, -10:]], 1).mean((0,1))
    m = d > 0.15*np.percentile(d, 99); vtx = int(np.nonzero(m.sum((0,1)) >= 500)[0].max())
    best, zr = 0, None
    for z in range(int(0.6*nz), nz-4):
        r = e[z:z+4].mean()/max(e[z-4:z].mean(), 1e-6)
        if r > best: best, zr = r, z
    if best < 1.5: print(f"{tid}\t-\t{vtx}\t{best:.2f}\t-\t-\t-\t-\t-\t-\t-", flush=True); continue
    A = d[:, :, zr:zr+4]; B = d[:, :, zr-4:zr]
    lo = 0.15*np.percentile(d, 99)*0.2
    qa = np.percentile(A[A > lo], np.arange(2, 99, 2)); qb = np.percentile(B[B > lo], np.arange(2, 99, 2))
    # model: observed above (qa) = a * true (qb proxy) + b
    a, b = np.polyfit(qb, qa, 1); r2 = np.corrcoef(qb, qa)[0,1]**2
    print("\t".join(map(str, [tid, zr, vtx, f"{best:.2f}", f"{e[zr-4:zr].mean():.0f}", f"{e[zr:zr+4].mean():.0f}",
          f"{a:.3f}", f"{b:.0f}", f"{b/(1-a):.0f}" if abs(1-a) > 1e-3 else "inf", f"{r2:.3f}", f"{(nz-zr)*abs(1.0):.0f}"])), flush=True)
