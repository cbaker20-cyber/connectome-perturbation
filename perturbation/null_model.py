"""Run same-size random null controls for targeted perturbations.

This module is intentionally conservative: it produces a null distribution for a
named target group under the existing sugar-stimulation pipeline. It does not
solve provenance, path, or biological-interpretation issues by itself.

Primary question:
    Is the target group's disruption larger than same-size random neuron groups?
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from analyze import compare_to_baseline
from baseline import NEU_SUGAR, PARAMS, PATH_RES
from cell_groups import get_group, load_annotated_sim_neurons
from perturb import run_single_perturbation


DEFAULT_THRESHOLD_HZ = 0.5


def effect_scores(comparison: pd.DataFrame, threshold_hz: float = DEFAULT_THRESHOLD_HZ) -> dict[str, float]:
    """Summarize baseline-vs-perturbation change.

    `absolute_total_delta_hz` is the primary null-model score because signed
    positive and negative changes can cancel.
    """

    delta = comparison["delta_hz"].fillna(0)
    return {
        "absolute_total_delta_hz": float(delta.abs().sum()),
        "signed_total_delta_hz": float(delta.sum()),
        "n_neurons_affected": int((delta.abs() > threshold_hz).sum()),
    }


def empirical_p_value(observed: float, null_scores: Iterable[float]) -> float:
    """One-sided empirical p-value with plus-one correction."""

    null = np.asarray(list(null_scores), dtype=float)
    if null.size == 0:
        raise ValueError("null_scores must contain at least one value")
    return float((1 + np.sum(null >= observed)) / (1 + null.size))


def candidate_pool(exclude_ids: set[int]) -> list[int]:
    """Return annotated simulation neurons not in the excluded set."""

    ann = load_annotated_sim_neurons()
    ids = [int(x) for x in ann["root_id"].tolist()]
    return [x for x in ids if x not in exclude_ids]


def sample_same_size_groups(
    pool: list[int],
    group_size: int,
    n_random: int,
    seed: int,
) -> list[list[int]]:
    """Sample same-size random groups without replacement within each group."""

    if group_size <= 0:
        raise ValueError("group_size must be positive")
    if group_size > len(pool):
        raise ValueError("group_size is larger than candidate pool")

    rng = np.random.default_rng(seed)
    return [rng.choice(pool, size=group_size, replace=False).astype(int).tolist() for _ in range(n_random)]


def run_target_and_null(
    target_group_name: str,
    target_ids: list[int],
    n_random: int,
    seed: int,
    force: bool,
    threshold_hz: float,
    n_run: int | None,
) -> pd.DataFrame:
    """Run/load target perturbation and same-size random controls."""

    params_override = None
    if n_run is not None:
        params_override = {"n_run": int(n_run)}
        PARAMS["n_run"] = int(n_run)

    Path(PATH_RES).mkdir(exist_ok=True)

    rows: list[dict[str, float | int | str]] = []

    target_exp = f"null_target_{target_group_name}"
    run_single_perturbation(target_ids, target_exp, force=force, params_override=params_override)
    target_scores = effect_scores(compare_to_baseline(target_exp), threshold_hz=threshold_hz)
    rows.append({
        "kind": "target",
        "name": target_group_name,
        "iteration": 0,
        "n_silenced": len(target_ids),
        **target_scores,
    })

    exclude = set(int(x) for x in target_ids) | set(int(x) for x in NEU_SUGAR)
    pool = candidate_pool(exclude)
    random_groups = sample_same_size_groups(pool, len(target_ids), n_random=n_random, seed=seed)

    for idx, group in enumerate(random_groups, start=1):
        exp_name = f"null_{target_group_name}_same_size_{idx:04d}"
        run_single_perturbation(group, exp_name, force=force, params_override=params_override)
        scores = effect_scores(compare_to_baseline(exp_name), threshold_hz=threshold_hz)
        rows.append({
            "kind": "same_size_random",
            "name": exp_name,
            "iteration": idx,
            "n_silenced": len(group),
            **scores,
        })

    out = pd.DataFrame(rows)
    observed = float(out.loc[out["kind"] == "target", "absolute_total_delta_hz"].iloc[0])
    null_scores = out.loc[out["kind"] == "same_size_random", "absolute_total_delta_hz"]
    p_value = empirical_p_value(observed, null_scores)
    out["primary_score"] = "absolute_total_delta_hz"
    out["empirical_p_value"] = p_value
    out["seed"] = seed
    out["n_random"] = n_random
    out["n_run"] = PARAMS.get("n_run")
    return out


def write_manifest(summary: pd.DataFrame, out_csv: Path, target_group_name: str) -> Path:
    manifest_path = out_csv.with_suffix(".manifest.json")
    manifest = {
        "target_group": target_group_name,
        "summary_csv": str(out_csv),
        "primary_score": "absolute_total_delta_hz",
        "empirical_p_value": float(summary["empirical_p_value"].iloc[0]),
        "n_random": int(summary["n_random"].iloc[0]),
        "n_run": int(summary["n_run"].iloc[0]),
        "interpretation_limit": "Model-predicted same-size random null only; not biological causality.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run same-size random null model for a target group.")
    parser.add_argument("--target-super-class", default="ascending")
    parser.add_argument("--n-random", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threshold-hz", type=float, default=DEFAULT_THRESHOLD_HZ)
    parser.add_argument("--n-run", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--out", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_ids = [int(x) for x in get_group(super_class=args.target_super_class)]
    if not target_ids:
        raise ValueError(f"No neurons found for super_class={args.target_super_class!r}")

    summary = run_target_and_null(
        target_group_name=args.target_super_class,
        target_ids=target_ids,
        n_random=args.n_random,
        seed=args.seed,
        force=args.force,
        threshold_hz=args.threshold_hz,
        n_run=args.n_run,
    )

    out_csv = Path(args.out) if args.out else Path(PATH_RES) / f"null_model_{args.target_super_class}.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_csv, index=False)
    manifest_path = write_manifest(summary, out_csv, args.target_super_class)

    print(summary)
    print(f"Saved null summary to {out_csv}")
    print(f"Saved manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
