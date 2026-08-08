"""Rank dynamical motor dHz effects against a structural predictor.

Reads the validated surrogate table
(``results/jo_ground_truth/surrogate_vs_ground_truth.csv``) and adds, for each
JO lesion group, a rank by observed dHz, a rank by a structural predictor
(mean modal controllability), and the rank difference. Pure artifact
comparison: no Brian2 simulation is run.

Ranking conventions:
* ``rank_by_observed_delta_hz``: 1 = most negative dHz (strongest suppression).
* ``rank_by_structural``: 1 = highest mean modal controllability (the ranking
  topology would predict if it predicted dynamics).

Output: ``results/jo_ground_truth/residual_ranking.csv``
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DEFAULT_SURROGATE = "results/jo_ground_truth/surrogate_vs_ground_truth.csv"
DEFAULT_OUTPUT = "results/jo_ground_truth/residual_ranking.csv"
STRUCTURAL_COLUMN = "mean_modal_controllability"
OUTPUT_COLUMNS = [
    "target_class",
    "n_silenced",
    "delta_hz_obs",
    STRUCTURAL_COLUMN,
    "rank_by_observed_delta_hz",
    "rank_by_structural",
    "rank_difference",
    "y_hat_struct",
    "delta_leverage",
]


def main() -> int:
    surrogate_csv = Path(DEFAULT_SURROGATE)
    if not surrogate_csv.is_file():
        print(f"Missing input artifact: {surrogate_csv}")
        return 1

    table = pd.read_csv(surrogate_csv)
    required = {"target_class", "delta_hz_obs", STRUCTURAL_COLUMN, "y_hat_struct", "delta_leverage"}
    missing = required - set(table.columns)
    if missing:
        raise ValueError(f"surrogate CSV missing columns: {sorted(missing)}")

    table["rank_by_observed_delta_hz"] = table["delta_hz_obs"].rank(method="min", ascending=True).astype(int)
    table["rank_by_structural"] = table[STRUCTURAL_COLUMN].rank(method="min", ascending=False).astype(int)
    table["rank_difference"] = table["rank_by_structural"] - table["rank_by_observed_delta_hz"]

    out = table[OUTPUT_COLUMNS].sort_values("rank_by_observed_delta_hz").reset_index(drop=True)
    out_path = Path(DEFAULT_OUTPUT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print("\n=== Residual / ranking comparison (metric: mean modal controllability) ===")
    display = [
        "target_class", "delta_hz_obs", STRUCTURAL_COLUMN,
        "rank_by_observed_delta_hz", "rank_by_structural", "rank_difference", "delta_leverage",
    ]
    print(out[display].to_string(index=False))

    rho, p = stats.spearmanr(out["rank_by_observed_delta_hz"], out["rank_by_structural"])
    print(f"\nSpearman(observed rank, structural rank): rho={rho:.3f}, p={p:.3f} (n={len(out)})")
    print(f"Mean |rank difference|: {np.abs(out['rank_difference']).mean():.2f}")
    max_diff = out["rank_difference"].abs().idxmax()
    print(f"Max rank difference: {int(out.loc[max_diff, 'rank_difference'])} "
          f"({out.loc[max_diff, 'target_class']})")
    print(f"\nSaved to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
