#!/usr/bin/env python3
"""Verify and combine degree- and distance-matched null results.

Replaces build_q3_q2.py / aggregate_nulls.py / patch_distance.py with one
script that REFUSES to quietly combine bad data. It checks, for every group
in a results directory:

  1. That the null permutations used the same Brian2 trial count as the
     observed baseline/perturbed sweep (an unmatched trial count makes the
     null distribution artificially wide/narrow and biases the comparison).
  2. That enough permutations ran to make a p-value meaningful (floor: 10).

Anything that fails either check is reported as an [ISSUE] and excluded
from the p-value columns of the combined table (mean/std are still shown,
labeled as reference-only).

Usage:
    python scripts/verify_and_combine_nulls.py --results-dir results/jo_ground_truth_n20

Exit code is 1 if any [ISSUE] was found (so this can gate a CI/agent step),
0 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

MIN_PERMS_FOR_P_VALUE = 10


def _load_or_none(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def verify_and_combine(results_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    problems: list[str] = []

    stats_path = results_dir / "statistics.csv"
    stats_df = _load_or_none(stats_path)
    observed_n_trials = None
    if stats_df is None:
        problems.append(f"MISSING: {stats_path} -- cannot verify observed trial count.")
    elif "n_baseline_trials" not in stats_df.columns:
        problems.append(f"{stats_path} has no n_baseline_trials column -- cannot verify.")
    else:
        observed_n_trials = int(stats_df["n_baseline_trials"].iloc[0])

    degree_path = results_dir / "jo_degree_matched_nulls.csv"
    distance_path = results_dir / "jo_distance_matched_nulls.csv"
    degree_df = _load_or_none(degree_path)
    distance_df = _load_or_none(distance_path)
    if degree_df is None:
        problems.append(f"MISSING: {degree_path} -- run scripts/run_degree_matched_nulls.py first.")
    if distance_df is None:
        problems.append(f"MISSING: {distance_path} -- run scripts/run_distance_matched_nulls.py first.")

    for label, df in (("degree", degree_df), ("distance", distance_df)):
        if df is None:
            continue
        if observed_n_trials is not None and "n_trials_per_sim" in df.columns:
            mismatched = df.loc[df["n_trials_per_sim"] != observed_n_trials, "group"].tolist()
            if mismatched:
                problems.append(
                    f"{label}-null n_trials_per_sim != observed n_baseline_trials "
                    f"({observed_n_trials}) for groups: {mismatched}. Their p-values are "
                    "NOT a fair comparison -- rerun those groups with matched trials."
                )
        if "n_permutations" in df.columns:
            thin = df.loc[df["n_permutations"] < MIN_PERMS_FOR_P_VALUE, "group"].tolist()
            if thin:
                problems.append(
                    f"{label}-null below the {MIN_PERMS_FOR_P_VALUE}-permutation floor for "
                    f"groups: {thin}. Their p-values are placeholders, not evidence."
                )

    print("=" * 72)
    print(f"VERIFICATION: {results_dir}")
    print("=" * 72)
    if problems:
        for p in problems:
            print(f"  [ISSUE] {p}")
    else:
        print("  No consistency issues found.")
    print()

    if degree_df is None or distance_df is None:
        print("Cannot build combined table -- see missing files above.")
        return pd.DataFrame(), problems

    def _blank_bad_pvalues(df: pd.DataFrame, label: str) -> pd.DataFrame:
        df = df.copy()
        bad = pd.Series(False, index=df.index)
        if observed_n_trials is not None and "n_trials_per_sim" in df.columns:
            bad |= df["n_trials_per_sim"] != observed_n_trials
        if "n_permutations" in df.columns:
            bad |= df["n_permutations"] < MIN_PERMS_FOR_P_VALUE
        for col in ("empirical_p_one_sided", "empirical_p_two_sided", "z_score"):
            if col in df.columns:
                df.loc[bad, col] = float("nan")
        df["trustworthy"] = ~bad
        return df.add_prefix(f"{label}_").rename(columns={f"{label}_group": "group"})

    merged = _blank_bad_pvalues(degree_df, "degree").merge(
        _blank_bad_pvalues(distance_df, "distance"), on="group", how="outer"
    )
    out_path = results_dir / "null_comparison_verified.csv"
    merged.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
    print(f"\n{merged.to_string(index=False)}")
    return merged, problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=str, required=True,
                         help="e.g. results/jo_ground_truth_n20")
    args = parser.parse_args(argv)
    _, problems = verify_and_combine(Path(args.results_dir))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
