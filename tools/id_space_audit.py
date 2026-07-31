#!/usr/bin/env python3
"""
ID Space Audit / SourceMap Doctor.

This tool diagnoses the exact problem that can make context source sets look
empty: annotations, completeness, source-context files, and connectivity can use
slightly different node spaces, e.g. FlyWire root IDs versus simulator/Brian
indices.

It does not run simulations. It produces small CSVs that tell us which columns
and files overlap, so downstream analyses can use the correct node space.

Outputs:
  results/id_space_audit/id_space_overlap_summary.csv
  results/id_space_audit/context_overlap_by_candidate_space.csv
  results/id_space_audit/id_space_recommendation.txt

Example:
  python tools/id_space_audit.py \
    --connectivity 2023_03_23_connectivity_630_final.parquet \
    --annotations flywire_annotations.tsv \
    --completeness 2023_03_23_completeness_630_final.csv \
    --contexts metadata/source_contexts/source_context_manifest.csv \
    --output-dir results/id_space_audit
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from tools.path_resolver import resolve_input

DEFAULT_ANNOTATIONS_ID = "flywire_annotations.tsv"
DEFAULT_COMPLETENESS_ID = "2023_03_23_completeness_630_final.csv"
DEFAULT_CONNECTIVITY_ID = "2023_03_23_connectivity_630_final.parquet"
DEFAULT_MANIFEST = "data/input_manifest.json"


def numeric_set_from_series(s: pd.Series) -> set[int]:
    vals = pd.to_numeric(s, errors="coerce").dropna()
    if vals.empty:
        return set()
    return set(vals.astype("int64").map(int).tolist())


def parse_id_file(path: str | Path) -> list[int]:
    p = Path(path)
    if not p.exists():
        return []
    text = p.read_text().strip()
    if not text:
        return []
    toks = re.split(r"[\s,;]+", text)
    out: list[int] = []
    for tok in toks:
        if not tok:
            continue
        try:
            out.append(int(tok))
        except ValueError:
            pass
    return out


def load_annotations(path: Path) -> tuple[pd.DataFrame, set[int]]:
    ann = pd.read_csv(path, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError("annotations must contain root_id")
    ann = ann.copy()
    ann["root_id"] = pd.to_numeric(ann["root_id"], errors="coerce")
    ann = ann.dropna(subset=["root_id"])
    ann["root_id"] = ann["root_id"].astype("int64").map(int)
    return ann, set(ann["root_id"].tolist())


def load_completeness_candidate_sets(path: Path) -> dict[str, set[int]]:
    comp = pd.read_csv(path, low_memory=False)
    out: dict[str, set[int]] = {}
    # The CSV index is often the most important ID column, but pandas read_csv
    # without index_col exposes it as the first column when it was saved.
    for col in comp.columns:
        s = numeric_set_from_series(comp[col])
        if len(s) > 0:
            out[f"completeness_col:{col}"] = s
    comp_indexed = pd.read_csv(path, index_col=0, low_memory=False)
    idx = numeric_set_from_series(pd.Series(comp_indexed.index))
    if idx:
        out["completeness_index"] = idx
    return out


def load_connectivity_candidate_sets(path: Path, max_columns: int = 24) -> dict[str, set[int]]:
    con = pd.read_parquet(path)
    out: dict[str, set[int]] = {}
    priority_words = ["id", "index", "pre", "post", "root", "source", "target", "body"]
    cols = []
    for col in con.columns:
        low = str(col).lower()
        if any(w in low for w in priority_words):
            cols.append(col)
    # Keep deterministic and bounded, but include common schema columns first.
    preferred = [
        "Presynaptic_ID", "Postsynaptic_ID", "Presynaptic_Index", "Postsynaptic_Index",
        "pre_root_id", "post_root_id", "pre_pt_root_id", "post_pt_root_id",
        "source", "target", "source_id", "target_id", "pre", "post",
    ]
    ordered = []
    for p in preferred:
        if p in con.columns and p not in ordered:
            ordered.append(p)
    for c in cols:
        if c not in ordered:
            ordered.append(c)
    for col in ordered[:max_columns]:
        s = numeric_set_from_series(con[col])
        if len(s) > 0:
            out[f"connectivity_col:{col}"] = s
    return out


def load_contexts(path: Path) -> tuple[pd.DataFrame, dict[str, set[int]]]:
    manifest = pd.read_csv(path)
    out: dict[str, set[int]] = {}
    for row in manifest.itertuples(index=False):
        name = str(getattr(row, "context_name"))
        mode = str(getattr(row, "mode"))
        p = Path(str(getattr(row, "path")))
        ids = set(parse_id_file(p))
        out[f"context:{name}:{mode}"] = ids
    return manifest, out


def overlap_record(space_name: str, ids: set[int], reference_name: str, ref: set[int]) -> dict[str, object]:
    inter = len(ids & ref)
    return {
        "space_name": space_name,
        "space_n": len(ids),
        "reference_name": reference_name,
        "reference_n": len(ref),
        "overlap_n": inter,
        "overlap_fraction_of_space": inter / len(ids) if ids else 0.0,
        "overlap_fraction_of_reference": inter / len(ref) if ref else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose ID-space overlap across connectome project files.")
    parser.add_argument("--connectivity", default=DEFAULT_CONNECTIVITY_ID)
    parser.add_argument("--annotations", default=DEFAULT_ANNOTATIONS_ID)
    parser.add_argument("--completeness", default=DEFAULT_COMPLETENESS_ID)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--contexts", default="metadata/source_contexts/source_context_manifest.csv")
    parser.add_argument("--output-dir", default="results/id_space_audit")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    annotations_path = resolve_input(args.annotations, manifest_path=args.manifest)
    completeness_path = resolve_input(args.completeness, manifest_path=args.manifest)
    connectivity_path = resolve_input(args.connectivity, manifest_path=args.manifest)

    print("Loading annotations...")
    ann, ann_ids = load_annotations(annotations_path)
    print(f"Annotation root IDs: {len(ann_ids):,}")

    print("Loading completeness candidate spaces...")
    comp_spaces = load_completeness_candidate_sets(completeness_path)
    print(f"Completeness candidate spaces: {len(comp_spaces)}")

    print("Loading connectivity candidate spaces...")
    con_spaces = load_connectivity_candidate_sets(connectivity_path)
    print(f"Connectivity candidate spaces: {len(con_spaces)}")

    print("Loading source contexts...")
    manifest, ctx_spaces = load_contexts(Path(args.contexts))
    print(f"Context files: {len(ctx_spaces)}")

    # Summary overlaps between major spaces and annotations/completeness/context union.
    context_union: set[int] = set()
    for ids in ctx_spaces.values():
        context_union |= ids

    references = {"annotations_root_id": ann_ids, "context_union": context_union}
    references.update({k: v for k, v in comp_spaces.items() if k == "completeness_index" or "root" in k.lower() or "id" in k.lower()})

    rows = []
    all_spaces = {}
    all_spaces.update(comp_spaces)
    all_spaces.update(con_spaces)
    for name, ids in all_spaces.items():
        for ref_name, ref_ids in references.items():
            if name == ref_name:
                continue
            rows.append(overlap_record(name, ids, ref_name, ref_ids))
    summary = pd.DataFrame(rows).sort_values(["reference_name", "overlap_n"], ascending=[True, False])
    summary_path = out / "id_space_overlap_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Context-by-connectivity-space coverage table.
    ctx_rows = []
    for ctx_name, ctx_ids in ctx_spaces.items():
        for space_name, space_ids in con_spaces.items():
            inter = len(ctx_ids & space_ids)
            ctx_rows.append({
                "context_file": ctx_name,
                "context_n": len(ctx_ids),
                "candidate_space": space_name,
                "candidate_space_n": len(space_ids),
                "overlap_n": inter,
                "overlap_fraction_of_context": inter / len(ctx_ids) if ctx_ids else 0.0,
            })
    ctx_df = pd.DataFrame(ctx_rows).sort_values(["context_file", "overlap_n"], ascending=[True, False])
    ctx_path = out / "context_overlap_by_candidate_space.csv"
    ctx_df.to_csv(ctx_path, index=False)

    # Recommendation heuristic: best connectivity spaces for annotations and contexts.
    con_vs_ann = summary[(summary["space_name"].str.startswith("connectivity_col:")) & (summary["reference_name"] == "annotations_root_id")].copy()
    con_vs_ctx = summary[(summary["space_name"].str.startswith("connectivity_col:")) & (summary["reference_name"] == "context_union")].copy()
    best_ann = con_vs_ann.sort_values("overlap_n", ascending=False).head(3)
    best_ctx = con_vs_ctx.sort_values("overlap_n", ascending=False).head(3)

    rec_path = out / "id_space_recommendation.txt"
    with rec_path.open("w", encoding="utf-8") as f:
        f.write("ID Space Audit Recommendation\n")
        f.write("=============================\n\n")
        f.write(f"Annotation root IDs: {len(ann_ids):,}\n")
        f.write(f"Context union IDs: {len(context_union):,}\n\n")
        f.write("Top connectivity columns overlapping annotations:\n")
        if best_ann.empty:
            f.write("  none\n")
        else:
            for r in best_ann.itertuples(index=False):
                f.write(f"  {r.space_name}: overlap {r.overlap_n:,} / {r.reference_n:,} annotations\n")
        f.write("\nTop connectivity columns overlapping source contexts:\n")
        if best_ctx.empty:
            f.write("  none\n")
        else:
            for r in best_ctx.itertuples(index=False):
                f.write(f"  {r.space_name}: overlap {r.overlap_n:,} / {r.reference_n:,} context IDs\n")
        f.write("\nInterpretation rule:\n")
        f.write("  Use the connectivity column pair whose node universe overlaps BOTH annotations and source contexts.\n")
        f.write("  If annotations overlap one space but contexts overlap another, the context files are being written in the wrong ID space.\n")
        f.write("  Do not interpret context-conditioned biological results until this is aligned.\n")

    print(f"Wrote {summary_path}")
    print(f"Wrote {ctx_path}")
    print(f"Wrote {rec_path}")
    print("\nTop connectivity columns overlapping annotations:")
    if best_ann.empty:
        print("  none")
    else:
        print(best_ann[["space_name", "space_n", "overlap_n", "overlap_fraction_of_reference"]].to_string(index=False))
    print("\nTop connectivity columns overlapping context union:")
    if best_ctx.empty:
        print("  none")
    else:
        print(best_ctx[["space_name", "space_n", "overlap_n", "overlap_fraction_of_reference"]].to_string(index=False))


if __name__ == "__main__":
    main()
