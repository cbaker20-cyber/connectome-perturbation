#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
exec 9>.run_all.lock
flock -n 9 || { echo "A run is already active in this folder. Use the status cell."; exit 1; }
module load ccrsoft/2024.04
module load gcccore/13.2.0 python/3.11.5
unset PYTHONPATH PIP_TARGET PIP_PREFIX PIP_USER
export PYTHONNOUSERSITE=1 PIP_CONFIG_FILE=/dev/null
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
if [ ! -x .pathway-venv/bin/python ]; then python -m venv .pathway-venv; fi
PYTHON="$PWD/.pathway-venv/bin/python"
"$PYTHON" -c 'import hashlib,json,pathlib; m=json.load(open("package_manifest.json")); assert all(hashlib.sha256(pathlib.Path(k).read_bytes()).hexdigest()==v for k,v in m.items()), "Package file changed"'
"$PYTHON" -m pip install -r requirements-ccr.txt
"$PYTHON" -m pip check
"$PYTHON" -m pytest tests -q
mkdir -p pathway_results
"$PYTHON" -m pip freeze > pathway_results/installed-libraries.txt
"$PYTHON" -u scripts/pcdr_pathway_run.py --plan diagnostic_plan.json --out pathway_results --hours 7 --workers 4
