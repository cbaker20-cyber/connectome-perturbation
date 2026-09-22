from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "2023_03_23_completeness_630_final.csv"
CON = ROOT / "2023_03_23_connectivity_630_final.parquet"
ANN = ROOT / "flywire_annotations.tsv"
MN9 = "720575940660219265"
SELECTION_SEEDS = [630101, 630102, 630103, 630104, 630105]
CONFIRMATION_SEEDS = list(range(630201, 630231))


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def atomic_parquet(path, frame):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    frame.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def root_ids(values):
    """Do not round 64-bit neuron identifiers through floating point."""
    out = []
    for x in values:
        if isinstance(x, (float, np.floating)) or pd.isna(x):
            raise ValueError("root IDs must be integer strings or exact integers")
        s = str(x)
        if not s.isdigit():
            raise ValueError(f"invalid root ID: {s!r}")
        out.append(s)
    return out


def neuron_ids():
    ids = root_ids(pd.read_csv(COMP, index_col=0).index)
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate completeness IDs")
    return ids


def sugar_ids():
    from perturbation.baseline import NEU_SUGAR
    return root_ids(NEU_SUGAR)


def environment():
    packages = {}
    for name in ["numpy", "scipy", "pandas", "pyarrow", "brian2", "Cython",
                 "matplotlib", "psutil", "pytest", "statsmodels"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": sys.version, "executable": sys.executable,
            "platform": platform.platform(), "packages": packages}


def provenance():
    paths = [COMP, CON, ANN]
    sources = [ROOT / "model.py", ROOT / "perturbation/baseline.py",
               ROOT / "perturbation/cell_groups.py"] + sorted((ROOT / "eigencircuits").glob("*.py"))
    return {"materialization": "630", "inputs": {p.name: sha256(p) for p in paths},
            "sources": {p.relative_to(ROOT).as_posix(): sha256(p) for p in sources},
            "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
            "environment": environment()}


def load_trials(paths):
    """Load complete trial directories; preserve completely silent trials."""
    manifests, spikes = [], []
    seen = set()
    for path in paths:
        p = Path(path)
        m = read_json(p / "manifest.json")
        if m["status"] != "complete":
            raise ValueError(f"incomplete trial: {p}")
        if m["trial_id"] in seen:
            raise ValueError("duplicate trial IDs")
        seen.add(m["trial_id"])
        if sha256(p / "spikes.parquet") != m["outputs"]["spikes.parquet"]:
            raise ValueError(f"spike checksum mismatch: {p}")
        d = pd.read_parquet(p / "spikes.parquet")
        if len(d) and set(d.trial) != {m["trial_id"]}:
            raise ValueError("spikes and manifest disagree on trial ID")
        d["flywire_id"] = pd.Series(root_ids(d.flywire_id), dtype="string")
        spikes.append(d)
        manifests.append(m)
    if not manifests:
        raise ValueError("no complete trials")
    return pd.concat(spikes, ignore_index=True), manifests
