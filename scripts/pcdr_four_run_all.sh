#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
exec 9>.four_run.lock
flock -n 9 || { echo 'This folder already has a running launcher.'; exit 1; }
test -n "${SLURM_JOB_ID:-}" || { echo 'Use the allocated compute session.'; exit 1; }
case "$(hostname)" in cpn-*) ;; *) echo 'Not a CCR compute node'; exit 1 ;; esac
test ! -e four_results || { echo 'Results already exist; preserve them and do not relaunch.'; exit 1; }
module load ccrsoft/2024.04
module load gcccore/13.2.0 python/3.11.5
unset PYTHONPATH PIP_TARGET PIP_PREFIX PIP_USER
export PYTHONNOUSERSITE=1 PIP_CONFIG_FILE=/dev/null
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
python -m venv .four-venv
PY="$PWD/.four-venv/bin/python"
timeout 900 "$PY" -m pip install -r requirements-ccr.txt
"$PY" -m pip check
"$PY" scripts/pcdr_four_trial.py verify
timeout 600 "$PY" -m pytest -q tests/test_pcdr_smaller_pilot.py tests/test_pcdr_four_trial.py --junitxml=remote_tests.xml
"$PY" -m pip freeze > installed-libraries.txt
exec "$PY" -u scripts/pcdr_four_trial.py run
