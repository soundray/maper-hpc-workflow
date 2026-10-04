#!/usr/bin/env python3
"""In-plane power spectrum check for zero-filled reconstruction (runbook 3.4). Native storage axes 0,1 = in-plane.
Mean over slices of |FFT2|^2; prints log10 mean power along kx and ky (other axis summed over |k|<=15% Nyquist
band to avoid mixing) in 16 bins of |k|/Nyquist; a sharp cliff to a flat floor below Nyquist indicates zero-fill.
Args: "id<TAB>path" ..."""
import sys, numpy as np, nibabel as nib
print("\t".join(["target_id","axis"]+[f"k{(i+1)/16:.2f}" for i in range(16)]))
for tid, path in (l.split("\t") for l in sys.argv[1:]):
    d = np.asarray(nib.load(path).dataobj, dtype=np.float32); n0, n1 = d.shape[:2]
    P = np.zeros((n0, n1), np.float64)
    for k in range(0, d.shape[2], 2): P += np.abs(np.fft.fftshift(np.fft.fft2(d[:, :, k])))**2
    for ax, name in ((0, "kx"), (1, "ky")):
        n = P.shape[ax]; c = n//2; o = P.shape[1-ax]; oc = o//2; w = max(1, int(0.15*o/2))
        band = P.take(range(oc-w, oc+w+1), axis=1-ax).mean(1-ax if False else (1 if ax == 0 else 0)) if False else (P[:, oc-w:oc+w+1].mean(1) if ax == 0 else P[oc-w:oc+w+1, :].mean(0))
        prof = np.array([band[c+int(i*c/16):c+int((i+1)*c/16)].mean() for i in range(16)])
        print("\t".join([tid, name]+[f"{np.log10(v):.2f}" for v in prof]), flush=True)
