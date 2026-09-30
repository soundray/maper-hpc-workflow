# MAPER HPC processing runbook

## Purpose

Operational workflow for processing T1-weighted MRI cohorts with MAPER on
NAISS Arrhenius.

This document records established processing decisions and validated
operational procedures. Cohort-specific provenance and QC belong in the
cohort project tree.

## 1. Software environment

MAPER is run from:

    /nobackup/proj/disk/metrimorphics0/apps/maper/maper.sif

The container contains MAPER, Pincram, PosNorm, MIRTK, NiftySeg, ANTs,
NiBabel/NumPy, and the local NIfTI geometry utilities.

MIRTK is the registration backend.

HD-BET is deliberately outside this workflow.

## 2. Arrhenius execution

Persistent data live under:

    /nobackup/proj/disk/metrimorphics0/shared/

Transient work uses:

    /scratch/local

`mcx` allocates a Slurm CPU worker and runs commands in the MAPER
container.

The project tree is bind-mounted into the container at the same path.

## 3. Input geometry normalization

These are separate operations.

### 3.1 Header geometry canonicalization

`maper-canonicalize-nifti`:

- voxel data unchanged;
- preserve input qform;
- replace sform with qform;
- preserve qform code;
- set sform code equal to qform code.

This does not repair incorrectly labelled geometry.

### 3.2 Storage orientation

`maper-reorient2std-nifti`:

- no interpolation;
- voxel-axis permutations/flips only;
- positive determinant -> RAS;
- negative determinant -> LAS;
- physical coordinates preserved.

### 3.3 Grid centring

`maper-centre-origin-nifti` places the voxel grid centre at
approximately (0,0,0), without changing voxel values.

This is required for historical MAPER/MIRTK behaviour on images with
substantially displaced origins.

### 3.4 Resampling

If the input images have unusually high resolution, downsampling may
be needed to enable processing within memory and time constraints.

## 4. Production target preprocessing

Current production recipe:

    original T1
      -> canonicalize
      -> storage reorientation
      -> centre origin
      -> unmasked default N4
      -> Pincram
      -> PosNorm

No routine FOV cropping is performed.

A difficult image may be retained with a QC flag rather than forcing the
pipeline to rescue it.

### N4

Use default 3-D N4 parameters unless a documented experiment establishes
otherwise.

Do not generalize special settings from stress-test cases.

## 5. Pincram

Current production configuration:

    levels 3
    atlasn 100
    parallelism chosen according to Arrhenius resource behaviour

Pincram generates:

    parenchyma.nii.gz
    icv.nii.gz

`parenchyma.nii.gz` is the normal MAPER target mask.

`icv.nii.gz` is retained for possible specialised preprocessing.

Masks are visually QC'd before MAPER processing.

### Resource considerations

Pincram is only partly parallel. High `-par` values can increase
allocated CPU-hours without proportional speedup and can increase memory
and scratch pressure.

The Arrhenius implementation exposes substantial node-local scratch
through CPU allocation.

Pincram's historical checkpoint/archive machinery is not part of the
production workflow.

## 6. PosNorm

Generate:

    posnorm -img T1.nii.gz -mask parenchyma.nii.gz \
            -dofout posnorm.dof.gz

## 7. MAPER source/target descriptions

CSV source/target descriptions use:

    id
    mri
    brainmask
    onepad
    pretransformation

Additional columns denote label sets. Label-set names are arbitrary but
correspond to directories under the atlas `seg/` tree.

Source and target PosNorm transforms are supplied separately. MAPER
combines them appropriately for registration.

## 8. Atlas strategy

Only original Hammers atlases `a1` ... `a30` are used.

`a31` ... `a60` are mirrored versions and are not used.

Pincram uses the 100-atlas IXI atlas:

    .../ixi-pincram-atlas-n100-dm

Pincram and MAPER atlas selections are independent.

## 9. MAPER caches

Caches are persistent on project storage.

Source cache:

    cache/g01/source

Target cache:

    cache/g02/target

Populate deliberately rather than relying on opportunistic cache creation.

A cache generation is tied to a specific software/data configuration;
do not assume automatic stale-cache detection is sufficient.

## 10. MAPER resource strategy on Arrhenius

Pairwise MAPER registration is efficient at approximately one thread.

Very short cached-DOF propagation jobs should be grouped into Slurm
allocations rather than submitted one per pair.

Fusion of 30 full-size propagated segmentations needs more memory than a
one-core allocation provides.

Therefore:

    registration/propagation -> 1 CPU
    fusion -> memory-sufficient allocation

Exact resource profiles belong in the Arrhenius site profile.

## 11. Reusing registrations for additional label sets

To transform another source label set after registrations already exist:

- keep the existing MAPER output directory;
- make a source description with the new label-set column;
- regenerate the launch list;
- reuse the existing cached/output DOFs;
- allow MAPER to perform propagation and fusion.

For very short cached propagation tasks, group commands into chunks.

## 12. Output geometry restoration

MAPER operates on the prepared target geometry.

Collaborator-facing segmentations must be restored to the original target
geometry before delivery.

Restoration consists of reversing the storage-orientation transform and
using the original target header.

No interpolation is used.

Before generating deliverables, verify that reversing the prepared
orientation reproduces the original raw voxel array exactly.

Then verify restored qform, sform, dimensions and codes against the
original input.

## 13. Provenance and QC

Cohort-specific records normally include:

    target-manifest.tsv
    pincram/v2/QC.tsv
    prepared/v2/provenance/
    maper/config/
    processing-history.md

Use per-file SHA256 checksums for frozen processing products.

## 14. Known issues / deferred work

Pincram contains historical HPC-reliability and checkpointing cruft.

Known areas for future refactoring include:

- removal of obsolete `-pickup` checkpointing;
- simplification of intermediate-file lifetimes;
- improved parallel scheduling;
- Slurm-native decomposition of embarrassingly parallel stages.

These changes should be developed and tested separately from production
cohort processing.
