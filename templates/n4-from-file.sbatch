#!/bin/bash
#SBATCH --job-name=n4-corr
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
# Required: ROOT, GEN, LIST. Default (unmasked) N4 on $ROOT/prepared/$GEN/<id>/03-slabcorr.nii.gz -> T1.nii.gz (after slab-correct-array.sbatch, runbook 4.1)
set -euo pipefail
: "${ROOT:?}" "${GEN:?}" "${LIST:?}"
METS=${METS:-/nobackup/proj/disk/metrimorphics0}; MAPER_SIF=${MAPER_SIF:-$METS/apps/maper-sif/maper.sif}
id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST" | cut -f1); out="$ROOT/prepared/$GEN/$id"; mkdir -p "$out/provenance"
apptainer exec --cleanenv --bind /scratch/local:/scratch/local --bind "$METS:$METS" --env TMPDIR=/scratch/local \
  --env ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS="$SLURM_CPUS_PER_TASK" "$MAPER_SIF" \
  N4BiasFieldCorrection -d 3 -i "$out/03-slabcorr.nii.gz" -o "[$out/T1.nii.gz,$out/provenance/N4-bias-field.nii.gz]"
