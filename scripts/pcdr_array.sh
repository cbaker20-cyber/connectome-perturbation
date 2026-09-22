#!/usr/bin/env bash
# Submit only after choosing the CCR account/partition and measuring node memory.
# Usage: sbatch --account=... --partition=... --mem=8G --time=00:20:00 \
#   --array=0-LAST%4 scripts/pcdr_array.sh results/pcdr/ccr_singles
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "${SLURM_SUBMIT_DIR:?Submit from the repository root}"
python -m eigencircuits.ccr worker --study "$1" --index "${SLURM_ARRAY_TASK_ID:?}"
