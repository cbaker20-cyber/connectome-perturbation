#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
exec 9>.run_all.lock
flock -n 9 || { echo 'An owned launcher already holds this folder lock.'; exit 1; }
test -n "${SLURM_JOB_ID:-}" || { echo 'Use a CCR compute allocation, not a login node.'; exit 1; }
case "$(hostname)" in cpn-*) ;; *) echo 'Not a CCR compute node'; exit 1 ;; esac
module load ccrsoft/2024.04
module load gcccore/13.2.0 python/3.11.5
unset PYTHONPATH PIP_TARGET PIP_PREFIX PIP_USER
export PYTHONNOUSERSITE=1 PIP_CONFIG_FILE=/dev/null
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
REMAINING=$(python -c 'import json,datetime; p=json.load(open("smaller_plan.json")); print(max(0,int((datetime.datetime.fromisoformat(p["deadline_utc"])-datetime.datetime.now(datetime.timezone.utc)).total_seconds())-30))')
test "$REMAINING" -gt 300 || { echo 'Research block expired or too little time remains'; exit 1; }
# The outer deadline also bounds installation; partial files remain if Slurm ends earlier.
timeout --signal=TERM --kill-after=20s "${REMAINING}s" bash -c '
set -euo pipefail
test ! -e smaller_results || { echo "Existing results preserved; do not relaunch this folder"; exit 1; }
python -m venv .smaller-venv
PY="$PWD/.smaller-venv/bin/python"
timeout 600 "$PY" -m pip install -r requirements-ccr.txt
"$PY" -m pip check
"$PY" scripts/pcdr_smaller_pilot.py verify
"$PY" -m pytest -q tests/test_pcdr_smaller_pilot.py
"$PY" -m pip freeze > installed-libraries.txt
"$PY" -u scripts/pcdr_smaller_pilot.py run
'
