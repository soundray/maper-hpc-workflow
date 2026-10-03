#!/usr/bin/env python3
"""Fourier (k-space) crop to a coarser voxel size, undoing zero-fill interpolation.

usage: fourier-crop.py in.nii.gz out.nii.gz TARGET_MM

Axes with spacing < TARGET_MM are cropped to N_new = N*spacing/TARGET_MM (must be an integer,
i.e. the field of view is kept exactly); other axes are left untouched. Exactly one axis must be
left untouched (it is looped over; all others are transformed together per slab).
A phase shift keeps the grid centre fixed: new voxel j sits at old index j*f + (f-1)/2, f = N/N_new.
NIfTI scaling is applied; output is float32, slope 1, sform := qform with the input qform code.
Negative values (Gibbs ringing) are clamped to 0; the count is printed.
"""
import sys, numpy as np, nibabel as nib

src, dst, target = sys.argv[1], sys.argv[2], float(sys.argv[3])
img = nib.load(src)
if img.ndim != 3: raise SystemExit("3-D input required")
q, qc = img.get_qform(coded=True)
if int(qc) == 0: raise SystemExit("qform code is 0; canonicalize first")
shape = np.array(img.shape); zooms = np.array(img.header.get_zooms()[:3], float)
crop = zooms < target - 1e-6
keep = np.flatnonzero(~crop)
if len(keep) != 1: raise SystemExit(f"expected exactly one uncropped axis, got {keep}")
keep = int(keep[0]); cax = [a for a in range(3) if crop[a]]

new_shape = shape.copy(); fac = np.ones(3); off = np.zeros(3)
for a in cax:
    m = shape[a] * zooms[a] / target
    if abs(m - round(m)) > 1e-3: raise SystemExit(f"axis {a}: FOV not a multiple of {target} mm ({m})")
    new_shape[a] = int(round(m)); fac[a] = shape[a] / new_shape[a]; off[a] = (fac[a] - 1) / 2

data = np.asanyarray(img.dataobj, dtype=np.float32)
out = np.empty(new_shape, np.float32)

# per-axis: cropped frequency indices (signed, original grid) and phase shift exp(2*pi*i*k*s/N)
sel, ramp = {}, {}
for a in cax:
    N, M = shape[a], new_shape[a]
    k = np.fft.fftfreq(M, 1.0 / M).astype(int)          # signed indices -M/2..M/2-1 in FFT order
    sel[a] = np.mod(k, N)                                # positions in the N-point spectrum
    ramp[a] = np.exp(2j * np.pi * k * off[a] / N)
scale = np.prod([new_shape[a] / shape[a] for a in cax])

ax2 = [a if a < keep else a - 1 for a in cax]           # crop axes within a slab
for i in range(shape[keep]):
    sl = np.take(data, i, axis=keep)
    F = np.fft.fftn(sl, axes=ax2)
    F = F[np.ix_(sel[cax[0]], sel[cax[1]])] if len(cax) == 2 else np.take(F, sel[cax[0]], axis=ax2[0])
    for a, b in zip(cax, ax2):
        sh = [1, 1]; sh[b] = -1; F = F * ramp[a].reshape(sh)
    r = np.real(np.fft.ifftn(F, axes=ax2)) * scale
    idx = [slice(None)] * 3; idx[keep] = i; out[tuple(idx)] = r

n = int((out < 0).sum()); out[out < 0] = 0

S = np.eye(4); S[:3, :3] = np.diag(fac); S[:3, 3] = off
A = q @ S
o = nib.Nifti1Image(out, A); o.set_data_dtype(np.float32)
o.header.set_xyzt_units(*img.header.get_xyzt_units())
o.set_qform(A, int(qc)); o.set_sform(A, int(qc)); nib.save(o, dst)
ctr = A @ np.r_[(new_shape - 1) / 2, 1]
print(f"{src} -> {dst}: {tuple(shape)} -> {tuple(new_shape)}, voxel {target} mm on axes {cax}; "
      f"clamped {n} negative voxels; grid centre {np.round(ctr[:3], 4)}")
