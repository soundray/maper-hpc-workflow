#!/bin/bash
#SBATCH --job-name=posnorm
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:15:00
# Required: ROOT, GEN (prepared generation with T1.nii.gz and parenchyma.nii.gz), LIST
set -euo pipefail
: "${ROOT:?}" "${GEN:?}" "${LIST:?}"
METS=${METS:-/nobackup/proj/disk/metrimorphics0}; MAPER_SIF=${MAPER_SIF:-$METS/apps/maper/maper.sif}
id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST" | cut -f1); [[ -n "${id:-}" ]] || { echo "No target" >&2; exit 1; }
d="$ROOT/prepared/$GEN/$id"
for f in "$d/T1.nii.gz" "$d/parenchyma.nii.gz"; do [[ -s "$f" ]] || { echo "Missing input: $f" >&2; exit 1; }; done
[[ ! -e "$d/posnorm.dof.gz" ]] || { echo "Output already exists: $d/posnorm.dof.gz" >&2; exit 1; }
srun apptainer exec --cleanenv --bind /scratch/local:/scratch/local --bind "$METS:$METS" --env TMPDIR=/scratch/local "$MAPER_SIF" \
  posnorm -img "$d/T1.nii.gz" -mask "$d/parenchyma.nii.gz" -dofout "$d/posnorm.dof.gz"
