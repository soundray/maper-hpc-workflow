#!/bin/bash
#SBATCH --job-name=slabcorr
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=00:15:00
# EXPERIMENTAL (runbook 4.1). Required: ROOT, GEN, LIST, SLAB_REF (reference profile from scripts/slab-reference.py, built from unaffected images).
# 03-centred.nii.gz -> 03-slabcorr.nii.gz (+ provenance/slab-log.tsv when a slab is found; else unchanged copy)
set -euo pipefail
: "${ROOT:?}" "${GEN:?}" "${LIST:?}" "${SLAB_REF:?}"
METS=${METS:-/nobackup/proj/disk/metrimorphics0}; MAPER_SIF=${MAPER_SIF:-$METS/apps/maper/maper.sif}
TOOLS=${TOOLS:-$METS/apps/maper-hpc-workflow/scripts}
id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST" | cut -f1); out="$ROOT/prepared/$GEN/$id"; mkdir -p "$out/provenance"
apptainer exec --cleanenv --bind "$METS:$METS" "$MAPER_SIF" python3 "$TOOLS/slab-correct.py" \
  "$out/03-centred.nii.gz" "$out/03-slabcorr.nii.gz" "$out/provenance/slab-log.tsv" "$SLAB_REF" | tee "$out/provenance/slab-correct.txt"
