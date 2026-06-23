#!/usr/bin/env python3
"""
Rank motor neurons by response to a perturbation experiment.

This is a curation helper for the BORA workflow. It does not define final
feeding/grooming targets automatically. Instead, it exports motor neurons whose
firing decreases or increases under a chosen perturbation so the user can review
candidate output modules with evidence.

Default experiment: hq_AN
Default baseline: baseline_sugar
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "perturbation")

from analyze import compare_to_baseline  # noqa: E402


def load_annotations(path: str | Path) -> pd.DataFrame:
    ann = pd.read_csv(path, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError(f"Annotation file lacks root_id column. Columns: {list(ann.columns)}")
    ann = ann.copy()
    ann["root_id"] = pd.to_numeric(ann["root_id"], errors="coerce")
    ann = ann.dropna(subset=["root_id"])
    ann["root_id"] = ann["root_id"].astype("int64")
    return ann


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank motor neurons by perturbation response.")
    parser.add_argument("--exp-name", default="hq_AN", help="Perturbation experiment name, without .parquet")
    parser.add_argument("--baseline-name", default="baseline_sugar", help="Baseline experiment name, without .parquet")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--output-dir", default="metadata")
    parser.add_argument("--threshold-hz", type=float, default=0.5)
    parser.add_argument("--top-n", type=int, default=25)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ann = load_annotations(args.annotations)
    motor = ann[ann["super_class"].astype(str).str.lower().eq("motor")].copy()
    motor_ids = set(motor["root_id"].astype("int64").tolist())

    comp = compare_to_baseline(args.exp_name, baseline_name=args.baseline_name)
    comp = comp.reset_index().rename(columns={"index": "root_id", "flywire_id": "root_id"})
    if "root_id" not in comp.columns:
        comp = comp.rename(columns={comp.columns[0]: "root_id"})
    comp["root_id"] = pd.to_numeric(comp["root_id"], errors="coerce")
    comp = comp.dropna(subset=["root_id"])
    comp["root_id"] = comp["root_id"].astype("int64")

    motor_comp = comp[comp["root_id"].isin(motor_ids)].copy()

    keep_cols = [
        c for c in [
            "root_id", "super_class", "cell_class", "cell_type", "hemibrain_type",
            "ito_lee_hemilineage", "side", "nerve", "flow", "top_nt", "tag", "description"
        ]
        if c in motor.columns
    ]
    annotated = motor_comp.merge(
        motor[keep_cols].drop_duplicates("root_id"),
        on="root_id",
        how="left",
    )

    annotated = annotated.sort_values("delta_hz")
    all_path = output_dir / f"motor_response_candidates_{args.exp_name}.csv"
    annotated.to_csv(all_path, index=False)

    inhibited = annotated[annotated["delta_hz"] <= -abs(args.threshold_hz)].copy()
    disinhibited = annotated[annotated["delta_hz"] >= abs(args.threshold_hz)].copy()

    inhibited_path = output_dir / f"provisional_feeding_candidates_from_{args.exp_name}_inhibited.csv"
    disinhibited_path = output_dir / f"provisional_grooming_candidates_from_{args.exp_name}_disinhibited.csv"
    inhibited.to_csv(inhibited_path, index=False)
    disinhibited.to_csv(disinhibited_path, index=False)

    # These ID lists are intentionally provisional. Do not copy into the final
    # BORA target files without biological curation.
    inhibited_ids_path = output_dir / f"provisional_feeding_ids_from_{args.exp_name}.txt"
    disinhibited_ids_path = output_dir / f"provisional_grooming_ids_from_{args.exp_name}.txt"

    inhibited.head(args.top_n)["root_id"].astype(str).to_csv(
        inhibited_ids_path, index=False, header=False
    )
    disinhibited.head(args.top_n)["root_id"].astype(str).to_csv(
        disinhibited_ids_path, index=False, header=False
    )

    print(f"Experiment: {args.exp_name}")
    print(f"Motor neurons in annotations: {len(motor_ids)}")
    print(f"Motor neurons present in comparison: {len(motor_comp)}")
    print(f"Inhibited motor candidates <= -{abs(args.threshold_hz)} Hz: {len(inhibited)}")
    print(f"Disinhibited motor candidates >= {abs(args.threshold_hz)} Hz: {len(disinhibited)}")
    print("Most inhibited motor candidates:")
    print(annotated.head(args.top_n)[["root_id", "baseline_hz", "perturbed_hz", "delta_hz", "cell_type", "top_nt"]].to_string(index=False))
    print("\nMost disinhibited motor candidates:")
    print(annotated.tail(args.top_n).sort_values("delta_hz", ascending=False)[["root_id", "baseline_hz", "perturbed_hz", "delta_hz", "cell_type", "top_nt"]].to_string(index=False))
    print("\nWrote:")
    print(f"  {all_path}")
    print(f"  {inhibited_path}")
    print(f"  {disinhibited_path}")
    print(f"  {inhibited_ids_path}")
    print(f"  {disinhibited_ids_path}")
    print("\nNOTE: These are provisional dynamic candidates, not final curated target sets.")


if __name__ == "__main__":
    main()
