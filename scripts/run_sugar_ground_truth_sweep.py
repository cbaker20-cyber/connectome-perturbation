#!/usr/bin/env python3
"""Run a sugar-context ground-truth sweep matched to the JO silencing panel.

Writes artifacts under ``results/sugar_ground_truth/`` using the same
perturbation groups as the JO sweep (AN, descending, LO, Kenyon_Cell, motor)
with sugar sensory excitation (NEU_SUGAR).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.path_resolver import repo_root_from


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-trials", type=int, default=5)
    parser.add_argument("--results-dir", default="results/sugar_ground_truth")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root_from()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if str(root / "perturbation") not in sys.path:
        sys.path.insert(0, str(root / "perturbation"))

    import importlib.util

    from brian2 import Hz, ms
    from model import default_params

    from perturbation.baseline import NEU_SUGAR, run_baseline
    from perturbation.perturb import run_perturbation_sweep

    jo_path = root / "scripts" / "run_jo_sweep.py"
    spec = importlib.util.spec_from_file_location("run_jo_sweep", jo_path)
    assert spec is not None and spec.loader is not None
    jo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = jo
    spec.loader.exec_module(jo)

    results_dir = root / args.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    group_specs = [
        {"name": "AN", "by": "cell_class", "value": "AN"},
        {"name": "descending", "by": "super_class", "value": "descending"},
        {"name": "LO", "by": "cell_class", "value": "LO"},
        {"name": "Kenyon_Cell", "by": "cell_class", "value": "Kenyon_Cell"},
        {"name": "motor", "by": "super_class", "value": "motor"},
    ]
    ann = jo.load_annotations(root / "flywire_annotations.tsv")
    sim_ids = jo.load_sim_ids(root / "2023_03_23_completeness_630_final.csv")
    groups = jo.select_perturbation_groups(ann, sim_ids, group_specs, exclude_ids=set(NEU_SUGAR))

    import perturbation.perturb as perturb_mod

    params = default_params.copy()
    params["n_run"] = int(args.n_trials)
    params["t_run"] = 1000 * ms
    params["r_poi"] = 150 * Hz
    perturb_mod.PARAMS = params

    print(f"Sugar sensory neurons: {len(NEU_SUGAR)}")
    for name, ids in groups.items():
        print(f"  group {name}: {len(ids)} neurons")

    print(f"=== Sugar baseline (n_run={args.n_trials}) ===")
    run_baseline(force=args.force, results_dir=str(results_dir))
    # Rename baseline_sugar.parquet stays as-is; perturb compares against baseline_sugar.

    print(f"=== Sugar perturbation sweep ({len(groups)} groups) ===")
    run_perturbation_sweep(
        groups,
        force=args.force,
        results_dir=str(results_dir),
        n_run=int(args.n_trials),
        neu_exc=list(NEU_SUGAR),
        baseline_name="baseline_sugar",
    )

    manifest = {
        "schema_version": "0.1",
        "run_name": "sugar_ground_truth",
        "context": "feeding_sugar",
        "claim_status": "not_interpretable_as_neuroscience",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": 42,
        "command": "python scripts/run_sugar_ground_truth_sweep.py "
        + " ".join(argv or sys.argv[1:]),
        "simulation": {
            "baseline_exp_name": "baseline_sugar",
            "n_run": int(args.n_trials),
            "t_run_ms": 1000,
            "r_poi_hz": 150,
            "n_sugar_neurons": len(NEU_SUGAR),
            "perturbation_groups": {k: {"n_silenced": len(v)} for k, v in groups.items()},
        },
    }
    (results_dir / "output_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {results_dir / 'output_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
