from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from .common import (CONFIRMATION_SEEDS, ROOT, SELECTION_SEEDS, atomic_json, atomic_parquet,
                     fingerprint, neuron_ids, now, provenance, read_json, sha256)
from .readouts import bh, paired_signflip, reference_test, summarize_pair
from .trials import trial


def prepare(pilot, out, phase="singles", mode_dir=None, controls_dir=None,
            singles_summary=None, modes_summary=None, backend="numpy", benchmark=None, analysis="analysis"):
    pilot, out = Path(pilot).resolve(), Path(out).resolve()
    if (out/"jobs.json").exists():
        raise FileExistsError("job manifest already frozen; choose a new directory")
    selection_path = pilot/analysis/"selection.json"
    selected = read_json(selection_path)
    analysis_record = read_json(pilot/analysis/"analysis_manifest.json")
    if analysis_record.get("input_protocol") != "fixed_binomial_tape_v1":
        raise ValueError("CCR selection requires corrected input protocol")
    if selected["n_trials"] != 5:
        raise ValueError("need five selection trials")
    if len({r["root_id"] for r in selected["cells"]}) != len(selected["cells"]):
        raise ValueError("selection contains repeated cells")
    if any(sum(r["role"] == role for r in selected["cells"]) != 10 for role in ["excitatory", "inhibitory"]):
        raise ValueError("selection requires ten E and ten I cells")
    if backend != "numpy":
        certificate = read_json(benchmark) if benchmark else {}
        if not certificate.get("passed"):
            raise ValueError("compiled backend requires a passed benchmark")
        if certificate["selection_sha256"] != sha256(selection_path) or certificate["provenance"]["inputs"] != provenance()["inputs"]:
            raise ValueError("benchmark used a different selection or dataset")
        for source in ["model.py", "eigencircuits/trials.py", "eigencircuits/common.py"]:
            if certificate["provenance"]["sources"][source] != provenance()["sources"][source]:
                raise ValueError("simulation code changed since backend benchmark")
    conditions = [{"name": "baseline", "ids": [], "role": "baseline"}]
    dependencies = {str(selection_path): sha256(selection_path)}
    feature_path = pilot/analysis/"features.parquet"
    if sha256(feature_path) != selected["features_sha256"]:
        raise ValueError("selection features changed")
    if phase == "singles":
        conditions += [{"name": f"cell_{i:02}", "ids": [r["root_id"]], "role": r["role"]}
                       for i, r in enumerate(selected["cells"])]
    else:
        if not singles_summary:
            raise ValueError("mode work requires completed single-cell study")
        single = read_json(singles_summary)
        if single.get("status") != "complete" or single.get("phase") != "singles" or single.get("n_ei_cells") != 20:
            raise ValueError("20 individual E/I lesions are not complete")
        if single.get("selection_sha256") != sha256(selection_path):
            raise ValueError("single-cell study used a different frozen selection")
        if not mode_dir:
            raise ValueError("mode directory required")
        mode_dir = Path(mode_dir).resolve()
        mode = read_json(mode_dir/"selection.json")
        metadata = read_json(mode_dir/"manifest.json")
        if mode["status"] != "selected" or metadata["features_sha256"] != sha256(feature_path):
            raise ValueError("no eligible mode for these selection baselines")
        dependencies.update({str(Path(singles_summary).resolve()): sha256(singles_summary),
                             str(mode_dir/"selection.json"): sha256(mode_dir/"selection.json"),
                             str(mode_dir/"manifest.json"): sha256(mode_dir/"manifest.json")})
        conditions += [{"name": "mode", "ids": mode["root_ids"], "role": "mode"}]
        if phase == "modes":
            if not controls_dir:
                raise ValueError("199 matched control sets required")
            controls_dir = Path(controls_dir).resolve()
            cm = read_json(controls_dir/"manifest.json")
            if cm["status"] != "ready" or not cm["full_matching"] or cm["accepted"] != 199:
                raise ValueError("full 199-set controls are not ready")
            if cm["target_ids"] != mode["root_ids"] or cm["features_sha256"] != sha256(feature_path):
                raise ValueError("controls do not match selected mode/features")
            if cm["controls_sha256"] != sha256(controls_dir/"controls.parquet"):
                raise ValueError("control table changed")
            control_table = pd.read_parquet(controls_dir/"controls.parquet")
            groups = list(control_table.groupby("control"))
            supports = [tuple(sorted(g.root_id)) for _, g in groups]
            if len(groups) != 199 or len(set(supports)) != 199:
                raise ValueError("need 199 distinct sets")
            for i, g in groups:
                if len(g) != len(mode["root_ids"]) or g.root_id.duplicated().any():
                    raise ValueError("invalid control set size")
                conditions.append({"name": f"control_{i:03}", "ids": g.root_id.tolist(), "role": "control"})
            dependencies[str(controls_dir/"manifest.json")] = sha256(controls_dir/"manifest.json")
            dependencies[str(controls_dir/"controls.parquet")] = sha256(controls_dir/"controls.parquet")
        else:
            prior = read_json(modes_summary) if modes_summary else {}
            if prior.get("status") != "complete" or prior.get("phase") != "modes" or prior.get("selection_sha256") != sha256(selection_path):
                raise ValueError("sensitivity follows completed mode confirmation")
    variants = [{"name": "default", "weight_scale": 1., "inhibitory_scale": 1., "strong_fraction": None}]
    if phase == "sensitivity":
        variants += [{"name": "ie_0.5", "weight_scale": 1., "inhibitory_scale": .5, "strong_fraction": None},
                     {"name": "ie_1.5", "weight_scale": 1., "inhibitory_scale": 1.5, "strong_fraction": None},
                     {"name": "weight_0.7", "weight_scale": .7, "inhibitory_scale": 1., "strong_fraction": None},
                     {"name": "weight_1.3", "weight_scale": 1.3, "inhibitory_scale": 1., "strong_fraction": None},
                     {"name": "strong_0.05", "weight_scale": 1., "inhibitory_scale": 1., "strong_fraction": .05}]
    # Confirmation seeds are separate from every baseline-selection seed.
    assert not set(CONFIRMATION_SEEDS) & set(SELECTION_SEEDS)
    jobs = []
    for variant in variants:
        for condition in conditions:
            for seed in CONFIRMATION_SEEDS:
                jobs.append({"index": len(jobs), "condition": condition["name"], "role": condition["role"],
                             "lesion_ids": condition["ids"], "seed": seed, "variant": variant,
                             "trial_id": f"{variant['name']}_{condition['name']}_{seed}"})
    durations = [read_json(p)["wall_seconds"] for p in pilot.glob("trials/baseline_*/manifest.json")]
    estimate = float(np.median(durations))*len(jobs)
    out.mkdir(parents=True, exist_ok=True)
    prov = provenance()
    record = {"phase": phase, "created_utc": now(), "backend": backend, "n_jobs": len(jobs),
              "jobs": jobs, "conditions": conditions, "variants": variants,
              "selection_sha256": sha256(selection_path), "features_sha256": sha256(feature_path),
              "dependencies": dependencies, "provenance": prov, "seeds": CONFIRMATION_SEEDS,
              "estimated_serial_hours_from_local": estimate/3600,
              "estimate_note": "local NumPy timing; CCR timing, memory and queue limits must be measured",
              "status": "prepared_not_submitted"}
    atomic_json(out/"jobs.json", record)
    print(f"Prepared {len(jobs)} jobs; local-rate serial estimate {estimate/3600:.2f} hours. Nothing submitted.")


def worker(study, index):
    study = Path(study).resolve()
    plan = read_json(study/"jobs.json")
    if not 0 <= index < len(plan["jobs"]):
        raise ValueError("array index outside job manifest")
    actual = provenance()
    for field in ["inputs", "sources"]:
        if actual[field] != plan["provenance"][field]:
            raise ValueError(f"frozen {field} differ; regenerate queue after documented changes")
    # Local and CCR Python paths may differ; package versions may not silently differ.
    if actual["environment"]["packages"] != plan["provenance"]["environment"]["packages"]:
        raise ValueError("package versions differ from the frozen study")
    job = plan["jobs"][index]
    variant = {k: v for k, v in job["variant"].items() if k != "name"}
    target = study/"trials"/job["trial_id"]
    lock = study/"locks"/f"{index}.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock.open("x", encoding="utf-8") as f:
            f.write(now())
    except FileExistsError:
        raise RuntimeError("job is locked; confirm no worker is running before removing a stale lock")
    try:
        trial(target, job["trial_id"], job["seed"], lesion_ids=job["lesion_ids"],
              backend=plan["backend"], **variant)
    finally:
        lock.unlink()


def collect(study, features_path):
    study = Path(study).resolve()
    plan = read_json(study/"jobs.json")
    if sha256(features_path) != plan["features_sha256"]:
        raise ValueError("features changed")
    missing = [j["index"] for j in plan["jobs"] if not (study/"trials"/j["trial_id"]/"manifest.json").exists()
               or read_json(study/"trials"/j["trial_id"]/"manifest.json").get("status") != "complete"]
    if missing:
        atomic_json(study/"missing_jobs.json", {"indices": missing, "n_missing": len(missing)})
        raise ValueError(f"{len(missing)} missing/incomplete jobs; no partial confirmation analysis")
    for job in plan["jobs"]:
        m = read_json(study/"trials"/job["trial_id"]/"manifest.json")
        if m["seed"] != job["seed"] or m["trial_id"] != job["trial_id"] or sorted(m["lesion_ids"]) != sorted(job["lesion_ids"]):
            raise ValueError("completed trial differs from frozen job")
        for key in ["weight_scale", "inhibitory_scale", "strong_fraction"]:
            if m[key] != job["variant"][key]:
                raise ValueError("trial network differs from frozen variant")
        if m["backend"] != plan["backend"] or m.get("input_protocol") != "fixed_binomial_tape_v1":
            raise ValueError("trial execution differs from frozen protocol")
        for key in ["inputs", "sources"]:
            if m["provenance"][key] != plan["provenance"][key]:
                raise ValueError("trial provenance differs from frozen study")
    features = pd.read_parquet(features_path)
    ids = features.root_id.tolist()
    motor_ids = features.loc[features.super_class == "motor", "root_id"].tolist()
    lookup = {x: i for i, x in enumerate(ids)}
    rows, secondary, primary = [], [], []
    for variant in plan["variants"]:
        vname = variant["name"]
        def directories(condition):
            return [study/"trials"/j["trial_id"] for j in plan["jobs"]
                    if j["variant"]["name"] == vname and j["condition"] == condition]
        baseline = directories("baseline")
        results = {}
        for c in plan["conditions"]:
            if c["role"] == "baseline":
                continue
            summary, delta = summarize_pair(baseline, directories(c["name"]), ids, c["ids"], motor_ids,
                                            study/"analysis"/vname/c["name"])
            results[c["name"]] = summary
            rows.append({"variant": vname, "condition": c["name"], "role": c["role"], **summary})
            if plan["phase"] == "singles" and c["role"] in ["excitatory", "inhibitory"]:
                from .common import MN9
                values = {"MN9": delta[:, lookup[MN9]],
                          "motor_total": delta[:, [lookup[i] for i in motor_ids]].sum(1)}
                for name, values in values.items():
                    secondary.append({"condition": c["name"], "readout": name,
                                      "delta_hz": float(values.mean()), "p": paired_signflip(values)})
        if plan["phase"] == "modes":
            primary.append({"variant": vname, **reference_test(results["mode"],
                [results[c["name"]] for c in plan["conditions"] if c["role"] == "control"])})
    if secondary:
        for row, q in zip(secondary, bh([r["p"] for r in secondary])):
            row["q_bh"] = float(q)
        atomic_parquet(study/"analysis/secondary_tests.parquet", pd.DataFrame(secondary))
    atomic_json(study/"analysis/results.json", rows)
    atomic_json(study/"summary.json", {"status": "complete", "phase": plan["phase"],
                "n_ei_cells": sum(c["role"] in ["excitatory", "inhibitory"] for c in plan["conditions"]),
                "selection_sha256": plan["selection_sha256"], "jobs_sha256": sha256(study/"jobs.json"),
                "n_seeds": len(plan["seeds"]), "primary": primary,
                "sensitivity_interpretation": "descriptive; own-network baselines, fixed support; no new matched-control significance",
                "finished_utc": now()})


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="action", required=True)
    prepare_p = sub.add_parser("prepare")
    prepare_p.add_argument("--pilot", required=True)
    prepare_p.add_argument("--analysis", default="analysis")
    prepare_p.add_argument("--out", required=True)
    prepare_p.add_argument("--phase", choices=["singles", "modes", "sensitivity"], default="singles")
    prepare_p.add_argument("--mode-dir")
    prepare_p.add_argument("--controls-dir")
    prepare_p.add_argument("--singles-summary")
    prepare_p.add_argument("--modes-summary")
    prepare_p.add_argument("--backend", choices=["numpy", "cython"], default="numpy")
    prepare_p.add_argument("--benchmark")
    worker_p = sub.add_parser("worker")
    worker_p.add_argument("--study", required=True)
    worker_p.add_argument("--index", type=int, required=True)
    collect_p = sub.add_parser("collect")
    collect_p.add_argument("--study", required=True)
    collect_p.add_argument("--features", required=True)
    a = vars(p.parse_args()); action = a.pop("action")
    if action == "prepare": prepare(**a)
    elif action == "worker": worker(**a)
    else: collect(a["study"], a["features"])


if __name__ == "__main__":
    main()
