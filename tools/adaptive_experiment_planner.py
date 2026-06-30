#!/usr/bin/env python3
"""
Adaptive Connectome Experiment Planner.

This is the first version of the "game-changing" software layer for the project:
it turns partial results into the next best simulations to run.

Instead of brute-forcing every context x perturbation target, this planner reads:
  - source-context manifest,
  - annotation groups,
  - optional context reachability audit,
  - optional perturbation sweep summary,

and recommends the next context-target pairs that should be simulated.

Principle:
  Maximize information per compute-hour.

Current scoring combines:
  1. structural exposure priority,
  2. novelty / not-yet-run priority,
  3. context diversity,
  4. target-size practicality,
  5. optional surprise from observed motor effects when previous runs exist.

Outputs:
  results/adaptive_experiment_planner/adaptive_plan.csv
  results/adaptive_experiment_planner/adaptive_plan_top.txt
  results/adaptive_experiment_planner/adaptive_plan_commands.ps1

Example after fast pilot:
    python tools/adaptive_experiment_planner.py \
      --annotations flywire_annotations.tsv \
      --contexts metadata/source_contexts/source_context_manifest.csv \
      --reachability results/fast_professor_pilot/context_reachability_fast/context_by_cell_type_exposure.csv \
      --sweep-summary results/fast_professor_pilot/tiny_perturbation_sweep/sweep_summary.csv \
      --group-by cell_class \
      --top-n 24 \
      --output-dir results/adaptive_experiment_planner
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


EXPOSURE_SCORES = {
    "Robustly Exposed": 1.00,
    "Weakly Exposed": 0.65,
    "Ambiguous": 0.35,
    "Tonic Active": 0.35,
    "Out-of-Context": 0.05,
}


def load_annotations(path: Path, group_by: str, min_group_size: int) -> pd.DataFrame:
    ann = pd.read_csv(path, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError("annotations must contain root_id")
    if group_by not in ann.columns:
        raise ValueError(f"annotations missing group column: {group_by}")
    ann = ann.copy()
    ann[group_by] = ann[group_by].fillna("").replace("", "unannotated").astype(str)
    counts = ann.groupby(group_by)["root_id"].count().rename("n_lesioned").reset_index()
    counts = counts[counts["n_lesioned"] >= min_group_size].copy()
    counts = counts.rename(columns={group_by: "perturbation_target"})
    return counts


def load_contexts(path: Path, mode: str, context_names: str | None) -> pd.DataFrame:
    manifest = pd.read_csv(path)
    manifest = manifest[manifest["mode"].astype(str).eq(mode)].copy()
    if context_names:
        wanted = {x.strip() for x in context_names.split(",") if x.strip()}
        manifest = manifest[manifest["context_name"].astype(str).isin(wanted)].copy()
    manifest = manifest.rename(columns={"context_name": "input_context", "n_ids": "n_source_ids"})
    return manifest[["input_context", "mode", "path", "n_source_ids"]].copy()


def normalize_series(s: pd.Series, invert: bool = False) -> pd.Series:
    vals = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan)
    if vals.notna().sum() == 0:
        out = pd.Series(0.5, index=s.index)
    else:
        lo = vals.min()
        hi = vals.max()
        if hi == lo:
            out = pd.Series(0.5, index=s.index)
        else:
            out = (vals - lo) / (hi - lo)
            out = out.fillna(0.0)
    return 1.0 - out if invert else out


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan the next most informative context perturbation simulations.")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--contexts", default="metadata/source_contexts/source_context_manifest.csv")
    parser.add_argument("--reachability", default="results/fast_professor_pilot/context_reachability_fast/context_by_cell_type_exposure.csv")
    parser.add_argument("--sweep-summary", default="results/fast_professor_pilot/tiny_perturbation_sweep/sweep_summary.csv")
    parser.add_argument("--context-mode", default="matched_size")
    parser.add_argument("--context-names", default="sugar,gustatory,mechanosensory,visual_projection,sensory_ascending")
    parser.add_argument("--group-by", default="cell_class", choices=["super_class", "cell_class", "cell_type"])
    parser.add_argument("--min-group-size", type=int, default=20)
    parser.add_argument("--top-n", type=int, default=24)
    parser.add_argument("--output-dir", default="results/adaptive_experiment_planner")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    contexts = load_contexts(Path(args.contexts), args.context_mode, args.context_names)
    targets = load_annotations(Path(args.annotations), args.group_by, args.min_group_size)
    if contexts.empty:
        raise ValueError("No contexts available for planning. Run create_source_contexts.py first.")
    if targets.empty:
        raise ValueError("No perturbation targets available. Lower --min-group-size or check annotations.")

    candidates = contexts.assign(_key=1).merge(targets.assign(_key=1), on="_key").drop(columns="_key")

    reach_path = Path(args.reachability)
    if reach_path.exists():
        reach = pd.read_csv(reach_path)
        target_col = args.group_by
        if target_col not in reach.columns and "perturbation_target" in reach.columns:
            target_col = "perturbation_target"
        keep = ["input_context", target_col, "exposure_label", "mean_source_exposure", "fold_vs_null_median", "q_exposure"]
        keep = [c for c in keep if c in reach.columns]
        reach = reach[keep].copy()
        reach = reach.rename(columns={target_col: "perturbation_target"})
        candidates = candidates.merge(reach, on=["input_context", "perturbation_target"], how="left")
    else:
        candidates["exposure_label"] = "Ambiguous"
        candidates["mean_source_exposure"] = np.nan
        candidates["fold_vs_null_median"] = np.nan
        candidates["q_exposure"] = np.nan

    candidates["exposure_label"] = candidates["exposure_label"].fillna("Ambiguous")
    candidates["exposure_priority"] = candidates["exposure_label"].map(EXPOSURE_SCORES).fillna(0.35)
    candidates["fold_priority"] = normalize_series(candidates.get("fold_vs_null_median", pd.Series(np.nan, index=candidates.index)))

    # Prefer groups that are big enough to matter but not so massive that they are trivial or too costly.
    n = pd.to_numeric(candidates["n_lesioned"], errors="coerce").fillna(0)
    log_n = np.log1p(n)
    if log_n.max() == log_n.min():
        candidates["size_practicality"] = 0.5
    else:
        centered = (log_n - log_n.median()).abs()
        candidates["size_practicality"] = 1.0 - normalize_series(centered)

    sweep_path = Path(args.sweep_summary)
    if sweep_path.exists():
        sweep = pd.read_csv(sweep_path)
        done = sweep[["input_context", "perturbation_target"]].drop_duplicates().copy()
        done["already_run"] = True
        candidates = candidates.merge(done, on=["input_context", "perturbation_target"], how="left")
        candidates["already_run"] = candidates["already_run"].fillna(False)

        # If any observed motor effects exist, prioritize contexts/targets near strong effects but avoid exact reruns.
        if "mean_abs_motor_delta" in sweep.columns:
            obs = sweep.copy()
            obs["mean_abs_motor_delta"] = pd.to_numeric(obs["mean_abs_motor_delta"], errors="coerce")
            context_signal = obs.groupby("input_context")["mean_abs_motor_delta"].mean().rename("context_observed_signal").reset_index()
            target_signal = obs.groupby("perturbation_target")["mean_abs_motor_delta"].mean().rename("target_observed_signal").reset_index()
            candidates = candidates.merge(context_signal, on="input_context", how="left")
            candidates = candidates.merge(target_signal, on="perturbation_target", how="left")
        else:
            candidates["context_observed_signal"] = np.nan
            candidates["target_observed_signal"] = np.nan
    else:
        candidates["already_run"] = False
        candidates["context_observed_signal"] = np.nan
        candidates["target_observed_signal"] = np.nan

    candidates["not_yet_run_priority"] = (~candidates["already_run"].astype(bool)).astype(float)
    candidates["context_signal_priority"] = normalize_series(candidates["context_observed_signal"])
    candidates["target_signal_priority"] = normalize_series(candidates["target_observed_signal"])

    # Context diversity bonus: under-sampled contexts get a boost.
    if sweep_path.exists():
        sweep = pd.read_csv(sweep_path)
        counts = sweep.groupby("input_context").size().rename("n_completed_in_context").reset_index()
        candidates = candidates.merge(counts, on="input_context", how="left")
    else:
        candidates["n_completed_in_context"] = 0
    candidates["n_completed_in_context"] = candidates["n_completed_in_context"].fillna(0)
    candidates["context_diversity_priority"] = normalize_series(candidates["n_completed_in_context"], invert=True)

    candidates["adaptive_priority_score"] = (
        0.30 * candidates["not_yet_run_priority"] +
        0.25 * candidates["exposure_priority"] +
        0.15 * candidates["fold_priority"] +
        0.10 * candidates["context_diversity_priority"] +
        0.10 * candidates["size_practicality"] +
        0.05 * candidates["context_signal_priority"] +
        0.05 * candidates["target_signal_priority"]
    )

    candidates = candidates.sort_values(
        ["adaptive_priority_score", "not_yet_run_priority", "exposure_priority", "n_lesioned"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)
    candidates["rank"] = np.arange(1, len(candidates) + 1)

    plan_path = out / "adaptive_plan.csv"
    candidates.to_csv(plan_path, index=False)

    top = candidates.head(args.top_n).copy()
    top_path = out / "adaptive_plan_top.txt"
    with top_path.open("w") as f:
        f.write("Adaptive Connectome Experiment Planner - Top Recommendations\n")
        f.write("=========================================================\n\n")
        for r in top.itertuples(index=False):
            f.write(
                f"#{r.rank}: context={r.input_context} | target={r.perturbation_target} | "
                f"score={r.adaptive_priority_score:.3f} | exposure={r.exposure_label} | "
                f"n_lesioned={r.n_lesioned} | already_run={r.already_run}\n"
            )

    # Create a ready-to-edit command file for the next small batch.
    cmd_path = out / "adaptive_plan_commands.ps1"
    contexts_to_run = ",".join(top["input_context"].drop_duplicates().astype(str).tolist())
    with cmd_path.open("w") as f:
        f.write("# Auto-generated next-batch command.\n")
        f.write("# Review adaptive_plan_top.txt before running.\n\n")
        f.write(".\\.venv\\Scripts\\python tools\\run_context_perturbation_sweep.py `\n")
        f.write("  --annotations flywire_annotations.tsv `\n")
        f.write("  --completeness Drosophila_brain_model\\2023_03_23_completeness_630_final.csv `\n")
        f.write("  --connectivity Drosophila_brain_model\\2023_03_23_connectivity_630_final.parquet `\n")
        f.write("  --contexts metadata\\source_contexts\\source_context_manifest.csv `\n")
        f.write(f"  --context-mode {args.context_mode} `\n")
        f.write(f"  --context-names {contexts_to_run} `\n")
        f.write(f"  --group-by {args.group_by} `\n")
        f.write("  --min-group-size 20 `\n")
        f.write("  --max-targets 24 `\n")
        f.write("  --n-run 3 `\n")
        f.write("  --t-run-ms 1000 `\n")
        f.write("  --n-proc 1 `\n")
        f.write("  --output-dir results\\adaptive_next_batch\n")

    print(f"Candidate pairs: {len(candidates):,}")
    print(f"Wrote full plan: {plan_path}")
    print(f"Wrote top recommendations: {top_path}")
    print(f"Wrote command template: {cmd_path}")
    print(top[["rank", "input_context", "perturbation_target", "adaptive_priority_score", "exposure_label", "n_lesioned", "already_run"]].to_string(index=False))


if __name__ == "__main__":
    main()
