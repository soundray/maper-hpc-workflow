#!/bin/bash
# Replay MAPER regprop (default tc2 path and -notc path) for one source/target cache pair, keeping every stage DOF
# usage: stagewise.sh SRC_CACHE_DIR TGT_CACHE_DIR SRC_SEG OUTDIR THREADS
set -euo pipefail
src=$1 tgt=$2 seg=$3 out=$4 th=$5 ds=2.5
pdir=/nix/store/ybbaz48cxi7dv7nv2s3z102n0y3nq0g3-maper/lib/maper
mkdir -p "$out"; cd "$out"; cp $pdir/neutral.dof.gz .
mirtk compose-dofs "$src"/pre.dof.gz "$tgt"/pre.dof.gz prealign.dof.gz -scale 1 -1
pick() { for i in "$@"; do echo "$(mirtk evaluate-similarity "$tgt"/mri.nii.gz "$src"/mri.nii.gz -metric NMI -noid -csv -precision 7 -dofin $i.dof.gz | tail -n 1), $i"; done | sort -rn | head -n 1 | cut -d, -f2 | tr -d ' '; }
# --- tc2 (default) path
mirtk register "$tgt"/mri.nii.gz "$src"/mri.nii.gz -dofout tc-r0.dof.gz -model Rigid -levels 4 4 -threads $th
mirtk register "$tgt"/mri.nii.gz "$src"/mri.nii.gz -dofin prealign.dof.gz -dofout tc-r1.dof.gz -model Rigid -levels 4 4 -threads $th
b=$(pick neutral prealign tc-r0 tc-r1); echo "tc path rigid choice: $b"; cp $b.dof.gz tc-coarse0.dof.gz
mirtk register "$tgt"/gmwmr.nii.gz "$tgt"/gmwml.nii.gz "$src"/gmwmr.nii.gz "$src"/gmwml.nii.gz \
  -dofin tc-coarse0.dof.gz -dofout tc-coarse1.dof.gz -bg -1 -model Affine+FFD -levels 4 4 \
  -par "Energy function" "0.5 SSD(I1, I3 o T) + 0.5 SSD(I2, I4 o T) + 1e-3 BE(T)" -ds $ds -threads $th
mirtk register "$tgt"/csf.nii.gz "$src"/csf.nii.gz \
  -dofin tc-coarse1.dof.gz -dofout tc-coarse.dof.gz -bg -1 -model Affine+FFD -levels 3 2 \
  -par "Energy function" "SSD(I1, I2 o T) + 1e-3 BE(T)" -ds $ds -threads $th
mirtk register "$tgt"/onepad.nii.gz "$src"/onepad.nii.gz -dofin tc-coarse.dof.gz -dofout tc-fine.dof.gz \
  -bg 0 -model FFD -levels 2 1 -ds $ds -threads $th -par "Strict step length range" "No" -par "Maximum streak of rejected steps" 2
# --- notc path
mirtk register "$tgt"/mri.nii.gz "$src"/mri.nii.gz -dofout nt-r0.dof.gz -model Rigid -levels 4 1 -threads $th
mirtk register "$tgt"/mri.nii.gz "$src"/mri.nii.gz -dofin prealign.dof.gz -dofout nt-r1.dof.gz -model Rigid -levels 4 1 -threads $th
b=$(pick neutral prealign nt-r0 nt-r1); echo "notc path rigid choice: $b"; cp $b.dof.gz nt-coarse0.dof.gz
mirtk register "$tgt"/onepad.nii.gz "$src"/onepad.nii.gz -dofin nt-coarse0.dof.gz -dofout nt-coarse.dof.gz -bg -1 -model Affine -levels 4 1 -threads $th
mirtk register "$tgt"/onepad.nii.gz "$src"/onepad.nii.gz -dofin nt-coarse.dof.gz -dofout nt-fine.dof.gz \
  -bg 0 -model FFD -levels 4 1 -ds $ds -threads $th -par "Strict step length range" "No" -par "Maximum streak of rejected steps" 2
for d in prealign tc-coarse0 tc-coarse1 tc-coarse tc-fine nt-coarse0 nt-coarse nt-fine; do
  mirtk transform-image "$seg" seg-$d.nii.gz -dofin $d.dof.gz -target "$tgt"/onepad.nii.gz -interp NN -threads $th
done
echo done
