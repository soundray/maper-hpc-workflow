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

HD-BET is not part of the default recipe and is not in the container. It is a documented fallback for target
masks when Pincram masks are poor (section 5.1), and then the basis of a numeric ICV estimate (section 12.3).

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
- confirm with the in-plane power spectrum of a native image (`scripts/inplane-spectrum.py`: a smooth fall to
  Nyquist, with no cliff and flat floor, means no zero-fill).

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

### 4.1 Superior slab artifact (experimental)

Some scanner/software configurations give a slab at the top of the head with compressed contrast: brain signal
falls to about 0.3-0.7 of its value, the background rises about 2x, and the boundary ramps over 6-8 slices at
20-60 mm below the vertex. Default N4 does not correct it, and Pincram then over- or underincludes at the top.

- Detect: `scripts/slab-step.py` (step in the anterior/posterior margin background along S; ratio >= 1.5).
  Best checked against the sagittal montage (`scripts/sagittal-slices.py`, `scripts/render-montage.py`).
- Correct (before N4, after centring): per-slice linear correction anchored on air and on a reference brain
  profile by depth below the vertex, built from the unaffected images of the cohort
  (`scripts/slab-reference.py`, `scripts/slab-correct.py`; jobs `templates/slab-correct-array.sbatch`, then
  `templates/n4-from-file.sbatch`). Images without a slab pass through unchanged. Never apply it after N4.
- Evidence (PARADE, 25 of 82 images): corrected masks followed the brain surface clearly better on visual QC.
  The reference profile is loose within about 18 mm of the vertex, and noise is amplified about 3x in the slab.
  Judge on visual mask QC. Residual inhomogeneity remains visible.

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

### 5.1 HD-BET fallback (poor Pincram masks)

Pincram stays the default. When many Pincram masks are poor and N4 variants do not fix them, use HD-BET masks
instead (PARADE: about 30% poor Pincram masks, mostly overinclusion; no-N4 never better, two-stage N4 better in
2 of 11, worse in 6; HD-BET masks of all 82 images were accepted on visual QC, and MAPER (-tc3) ran correctly from
them). Pincram's "parenchyma" mask also contains central CSF, so the two mask types are similar in kind.

- Install per project, outside the container: venv with CPU `torch` (PyTorch CPU wheel index) and `hd-bet` 1.1
  (PyPI). The five weight files (Zenodo record 2540695) download into `~/hd-bet_params` on first use; fetch
  them once on the login node (`HD_BET.utils.maybe_download_parameters(fold)`, folds 0-4) so batch jobs need no
  network, and record their sha256 and the versions in the cohort provenance.
- Run `templates/hdbet-array.sbatch`: CPU, `-mode accurate -tta 0`, input = the same T1 Pincram would get (N4,
  and slab correction if used). About 45-65 s per image on 8 CPUs. `brain_mask.nii.gz` is uint8 0/1 on the input
  grid.
- For PosNorm and MAPER make a prepared generation with the T1 (hard link) and the HD-BET mask copied as
  `parenchyma.nii.gz`; everything downstream is unchanged.
- HD-BET gives no ICV: see 12.3. Masks are still QC'd visually.

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

Keep fusion out of pair jobs: generate pair commands with `-atlasn` one
higher than the number of sources, then rerun one source's command per
target with the real `-atlasn` in a memory-sufficient allocation. MAPER
reuses the saved pair outputs and only fuses. This avoids out-of-memory
fusions and stale `fusion-semaphore-*` directories.

### 10.1 Registration path: always use -tc3

MAPER defaults to its tc2 path when neither `-tc2` nor `-tc3` is given.
This default is a bug: tc3 is intended. The tc2 path's second stage
registers the CSF map alone. On some targets (pre-neumra: 7 of 10) it
contracts the superior cortex, and the final FFD stage cannot recover.
Stage-by-stage replay (`scripts/maper-stagewise-*.sh`) localized the fault
to that stage. `-tc3` registers CSF together with GM in that stage and does
not show the problem. `-notc` also avoids it, but was slightly worse
inferiorly (cerebellum).

Pass `-tc3` explicitly in every launch list (append it after
`launchlist-gen`) until MAPER's default is fixed.

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

### 12.2 Volume deliverables

When deliverables are regional volumes rather than images, no restoration
is needed. Canonicalization, reorientation, centring and Fourier cropping
preserve physical volume. Measure on the prepared grid, which avoids the
nearest-neighbour step of 12.1.

Per-region volumes before and after tc3 separation, raw (ml) and as a fraction of ICV, wide and long formats:
`scripts/region-volumes.py` (ICV from masks, or numeric with `--icv-table`, 12.3).

The established NeumRA format (`scripts/neumra-format-volumes.py`):

- one row per value present in the MAPER tissue-separated file
  (`labelno` = 121 * tissue class + seg120 label, 0-483; classes BG, CSF,
  GM, WM);
- `vol_mm3` and `vol_mm3_corr` in mm3;
- ICV correction by proportional scaling:
  `vol_mm3 / ICV * reference mean ICV`. The default reference is the 2024
  NeumRA + IXI mean (1481696.297 mm3), which keeps new cohorts comparable
  with earlier exports.
- companion files: whole-brain tissue-class volumes and GM+WM / ICV ratios.

Region names follow the 2023 NeumRA files (`reference/`), including two
spelling quirks, so that new and old exports join cleanly.

### 12.3 ICV when only an HD-BET mask exists

Estimate the ICV numerically: ICV_est = 1.0597 x HD-BET mask volume (`scripts/hdbet-icv-estimate.py`).

The factor is the pooled ratio of manual ICV to HD-BET (1.1, CPU, accurate, TTA off) mask volume in two reference
sets: 62 manually traced ICVs (Klasson et al. 2015; 1.0576, sd 1.7%) and the 100-image IXI Pincram atlas (ICV =
union of two raters; 1.0611, sd 2.2%). Pooled n = 162: mean 1.0597, sd 2.1%, i.e. about 2% (about 30 mL) error
per scan. The two means differ by 0.3% (t = 1.0).

- HD-BET masks lie 98-99% inside the manual ICV (Dice 0.96 unconverted). The manual ICV reaches 7 mm (0-16) lower,
  at the C1 level. Uniform dilation of the HD-BET mask does not reduce the volume scatter (best Dice 0.962 at 1 mm).
  A field of view ending 2 mm below the mask loses at most 0.3% of the ICV.
- Do not estimate the ICV of clipped heads (`mask_touches_fov`, or a small margin and visible clipping).
- Pincram ICV is not a substitute where Pincram masks are poor (PARADE: Pincram ICV / HD-BET median 1.14, sd
  0.074, correlation 0.69, against the reference 1.058).
- Validated on older (MCI) and mixed-age healthy sets only; the brain/ICV ratio depends on CSF space. Check it
  with `scripts/icv-ratio-set.py` when manual ICVs exist for a new population.
- `scripts/neumra-format-volumes.py --icv-table <tsv>` and `scripts/region-volumes.py --icv-table <tsv>` take the numeric ICV instead of ICV masks (TSV with an id
  column and `icv_mm3`, `icv_est_mL` or `icv_mL`; the output `icv` column then holds the estimate). Tested: without
  the option, and with a table of mask-derived ICVs, it reproduces the pre-neumra deliverables byte for byte.

## 13. Provenance and QC

Cohort-specific records normally include:

    target-manifest.tsv
    pincram/v2/QC.tsv
    prepared/v2/provenance/
    maper/config/
    processing-history.md

Use per-file SHA256 checksums for frozen processing products.

### 13.1 QC aids

Visual QC decides; these only help to look. `scripts/mask-qc-tiles.py` and `scripts/render-maskqc.py` (mask
contour on sagittal, coronal and superior axial slices), `scripts/seg-qc-tiles.py` (label overlay),
`scripts/scalp-metrics.py` (fraction of the mask within 6 voxels of the head surface, a rough overinclusion
proxy, weak for moderate cases and blind to underinclusion), `scripts/mask-volumes.py`, `scripts/hdbet-volumes.py`.
Left/right label checks (`scripts/seg-lr-aligned.py`, `templates/align-labels-array.sbatch`) must first apply the
target's PosNorm transform (`mirtk transform-image ... -dofin posnorm.dof.gz -interp NN`): it aligns the estimated
midsagittal plane with the grid-centre plane, and raw storage halves mislead for tilted heads.

## 14. Known issues / deferred work

Pincram contains historical HPC-reliability and checkpointing cruft.

Known areas for future refactoring include:

- removal of obsolete `-pickup` checkpointing;
- simplification of intermediate-file lifetimes;
- improved parallel scheduling;
- Slurm-native decomposition of embarrassingly parallel stages.

These changes should be developed and tested separately from production
cohort processing.

Also open:

- The slab correction (4.1) is validated on one cohort only.
- The HD-BET ICV factor is validated on two reference sets only (12.3).
