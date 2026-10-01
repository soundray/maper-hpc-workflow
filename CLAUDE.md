# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Reusable orchestration, Slurm templates, validation tools, and runbooks for
MAPER/Pincram brain-image cohort processing on HPC systems. This is
workflow-level infrastructure only — the MAPER and Pincram software itself
lives in separate repositories and is delivered here as a prebuilt
Apptainer/Singularity container (`maper.sif`).

There is no build, lint, or test tooling in this repo. Content is shell
function libraries and Markdown operational documentation.

## Repository layout

- `lib/` — reusable shell functions sourced into a working shell, not
  executed directly. `lib/arrhenius-shell.sh` defines `mcx` (allocate a
  Slurm CPU worker via `srun` and run a command inside the MAPER Apptainer
  container) and `mx` (run a command in the MAPER container without a Slurm
  allocation, for use on a node that already has one). Both require
  `MAPER_SIF` to be set; `mcx` additionally requires `PROJ`.
- `profiles/` — per-site, empirically validated resource settings (CPU
  counts, chunk sizes) as plain shell variable assignments, e.g.
  `profiles/maper-arrhenius.sh`. These are sourced, not run.
- `sites/` — per-site scheduler/filesystem properties (partition name,
  local scratch path), e.g. `sites/arrhenius.sh`. Project-specific paths
  (`PROJ`, `METS`, `MAPER_SIF`) are deliberately left to the user's
  environment rather than hardcoded here.
- `docs/runbook.md` — the authoritative operational reference: software
  environment, the production preprocessing recipe, Pincram/MAPER
  configuration, resource strategy, caching, and output-geometry
  restoration requirements. Read this before making changes that touch
  processing order, resource allocation, or geometry handling.
- `docs/new-cohort-checklist.md` — step-by-step checklist for onboarding a
  new cohort, mirroring the runbook's production recipe.
- `docs/chat-primer.md` — primer to prime an assistant session with the
  established framework and known findings (v2 pipeline order, threading
  behavior, restoration requirements) when starting new-cohort work.

## Core domain knowledge (do not contradict without explicit evidence)

- Geometry normalization is a set of **distinct** operations: canonicalize
  (header only, sform := qform) → reorient to standard storage orientation
  (RAS/LAS, no interpolation) → centre the voxel grid origin near (0,0,0).
  None of these change voxel values or use interpolation. Resampling
  (downsampling unusually high-resolution input to fit memory/time
  constraints) is a separate, conditional operation, used only when
  needed — not part of the routine canonicalize/reorient/centre sequence.
- Production preprocessing recipe (v2): canonicalize → reorient → centre →
  unmasked default N4 → Pincram → PosNorm.
- MAPER pairwise registration is efficient at ~1 thread on Arrhenius;
  fusion of full-size propagated label images needs a memory-sufficient
  (not just CPU-sufficient) allocation.
- Cached-DOF propagation jobs are individually very short (seconds) and
  must be chunked into grouped Slurm allocations rather than submitted as
  one job per pair.
- Only original Hammers atlases `a1`–`a30` are used for MAPER; `a31`–`a60`
  are mirrored duplicates and must not be used. Pincram uses a separate
  100-atlas IXI atlas set; the two atlas selections are independent of
  each other.
- Collaborator-facing outputs must be restored to the exact original
  input geometry (reverse the storage-orientation transform, reapply the
  original header, no interpolation) before delivery, with qform/sform/
  dimensions/codes verified against the original. Exception: if targets
  were resampled, labels are first nearest-neighbour resampled back to
  the centred native grid (runbook §12.1).
- HD-BET is deliberately excluded from this workflow.
- Pincram's checkpoint/archive (`-pickup`) machinery is legacy and not
  part of the production workflow; treat it as known cruft, not a
  pattern to extend.

When editing docs or scripts, keep them consistent with `docs/runbook.md`
— it is the source of truth for processing order and resource strategy,
and other docs (checklist, primer) are meant to mirror it.
