We are starting a new MAPER cohort on Arrhenius.

Use the supplied workflow runbook, Arrhenius site profile, and new-cohort
checklist as the established processing framework. Job templates are in
`templates/`, tools in `scripts/`.

Work checkpoint by checkpoint. Give literal shell commands where useful.
Before substantial batch processing, test representative cases and state
the expected result. Preserve cohort-specific provenance and QC in the
project tree.

Important established findings:
- geometry normalization, storage reorientation, and centring are distinct;
- v2 uses canonicalize -> reorient -> centre -> N4 -> Pincram -> PosNorm;
- check for zero-filled high-resolution inputs; Fourier-crop to the acquired
  resolution rather than smoothing/interpolating (ANTs ResampleImageBySpacing
  and MIRTK resample-image were unsuitable);
- a single unmasked N4 can leave centre-bright bias that makes Pincram
  underinclude superior cortex; the two-stage N4 option fixes this;
- MAPER labels follow the parenchyma mask, so judge masks visually; coverage
  metrics relative to the mask cannot detect mask errors;
- always run MAPER with -tc3; its default tc2 path is faulty;
- MAPER pair registrations run at 1 thread, but allocate 2 CPUs per pair for
  memory headroom on Arrhenius;
- fusion needs a larger allocation for memory; keep it out of pair jobs;
- Pincram at ~0.75 mm needs ~80 GB of work space; use project storage;
- cached-DOF propagation should be chunked rather than submitted as
  thousands of few-second Slurm jobs;
- collaborator-facing images must be restored to original image geometry;
  volume deliverables are measured on the prepared grid.

The previous cohort's full record is
`/nobackup/proj/disk/metrimorphics0/shared/projects/pre-neumra/processing-history.md`.
