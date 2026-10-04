#!/usr/bin/env python3
"""Extract a head-centred sagittal slice per image as raw 8-bit tiles (rendered on host with PIL).
Canonical RAS; tile is [S up, A right], shape (H=Z, W=Y) written row-major. Intensity: clip at p99.5 of volume.
Args: outdir "id<TAB>path" ..."""
import sys, os, numpy as np, nibabel as nib
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for tid, path in (l.split("\t") for l in sys.argv[2:]):
    img = nib.as_closest_canonical(nib.load(path))
    d = np.asarray(img.dataobj, dtype=np.float32)
    hi = np.percentile(d, 99.5); m = d > 0.15 * np.percentile(d, 99)
    xs = np.nonzero(m.any(axis=(1, 2)))[0]
    xc = int(round(np.average(np.arange(d.shape[0]), weights=m.sum(axis=(1, 2)))))
    s = d[xc].T[::-1]                                  # rows: superior at top; cols: posterior->anterior
    t = np.clip(s / hi, 0, 1) * 255
    open(f"{out}/{tid}.u8", "wb").write(t.astype(np.uint8).tobytes())
    print(tid, s.shape[1], s.shape[0], xc, flush=True)
