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
