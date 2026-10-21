#!/bin/bash
set -euo pipefail
module load ccrsoft/2024.04
module load gcccore/13.2.0 python/3.11.5
unset PYTHONPATH PIP_TARGET PIP_PREFIX PIP_USER
export PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
cd /user/cbaker4/connectome_four_trial
exec .four-venv/bin/python -u scripts/pcdr_checkpoint_validation.py --out /projects/academic/smuldoon/cbaker4_checkpoint_validation_20261021/run
