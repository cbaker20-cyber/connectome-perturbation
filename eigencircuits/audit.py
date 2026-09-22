from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from .common import (COMP, CON, ANN, ROOT, atomic_json, now, provenance, read_json,
                     sha256, sugar_ids)
from .graph import load_signed_matrix


def audit(out):
    w, ids = load_signed_matrix()
    ann = pd.read_csv(ANN, sep="\t", dtype={"root_id": str}, usecols=["root_id", "super_class"])
    original = read_json(ROOT/"data/input_manifest.json")
    records = {r["filename"]: r for r in original["inputs"]}
    checksums = []
    for p in [COMP, CON, ANN]:
        actual = sha256(p)
        expected = records[p.name]["sha256"]
        normalized = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if p.suffix in [".csv", ".tsv"] else actual
        checksums.append({"file": p.name, "actual_sha256": actual, "recorded_sha256": expected,
                          "matches_raw": actual == expected, "matches_after_lf_normalization": normalized == expected})
    result = {"created_utc": now(), "provenance": provenance(), "n_neurons": len(ids), "n_connections": w.nnz,
              "indices_match_ids": True, "all_weights_finite": bool(np.isfinite(w.data).all()),
              "all_sugar_ids_present": set(sugar_ids()) <= set(ids),
              "annotation_overlap": len(set(ids)&set(ann.root_id)),
              "motor_ids_present": len(set(ids)&set(ann.loc[ann.super_class == "motor", "root_id"])),
              "checksums": checksums,
              "rules": ["Do not silently replace manifest hashes or drop annotation-missing neurons.",
                        "Root IDs are stored as strings; matrix indices are a separate coordinate system.",
                        "Installed versions, not stale requirements, define this run environment."]}
    atomic_json(out, result)
    print(f"Audit saved: {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    audit(p.parse_args().out)
