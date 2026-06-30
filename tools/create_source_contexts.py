#!/usr/bin/env python3
"""
Create source-context ID files for the context-conditional benchmark.

This script creates biologically defined source sets and matched-size exploratory
sets from flywire_annotations.tsv, restricted to neurons present in the simulator
completeness table. It intentionally does NOT force every source context to K=21
as the only analysis mode. Instead it writes:

1. biologically complete context files when an annotation class exists;
2. optional matched-size source files for pilot/debug runs;
3. a manifest describing how each context was generated.

Example:
    python tools/create_source_contexts.py \
        --annotations flywire_annotations.tsv \
        --completeness Drosophila_brain_model/2023_03_23_completeness_630_final.csv \
        --sugar-ids metadata/sugar_ids_21.txt \
        --output-dir metadata/source_contexts \
        --matched-k 21 \
        --seed 13
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def parse_id_file(path: str | Path) -> list[int]:
    p = Path(path)
    if not p.exists():
        return []
    text = p.read_text().strip()
    if not text:
        return []
    tokens = re.split(r"[\s,;]+", text)
    return [int(float(tok)) for tok in tokens if tok]


def write_ids(path: Path, ids: Iterable[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ids = [int(x) for x in ids]
    path.write_text("\n".join(str(x) for x in ids) + ("\n" if ids else ""))


def load_annotations(annotations_path: Path, completeness_path: Path) -> pd.DataFrame:
    ann = pd.read_csv(annotations_path, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError("annotations file must contain root_id")
    comp = pd.read_csv(completeness_path, index_col=0)
    sim_ids = set(pd.to_numeric(pd.Series(comp.index), errors="coerce").dropna().astype("int64").map(int))
    ann = ann.copy()
    ann["root_id"] = pd.to_numeric(ann["root_id"], errors="coerce")
    ann = ann.dropna(subset=["root_id"])
    ann["root_id"] = ann["root_id"].astype("int64").map(int)
    ann = ann[ann["root_id"].isin(sim_ids)].copy()
    for col in ["super_class", "cell_class", "cell_type", "hemibrain_type"]:
        if col not in ann.columns:
            ann[col] = ""
        ann[col] = ann[col].fillna("").astype(str)
    return ann


def select_contains(ann: pd.DataFrame, columns: list[str], patterns: list[str]) -> pd.DataFrame:
    mask = pd.Series(False, index=ann.index)
    for col in columns:
        text = ann[col].fillna("").astype(str).str.lower()
        for pat in patterns:
            mask |= text.str.contains(pat.lower(), regex=False, na=False)
    return ann[mask].copy()


def select_exact(ann: pd.DataFrame, col: str, value: str) -> pd.DataFrame:
    return ann[ann[col].fillna("").astype(str).str.lower().eq(value.lower())].copy()


def matched_sample(ids: list[int], k: int, rng: np.random.Generator) -> list[int]:
    ids = sorted(set(int(x) for x in ids))
    if k <= 0 or len(ids) <= k:
        return ids
    return sorted(int(x) for x in rng.choice(ids, size=k, replace=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create source-context ID files.")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--completeness", default="Drosophila_brain_model/2023_03_23_completeness_630_final.csv")
    parser.add_argument("--sugar-ids", default="metadata/sugar_ids_21.txt")
    parser.add_argument("--output-dir", default="metadata/source_contexts")
    parser.add_argument("--matched-k", type=int, default=21)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    ann = load_annotations(Path(args.annotations), Path(args.completeness))
    sugar_ids = parse_id_file(args.sugar_ids)
    sim_ids = set(ann["root_id"].map(int).tolist())
    sugar_ids = [x for x in sugar_ids if x in sim_ids]

    context_frames: dict[str, pd.DataFrame] = {}
    context_frames["sugar"] = ann[ann["root_id"].isin(sugar_ids)].copy()
    context_frames["gustatory"] = select_contains(ann, ["cell_class", "cell_type", "hemibrain_type"], ["gustatory"])
    context_frames["mechanosensory"] = select_contains(ann, ["cell_class", "cell_type", "hemibrain_type"], ["mechanosensory"])
    context_frames["visual_projection"] = select_exact(ann, "super_class", "visual_projection")
    context_frames["sensory_ascending"] = select_exact(ann, "super_class", "sensory_ascending")
    context_frames["all_sensory"] = ann[ann["super_class"].str.lower().str.contains("sensory", na=False)].copy()
    context_frames["no_input"] = ann.iloc[0:0].copy()

    manifest_rows = []
    for name, frame in context_frames.items():
        ids = sorted(set(frame["root_id"].map(int).tolist()))
        complete_path = out / f"{name}_complete.txt"
        write_ids(complete_path, ids)
        manifest_rows.append({
            "context_name": name,
            "mode": "complete",
            "path": str(complete_path),
            "n_ids": len(ids),
            "seed": "",
            "matched_k": "",
            "notes": "biologically complete annotated source set; may be empty if annotation is unavailable",
        })

        if name != "no_input":
            m_ids = matched_sample(ids, args.matched_k, rng)
            matched_path = out / f"{name}_matchedK{args.matched_k}_seed{args.seed}.txt"
            write_ids(matched_path, m_ids)
            manifest_rows.append({
                "context_name": name,
                "mode": "matched_size",
                "path": str(matched_path),
                "n_ids": len(m_ids),
                "seed": args.seed,
                "matched_k": args.matched_k,
                "notes": "matched-size exploratory source set for pilot/debug runs, not final biological-complete mode",
            })

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = out / "source_context_manifest.csv"
    manifest.to_csv(manifest_path, index=False)

    print(f"Loaded {len(ann):,} annotated simulator neurons")
    print(f"Wrote manifest: {manifest_path}")
    print(manifest[["context_name", "mode", "n_ids", "path"]].to_string(index=False))


if __name__ == "__main__":
    main()
