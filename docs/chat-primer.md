We are starting a new MAPER cohort on Arrhenius.

Use the supplied workflow runbook, Arrhenius site profile, and new-cohort
checklist as the established processing framework.

Work checkpoint by checkpoint. Give literal shell commands where useful.
Before substantial batch processing, test representative cases and state
the expected result. Preserve cohort-specific provenance and QC in the
project tree.

Important established findings:
- geometry normalization, storage reorientation, and centring are distinct;
- v2 uses canonicalize -> reorient -> centre -> N4 -> Pincram -> PosNorm;
- MAPER pair registrations are efficient at 1 thread on Arrhenius;
- fusion needs a larger allocation for memory;
- cached-DOF propagation should be chunked rather than submitted as
  thousands of few-second Slurm jobs;
- collaborator-facing outputs must be restored to original image geometry.
