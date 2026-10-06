# Scripts

Standalone tools. Python tools need nibabel/numpy and run inside the MAPER
container: `mx` for quick header-only work, `mcx` (with `MCX_CPUS=4` when
loading several 0.75 mm volumes) or a Slurm job for anything heavier.

| Script | Purpose |
|---|---|
| geometry-audit.py | header audit: dims, voxel size, q/sform codes and agreement, axcodes, grid centre. Args: `"id<TAB>path"` ... |
| fourier-crop.py | k-space crop to the acquired resolution for zero-filled inputs (runbook 3.4). `in out TARGET_MM` |
| flip-storage-x.py | flip voxel storage along axis 0 with compensating affine (LAS <-> RAS, no interpolation) |
| maper-stagewise-tc2-notc.sh | replay MAPER regprop (default tc2 and -notc paths) for one cache pair, keeping every stage's DOF and transformed labels |
| maper-stagewise-tc3.sh | same for the -tc3 path |
| neumra-format-volumes.py | regional volumes in the 2024 NeumRA deliverable format, incl. ICV correction (see `--help`); ICV from masks, or from a numeric table with `--icv-table` (runbook 12.3); `--extra-columns` appends targets-table columns (e.g. `is_paired,pair_status`) |
| region-volumes.py | per-region seg120 volumes, total and per tissue (CSF/GM/WM/unclassified), raw (ml) and as a fraction of ICV; ICV from masks or `--icv-table`; `--extra-columns` appends targets columns to the long TSV. `--final DIR --targets TSV --out DIR` |
| inplane-spectrum.py | in-plane power spectrum per image, to check for zero-filled reconstruction (runbook 3.4). `"id<TAB>path"` ... |
| slab-step.py | detect the superior-slab contrast artifact (runbook 4.1) from the margin background along S. `"id<TAB>path"` ... |
| slab-reference.py | reference brain-signal profile by depth below the vertex, from unaffected images. `out "id<TAB>path"` ... |
| slab-correct.py | experimental per-slice slab correction (before N4). `in out slice-log.tsv [reference.tsv]` |
| sagittal-slices.py, render-montage.py | head-centred sagittal tiles (container) and labelled montage sheets (host, PIL) for visual screening |
| mask-qc-tiles.py, render-maskqc.py | mask contour QC rows (container) and sheets (host, PIL); `MASKTPL` selects other mask paths (pass as `APPTAINERENV_MASKTPL`, `mcx` uses `--cleanenv`) |
| seg-qc-tiles.py | MAPER label overlay QC rows (render with render-maskqc.py) |
| mask-volumes.py, hdbet-volumes.py | mask volumes and extents (Pincram parenchyma/icv; HD-BET masks with grid check) |
| scalp-metrics.py | fraction of mask near the head surface (rough overinclusion proxy), scalp/brain intensity, N4 bias-field ratio |
| seg-lr-aligned.py | left/right label-pair volume check on PosNorm-aligned labels, with robust outlier statistics (align first: `templates/align-labels-array.sbatch`) |
| hdbet-icv-estimate.py | numeric ICV estimate = 1.0597 x HD-BET mask volume, with FOV-clipping flags (runbook 12.3) |
| icv-ratio-set.py | ICV / HD-BET volume ratio, Dice, regression and leave-one-out error on a reference set with manual ICVs |

The stagewise scripts hard-code the MAPER library path inside the current
container (`/nix/store/...-maper/lib/maper`); update it if the SIF changes.
Reference tables used by `neumra-format-volumes.py` are in `../reference/`.
