#!/usr/bin/env python3
"""
Targeted Context Validation Runner.

Purpose:
    Run a small, explicit, hypothesis-driven Brian2 validation set instead of a
    broad brute-force sweep.

This is the next step after the structural surrogate benchmark. It tests whether
surrogate-prioritized context-target pairs produce actual motor-output changes
in the nonlinear spiking model.

Default validation design:
    contexts: sensory_ascending, mechanosensory, gustatory, sugar
    targets:  AN, brain_motor_neuron

Interpretation:
    - brain_motor_neuron is a positive-control / motor-proximal target.
    - AN is the upstream biological candidate.
    - Any result is preliminary until trial count is increased and seed robustness
      is assessed.

Outputs:
    results/targeted_context_validation/sweep_summary.csv
    results/targeted_context_validation/sweep_run_info.csv
    results/targeted_context_validation/*.parquet

Example:
    python tools/run_targeted_context_validation.py \
      --annotations flywire_annotations.tsv \
      --completeness 2023_03_23_completeness_630_final.csv \
      --connectivity 2023_03_23_connectivity_630_final.parquet \
      --contexts metadata/source_contexts/source_context_manifest.csv \
      --context-mode matched_size \
      --context-names sensory_ascending,mechanosensory,gustatory,sugar \
      --target-names AN,brain_motor_neuron \
      --group-by cell_class \
      --n-run 3 \
      --t-run-ms 1000 \
      --n-proc 1 \
      --output-dir results/targeted_context_validation
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from time import time

import numpy as np
import pandas as pd
from brian2 import ms

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / ""))
from model import run_exp, default_params  # type: ignore


def safe_name(text: str, max_len: int = 80) -> str:
    text = str(text).strip().replace("/", ".")
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:max_len] or "unnamed"


def parse_id_file(path: str | Path) -> list[int]:
    p = Path(path)
    if not p.exists():
        return []
    text = p.read_text().strip()
    if not text:
        return []
    toks = re.split(r"[\s,;]+", text)
    # FlyWire root IDs are 18-digit integers. Never parse through float.
    return [int(t) for t in toks if t]


def load_annotations(annotations: Path, completeness: Path) -> pd.DataFrame:
    ann = pd.read_csv(annotations, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError("annotations must contain root_id")
    comp = pd.read_csv(completeness, index_col=0)
    sim_ids = set(pd.to_numeric(pd.Series(comp.index), errors="coerce").dropna().astype("int64").map(int))
    ann = ann.copy()
    ann["root_id"] = pd.to_numeric(ann["root_id"], errors="coerce")
    ann = ann.dropna(subset=["root_id"])
    ann["root_id"] = ann["root_id"].astype("int64").map(int)
    ann = ann[ann["root_id"].isin(sim_ids)].copy()
    for col in ["super_class", "cell_class", "cell_type", "top_nt"]:
        if col not in ann.columns:
            ann[col] = ""
        ann[col] = ann[col].fillna("").astype(str)
    return ann


def load_contexts(manifest_path: Path, mode: str, context_names: str) -> list[tuple[str, list[int], str]]:
    man = pd.read_csv(manifest_path)
    man = man[man["mode"].astype(str).eq(mode)].copy()
    wanted = [x.strip() for x in context_names.split(",") if x.strip()]
    man = man[man["context_name"].astype(str).isin(set(wanted))].copy()
    order = {name: i for i, name in enumerate(wanted)}
    man["_order"] = man["context_name"].map(order)
    man = man.sort_values("_order")
    contexts: list[tuple[str, list[int], str]] = []
    for row in man.itertuples(index=False):
        p = Path(str(row.path))
        ids = parse_id_file(p)
        contexts.append((str(row.context_name), ids, str(p)))
    return contexts


def select_targets(ann: pd.DataFrame, group_by: str, target_names: str) -> list[tuple[str, list[int]]]:
    target_order = [x.strip() for x in target_names.split(",") if x.strip()]
    a = ann.copy()
    a[group_by] = a[group_by].replace("", "unannotated")
    targets: list[tuple[str, list[int]]] = []
    for target in target_order:
        ids = sorted(set(a.loc[a[group_by].astype(str).eq(target), "root_id"].map(int).tolist()))
        if not ids:
            print(f"WARNING: target {target!r} has 0 IDs for group_by={group_by}; skipping")
            continue
        targets.append((target, ids))
    return targets


def get_motor_ids(ann: pd.DataFrame) -> list[int]:
    motor = ann[ann["super_class"].str.lower().eq("motor")]
    return sorted(set(motor["root_id"].map(int).tolist()))


def rates_for_ids(exp_path: Path, ids: list[int], n_run: int, t_run_s: float) -> pd.Series:
    ids = [int(x) for x in ids]
    if not exp_path.exists():
        raise FileNotFoundError(exp_path)
    df = pd.read_parquet(exp_path)
    if df.empty:
        return pd.Series(0.0, index=pd.Index(ids, name="flywire_id"))
    counts = df[df["flywire_id"].isin(ids)].groupby("flywire_id").size()
    return counts.reindex(pd.Index(ids, name="flywire_id"), fill_value=0).astype(float) / (float(n_run) * float(t_run_s))


def motor_metrics(baseline_path: Path, perturb_path: Path, motor_ids: list[int], n_run: int, t_run_s: float) -> dict[str, float | int]:
    base = rates_for_ids(baseline_path, motor_ids, n_run, t_run_s)
    pert = rates_for_ids(perturb_path, motor_ids, n_run, t_run_s)
    delta = pert - base
    abs_delta = delta.abs()
    top_k = min(10, len(abs_delta))
    return {
        "n_motor_ids": int(len(motor_ids)),
        "mean_abs_motor_delta": float(abs_delta.mean()) if len(abs_delta) else 0.0,
        "l2_motor_delta": float(np.sqrt(np.sum(np.square(delta.to_numpy(dtype=float))))) if len(delta) else 0.0,
        "top10_motor_shift": float(abs_delta.sort_values(ascending=False).head(top_k).sum()) if len(abs_delta) else 0.0,
        "sum_motor_delta": float(delta.sum()) if len(delta) else 0.0,
        "n_motor_affected_abs_gt_0p5": int((abs_delta > 0.5).sum()),
        "n_motor_inhibited_lt_neg_0p5": int((delta < -0.5).sum()),
        "n_motor_disinhibited_gt_0p5": int((delta > 0.5).sum()),
        "strongest_inhibition": float(delta.min()) if len(delta) else 0.0,
        "strongest_disinhibition": float(delta.max()) if len(delta) else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run targeted context-conditioned Brian2 validation.")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--completeness", default="2023_03_23_completeness_630_final.csv")
    parser.add_argument("--connectivity", default="2023_03_23_connectivity_630_final.parquet")
    parser.add_argument("--contexts", default="metadata/source_contexts/source_context_manifest.csv")
    parser.add_argument("--context-mode", default="matched_size")
    parser.add_argument("--context-names", default="sensory_ascending,mechanosensory,gustatory,sugar")
    parser.add_argument("--group-by", default="cell_class", choices=["super_class", "cell_class", "cell_type"])
    parser.add_argument("--target-names", default="AN,brain_motor_neuron")
    parser.add_argument("--n-run", type=int, default=3)
    parser.add_argument("--t-run-ms", type=float, default=1000.0)
    parser.add_argument("--n-proc", type=int, default=1)
    parser.add_argument("--output-dir", default="results/targeted_context_validation")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    start = time()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ann = load_annotations(Path(args.annotations), Path(args.completeness))
    contexts = load_contexts(Path(args.contexts), args.context_mode, args.context_names)
    targets = select_targets(ann, args.group_by, args.target_names)
    motor_ids = get_motor_ids(ann)

    print(f"Annotated simulator neurons: {len(ann):,}")
    print(f"Contexts: {[(c, len(ids)) for c, ids, _ in contexts]}")
    print(f"Targets: {[(t, len(ids)) for t, ids in targets]}")
    print(f"Motor neurons: {len(motor_ids)}")
    print(f"Output dir: {out}")

    params = default_params.copy()
    params["n_run"] = int(args.n_run)
    params["t_run"] = float(args.t_run_ms) * ms
    t_run_s = float(args.t_run_ms) / 1000.0

    summary_rows = []
    for context_name, source_ids, source_path in contexts:
        if not source_ids and context_name != "no_input":
            print(f"Skipping context {context_name}: no source IDs")
            continue
        ctx_safe = safe_name(context_name)
        baseline_exp = f"ctx_{ctx_safe}_intact"
        baseline_path = out / f"{baseline_exp}.parquet"
        print(f"\n=== Context {context_name}: {len(source_ids)} sources ===")
        run_exp(
            exp_name=baseline_exp,
            neu_exc=source_ids,
            neu_slnc=[],
            path_res=out,
            path_comp=args.completeness,
            path_con=args.connectivity,
            params=params,
            n_proc=args.n_proc,
            force_overwrite=args.force,
        )

        for idx, (target_name, target_ids) in enumerate(targets, start=1):
            target_safe = safe_name(target_name)
            exp_name = f"ctx_{ctx_safe}__lesion_{args.group_by}_{target_safe}"
            exp_path = out / f"{exp_name}.parquet"
            print(f"[{idx}/{len(targets)}] {context_name} | lesion {target_name} ({len(target_ids)} neurons)")
            run_exp(
                exp_name=exp_name,
                neu_exc=source_ids,
                neu_slnc=target_ids,
                path_res=out,
                path_comp=args.completeness,
                path_con=args.connectivity,
                params=params,
                n_proc=args.n_proc,
                force_overwrite=args.force,
            )
            try:
                mm = motor_metrics(baseline_path, exp_path, motor_ids, args.n_run, t_run_s)
            except Exception as e:
                print(f"  WARNING: motor metric failed for {exp_name}: {e}")
                mm = {}
            row = {
                "input_context": context_name,
                "context_mode": args.context_mode,
                "source_path": source_path,
                "n_source_ids": len(source_ids),
                "perturbation_group_by": args.group_by,
                "perturbation_target": target_name,
                "n_lesioned": len(target_ids),
                "baseline_exp_name": baseline_exp,
                "perturbation_exp_name": exp_name,
                "n_run": args.n_run,
                "t_run_s": t_run_s,
            }
            row.update(mm)
            summary_rows.append(row)
            pd.DataFrame(summary_rows).to_csv(out / "sweep_summary.csv", index=False)

    elapsed = time() - start
    pd.DataFrame([{
        "annotations": args.annotations,
        "completeness": args.completeness,
        "connectivity": args.connectivity,
        "contexts": args.contexts,
        "context_mode": args.context_mode,
        "context_names": args.context_names,
        "group_by": args.group_by,
        "target_names": args.target_names,
        "n_run": args.n_run,
        "t_run_ms": args.t_run_ms,
        "n_proc": args.n_proc,
        "output_dir": str(out),
        "elapsed_s": elapsed,
        "n_summary_rows": len(summary_rows),
    }]).to_csv(out / "sweep_run_info.csv", index=False)
    print(f"\nDONE. Summary: {out / 'sweep_summary.csv'}")
    print(f"Elapsed seconds: {elapsed:.1f}")


if __name__ == "__main__":
    main()
