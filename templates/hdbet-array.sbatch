#!/bin/bash
#SBATCH --job-name=hdbet
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:30:00
# HD-BET fallback mask (runbook 5.1). CPU mode, 'accurate' ensemble, TTA off.
# Required: ROOT, IN_GEN (prepared generation with T1.nii.gz), LIST.
# Optional: HDBET_VENV (default: shared install $METS/apps/hdbet/hd-bet-1.1/venv), HD_BET_PARAMS (default: its params/).
# Output: $ROOT/hdbet/<id>/{brain,brain_mask}.nii.gz. No network needed: weights ship with the shared install (runbook 5.1).
set -euo pipefail
METS=${METS:-/nobackup/proj/disk/metrimorphics0}
: "${ROOT:?}" "${IN_GEN:?}" "${LIST:?}"
id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST" | cut -f1); out="$ROOT/hdbet/$id"; mkdir -p "$out"
HDBET_HOME=$METS/apps/hdbet/hd-bet-1.1
source "${HDBET_VENV:-$HDBET_HOME/venv}/bin/activate"
export HD_BET_PARAMS=${HD_BET_PARAMS:-$HDBET_HOME/params}
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK
echo "target: $id host: $HOSTNAME"; date
hd-bet -i "$ROOT/prepared/$IN_GEN/$id/T1.nii.gz" -o "$out/brain.nii.gz" -device cpu -mode accurate -tta 0 -pp 1 -s 1
date; ls -la "$out"
