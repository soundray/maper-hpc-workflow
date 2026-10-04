#!/usr/bin/env python3
"""Overinclusion / scalp-brightness diagnostics per target (prepared gen, pincram gen). Head mask H = T1 > 0.15*p99 of T1;
depth = iterations of 6-connected erosion of H (FOV borders count as inside), in voxels (~mm).
f6 = fraction of parenchyma voxels with depth <= 6 (mask reaching scalp/skull region; ~0 expected);
f6_sup = same for the upper half of the mask's z-range.
S/W (post-N4 and pre-N4 (03-slabcorr)) = median intensity at depth 2-5 / P75 at depth >= 22.
biasS/biasW = N4 bias field mean at depth 2-5 / mean at depth >= 22.
Args: ROOT gen id...  (env MASKGEN: score masks from another pincram generation on the same prepared images)"""
import sys, os, numpy as np, nibabel as nib
root, gen, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
def erode(h):
    p = np.pad(h, 1, constant_values=True)
    return h & p[:-2,1:-1,1:-1] & p[2:,1:-1,1:-1] & p[1:-1,:-2,1:-1] & p[1:-1,2:,1:-1] & p[1:-1,1:-1,:-2] & p[1:-1,1:-1,2:]
print("\t".join(["target_id","f6","f6_sup","S_over_W_N4","S_over_W_preN4","biasS_over_biasW","bg_level"]))
for i in ids:
    L = lambda p: np.squeeze(np.asarray(nib.load(p).dataobj)).astype(np.float32)
    t1 = L(f"{root}/prepared/{gen}/{i}/T1.nii.gz"); pre = L(f"{root}/prepared/{gen}/{i}/03-slabcorr.nii.gz")
    bf = L(f"{root}/prepared/{gen}/{i}/provenance/N4-bias-field.nii.gz"); pm = L(os.environ['MASKTPL'].format(root=root, i=i) if 'MASKTPL' in os.environ else f"{root}/pincram/{os.environ.get('MASKGEN', gen)}/{i}-n100/parenchyma.nii.gz") > 0
    h = t1 > 0.15*np.percentile(t1, 99)
    fl = lambda a, ax: (np.cumsum(a, ax) > 0) & (np.flip(np.cumsum(np.flip(a, ax), ax), ax) > 0)
    h = fl(h, 0) & fl(h, 1)                      # fill holes (CSF/dark GM) along x and y
    depth = np.zeros(h.shape, np.int16); cur = h.copy()
    for k in range(1, 41):
        cur = erode(cur); depth += cur
    sc = h & (depth >= 2) & (depth <= 5); core = depth >= 22
    zs = np.nonzero(pm.any((0, 1)))[0]; zmid = (zs.min()+zs.max())//2
    sup = pm.copy(); sup[:, :, :zmid] = False
    f6 = (pm & (depth <= 6)).sum()/pm.sum(); f6s = (sup & (depth <= 6)).sum()/max(sup.sum(), 1)
    sw = lambda v: np.median(v[sc])/np.percentile(v[core], 75) if sc.any() and core.any() else float('nan')
    print("\t".join([i, f"{f6:.4f}", f"{f6s:.4f}", f"{sw(t1):.3f}", f"{sw(pre):.3f}", f"{(bf[sc].mean()/bf[core].mean() if sc.any() and core.any() else float('nan')):.3f}", f"{np.median(t1[~h]):.0f}"]), flush=True)
