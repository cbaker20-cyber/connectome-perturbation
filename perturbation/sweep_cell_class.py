import sys
sys.path.insert(0, "Drosophila_brain_model")
sys.path.insert(0, "perturbation")
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from pathlib import Path
from cell_groups import get_group, load_annotated_sim_neurons
from perturb import run_single_perturbation
from analyze import compare_to_baseline
from motor_analysis import motor_impact

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
