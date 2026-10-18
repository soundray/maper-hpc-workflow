#!/bin/bash
#SBATCH --job-name=n4-masked-sc
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
# Two-stage N4 (runbook section 4) for this cohort: second N4 on the slab-corrected (pre-N4) image 03-slabcorr, masked with the stage-1 ICV. Project variant of templates/n4-masked-array.sbatch (that one starts from 03-centred and would drop the slab correction).
# Required: ROOT, SRC_GEN (prepared generation holding 03-slabcorr.nii.gz), MASK_GEN (stage-1 pincram generation), OUT_GEN, LIST.
set -euo pipefail
: "${ROOT:?}" "${SRC_GEN:?}" "${MASK_GEN:?}" "${OUT_GEN:?}" "${LIST:?}"
METS=${METS:-/nobackup/proj/disk/metrimorphics0}; MAPER_SIF=${MAPER_SIF:-$METS/apps/maper-sif/maper.sif}
id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$LIST" | cut -f1); [[ -n "${id:-}" ]] || { echo "No target" >&2; exit 1; }
src="$ROOT/prepared/$SRC_GEN/$id"; out="$ROOT/prepared/$OUT_GEN/$id"
[[ ! -e "$out/T1.nii.gz" ]] || { echo "Output exists: $out/T1.nii.gz" >&2; exit 1; }
mkdir -p "$out/provenance"
cp -p "$src/03-slabcorr.nii.gz" "$out/"; in="$out/03-slabcorr.nii.gz"
cp -p "$src/provenance/source.txt" "$src/provenance/SOURCE_SHA256SUM" "$out/provenance/" 2>/dev/null || true
run() { apptainer exec --cleanenv --bind /scratch/local:/scratch/local --bind "$METS:$METS" \
          --env TMPDIR=/scratch/local --env ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS="$SLURM_CPUS_PER_TASK" "$MAPER_SIF" "$@"; }
# Pincram writes 4-D singleton masks with sform code 0; squeeze onto the image grid first.
run python3 - "$ROOT/pincram/$MASK_GEN/${id}-n100/icv.nii.gz" "$in" "$out/provenance/n4-mask-icv.nii.gz" <<'PY'
import sys, nibabel as nib, numpy as np
i=nib.load(sys.argv[1]); t=nib.load(sys.argv[2])
d=(np.asanyarray(i.dataobj).reshape(i.shape[:3])>0).astype(np.uint8)
assert d.shape==t.shape and np.allclose(i.get_qform(), t.get_qform(), atol=1e-4)
o=nib.Nifti1Image(d,t.affine); o.set_qform(t.get_qform(),1); o.set_sform(t.get_qform(),1); nib.save(o,sys.argv[3])
PY
run N4BiasFieldCorrection -d 3 -i "$in" -x "$out/provenance/n4-mask-icv.nii.gz" -o "[$out/T1.nii.gz,$out/provenance/N4-bias-field.nii.gz]"
echo "done: $id"
