#!/usr/bin/env python3
"""Flip voxel storage along array axis 0 and compensate the affine (no interpolation;
physical coordinates of every voxel value unchanged). Turns LAS storage into RAS.
usage: flip-storage-x.py in.nii.gz out.nii.gz"""
import sys, numpy as np, nibabel as nib
img = nib.load(sys.argv[1]); d = np.asanyarray(img.dataobj.get_unscaled())
q, qc = img.get_qform(coded=True); s, sc = img.get_sform(coded=True)
n = img.shape[0]; F = np.eye(4); F[0, 0] = -1; F[0, 3] = n - 1
out = nib.Nifti1Image(np.flip(d, axis=0).copy(), None, img.header)
out.set_qform(q @ F, int(qc))
if int(sc): out.set_sform(s @ F, int(sc))
else: out.set_sform(None, 0)
nib.save(out, sys.argv[2])
# verify: voxel i in output sits where voxel n-1-i sat in input
o = nib.load(sys.argv[2]); i = np.array([3, 17, 29, 1]); j = i.copy(); j[0] = n - 1 - i[0]
assert np.allclose(o.get_qform() @ i, q @ j, atol=1e-4)
assert np.array_equal(np.asanyarray(o.dataobj.get_unscaled())[3, 17, 29], d[j[0], 17, 29])
print(sys.argv[2], ''.join(nib.aff2axcodes(o.get_qform())), 'det', np.sign(np.linalg.det(o.get_qform()[:3, :3])), 'codes', int(o.header['qform_code']), int(o.header['sform_code']))
