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
| neumra-format-volumes.py | regional volumes in the 2024 NeumRA deliverable format, incl. ICV correction (see `--help`) |

The stagewise scripts hard-code the MAPER library path inside the current
container (`/nix/store/...-maper/lib/maper`); update it if the SIF changes.
Reference tables used by `neumra-format-volumes.py` are in `../reference/`.
