# Slurm templates

Cohort-agnostic job scripts for Arrhenius. Each reads its configuration from
environment variables (pass with `sbatch --export=ALL,VAR=value,...`) and
expects the standard cohort layout:

    $ROOT/prepared/<gen>/<id>/   01-canonical, 02-reoriented, 03-centred,
                                 [04-resampled], T1, parenchyma, posnorm.dof.gz
    $ROOT/pincram/<gen>/<id>-n100/
    $ROOT/maper/{config,cache,log,output}/<gen>/

`LIST` is a TSV whose first column is the target id (other columns ignored,
except `prepare-t1-array.sbatch`, which needs `id<TAB>source_relpath`).
Set `--array=1-N` to the number of list lines. Account: `sbatch -A $PROJ`.
Logs: pass `-o`/`-e`, e.g. `-o $ROOT/prepared/v1/log/%x_%A_%a.out`.

| Template | Purpose | Typical allocation |
|---|---|---|
| prepare-t1-array.sbatch | canonicalize -> reorient -> centre -> [Fourier crop] -> N4 | 8 CPUs, 30-60 min |
| pincram-array.sbatch | Pincram, work dir on project storage, peak usage logged | 8 CPUs, 3 h |
| n4-masked-array.sbatch | second-stage N4 (two-stage option, runbook section 4) | 4 CPUs, 30 min |
| posnorm-array.sbatch | PosNorm | 1 CPU, 15 min |
| maper-launchlist-array.sbatch | run line N of a MAPER launch list | 2 CPUs pairs, 8 CPUs fusion |
| hdbet-array.sbatch | HD-BET fallback mask on CPU (runbook 5.1); `HDBET_VENV`, weights in `~/hd-bet_params` | 8 CPUs, ~1 min |
| slab-correct-array.sbatch | experimental slab correction before N4 (runbook 4.1); needs `SLAB_REF` | 2 CPUs, <1 min |
| n4-from-file.sbatch | default N4 on `03-slabcorr.nii.gz` | 4 CPUs, minutes |
| n4-masked-slabcorr-array.sbatch | two-stage N4 variant starting from `03-slabcorr` (the original `n4-masked-array.sbatch` would drop the slab correction) | 4 CPUs, 30 min |
| align-labels-array.sbatch | apply the target PosNorm transform to fused labels (nearest neighbour) for the L/R check | 1 CPU, <1 min |

See docs/new-cohort-checklist.md for the order of use.
