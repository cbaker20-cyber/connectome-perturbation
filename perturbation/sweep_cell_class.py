from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_PERTURBATION_DIR = Path(__file__).resolve().parent
if str(_PERTURBATION_DIR) not in sys.path:
    sys.path.insert(0, str(_PERTURBATION_DIR))

from analyze import compare_to_baseline
from cell_groups import get_group, load_annotated_sim_neurons
from motor_analysis import motor_impact
from perturb import run_single_perturbation

def run_cell_class_sweep(min_neurons=20, force=False):
    ann = load_annotated_sim_neurons()
    motor_ids = get_group(super_class="motor")
    print(f"Motor neurons to track: {len(motor_ids)}")

    counts = ann.groupby("cell_class")["root_id"].count()
    classes = counts[counts >= min_neurons].index.tolist()
    print(f"Cell classes to test (>={min_neurons} neurons): {len(classes)}")

    results = []
    for i, cc in enumerate(classes):
        exp_name = f"cc_{cc.replace("/", ".").replace(" ", "_")}"
        print(f"[{i+1}/{len(classes)}] {cc} ({counts[cc]} neurons)")

        ids = ann[ann["cell_class"] == cc]["root_id"].tolist()

        try:
            run_single_perturbation(ids, exp_name, force=force)
            r = motor_impact(exp_name, motor_ids)
            r["cell_class"] = cc
            r["n_silenced"] = len(ids)
            results.append(r)

            df = pd.DataFrame(results)
            df.to_csv("results/cell_class_sweep.csv", index=False)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    print("Done. Results in results/cell_class_sweep.csv")
    return pd.DataFrame(results)

if __name__ == "__main__":
    run_cell_class_sweep(min_neurons=20, force=False)
