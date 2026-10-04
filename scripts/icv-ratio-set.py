#!/usr/bin/env python3
"""ICV / HD-BET volume ratio for a reference set. Args: name icv_mask_dir hdbet_dir n [brainmask_dir]  (ids m1..mN; HD-BET mask at hdbet_dir/<id>/brain_mask.nii.gz)
Writes <name>-ratio-per-case.tsv to the current directory. Volumes in mL from header voxel sizes (canonical orientation); Dice(H, ICV), fraction of H inside ICV, ratio ICV/H, regression and leave-one-out error."""
import sys, numpy as np, nibabel as nib
name, mdir, hdir, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]); bdir = sys.argv[5] if len(sys.argv) > 5 else None
def ld(p):
    im = nib.as_closest_canonical(nib.load(p)); return np.squeeze(np.asarray(im.dataobj)) > 0, np.prod(im.header.get_zooms()[:3])/1000
rows = []
for k in range(1, n+1):
    i = f"m{k}"; M, v = ld(f"{mdir}/{i}.nii.gz"); H, _ = ld(f"{hdir}/{i}/brain_mask.nii.gz"); assert M.shape == H.shape, i
    inter = (M & H).sum(); r = dict(id=i, vm=M.sum()*v, vh=H.sum()*v, dice=2*inter/(M.sum()+H.sum()), fin=inter/H.sum())
    if bdir: B, _ = ld(f"{bdir}/{i}.nii.gz"); r.update(vb=B.sum()*v, diceB=2*(B & H).sum()/(B.sum()+H.sum()))
    rows.append(r)
with open(f"{name}-ratio-per-case.tsv", "w") as f:
    f.write("id\tICV_mL\tHDBET_mL\tratio\tdice\tfrac_H_in_ICV" + ("\tbrainAND_mL\tdice_H_vs_AND" if bdir else "") + "\n")
    for r in rows: f.write(f"{r['id']}\t{r['vm']:.1f}\t{r['vh']:.1f}\t{r['vm']/r['vh']:.4f}\t{r['dice']:.4f}\t{r['fin']:.4f}" + (f"\t{r['vb']:.1f}\t{r['diceB']:.4f}" if bdir else "") + "\n")
vm = np.array([r["vm"] for r in rows]); vh = np.array([r["vh"] for r in rows]); rat = vm/vh; A = np.c_[vh, np.ones(n)]
coef = np.linalg.lstsq(A, vm, rcond=None)[0]; res = vm-A @ coef
loo = np.array([vm[j]-np.r_[vh[j], 1] @ np.linalg.lstsq(np.delete(A, j, 0), np.delete(vm, j), rcond=None)[0] for j in range(n)])
print(f"[{name}] n={n}  ICV mean {vm.mean():.0f} mL (sd {vm.std():.0f}); HD-BET mean {vh.mean():.0f} mL")
print(f"  Dice(HD-BET, ICV) median {np.median([r['dice'] for r in rows]):.3f} (min {min(r['dice'] for r in rows):.3f}); fraction of HD-BET inside ICV median {np.median([r['fin'] for r in rows]):.3f} (min {min(r['fin'] for r in rows):.3f})")
print(f"  ratio ICV/HD-BET mean {rat.mean():.4f} median {np.median(rat):.4f} sd {rat.std():.4f} ({100*rat.std()/rat.mean():.1f}%), range {rat.min():.3f}-{rat.max():.3f}")
print(f"  regression ICV = {coef[0]:.3f}*H + {coef[1]:.0f}: r={np.corrcoef(vh, vm)[0,1]:.3f}, resid sd {res.std():.1f} mL ({100*res.std()/vm.mean():.1f}%), LOO sd {loo.std():.1f} mL")
print(f"  error using the klasson factor 1.0575: mean {np.mean(1.0575*vh-vm):+.1f} mL ({100*np.mean(1.0575*vh-vm)/vm.mean():+.1f}%), sd {np.std(1.0575*vh-vm):.1f} mL ({100*np.std(1.0575*vh-vm)/vm.mean():.1f}%)")
if bdir: print(f"  brain AND-mask: mean {np.mean([r['vb'] for r in rows]):.0f} mL; Dice(HD-BET, AND) median {np.median([r['diceB'] for r in rows]):.3f}; HD-BET/AND mean ratio {np.mean(vh/np.array([r['vb'] for r in rows])):.3f}")
