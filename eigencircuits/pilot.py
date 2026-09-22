from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time

from .common import ROOT, SELECTION_SEEDS, atomic_json, now, read_json


def run_step(root, name, seed, *, context="sugar", lesion=None):
    budget = read_json(root / "pilot.json")
    remaining = budget["deadline_epoch"] - time.time()
    if remaining <= 0:
        print("Local two-hour budget exhausted; remaining work goes to CCR.", flush=True)
        return False
    target = root / "trials" / name
    cmd = [sys.executable, "-m", "eigencircuits.trials", "--out", str(target),
           "--trial-id", name, "--seed", str(seed), "--context", context]
    if lesion:
        cmd += ["--lesion-id", str(lesion)]
    root.joinpath("logs").mkdir(exist_ok=True)
    with (root / "logs" / (name + ".txt")).open("a", encoding="utf-8") as log:
        try:
            print("Starting " + name, flush=True)
            subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                           timeout=remaining, check=True)
        except subprocess.TimeoutExpired:
            mpath = target / "manifest.json"
            if mpath.exists():
                m = read_json(mpath)
                m.update(status="timed_out", finished_utc=now())
                atomic_json(mpath, m)
            return False
    m = read_json(target / "manifest.json")
    print(f"Completed {name}: {m['wall_seconds']:.1f}s, {m['recruited_noninput']} recruited", flush=True)
    return True


def run(root, stage, analysis="analysis"):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "pilot.json").exists():
        atomic_json(root / "pilot.json", {"started_utc": now(), "deadline_epoch": time.time()+7200,
                    "budget_seconds": 7200, "selection_seeds": SELECTION_SEEDS,
                    "command": sys.argv, "status": "running"})
    if stage == "baseline":
        steps = [("baseline_0", SELECTION_SEEDS[0], "sugar"),
                 ("replay_0", SELECTION_SEEDS[0], "sugar"),
                 ("no_input_0", SELECTION_SEEDS[0], "no_input")]
        steps += [(f"baseline_{i}", seed, "sugar") for i, seed in enumerate(SELECTION_SEEDS[1:], 1)]
        for name, seed, ctx in steps:
            if not run_step(root, name, seed, context=ctx):
                break
        if (root / "trials/replay_0/manifest.json").exists():
            a = read_json(root / "trials/baseline_0/manifest.json")
            b = read_json(root / "trials/replay_0/manifest.json")
            if a["status"] == b["status"] == "complete":
                result = {"identical_spikes": a["spike_digest"] == b["spike_digest"],
                          "identical_inputs": a["input_digest"] == b["input_digest"]}
                atomic_json(root / "replay_check.json", result)
                if not all(result.values()):
                    raise ValueError("baseline replay failed")
    else:
        from .common import sha256
        selection_file = root / analysis / "selection.json"
        frozen = read_json(selection_file)
        suffix = "" if analysis == "analysis" else "_"+sha256(selection_file)[:8]
        for polarity in ["excitatory", "inhibitory"]:
            selected = next(x for x in frozen["cells"] if x["role"] == polarity)
            name = "lesion_"+polarity+suffix
            if not run_step(root, name, SELECTION_SEEDS[0], lesion=selected["root_id"]):
                break
            a = read_json(root / "trials/baseline_0/manifest.json")
            b = read_json(root / ("trials/"+name+"/manifest.json"))
            if a["input_digest"] != b["input_digest"]:
                raise ValueError("lesion and baseline received different input events")
    budget = read_json(root / "pilot.json")
    budget.update(last_updated_utc=now(), last_stage=stage,
                  status="budget_exhausted" if time.time() >= budget["deadline_epoch"] else "stage_finished")
    atomic_json(root / "pilot.json", budget)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--stage", choices=["baseline", "lesions"], default="baseline")
    p.add_argument("--analysis", default="analysis")
    a = p.parse_args()
    run(a.out, a.stage, a.analysis)


if __name__ == "__main__":
    main()
