#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
# A second Run All must not create two installers or controllers in this folder.
exec 9>.run_all.lock
if ! flock -n 9; then
    echo 'This folder already has an active Run All process. Follow run_all.log.'
    exit 1
fi
module load ccrsoft/2024.04
module load gcccore/13.2.0 python/3.11.5
unset PYTHONPATH PIP_TARGET PIP_PREFIX PIP_USER
export PYTHONNOUSERSITE=1
export PIP_CONFIG_FILE=/dev/null
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
python -c 'import sys; assert sys.version_info[:2] == (3,11), sys.version'
if [ ! -x .fine-venv/bin/python ]; then
    python -m venv .fine-venv
fi
PYTHON="$PWD/.fine-venv/bin/python"
"$PYTHON" -m pip install -r requirements-ccr.txt
"$PYTHON" -m pip check
"$PYTHON" -m pytest -q tests/test_pcdr_fine_sim.py tests/test_pcdr_fine_ccr.py
mkdir -p fine_results
"$PYTHON" -m pip freeze > fine_results/installed-libraries.txt
"$PYTHON" -u scripts/pcdr_fine_ccr.py run --hours 70
