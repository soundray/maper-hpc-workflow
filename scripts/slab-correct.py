#!/usr/bin/env python3
"""Per-slice correction of the superior-slab contrast compression (experimental).
usage: slab-correct.py in.nii.gz out.nii.gz slice-log.tsv [reference-profile.tsv]
Input: prepared image with axis 2 = S (LAS/RAS). Model: obs(z) = alpha(z)*true + beta(z) (affine per axial slice, applies
to all voxels of the slice). Two anchors per slice: (1) air: true level bg0 (median edge background below the slab) ->
observed edge background e(z); (2) brain: true P75 in the central ROI = W0 * R(depth), R = population reference profile
from unaffected images (slab-reference.py), W0 from unaffected slices below the slab -> observed ROI P75 w(z).
alpha = (w-e)/(T-bg0), beta = e - alpha*bg0; smoothed over z; applied to slices from z_r-8 up. Negative results clipped to 0.
Output float32, same header. Images without a detected slab (edge-bg step < 1.5) are copied unchanged."""
import sys, numpy as np, nibabel as nib
src, dst, logf = sys.argv[1:4]; refp = sys.argv[4] if len(sys.argv) > 4 else "qc/slab-reference-profile.tsv"
im = nib.load(src); assert "".join(nib.aff2axcodes(im.get_qform()))[2] in "SI", "axis 2 must be S-I"
flip = nib.aff2axcodes(im.get_qform())[2] == "I"
d = np.asarray(im.dataobj, dtype=np.float32); sc = d[:, :, ::-1] if flip else d      # sc: index increases superior
nz = sc.shape[2]; dz = abs(im.header.get_zooms()[2]); cx, cy = sc.shape[0]//2, sc.shape[1]//2
R = np.genfromtxt(refp, names=True); Rf = lambda dep: np.interp(dep, R["depth_mm"] + 1, R["median"])
m = sc > 0.15*np.percentile(sc, 99); vtx = int(np.nonzero(m.sum((0, 1)) >= 500)[0].max())
e = np.concatenate([sc[cx-30:cx+30, :10], sc[cx-30:cx+30, -10:]], 1).mean((0, 1))
best, zr = 0, None
for z in range(int(0.6*nz), nz-4):
    r = e[z:z+4].mean()/max(e[z-4:z].mean(), 1e-6)
    if r > best: best, zr = r, z
if best < 1.5:
    nib.save(im, dst); print(f"no slab (step {best:.2f}); copied"); sys.exit(0)
w = np.full(nz, np.nan)
for z in range(vtx+1):
    s = sc[cx-40:cx+40, cy-50:cy+50, z]; ms = m[cx-40:cx+40, cy-50:cy+50, z]
    if ms.sum() > 100: w[z] = np.percentile(s[ms], 75)
depth = (vtx - np.arange(nz))*dz; bg0 = np.median(e[zr-30:zr-8])
base = (depth >= (vtx-zr)*dz + 8) & (depth <= (vtx-zr)*dz + 28) & ~np.isnan(w)
W0 = np.median(w[base]/Rf(depth[base]))
T = W0*Rf(depth)
alpha = np.full(nz, 1.0); beta = np.zeros(nz)
zs = np.arange(zr-8, vtx+1)
a = np.clip((w[zs] - e[zs])/(T[zs] - bg0), 0.2, 1.0); a = np.where(np.isnan(a), 1.0, a)
k = np.ones(5)/5; ap = np.pad(a, 2, mode="edge"); a_s = np.convolve(ap, k, mode="valid")
alpha[zs] = a_s; beta[zs] = e[zs] - a_s*bg0
alpha[vtx+1:] = alpha[vtx]; beta[vtx+1:] = beta[vtx]
a1 = alpha[None, None, :]; b1 = beta[None, None, :]
out = np.where(np.arange(nz)[None, None, :] >= zr-8, np.clip((sc - b1)/a1, 0, None), sc).astype(np.float32)
res = out[:, :, ::-1] if flip else out
hdr = im.header.copy(); hdr.set_data_dtype(np.float32); hdr["scl_slope"] = 1; hdr["scl_inter"] = 0
nib.save(nib.Nifti1Image(res, im.affine, hdr), dst)
with open(logf, "w") as f:
    f.write(f"# z_r={zr} vertex={vtx} step={best:.2f} bg0={bg0:.1f} W0={W0:.0f}\nz\tdepth_mm\tedge_bg\troi_p75\ttrue_p75_model\talpha\tbeta\n")
    for z in range(zr-12, vtx+1): f.write(f"{z}\t{depth[z]:.0f}\t{e[z]:.0f}\t{w[z]:.0f}\t{T[z]:.0f}\t{alpha[z]:.3f}\t{beta[z]:.0f}\n")
print(f"slab z_r={zr} vertex={vtx} W0={W0:.0f} bg0={bg0:.0f} alpha plateau~{np.median(alpha[zr+4:vtx-2]):.2f}")
