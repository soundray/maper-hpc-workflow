#!/usr/bin/env python3
"""RGB QC tiles: MAPER seg120 (nearest-colour palette by label, alpha 0.45) over the prepared T1, canonical RAS.
Views: sagittal, coronal, axial through the brain centre, axial 20 and 40 mm below the segmentation's superior limit.
Per label a 1280x256 .rgb file. Args: out segfile_template(with {i}) prepared_gen label:id ..."""
import sys, os, numpy as np, nibabel as nib
out, tpl, igen = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
rng = np.random.RandomState(7); pal = rng.randint(60, 256, size=(2000, 3)).astype(np.float32); pal[0] = 0
def sq(a):
    s = 256/max(a.shape[:2]); r = np.clip((np.arange(256)[:, None]/s).astype(int), 0, a.shape[0]-1); c = np.clip((np.arange(256)[None, :]/s).astype(int), 0, a.shape[1]-1)
    return a[r, c]
for spec in sys.argv[4:]:
    label, i = spec.split(":")
    t = nib.as_closest_canonical(nib.load(f"prepared/{igen}/{i}/T1.nii.gz")); s = nib.as_closest_canonical(nib.load(tpl.format(i=i)))
    d = np.asarray(t.dataobj, dtype=np.float32); L = np.squeeze(np.asarray(s.dataobj)).astype(int); hi = np.percentile(d, 99.5)
    m = L > 0; zs = np.nonzero(m.any((0, 1)))[0]; ztop = zs.max(); dz = abs(t.header.get_zooms()[2])
    xs = np.nonzero(m.any((1, 2)))[0]; ys = np.nonzero(m.any((0, 2)))[0]; xc, yc, zc = int(xs.mean()), int(ys.mean()), int(zs.mean())
    sl = [(d[xc].T[::-1], L[xc].T[::-1]), (d[:, yc].T[::-1], L[:, yc].T[::-1])]
    for z in (zc, int(ztop-20/dz), int(ztop-40/dz)): sl.append((d[:, :, z].T[::-1], L[:, :, z].T[::-1]))
    tiles = []
    for im, lb in sl:
        g = np.clip(im/hi, 0, 1)[..., None]*255*np.ones(3); c = pal[np.clip(lb, 0, 1999)]; a = (lb > 0)[..., None]*0.45
        rgb = (g*(1-a)+c*a).astype(np.uint8); tiles.append(np.stack([sq(rgb[..., k]) for k in range(3)], -1))
    open(f"{out}/{label}.rgb", "wb").write(np.concatenate(tiles, 1).astype(np.uint8).tobytes()); print(label, flush=True)
