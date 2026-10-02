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

Resampling is conditional and is the only step in target preparation
that interpolates. It runs after centring and before N4; keep the
centred native-resolution image (`03-centred.nii.gz`) because output
restoration depends on it.

Before choosing a method, check whether the high resolution is real or
the result of zero-filled reconstruction:

- compare acquisition and reconstruction matrices in the sidecars
  (e.g. dcm2niix `AcquisitionMatrixPE` / `ReconMatrixPE`);
- confirm with the in-plane power spectrum of a native image.

For zero-filled inputs, Fourier (k-space) cropping to the acquired
resolution is preferred: it keeps the field of view exactly, recovers
the acquired image with negligible loss, and, with a half-voxel phase
shift, keeps the grid centre fixed. Apply NIfTI scaling, write float32
with sform := qform, and clamp Gibbs-ringing negatives to 0 before N4.
Reference implementation: `pre-neumra/scripts/fourier-crop.py`
(800x800 at 0.3 mm in-plane -> 320x320 at 0.75 mm, the acquired
resolution of a 322x336 Philips acquisition).

Methods found unsuitable (pre-neumra):

- ANTs `ResampleImageBySpacing` with smoothing: poor image quality;
- MIRTK `resample-image`: ignores `scl_slope`/`scl_inter`, writes the
  input datatype (integer rounding), and writes 4-D singleton images with
  sform code 0.

Record any resampling, its target grid, and its effect on restoration
in the cohort's `processing-history.md`.

## 4. Production target preprocessing

Current production recipe:

    original T1
      -> canonicalize
      -> storage reorientation
      -> centre origin
      -> [resample, only if needed; see 3.4]
      -> unmasked default N4
      -> Pincram
      -> PosNorm

If bias residue causes mask underinclusion, use the two-stage N4 option
below.

No routine FOV cropping is performed.

A difficult image may be retained with a QC flag rather than forcing the
pipeline to rescue it.

### N4

Use default 3-D N4 parameters unless a documented experiment establishes
otherwise.

Do not generalize special settings from stress-test cases.

### Two-stage N4 (option)

A single unmasked N4 can leave substantial low-frequency bias, for
example centre-bright "blooming" and a darker superior brain. Pincram
then underincludes superior cortex, and MAPER labels follow the mask, so
the underinclusion carries through to the segmentation whatever the
MAPER settings.

Two-stage recipe:

    centred (or resampled) image, uncorrected
      -> unmasked default N4 -> Pincram (stage 1)
      -> default N4 on the *uncorrected* image, masked (-x) with the
         stage-1 Pincram icv.nii.gz -> Pincram (stage 2)
      -> PosNorm

Keep default N4 parameters for the second pass. In pre-neumra, extra
effort (shrink 2, more iterations, full resolution) trended towards
overcorrection with falling WM/GM contrast, and an additional fitting
level clearly flattened tissue contrast. Do not use white-matter
weighting: no WM map exists before MAPER in routine work.

Use it when masks or segmentations show superior underinclusion, or when
the residual bias is visible (e.g. brightness spreading from the centre
as the window is raised). Judge it on visual mask QC, not mask volume.

Cost: one extra Pincram run per target (see the site profile for
work-dir size).

Evidence (pre-neumra, 10 targets): masks grew by 12-73 ml, most at the
superior end, and most where the stage-1 underinclusion was worst. All
masks were accepted on visual QC; one had overinclusions accepted as
harmless. An earlier variant on mubaraq (second N4 applied to the
already-corrected image, judged on two cases by mask only) was not
adopted.

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

Some atlas pairs need close to the memory of a one-core allocation and
slow down or fail there, so pair jobs get a little memory headroom even
though MAPER itself runs single-threaded.

Therefore:

    registration -> MAPER -threads 1; allocation per site profile
                    (memory headroom)
    cached propagation -> chunked, see section 11
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

### 12.1 Exception: resampled targets

If targets were resampled (section 3.4), segmentations live on the
resampled grid and cannot be restored without interpolation. In that
case only:

- first resample labels with nearest-neighbour interpolation from the
  prepared grid onto the centred native grid (`03-centred.nii.gz`);
- then restore as above (reverse storage orientation, original header,
  no further interpolation).

The exact raw-voxel round-trip check still applies to the
orientation/header steps, using the original image. The final qform,
sform, dimension and code checks against the original input are
unchanged. Record the exception in the cohort's `processing-history.md`
and in collaborator-facing notes, since label boundaries are limited by
the resampled grid.

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
