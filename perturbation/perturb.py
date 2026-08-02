from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_PERTURBATION_DIR = Path(__file__).resolve().parent
if str(_PERTURBATION_DIR) not in sys.path:
    sys.path.insert(0, str(_PERTURBATION_DIR))

from model import run_exp  # type: ignore  # noqa: E402
from analyze import compare_to_baseline  # noqa: E402
from baseline import (  # noqa: E402
    DEFAULT_COMPLETENESS_ID,
    DEFAULT_CONNECTIVITY_ID,
    DEFAULT_RESULTS_DIR,
    NEU_SUGAR,
    PARAMS,
    resolve_baseline_inputs,
)


def run_single_perturbation(
    neuron_ids: list[int],
    exp_name: str,
    force: bool = False,
    manifest_path: str = "data/input_manifest.json",
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    connectivity_id: str = DEFAULT_CONNECTIVITY_ID,
    results_dir: str = DEFAULT_RESULTS_DIR,
    n_run: int = 5,
    neu_exc: list[int] | None = None,
) -> None:
    """Run one sensory-input perturbation with manifest-resolved inputs.

    ``neu_exc`` defaults to the sugar sensory set so legacy callers keep working.
    Dual-context sweeps (e.g. Johnston's Organ) pass an alternate excitation list.
    """

    path_comp, path_con = resolve_baseline_inputs(
        completeness_id=completeness_id,
        connectivity_id=connectivity_id,
        manifest_path=manifest_path,
    )
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    params = PARAMS.copy()
    params["n_run"] = n_run
    run_exp(
        exp_name=exp_name,
        neu_exc=list(NEU_SUGAR if neu_exc is None else neu_exc),
        neu_slnc=neuron_ids,
        path_res=results_dir,
        path_comp=str(path_comp),
        path_con=str(path_con),
        params=params,
        n_proc=1,
        force_overwrite=force,
    )


def run_perturbation_sweep(
    groups: dict[str, list[int]],
    force: bool = False,
    manifest_path: str = "data/input_manifest.json",
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    connectivity_id: str = DEFAULT_CONNECTIVITY_ID,
    results_dir: str = DEFAULT_RESULTS_DIR,
    n_run: int = 5,
    neu_exc: list[int] | None = None,
    baseline_name: str = "baseline_sugar",
) -> pd.DataFrame:
    """Run a small perturbation sweep and compare each result to the baseline."""

    results = []
    for group_name, neuron_ids in groups.items():
        exp_name = f"perturb_{group_name}"
        print(f"--- Silencing group: {group_name} ({len(neuron_ids)} neurons) ---")
        run_single_perturbation(
            neuron_ids,
            exp_name,
            force=force,
            manifest_path=manifest_path,
            completeness_id=completeness_id,
            connectivity_id=connectivity_id,
            results_dir=results_dir,
            n_run=n_run,
            neu_exc=neu_exc,
        )
        comparison = compare_to_baseline(
            exp_name,
            baseline_name=baseline_name,
            path_res=results_dir,
        )
        total_delta = comparison["delta_hz"].sum()
        n_affected = (comparison["delta_hz"].abs() > 0.5).sum()
        results.append(
            {
                "group": group_name,
                "n_silenced": len(neuron_ids),
                "total_delta_hz": total_delta,
                "n_neurons_affected": n_affected,
            }
        )
        print(f"    Total firing change: {total_delta:.1f} Hz | Neurons affected: {n_affected}")
    summary = pd.DataFrame(results).set_index("group")
    summary_path = Path(results_dir) / "perturbation_summary.csv"
    summary.to_csv(summary_path)
    print(f"Summary saved to {summary_path}")
    return summary


def build_demo_groups(
    manifest_path: str,
    completeness_id: str,
    connectivity_id: str,
    seed: int,
    group_size: int,
) -> dict[str, list[int]]:
    """Build deterministic toy-sized random groups from the manifest-resolved completeness table."""

    path_comp, _ = resolve_baseline_inputs(
        completeness_id=completeness_id,
        connectivity_id=connectivity_id,
        manifest_path=manifest_path,
    )
    df = pd.read_csv(path_comp, index_col=0)
    all_ids = [int(x) for x in df.index.tolist()]
    candidates = [i for i in all_ids if i not in set(NEU_SUGAR)]
    rng = np.random.default_rng(seed)
    return {
        "group_A": rng.choice(candidates, group_size, replace=False).astype(int).tolist(),
        "group_B": rng.choice(candidates, group_size, replace=False).astype(int).tolist(),
        "group_C": rng.choice(candidates, group_size, replace=False).astype(int).tolist(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a small manifest-resolved perturbation smoke sweep.")
    parser.add_argument("--manifest", default="data/input_manifest.json")
    parser.add_argument("--completeness-id", default=DEFAULT_COMPLETENESS_ID)
    parser.add_argument("--connectivity-id", default=DEFAULT_CONNECTIVITY_ID)
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--n-run", type=int, default=5)
    parser.add_argument("--group-size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    groups = build_demo_groups(
        manifest_path=args.manifest,
        completeness_id=args.completeness_id,
        connectivity_id=args.connectivity_id,
        seed=args.seed,
        group_size=args.group_size,
    )
    summary = run_perturbation_sweep(
        groups,
        force=args.force,
        manifest_path=args.manifest,
        completeness_id=args.completeness_id,
        connectivity_id=args.connectivity_id,
        results_dir=args.results_dir,
        n_run=args.n_run,
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
