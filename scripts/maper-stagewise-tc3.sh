#!/bin/bash
# Replay MAPER regprop -tc3 path for one pair, keeping every stage's DOF (mirrors maper lines 316-381).
# usage: stagewise-tc3.sh SRC_CACHE_DIR TGT_CACHE_DIR SRC_SEG OUTDIR THREADS
set -euo pipefail
src=$1 tgt=$2 seg=$3 out=$4 th=$5 ds=2.5
pdir=/nix/store/ybbaz48cxi7dv7nv2s3z102n0y3nq0g3-maper/lib/maper
mkdir -p "$out"; cd "$out"; cp $pdir/neutral.dof.gz .
mirtk compose-dofs "$src"/pre.dof.gz "$tgt"/pre.dof.gz prealign.dof.gz -scale 1 -1
pick() { for i in "$@"; do echo "$(mirtk evaluate-similarity "$tgt"/mri.nii.gz "$src"/mri.nii.gz -metric NMI -noid -csv -precision 7 -dofin $i.dof.gz | tail -n 1), $i"; done | sort -rn | head -n 1 | cut -d, -f2 | tr -d ' '; }
mirtk register "$tgt"/mri.nii.gz "$src"/mri.nii.gz -dofout t3-r0.dof.gz -model Rigid -levels 4 4 -threads $th
mirtk register "$tgt"/mri.nii.gz "$src"/mri.nii.gz -dofin prealign.dof.gz -dofout t3-r1.dof.gz -model Rigid -levels 4 4 -threads $th
b=$(pick neutral prealign t3-r0 t3-r1); echo "tc3 rigid choice: $b"; cp $b.dof.gz t3-coarse0.dof.gz
mirtk register "$tgt"/wmr.nii.gz "$tgt"/wml.nii.gz "$src"/wmr.nii.gz "$src"/wml.nii.gz \
  -dofin t3-coarse0.dof.gz -dofout t3-coarse1.dof.gz -bg -1 -model Affine+FFD -levels 4 4 \
  -par "Energy function" "0.5 SSD(I1, I3 o T) + 0.5 SSD(I2, I4 o T) + 1e-3 BE(T)" -ds $ds -threads $th
mirtk register "$tgt"/csf.nii.gz "$tgt"/gm.nii.gz "$src"/csf.nii.gz "$src"/gm.nii.gz \
  -dofin t3-coarse1.dof.gz -dofout t3-coarse.dof.gz -bg -1 -model Affine+FFD -levels 3 2 \
  -par "Energy function" "0.6 SSD(I1, I3 o T) + 0.4 SSD(I2, I4 o T) + 1e-3 BE(T)" -ds $ds -threads $th
mirtk register "$tgt"/onepad.nii.gz "$src"/onepad.nii.gz -dofin t3-coarse.dof.gz -dofout t3-fine.dof.gz \
  -bg 0 -model FFD -levels 2 1 -ds $ds -threads $th -par "Strict step length range" "No" -par "Maximum streak of rejected steps" 2
for d in t3-coarse0 t3-coarse1 t3-coarse t3-fine; do
  mirtk transform-image "$seg" seg-$d.nii.gz -dofin $d.dof.gz -target "$tgt"/onepad.nii.gz -interp NN -threads $th
done
echo done
