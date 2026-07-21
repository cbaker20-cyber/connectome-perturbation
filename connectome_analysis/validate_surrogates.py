"""Correlate graph surrogates against CEO-007-shaped firing-rate ground truth.

Loads Modal Controllability ``c_i`` and Path Attenuation ``eta`` from
``results/surrogate_correlations.csv``, extracts motor-neuron firing-rate
deltas (ΔHz) from ``results/sugar_ground_truth/baseline_sugar.parquet`` and
``perturb_*.parquet``, then reports Spearman ``r_s`` and Pearson ``r``.

This is statistical plumbing only. Outputs are marked
``not_interpretable_as_neuroscience`` until full-connectome surrogates are
joined to a provenance-bound CEO-007 run with matching neuron IDs.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from connectome_analysis.graph_surrogates import (
    CLAIM_STATUS,
    build_synthetic_surrogate_fixture,
    compute_surrogate_correlation_rows,
    spearman_rho,
    write_surrogate_correlations_csv,
)
from tools.path_resolver import repo_root_from, require_repo_path

SPIKE_COLUMNS = ("t", "trial", "flywire_id", "exp_name")
DEFAULT_SURROGATE_CSV = "results/surrogate_correlations.csv"
DEFAULT_GROUND_TRUTH_DIR = "results/sugar_ground_truth"
DEFAULT_OUTPUT_CSV = "results/surrogate_vs_ground_truth.csv"
BASELINE_NAME = "baseline_sugar"


def pearson_r(x: Sequence[float], y: Sequence[float]) -> float:
    """Pearson correlation for small deterministic vectors (no SciPy)."""
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if a.shape != b.shape or a.size < 2:
        raise ValueError("x and y must be same-length vectors with length >= 2")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ValueError("x and y must be finite")
    a = a - a.mean()
    b = b - b.mean()
    denom = float(np.sqrt(np.sum(a**2) * np.sum(b**2)))
    if denom == 0.0:
        return float("nan")
    return float(np.sum(a * b) / denom)


def load_surrogate_metrics(
    csv_path: str | Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, dict[str, float]]:
    """Load modal controllability and path attenuation tables from CSV.

    Returns
    -------
    dict
        ``{"modal_controllability": {node_id: c_i}, "path_attenuation_ratio": {group: eta}}``
    """
    root = repo_root_from(repo_root)
    path = require_repo_path(root, root / Path(csv_path), "surrogate correlations csv")
    if not path.is_file():
        raise FileNotFoundError(f"Surrogate correlations not found: {path}")

    modal: dict[str, float] = {}
    attenuation: dict[str, float] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            metric = (row.get("metric") or "").strip()
            key = (row.get("node_or_group") or "").strip()
            if not key:
                continue
            try:
                value = float(row["value"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid surrogate value in {path}: {row!r}") from exc
            if metric == "modal_controllability":
                modal[key] = value
            elif metric == "path_attenuation_ratio":
                attenuation[key] = value

    if not modal and not attenuation:
        raise ValueError(f"No modal_controllability or path_attenuation_ratio rows in {path}")
    return {
        "modal_controllability": modal,
        "path_attenuation_ratio": attenuation,
    }


def per_neuron_firing_rates(df: pd.DataFrame, *, t_run: float = 1.0) -> pd.Series:
    """Mean spike rate (Hz) per ``flywire_id`` across trials."""
    if t_run <= 0:
        raise ValueError("t_run must be positive")
    if df.empty:
        return pd.Series(dtype=float, name="hz")
    required = {"trial", "flywire_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Spike table missing columns: {sorted(missing)}")
    n_trials = int(df["trial"].nunique())
    if n_trials <= 0:
        raise ValueError("Spike table has no trials")
    rates = df.groupby("flywire_id").size().astype(float).div(n_trials * float(t_run))
    rates.name = "hz"
    return rates


def motor_delta_hz(
    baseline_df: pd.DataFrame,
    perturb_df: pd.DataFrame,
    motor_ids: Sequence[int] | None = None,
    *,
    t_run: float = 1.0,
) -> pd.Series:
    """Per-motor ΔHz = perturbed_hz - baseline_hz (missing neurons treated as 0 Hz)."""
    base = per_neuron_firing_rates(baseline_df, t_run=t_run)
    pert = per_neuron_firing_rates(perturb_df, t_run=t_run)
    if motor_ids is not None:
        index = pd.Index([int(i) for i in motor_ids], name="flywire_id")
        base = base.reindex(index, fill_value=0.0)
        pert = pert.reindex(index, fill_value=0.0)
        delta = pert - base
    else:
        delta = pert.sub(base, fill_value=0.0)
    delta.name = "delta_hz"
    return delta.sort_index()


def list_perturbation_parquets(results_dir: Path) -> list[Path]:
    """Return sorted ``perturb_*.parquet`` paths under ``results_dir``."""
    return sorted(results_dir.glob("perturb_*.parquet"))


def extract_condition_motor_deltas(
    results_dir: str | Path,
    *,
    baseline_name: str = BASELINE_NAME,
    motor_ids: Sequence[int] | None = None,
    t_run: float = 1.0,
    repo_root: Path | None = None,
) -> pd.DataFrame:
    """Extract population and per-motor motor ΔHz for every perturbation Parquet.

    Parameters
    ----------
    motor_ids
        If provided, restrict ΔHz to these FlyWire IDs. If ``None``, use the
        union of neuron IDs present in baseline and perturbation tables
        (fixture / CEO-007 mini tables often encode motors only).
    """
    root = repo_root_from(repo_root)
    directory = require_repo_path(root, root / Path(results_dir), "sugar ground truth dir")
    baseline_path = directory / f"{baseline_name}.parquet"
    if not baseline_path.is_file():
        raise FileNotFoundError(f"Missing baseline Parquet: {baseline_path}")

    baseline_df = pd.read_parquet(baseline_path)
    rows: list[dict[str, object]] = []
    for perturb_path in list_perturbation_parquets(directory):
        condition = perturb_path.stem  # perturb_<name>
        group = condition.removeprefix("perturb_")
        perturb_df = pd.read_parquet(perturb_path)
        deltas = motor_delta_hz(baseline_df, perturb_df, motor_ids, t_run=t_run)
        # Firing-rate *drops* are positive when activity falls.
        drop = (-deltas).clip(lower=0.0)
        rows.append(
            {
                "condition": condition,
                "group": group,
                "n_motors": int(len(deltas)),
                "motor_delta_hz_sum": float(deltas.sum()),
                "motor_drop_hz_sum": float(drop.sum()),
                "motor_delta_hz_mean": float(deltas.mean()) if len(deltas) else float("nan"),
                "per_motor_delta_hz": {int(k): float(v) for k, v in deltas.items()},
            }
        )
    if not rows:
        raise FileNotFoundError(f"No perturb_*.parquet files under {directory}")
    return pd.DataFrame(rows)


def _align_pairs(
    predicted: dict[str, float],
    actual: dict[str, float],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    keys = sorted(set(predicted) & set(actual))
    if len(keys) < 2:
        return (
            np.asarray([], dtype=float),
            np.asarray([], dtype=float),
            keys,
        )
    x = np.asarray([predicted[k] for k in keys], dtype=float)
    y = np.asarray([actual[k] for k in keys], dtype=float)
    return x, y, keys


def correlation_row(
    *,
    comparison: str,
    predicted_metric: str,
    actual_metric: str,
    predicted: Sequence[float],
    actual: Sequence[float],
    paired_keys: Sequence[str],
    claim_status: str = CLAIM_STATUS,
) -> dict[str, object]:
    """Build one summary row with Spearman and Pearson correlations."""
    x = list(predicted)
    y = list(actual)
    n = len(x)
    if n >= 2:
        rs = spearman_rho(x, y)
        r = pearson_r(x, y)
    else:
        rs = float("nan")
        r = float("nan")
    return {
        "comparison": comparison,
        "predicted_metric": predicted_metric,
        "actual_metric": actual_metric,
        "n_pairs": n,
        "paired_keys": ";".join(str(k) for k in paired_keys),
        "spearman_rs": rs,
        "pearson_r": r,
        "claim_status": claim_status,
    }


def compute_surrogate_vs_ground_truth_rows(
    surrogate_metrics: dict[str, dict[str, float]],
    condition_deltas: pd.DataFrame,
    *,
    claim_status: str = CLAIM_STATUS,
) -> list[dict[str, object]]:
    """Correlate path attenuation / modal controllability with motor drops.

    Pairing rules
    -------------
    - Path attenuation ``eta`` for group ``G`` pairs with condition
      ``perturb_G`` via ``motor_drop_hz_sum`` (predicted attenuation vs actual
      firing-rate drop).
    - Modal controllability ``c_i`` for node ``i`` pairs with condition
      ``perturb_i`` (or ``perturb_node_i``) via ``motor_drop_hz_sum``.
    - Additionally, when per-motor ΔHz are available under a reference
      condition whose group is ``motor_panel``, pair ``c_i`` (string node id)
      with that motor's absolute drop.
    """
    rows: list[dict[str, object]] = []

    drop_by_group = {
        str(row["group"]): float(row["motor_drop_hz_sum"])
        for _, row in condition_deltas.iterrows()
    }

    eta = dict(surrogate_metrics.get("path_attenuation_ratio") or {})
    x_eta, y_eta, keys_eta = _align_pairs(eta, drop_by_group)
    rows.append(
        correlation_row(
            comparison="path_attenuation_vs_motor_drop",
            predicted_metric="path_attenuation_ratio",
            actual_metric="motor_drop_hz_sum",
            predicted=x_eta,
            actual=y_eta,
            paired_keys=keys_eta,
            claim_status=claim_status,
        )
    )

    modal = dict(surrogate_metrics.get("modal_controllability") or {})
    # Accept perturb_<node> and perturb_node_<node> group labels.
    modal_actual: dict[str, float] = {}
    for group, drop in drop_by_group.items():
        key = group.removeprefix("node_")
        if key in modal:
            modal_actual[key] = drop
    x_c, y_c, keys_c = _align_pairs(modal, modal_actual)
    rows.append(
        correlation_row(
            comparison="modal_controllability_vs_motor_drop",
            predicted_metric="modal_controllability",
            actual_metric="motor_drop_hz_sum",
            predicted=x_c,
            actual=y_c,
            paired_keys=keys_c,
            claim_status=claim_status,
        )
    )

    # Optional per-motor panel: condition group "motor_panel" carries per-motor deltas.
    panel = condition_deltas.loc[condition_deltas["group"] == "motor_panel"]
    if not panel.empty:
        per_motor = panel.iloc[0]["per_motor_delta_hz"]
        if isinstance(per_motor, dict) and per_motor:
            motor_drop = {str(k): float(max(-v, 0.0)) for k, v in per_motor.items()}
            x_m, y_m, keys_m = _align_pairs(modal, motor_drop)
            rows.append(
                correlation_row(
                    comparison="modal_controllability_vs_per_motor_drop",
                    predicted_metric="modal_controllability",
                    actual_metric="per_motor_drop_hz",
                    predicted=x_m,
                    actual=y_m,
                    paired_keys=keys_m,
                    claim_status=claim_status,
                )
            )

    # Ground-truth inventory rows (one per condition) for auditability.
    for _, row in condition_deltas.iterrows():
        rows.append(
            {
                "comparison": "ground_truth_condition",
                "predicted_metric": "",
                "actual_metric": "motor_delta_hz_sum",
                "n_pairs": int(row["n_motors"]),
                "paired_keys": str(row["condition"]),
                "spearman_rs": "",
                "pearson_r": "",
                "claim_status": claim_status,
                "motor_delta_hz_sum": float(row["motor_delta_hz_sum"]),
                "motor_drop_hz_sum": float(row["motor_drop_hz_sum"]),
            }
        )
    return rows


def _spike_rows(
    *,
    exp_name: str,
    neuron_rates_hz: dict[int, float],
    n_trials: int,
    t_run: float,
) -> list[dict[str, object]]:
    """Materialize a sparse spike table from target mean rates (deterministic)."""
    rows: list[dict[str, object]] = []
    for trial in range(n_trials):
        for neuron_id, rate in neuron_rates_hz.items():
            n_spikes = int(round(float(rate) * float(t_run)))
            for spike_i in range(max(n_spikes, 0)):
                # Spread spikes evenly in [0, t_run).
                t = (spike_i + 0.5) * (float(t_run) / max(n_spikes, 1))
                rows.append(
                    {
                        "t": float(t),
                        "trial": int(trial),
                        "flywire_id": int(neuron_id),
                        "exp_name": exp_name,
                    }
                )
    if not rows:
        # Keep schema even when a condition abolishes spikes.
        rows.append(
            {
                "t": 0.0,
                "trial": 0,
                "flywire_id": -1,
                "exp_name": exp_name,
            }
        )
    return rows


def write_synthetic_sugar_ground_truth(
    results_dir: str | Path = DEFAULT_GROUND_TRUTH_DIR,
    *,
    repo_root: Path | None = None,
    n_trials: int = 5,
    t_run: float = 1.0,
    seed: int = 57,
) -> Path:
    """Write CEO-007-shaped Parquets aligned to the synthetic surrogate fixture.

    Motor neurons are fixture nodes ``3`` and ``4``. Silencing a gate or node
    reduces motor rates in proportion to that unit's surrogate score so that
    Spearman/Pearson against ``surrogate_correlations.csv`` are well-defined.
    """
    root = repo_root_from(repo_root)
    out_dir = require_repo_path(root, root / Path(results_dir), "sugar ground truth dir")
    out_dir.mkdir(parents=True, exist_ok=True)

    fixture = build_synthetic_surrogate_fixture(seed=seed)
    rows = compute_surrogate_correlation_rows(fixture)
    modal = {
        str(r["node_or_group"]): float(r["value"])
        for r in rows
        if r["metric"] == "modal_controllability"
    }
    eta = {
        str(r["node_or_group"]): float(r["value"])
        for r in rows
        if r["metric"] == "path_attenuation_ratio"
    }
    motors = [int(i) for i in fixture["motor"]]  # type: ignore[arg-type]
    # Baseline spike budget per trial (Hz when t_run==1). Use a large integer
    # budget so rounded spike counts preserve surrogate rank order.
    baseline_spikes = 1000
    baseline_rates = {m: float(baseline_spikes) / float(t_run) for m in motors}
    pd.DataFrame(
        _spike_rows(
            exp_name=BASELINE_NAME,
            neuron_rates_hz=baseline_rates,
            n_trials=n_trials,
            t_run=t_run,
        )
    ).to_parquet(out_dir / f"{BASELINE_NAME}.parquet", index=False)

    def _rates_for_drop_fraction(frac: float) -> dict[int, float]:
        kept = max(0, int(round(baseline_spikes * (1.0 - float(np.clip(frac, 0.0, 1.0))))))
        return {m: float(kept) / float(t_run) for m in motors}

    # Gate lesions: drop fraction equals eta (feeding gate drops more).
    for group, eta_val in eta.items():
        rates = _rates_for_drop_fraction(float(eta_val))
        name = f"perturb_{group}"
        pd.DataFrame(
            _spike_rows(exp_name=name, neuron_rates_hz=rates, n_trials=n_trials, t_run=t_run)
        ).to_parquet(out_dir / f"{name}.parquet", index=False)

    # Node lesions: drop fraction equals |c_i| / max|c|.
    c_vals = np.asarray(list(modal.values()), dtype=float)
    c_max = float(np.max(np.abs(c_vals))) if c_vals.size else 1.0
    c_max = c_max if c_max > 0 else 1.0
    for node, c_i in modal.items():
        frac = abs(float(c_i)) / c_max
        rates = _rates_for_drop_fraction(frac)
        name = f"perturb_{node}"
        pd.DataFrame(
            _spike_rows(exp_name=name, neuron_rates_hz=rates, n_trials=n_trials, t_run=t_run)
        ).to_parquet(out_dir / f"{name}.parquet", index=False)

    # Per-motor panel: encode each motor's own |c_i| as its drop under a panel condition.
    panel_rates: dict[int, float] = {}
    for m in motors:
        frac = abs(float(modal.get(str(m), 0.0))) / c_max
        kept = max(0, int(round(baseline_spikes * (1.0 - frac))))
        panel_rates[m] = float(kept) / float(t_run)
    pd.DataFrame(
        _spike_rows(
            exp_name="perturb_motor_panel",
            neuron_rates_hz=panel_rates,
            n_trials=n_trials,
            t_run=t_run,
        )
    ).to_parquet(out_dir / "perturb_motor_panel.parquet", index=False)

    return out_dir


def write_surrogate_vs_ground_truth_csv(
    output_path: str | Path = DEFAULT_OUTPUT_CSV,
    *,
    surrogate_csv: str | Path = DEFAULT_SURROGATE_CSV,
    ground_truth_dir: str | Path = DEFAULT_GROUND_TRUTH_DIR,
    baseline_name: str = BASELINE_NAME,
    motor_ids: Sequence[int] | None = None,
    t_run: float = 1.0,
    ensure_synthetic_ground_truth: bool = True,
    repo_root: Path | None = None,
) -> Path:
    """Compute correlations and write ``results/surrogate_vs_ground_truth.csv``."""
    root = repo_root_from(repo_root)
    surrogate_path = require_repo_path(root, root / Path(surrogate_csv), "surrogate csv")
    if not surrogate_path.is_file():
        write_surrogate_correlations_csv(surrogate_csv, repo_root=root)

    gt_dir = require_repo_path(root, root / Path(ground_truth_dir), "ground truth dir")
    baseline_path = gt_dir / f"{baseline_name}.parquet"
    if ensure_synthetic_ground_truth and (
        not baseline_path.is_file() or not list_perturbation_parquets(gt_dir)
    ):
        write_synthetic_sugar_ground_truth(ground_truth_dir, repo_root=root, t_run=t_run)

    if motor_ids is None:
        # Default motors for the synthetic fixture; real CEO-007 callers should pass IDs.
        fixture = build_synthetic_surrogate_fixture()
        motor_ids = [int(i) for i in fixture["motor"]]  # type: ignore[arg-type]

    metrics = load_surrogate_metrics(surrogate_csv, repo_root=root)
    condition_deltas = extract_condition_motor_deltas(
        ground_truth_dir,
        baseline_name=baseline_name,
        motor_ids=motor_ids,
        t_run=t_run,
        repo_root=root,
    )
    summary_rows = compute_surrogate_vs_ground_truth_rows(metrics, condition_deltas)

    out = require_repo_path(root, root / Path(output_path), "surrogate vs ground truth output")
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "comparison",
        "predicted_metric",
        "actual_metric",
        "n_pairs",
        "paired_keys",
        "spearman_rs",
        "pearson_r",
        "claim_status",
        "motor_delta_hz_sum",
        "motor_drop_hz_sum",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in summary_rows:
            serialized = {
                key: ("" if value is None else value)
                for key, value in row.items()
                if key in fieldnames
            }
            # Canonicalize floats.
            for key in ("spearman_rs", "pearson_r", "motor_delta_hz_sum", "motor_drop_hz_sum"):
                val = serialized.get(key, "")
                if isinstance(val, float):
                    serialized[key] = "" if not np.isfinite(val) else repr(val)
            writer.writerow(serialized)
    return out


def main(argv: Iterable[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surrogate-csv", default=DEFAULT_SURROGATE_CSV)
    parser.add_argument("--ground-truth-dir", default=DEFAULT_GROUND_TRUTH_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--t-run", type=float, default=1.0)
    parser.add_argument(
        "--no-synthetic-fallback",
        action="store_true",
        help="Fail if CEO-007 Parquets are missing instead of writing the fixture bundle",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    path = write_surrogate_vs_ground_truth_csv(
        args.output,
        surrogate_csv=args.surrogate_csv,
        ground_truth_dir=args.ground_truth_dir,
        t_run=args.t_run,
        ensure_synthetic_ground_truth=not args.no_synthetic_fallback,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
