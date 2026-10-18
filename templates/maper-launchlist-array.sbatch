#!/bin/bash
#SBATCH --job-name=maper
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=01:00:00
# Usage: sbatch -A $PROJ --job-name=<name> --array=1-N [--cpus-per-task=8 for fusion] -o ... -e ... \
#          maper-launchlist-array.sbatch <launchlist>
# Runs line SLURM_ARRAY_TASK_ID of a launchlist-gen launch list in the MAPER container.
# Pairs: 2 CPUs (memory headroom; MAPER -threads 1). Fusion: 8 CPUs.
set -euo pipefail
METS=${METS:-/nobackup/proj/disk/metrimorphics0}; MAPER_SIF=${MAPER_SIF:-$METS/apps/maper-sif/maper.sif}
LAUNCHLIST=${1:?launch list required}
cmd=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LAUNCHLIST"); [[ -n "$cmd" ]] || { echo "No entry $SLURM_ARRAY_TASK_ID" >&2; exit 1; }
echo "launchlist: $LAUNCHLIST  task: $SLURM_ARRAY_TASK_ID  host: $HOSTNAME"; echo "command: $cmd"
srun apptainer exec --cleanenv --bind /scratch/local:/scratch/local --bind "$METS:$METS" --env TMPDIR=/scratch/local "$MAPER_SIF" bash -c "$cmd"
