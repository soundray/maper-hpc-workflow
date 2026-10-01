# Empirically validated MAPER/Pincram settings on Arrhenius

MAPER_REG_CPUS=1
MAPER_REG_THREADS=1

# Fusion of 30 full-size propagated label images needs more memory.
MAPER_FUSION_CPUS=8

# Cached-DOF propagation is only a few seconds per pair, so group
# many commands into one Slurm allocation.
MAPER_CACHED_PROPAGATION_CHUNK=100

# Current conservative Pincram setting.
PINCRAM_CPUS=8
PINCRAM_PAR=4

# Peak Pincram work-dir usage (atlasn 100, -par 4) is ~75-81 GB per target
# at 320x320x170 voxels (0.75x0.75x1 mm; pre-neumra). This exceeds the
# node-local scratch of an 8-CPU allocation, so put the work dir on project
# storage. Usage scales roughly with target voxel count.
PINCRAM_WORKDIR_GB=80
