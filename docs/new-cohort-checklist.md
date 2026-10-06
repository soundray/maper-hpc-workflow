# New MAPER cohort checklist

Templates referred to below are in `templates/`, tools in `scripts/`.

## Inputs and geometry

- Inventory original images, IDs, mappings, and checksums.
- Select representative normal, difficult, and largest-volume cases.
- Audit qform/sform, orientation, voxel dimensions, and centring
  (`scripts/geometry-audit.py`).
- Look for duplicated voxel data across IDs and for superior-slab contrast artifacts (sagittal montage,
  `scripts/slab-step.py`; runbook 4.1). Record exceptions in the cohort QC flags.
- Check for zero-filled reconstruction (sidecar acquisition vs reconstruction
  matrix; in-plane spectrum). If present, plan a Fourier crop to the acquired
  resolution (runbook 3.4) and record the restoration exception (12.1).

## Target preparation

- Run preprocessing on representatives before batch processing.
- Canonicalize -> reorient -> centre -> [Fourier crop] -> N4
  (`templates/prepare-t1-array.sbatch`).
- Run Pincram on representatives and visually inspect masks
  (`templates/pincram-array.sbatch`; work dir on project storage).
- Batch Pincram only after representative acceptance.
- If many Pincram masks are poor and N4 variants do not help, use the HD-BET fallback (runbook 5.1,
  `templates/hdbet-array.sbatch`) and judge the masks visually.
- Record Pincram visual QC for every target.
- If masks underinclude superior cortex or residual bias is visible, use the
  two-stage N4 option (runbook section 4; `templates/n4-masked-array.sbatch`,
  then Pincram again).
- Remember that MAPER labels stay inside the parenchyma mask: mask
  underinclusion cannot be fixed at the MAPER stage, and coverage metrics
  computed relative to the mask cannot detect it.
- Generate PosNorm transforms (`templates/posnorm-array.sbatch`).
- Freeze/checksum prepared target products.

## MAPER

- Always pass `-tc3`. The default (tc2) path's CSF-only stage contracts
  superior cortex on some cohorts (runbook 10.1).
- Populate MAPER target caches deliberately with one source.
- Validate MAPER resource settings for the current site.
- Run pair registrations with MAPER `-threads 1` and the site profile's
  allocation (2 CPUs on Arrhenius).
- Keep fusion out of pair jobs (`-atlasn` one higher than the number of
  sources), then trigger fusion with a memory-sufficient allocation
  (`templates/maper-launchlist-array.sbatch`).
- For additional source label sets, reuse saved DOFs.
- Chunk very short cached-DOF propagation tasks within Slurm jobs.
- Visually QC fused outputs.

## Outputs

- For image deliverables: restore outputs to the exact original target
  geometry and verify qform, sform, dimensions, and codes against originals.
- For volume deliverables: measure on the prepared grid (preparation is
  volume-preserving); use `scripts/neumra-format-volumes.py` for the NeumRA
  format and ICV correction (runbook 12.2).
- With HD-BET masks there is no ICV mask: estimate it numerically (1.0597 x HD-BET volume,
  `scripts/hdbet-icv-estimate.py`; runbook 12.3; feed the table to `neumra-format-volumes.py --icv-table`). Do not
  estimate it for clipped heads.
- Region volumes: `scripts/region-volumes.py` and `scripts/neumra-format-volumes.py`; verify that every scan's rows
  sum to the field of view and that the two tools agree.
- Create collaborator-facing deliverables with README and checksums.
- Record exceptions and QC flags in the cohort manifest.
