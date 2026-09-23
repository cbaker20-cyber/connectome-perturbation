#!/usr/bin/env bash
# Submit a four-task array only after setting actual allocation and environment.
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "${SLURM_SUBMIT_DIR:?Submit from the extracted snapshot root}"
: "${CCR_PYTHON:?Set CCR_PYTHON to the absolute environment Python path}"
"$CCR_PYTHON" scripts/pcdr_ccr_transfer.py worker --study "${1:?Smoke study directory required}" --index "${SLURM_ARRAY_TASK_ID:?Array index required}"
