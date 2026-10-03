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

See docs/new-cohort-checklist.md for the order of use.
