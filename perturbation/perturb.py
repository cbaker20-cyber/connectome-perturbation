"""Manifest-resolved sensory-input perturbation sweeps.

Supports sugar ground-truth runs (CEO-007) and dual-context sweeps such as
Johnston's Organ by accepting an optional ``neu_exc`` excitation list.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Bootstrap: make the repository root importable before loading the resolver.
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[1]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from tools.path_resolver import ensure_repo_on_path

_REPO_ROOT = ensure_repo_on_path(Path(__file__))

from analyze import compare_to_baseline  # noqa: E402
from baseline import (  # noqa: E402
    DEFAULT_COMPLETENESS_ID,
    DEFAULT_CONNECTIVITY_ID,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_RESULTS_DIR,
    NEU_SUGAR,
    PARAMS as _BASELINE_PARAMS,
    resolve_baseline_inputs,
    resolve_results_dir,
)
from model import run_exp  # noqa: E402

# Module-level PARAMS so callers (e.g. scripts/run_jo_sweep.py) can rebind
# ``perturb.PARAMS`` before invoking the helpers below.
PARAMS = _BASELINE_PARAMS


def _params_for_run(
    n_run: int | None = None,
    t_run_ms: float | None = None,
    random_seed: int | None = None,
) -> dict:
    """Copy module PARAMS and optionally override trial count/duration/seed."""
    params = PARAMS.copy()
    if n_run is not None:
        params["n_run"] = int(n_run)
    if t_run_ms is not None:
        from brian2 import ms

        params["t_run"] = float(t_run_ms) * ms
    if random_seed is not None:
        params["random_seed"] = int(random_seed)
    return params


def run_single_perturbation(
    neuron_ids: list[int],
    exp_name: str,
    force: bool = False,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    connectivity_id: str = DEFAULT_CONNECTIVITY_ID,
    results_dir: str = DEFAULT_RESULTS_DIR,
    n_run: int | None = None,
    t_run_ms: float | None = None,
    random_seed: int | None = None,
    n_proc: int = 1,
    neu_exc: list[int] | None = None,
) -> Path | None:
    """Run one sensory-input perturbation with manifest-resolved inputs.

    ``neu_exc`` defaults to the sugar sensory set so legacy callers keep working.
    Dual-context sweeps (e.g. Johnston's Organ) pass an alternate excitation list.
    """

    path_comp, path_con = resolve_baseline_inputs(
        completeness_id=completeness_id,
        connectivity_id=connectivity_id,
        manifest_path=manifest_path,
        repo_root=Path(__file__),
    )
    results_path = resolve_results_dir(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    params = _params_for_run(n_run=n_run, t_run_ms=t_run_ms, random_seed=random_seed)
    return run_exp(
        exp_name=exp_name,
        neu_exc=list(NEU_SUGAR if neu_exc is None else neu_exc),
        neu_slnc=neuron_ids,
        path_res=str(results_path),
        path_comp=str(path_comp),
        path_con=str(path_con),
        params=params,
        n_proc=n_proc,
        force_overwrite=force,
    )


def run_perturbation_sweep(
    groups: dict[str, list[int]],
    force: bool = False,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    connectivity_id: str = DEFAULT_CONNECTIVITY_ID,
    results_dir: str = DEFAULT_RESULTS_DIR,
    n_run: int | None = None,
    t_run_ms: float | None = None,
    random_seed: int | None = None,
    n_proc: int = 1,
    neu_exc: list[int] | None = None,
    baseline_name: str = "baseline_sugar",
) -> pd.DataFrame:
    """Run a perturbation sweep and compare each result to the baseline."""

    results_path = resolve_results_dir(results_dir)

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
            results_dir=str(results_path),
            n_run=n_run,
            t_run_ms=t_run_ms,
            random_seed=random_seed,
            n_proc=n_proc,
            neu_exc=neu_exc,
        )
        comparison = compare_to_baseline(
            exp_name,
            baseline_name=baseline_name,
            path_res=results_path,
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
        print(
            f"    Total firing change: {total_delta:.1f} Hz | "
            f"Neurons affected: {n_affected}"
        )
    summary = pd.DataFrame(results).set_index("group")
    summary_path = results_path / "perturbation_summary.csv"
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
    """Build deterministic toy-sized random groups from the completeness table."""

    path_comp, _ = resolve_baseline_inputs(
        completeness_id=completeness_id,
        connectivity_id=connectivity_id,
        manifest_path=manifest_path,
        repo_root=Path(__file__),
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


def build_sugar_ground_truth_groups(
    manifest_path: str,
    completeness_id: str,
    connectivity_id: str,
    seed: int,
    group_size: int | None = None,
) -> dict[str, list[int]]:
    """Build sugar-self positive control plus two size-matched non-sugar controls."""

    size = int(group_size) if group_size is not None else len(NEU_SUGAR)
    path_comp, _ = resolve_baseline_inputs(
        completeness_id=completeness_id,
        connectivity_id=connectivity_id,
        manifest_path=manifest_path,
        repo_root=Path(__file__),
    )
    df = pd.read_csv(path_comp, index_col=0)
    all_ids = [int(x) for x in df.index.tolist()]
    candidates = [i for i in all_ids if i not in set(NEU_SUGAR)]
    rng = np.random.default_rng(seed)
    return {
        "sugar_self": list(NEU_SUGAR),
        "control_A": rng.choice(candidates, size, replace=False).astype(int).tolist(),
        "control_B": rng.choice(candidates, size, replace=False).astype(int).tolist(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a small manifest-resolved perturbation smoke sweep."
    )
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--completeness-id", default=DEFAULT_COMPLETENESS_ID)
    parser.add_argument("--connectivity-id", default=DEFAULT_CONNECTIVITY_ID)
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--n-run", type=int, default=None)
    parser.add_argument("--t-run-ms", type=float, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--group-size", type=int, default=10)
    parser.add_argument("--n-proc", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--ground-truth-groups",
        action="store_true",
        help="Use sugar-self + size-matched controls instead of demo groups",
    )
    args = parser.parse_args(argv)

    if args.ground_truth_groups:
        groups = build_sugar_ground_truth_groups(
            manifest_path=args.manifest,
            completeness_id=args.completeness_id,
            connectivity_id=args.connectivity_id,
            seed=args.seed,
            group_size=args.group_size,
        )
    else:
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
        t_run_ms=args.t_run_ms,
        random_seed=args.seed,
        n_proc=args.n_proc,
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
