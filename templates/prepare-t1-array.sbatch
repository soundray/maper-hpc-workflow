#!/bin/bash
#SBATCH --job-name=prep-t1
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
# Required: ROOT, GEN (prepared generation, e.g. v1), LIST (id<TAB>source path relative to ROOT)
# Optional: CROP_MM (e.g. 0.75) -> Fourier-crop axes finer than CROP_MM (zero-filled inputs only, runbook 3.4)
# Optional: N4_MODE=none to stop before N4 (e.g. when only the masked second N4 will be used)
set -euo pipefail
: "${ROOT:?}" "${GEN:?}" "${LIST:?}"
METS=${METS:-/nobackup/proj/disk/metrimorphics0}; MAPER_SIF=${MAPER_SIF:-$METS/apps/maper/maper.sif}
TOOLS=${TOOLS:-$METS/apps/maper-hpc-workflow/scripts}
IFS=$'\t' read -r id src_rel _ <<< "$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST")"
[[ -n "${id:-}" && -n "${src_rel:-}" ]] || { echo "Invalid list entry" >&2; exit 1; }
out="$ROOT/prepared/$GEN/$id"; [[ ! -e "$out/T1.nii.gz" ]] || { echo "Output exists: $out/T1.nii.gz" >&2; exit 1; }
mkdir -p "$out/provenance"; tmp=$(mktemp -d /scratch/local/prep-XXXXXX); trap 'rm -rf "$tmp"' EXIT
run() { apptainer exec --cleanenv --bind /scratch/local:/scratch/local --bind "$METS:$METS" \
          --env TMPDIR=/scratch/local --env ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS="$SLURM_CPUS_PER_TASK" "$MAPER_SIF" "$@"; }
echo "target: $id  host: $HOSTNAME"
run maper-canonicalize-nifti  "$ROOT/$src_rel"           "$out/01-canonical.nii.gz"
# maper-reorient2std-nifti can fail its own qform check on oblique images by ~2e-5 (atol 1e-5, float32
# quaternion rounding; pre-neumra EN-dag1). If so: accept 02-reoriented and re-run maper-canonicalize-nifti on it.
run maper-reorient2std-nifti  "$out/01-canonical.nii.gz" "$out/02-reoriented.nii.gz"
run maper-centre-origin-nifti "$out/02-reoriented.nii.gz" "$out/03-centred.nii.gz"
n4in="$out/03-centred.nii.gz"
if [[ -n "${CROP_MM:-}" ]]; then
  run python3 "$TOOLS/fourier-crop.py" "$out/03-centred.nii.gz" "$tmp/fc.nii.gz" "$CROP_MM"
  run maper-centre-origin-nifti "$tmp/fc.nii.gz" "$out/04-resampled.nii.gz"
  n4in="$out/04-resampled.nii.gz"
fi
if [[ "${N4_MODE:-default}" != none ]]; then
  run N4BiasFieldCorrection -d 3 -i "$n4in" -o "[$out/T1.nii.gz,$out/provenance/N4-bias-field.nii.gz]"
fi
echo "$src_rel" > "$out/provenance/source.txt"; (cd "$ROOT" && sha256sum "$src_rel") > "$out/provenance/SOURCE_SHA256SUM"
echo "done: $id"
