#!/bin/bash
#SBATCH --job-name=pincram
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=03:00:00
# Required: ROOT, IN_GEN (prepared generation holding T1.nii.gz), OUT_GEN (pincram generation), LIST
# Settings per profiles/maper-arrhenius.sh: levels 3, atlasn 100, -par 4, 8 CPUs. Work dir on project storage
# (node-local scratch of 8 CPUs is too small at ~0.75 mm: ~80 GB peak).
set -euo pipefail
: "${ROOT:?}" "${IN_GEN:?}" "${OUT_GEN:?}" "${LIST:?}"
METS=${METS:-/nobackup/proj/disk/metrimorphics0}; MAPER_SIF=${MAPER_SIF:-$METS/apps/maper/maper.sif}
ATLAS=${PINCRAM_ATLAS:-$METS/shared/reference/ixi-pincram-atlas-n100-dm}
id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST" | cut -f1); [[ -n "${id:-}" ]] || { echo "No target" >&2; exit 1; }
input="$ROOT/prepared/$IN_GEN/$id/T1.nii.gz"; result="$ROOT/pincram/$OUT_GEN/${id}-n100"
[[ -s "$input" ]] || { echo "Missing input: $input" >&2; exit 1; }
[[ ! -e "$result" ]] || { echo "Result directory already exists: $result" >&2; exit 1; }
mkdir -p "$ROOT/pincram/work"; work=$(mktemp -d "$ROOT/pincram/work/${id}-${SLURM_JOB_ID}-XXXX")
( peak=0; while sleep 60; do u=$(du -sm "$work" 2>/dev/null | cut -f1); (( ${u:-0} > peak )) && peak=$u && echo "$peak" > "$work.peak-MB"; done ) &
mon=$!
trap 'kill $mon 2>/dev/null || true; echo "peak work dir usage (MB): $(cat "$work.peak-MB" 2>/dev/null)"; rm -rf "$work" "$work.peak-MB"' EXIT
echo "target: $id  input: $input  result: $result  host: $HOSTNAME"
srun apptainer exec --cleanenv --bind "$METS:$METS" --env TMPDIR="$work" "$MAPER_SIF" \
  pincram "$input" -atlas "$ATLAS" -result "$result" -workdir "$work" -levels 3 -atlasn 100 -par 4
