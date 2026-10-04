#!/bin/bash
#SBATCH --job-name=hdbet
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:30:00
# HD-BET fallback mask (runbook 5.1). CPU mode, 'accurate' ensemble, TTA off.
# Required: ROOT, IN_GEN (prepared generation with T1.nii.gz), LIST. Optional: HDBET_VENV (default $ROOT/venvs/hdbet).
# Output: $ROOT/hdbet/<id>/{brain,brain_mask}.nii.gz. Weights must already be in ~/hd-bet_params (runbook 5.1).
set -euo pipefail
: "${ROOT:?}" "${IN_GEN:?}" "${LIST:?}"
id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST" | cut -f1); out="$ROOT/hdbet/$id"; mkdir -p "$out"
source "${HDBET_VENV:-$ROOT/venvs/hdbet}/bin/activate"
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK
echo "target: $id host: $HOSTNAME"; date
hd-bet -i "$ROOT/prepared/$IN_GEN/$id/T1.nii.gz" -o "$out/brain.nii.gz" -device cpu -mode accurate -tta 0 -pp 1 -s 1
date; ls -la "$out"
