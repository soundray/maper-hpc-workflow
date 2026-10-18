#!/bin/bash
#SBATCH --job-name=alignlab
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:15:00
# Required: ROOT, GEN (prepared gen with posnorm.dof.gz), SEGDIR, LIST. Applies the target PosNorm transform (-dofin; verified direction:
# aligns the estimated midsagittal plane with the grid-centre plane) to f30-seg120-<id>.nii.gz, nearest neighbour -> $ROOT/qc/seg-aligned/<id>.nii.gz
set -euo pipefail
: "${ROOT:?}" "${GEN:?}" "${SEGDIR:?}" "${LIST:?}"
METS=${METS:-/nobackup/proj/disk/metrimorphics0}; MAPER_SIF=${MAPER_SIF:-$METS/apps/maper-sif/maper.sif}
id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST" | cut -f1); mkdir -p "$ROOT/qc/seg-aligned"
apptainer exec --cleanenv --bind /scratch/local:/scratch/local --bind "$METS:$METS" --env TMPDIR=/scratch/local "$MAPER_SIF" \
  mirtk transform-image "$SEGDIR/f30-seg120-$id.nii.gz" "$ROOT/qc/seg-aligned/$id.nii.gz" -dofin "$ROOT/prepared/$GEN/$id/posnorm.dof.gz" -interp NN
