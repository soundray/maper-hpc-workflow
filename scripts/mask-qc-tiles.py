#!/usr/bin/env python3
"""RGB QC tiles with parenchyma-mask contour (red) over T1, canonical RAS. Views: sagittal (head centre of mask), coronal,
axial at 10/20/30 mm below the mask's superior limit. Per-id file {out}/{label}.rgb, tile size 256x256 each (w x h), 5 tiles
side by side => 1280x256 (nearest-neighbour fit into square, intensity clipped at p99.5 of T1).
Args: out pincram_generation prepared_generation label:id ..."""
import sys, os, numpy as np, nibabel as nib
out, pgen, igen = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
def sq(a):                                  # a: (rows, cols) -> 256x256 centred
    s = 256/max(a.shape); r = np.clip((np.arange(256)[:, None]/s).astype(int), 0, a.shape[0]-1); c = np.clip((np.arange(256)[None, :]/s).astype(int), 0, a.shape[1]-1)
    return a[r, c]
for spec in sys.argv[4:]:
    label, i = spec.split(":")
    t = nib.as_closest_canonical(nib.load(f"prepared/{igen}/{i}/T1.nii.gz")); mk = nib.as_closest_canonical(nib.load(os.environ.get("MASKTPL", "pincram/{pgen}/{i}-n100/parenchyma.nii.gz").format(pgen=pgen, i=i)))
    d = np.asarray(t.dataobj, dtype=np.float32); m = np.squeeze(np.asarray(mk.dataobj)) > 0; hi = np.percentile(d, 99.5)
    zs = np.nonzero(m.any((0, 1)))[0]; ztop = zs.max(); dz = abs(t.header.get_zooms()[2])
    xs = np.nonzero(m.any((1, 2)))[0]; ys = np.nonzero(m.any((0, 2)))[0]
    sl = [(d[int(xs.mean())].T[::-1], m[int(xs.mean())].T[::-1]), (d[:, int(ys.mean())].T[::-1], m[:, int(ys.mean())].T[::-1])]
    for mm in (10, 20, 30):
        z = int(ztop - mm/dz); sl.append((d[:, :, z].T[::-1], m[:, :, z].T[::-1]))
    tiles = []
    for im, mm_ in sl:
        g = (np.clip(im/hi, 0, 1)*255).astype(np.uint8); p = np.pad(mm_, 1); e = mm_ & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        rgb = np.stack([g, g, g], -1); rgb[e] = (255, 40, 40); tiles.append(np.stack([sq(rgb[..., k]) for k in range(3)], -1))
    open(f"{out}/{label}.rgb", "wb").write(np.concatenate(tiles, 1).astype(np.uint8).tobytes()); print(label, "ztop", ztop, flush=True)
