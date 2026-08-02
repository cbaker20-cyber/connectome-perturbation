"""Differential Vulnerability Index across sugar vs JO sensory contexts (CEO-071B).

Computes motor-population ΔHz for shared silenced target classes under both
sensory drives, forms the signed DVI ratio, assigns dominant context, and
reports Spearman rank correlation of the two effect profiles.

Claim status: not_interpretable_as_neuroscience.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy import stats

from connectome_analysis.graph_surrogates import CLAIM_STATUS
from connectome_analysis.validate_surrogates import (
    extract_provenance,
    load_spike_table,
    motor_delta_hz,
    select_groups_and_jo_ids,
)
from tools.path_resolver import require_repo_path, resolve_input, repo_root_from

LOGGER = logging.getLogger(__name__)

DEFAULT_SUGAR_DIR = "results/sugar_ground_truth"
DEFAULT_JO_DIR = "results/jo_ground_truth"
DEFAULT_OUTPUT = "results/sugar_vs_jo_context_shift.csv"
DEFAULT_MANIFEST = "data/input_manifest.json"
EPS = 1e-6
NEUTRAL_ABS_DVI = 0.1
TARGET_CLASSES = ["AN", "descending", "LO", "Kenyon_Cell", "motor"]

# CEO-071B required output schema (exactly 15 columns).
OUTPUT_COLUMNS = [
    "target_class",
    "delta_hz_sugar",
    "delta_hz_jo",
    "dvi",
    "abs_dvi",
    "dominant_context",
    "n_silenced_sugar",
    "n_silenced_jo",
    "spearman_rs",
    "spearman_p",
    "commit_sha",
    "random_seed",
    "claim_status",
    "epsilon",
    "n_shared_targets",
]


def _setup_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )


def resolve_repo_input(identifier: str, *, manifest_path: str = DEFAULT_MANIFEST, repo_root: Path | None = None) -> Path:
    return resolve_input(identifier, manifest_path=manifest_path, repo_root=repo_root)


def load_output_manifest(results_dir_id: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    path = resolve_repo_input(f"{results_dir_id.rstrip('/')}/output_manifest.json", repo_root=repo_root)
    return json.loads(path.read_text(encoding="utf-8"))


def compute_dvi(delta_sugar: float, delta_jo: float, *, epsilon: float = EPS) -> float:
    """DVI(c) = (Δ_sugar − Δ_JO) / (Δ_sugar + Δ_JO + ε)."""
    return float((delta_sugar - delta_jo) / (delta_sugar + delta_jo + epsilon))


def assign_dominant_context(dvi: float, *, neutral_abs: float = NEUTRAL_ABS_DVI) -> str:
    """Return sugar / jo / neutral from signed DVI."""
    if not np.isfinite(dvi):
        return "neutral"
    if abs(dvi) < neutral_abs:
        return "neutral"
    if dvi > 0:
        return "sugar"
    if dvi < 0:
        return "jo"
    return "neutral"


def detect_baseline_name(results_dir_id: str, *, repo_root: Path | None = None) -> str:
    """Infer baseline parquet stem from output_manifest or directory contents."""
    root = repo_root_from(repo_root)
    results_dir_id = results_dir_id.replace("\\", "/").rstrip("/")
    try:
        manifest = load_output_manifest(results_dir_id, repo_root=root)
        sim = manifest.get("simulation") or {}
        name = sim.get("baseline_exp_name")
        if name:
            return str(name)
    except FileNotFoundError:
        pass
    directory = resolve_repo_input(results_dir_id, repo_root=root)
    baselines = sorted(directory.glob("baseline_*.parquet"))
    if not baselines:
        raise FileNotFoundError(f"No baseline_*.parquet under {directory}")
    return baselines[0].stem


def context_motor_deltas(
    results_dir_id: str,
    targets: Sequence[str],
    motor_ids: Sequence[int],
    *,
    t_run_s: float,
    repo_root: Path | None = None,
) -> dict[str, float]:
    results_dir_id = results_dir_id.replace("\\", "/").rstrip("/")
    baseline_name = detect_baseline_name(results_dir_id, repo_root=repo_root)
    baseline = load_spike_table(f"{results_dir_id}/{baseline_name}.parquet", repo_root=repo_root)
    out: dict[str, float] = {}
    for name in targets:
        perturb = load_spike_table(f"{results_dir_id}/perturb_{name}.parquet", repo_root=repo_root)
        out[str(name)] = motor_delta_hz(baseline, perturb, motor_ids, t_run_s=t_run_s)
    return out


def load_n_silenced_from_summary(results_dir_id: str, *, repo_root: Path | None = None) -> dict[str, int]:
    path = resolve_repo_input(
        f"{results_dir_id.rstrip('/')}/perturbation_summary.csv",
        repo_root=repo_root,
    )
    df = pd.read_csv(path)
    if "group" not in df.columns:
        df = df.rename_axis("group").reset_index()
    return {str(r.group): int(r.n_silenced) for r in df.itertuples(index=False)}


def compare_contexts(
    sugar_dir_id: str = DEFAULT_SUGAR_DIR,
    jo_dir_id: str = DEFAULT_JO_DIR,
    *,
    targets: Sequence[str] | None = None,
    epsilon: float = EPS,
    repo_root: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run CEO-071B Task B and return ``(table, metrics)``."""
    root = repo_root_from(repo_root)
    sugar_dir_id = sugar_dir_id.replace("\\", "/").rstrip("/")
    jo_dir_id = jo_dir_id.replace("\\", "/").rstrip("/")
    targets = list(targets or TARGET_CLASSES)

    jo_manifest = load_output_manifest(jo_dir_id, repo_root=root)
    sugar_manifest = load_output_manifest(sugar_dir_id, repo_root=root)
    commit_sha, random_seed = extract_provenance(jo_manifest)
    if not commit_sha:
        commit_sha, _ = extract_provenance(sugar_manifest)
    if random_seed is None:
        _, random_seed = extract_provenance(sugar_manifest)

    jo_sim = jo_manifest.get("simulation") or {}
    sugar_sim = sugar_manifest.get("simulation") or {}
    t_run_jo = float(jo_sim.get("t_run_ms", 1000)) / 1000.0
    t_run_sugar = float(sugar_sim.get("t_run_ms", 1000)) / 1000.0

    LOGGER.info(
        "context_comparison: sugar=%s jo=%s commit_sha=%s random_seed=%s",
        sugar_dir_id,
        jo_dir_id,
        commit_sha,
        random_seed,
    )

    _, _, motor_ids = select_groups_and_jo_ids(repo_root=root)
    sugar_deltas = context_motor_deltas(
        sugar_dir_id, targets, motor_ids, t_run_s=t_run_sugar, repo_root=root
    )
    jo_deltas = context_motor_deltas(
        jo_dir_id, targets, motor_ids, t_run_s=t_run_jo, repo_root=root
    )
    n_sugar = load_n_silenced_from_summary(sugar_dir_id, repo_root=root)
    n_jo = load_n_silenced_from_summary(jo_dir_id, repo_root=root)

    shared = [t for t in targets if t in sugar_deltas and t in jo_deltas]
    if not shared:
        raise ValueError("No shared target classes between sugar and JO contexts")

    delta_sugar_vals = [sugar_deltas[t] for t in shared]
    delta_jo_vals = [jo_deltas[t] for t in shared]
    if len(shared) >= 3:
        rs, p = stats.spearmanr(delta_sugar_vals, delta_jo_vals)
        spearman_rs, spearman_p = float(rs), float(p)
    else:
        spearman_rs = spearman_p = float("nan")

    rows: list[dict[str, Any]] = []
    for name in shared:
        ds = float(sugar_deltas[name])
        dj = float(jo_deltas[name])
        dvi = compute_dvi(ds, dj, epsilon=epsilon)
        rows.append(
            {
                "target_class": name,
                "delta_hz_sugar": ds,
                "delta_hz_jo": dj,
                "dvi": dvi,
                "abs_dvi": abs(dvi),
                "dominant_context": assign_dominant_context(dvi),
                "n_silenced_sugar": int(n_sugar.get(name, 0)),
                "n_silenced_jo": int(n_jo.get(name, 0)),
                "spearman_rs": spearman_rs,
                "spearman_p": spearman_p,
                "commit_sha": commit_sha,
                "random_seed": int(random_seed),
                "claim_status": CLAIM_STATUS,
                "epsilon": float(epsilon),
                "n_shared_targets": int(len(shared)),
            }
        )

    table = pd.DataFrame(rows).sort_values("abs_dvi", ascending=False).reset_index(drop=True)
    table = table[OUTPUT_COLUMNS]
    metrics: dict[str, Any] = {
        "claim_status": CLAIM_STATUS,
        "n_shared_targets": int(len(shared)),
        "spearman_rs": spearman_rs,
        "spearman_p": spearman_p,
        "commit_sha": commit_sha,
        "random_seed": int(random_seed),
        "max_abs_dvi_group": str(table.iloc[0]["target_class"]) if len(table) else "",
        "max_abs_dvi": float(table.iloc[0]["abs_dvi"]) if len(table) else float("nan"),
    }
    return table, metrics


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sugar-dir", default=DEFAULT_SUGAR_DIR)
    parser.add_argument("--jo-dir", default=DEFAULT_JO_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--epsilon", type=float, default=EPS)
    args = parser.parse_args(argv)

    root = repo_root_from()
    table, metrics = compare_contexts(
        args.sugar_dir,
        args.jo_dir,
        epsilon=args.epsilon,
        repo_root=root,
    )
    out_path = require_repo_path(root, root / args.output, "context comparison output")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)

    LOGGER.info("Wrote %s", out_path)
    print(f"Wrote {out_path}")
    print(f"claim_status: {metrics['claim_status']}")
    print(f"commit_sha: {metrics['commit_sha']} random_seed: {metrics['random_seed']}")
    print(
        f"Spearman sugar vs JO rankings: r_s={metrics['spearman_rs']:.4f}, "
        f"p={metrics['spearman_p']:.4g}"
    )
    print(
        f"Max |DVI| group={metrics['max_abs_dvi_group']!r} "
        f"(|DVI|={metrics['max_abs_dvi']:.4f})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
