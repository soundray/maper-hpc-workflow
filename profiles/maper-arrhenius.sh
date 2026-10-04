# Empirically validated MAPER/Pincram settings on Arrhenius

# Pairwise registration: keep MAPER at 1 thread, but allocate 2 CPUs for the
# memory that comes with them (~3 GB per CPU). Some atlas pairs peak near
# 2.8 GB (a28 under -notc) and at 1 CPU they slow down or are OOM-killed.
# pre-neumra (0.75x0.75x1 mm targets): -notc pairs took 7.7 min mean at
# 1 CPU (298 pairs) vs 3.7 min at 2 CPUs (29 pairs), i.e. about the same
# CPU-hours at half the wall time; -tc3 pairs 5.2 min at 2 CPUs (60 pairs).
# Small 2-CPU sample, on one cohort.
MAPER_REG_CPUS=2
MAPER_REG_THREADS=1

# Fusion of 30 full-size propagated label images needs more memory.
MAPER_FUSION_CPUS=8

# Cached-DOF propagation is only a few seconds per pair, so group
# many commands into one Slurm allocation.
MAPER_CACHED_PROPAGATION_CHUNK=100

# Current conservative Pincram setting.
PINCRAM_CPUS=8
PINCRAM_PAR=4

# HD-BET fallback mask (runbook 5.1): CPU mode, -mode accurate -tta 0, about 45-65 s per image at 8 CPUs
# (PARADE, 256x256x176 voxels at ~0.94x0.94x1 mm); memory is not a concern at this size.
HDBET_CPUS=8

# Peak Pincram work-dir usage (atlasn 100, -par 4) is ~75-81 GB per target
# at 320x320x170 voxels (0.75x0.75x1 mm; pre-neumra). This exceeds the
# node-local scratch of an 8-CPU allocation, so put the work dir on project
# storage. Usage scales roughly with target voxel count.
PINCRAM_WORKDIR_GB=80
