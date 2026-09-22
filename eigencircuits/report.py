"""Assemble a local pilot report from manifests, not inferred trial counts."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .common import atomic_json, now, read_json, sha256
from .readouts import summarize_pair


def report(pilot, analysis="analysis"):
    pilot = Path(pilot).resolve()
    analysis_dir = pilot/analysis
    f = pd.read_parquet(analysis_dir/"features.parquet")
    selected = read_json(analysis_dir/"selection.json")
    baseline = read_json(analysis_dir/"baseline_summary.json")
    correlations = read_json(analysis_dir/"correlation_summary.json")
    surrogates = pd.read_parquet(analysis_dir/"surrogates.parquet")
    replay = read_json(pilot/"replay_check.json")
    undriven = read_json(pilot/"trials/no_input_0/manifest.json")
    if not all(replay.values()) or undriven["status"] != "complete" or undriven["spike_count"] != 0:
        raise ValueError("rule-out checks failed")
    ids = f.root_id.tolist()
    motor = f.loc[f.super_class == "motor", "root_id"].tolist()
    results = []
    for role in ["excitatory", "inhibitory"]:
        neuron = next(r["root_id"] for r in selected["cells"] if r["role"] == role)
        possible = []
        for path in sorted(pilot.glob("trials/lesion_*/manifest.json")):
            m = read_json(path)
            if m.get("status") == "complete" and m["lesion_ids"] == [neuron]:
                possible.append(path.parent)
        if len(possible) != 1:
            raise ValueError(f"need exactly one pilot lesion for selected {role}; found {len(possible)}")
        summary, _ = summarize_pair([pilot/"trials/baseline_0"], possible, ids, [neuron], motor,
                                     pilot/"report"/role)
        results.append({"role": role, **summary})
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    for ax, key, label in zip(axes, ["mn9_hz", "motor_total_hz"], ["MN9 firing (Hz)", "Total motor firing (Hz)"]):
        ax.plot(range(1, len(baseline)+1), [r[key] for r in baseline], "o-", color="#265b82")
        ax.set(xlabel="Independent selection trial", ylabel=label, xticks=range(1, len(baseline)+1))
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Sugar baseline: 150 Hz input, 1 s trials")
    fig.tight_layout()
    fig.savefig(pilot/"report/baseline_rates.png", dpi=180)
    plt.close(fig)
    for role in ["excitatory", "inhibitory"]:
        d = pd.read_parquet(pilot/"report"/role/"footprint.parquet")
        d["abs_delta"] = abs(d.delta_hz)
        d = d.nlargest(15, "abs_delta").sort_values("delta_hz")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(d.root_id, d.delta_hz, color=np.where(d.delta_hz >= 0, "#a94b44", "#265b82"))
        ax.axvline(0, color="black", linewidth=.6)
        ax.set(xlabel="Lesion minus paired baseline (Hz)", ylabel="Root ID",
               title=f"One {role} cell: largest changes, one seed pair")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(pilot/"report"/role/"footprint.png", dpi=170)
        plt.close(fig)
    null_summary = {kind: {"median": float(g.within_group_mean_r.median()),
                          "range": [float(g.within_group_mean_r.min()), float(g.within_group_mean_r.max())]}
                    for kind, g in surrogates.groupby("surrogate")}
    result = {"created_utc": now(), "baseline": baseline, "correlations": correlations,
              "surrogate_coherence": null_summary, "replay": replay, "no_input_spikes": 0,
              "lesions": results, "selection_sha256": sha256(analysis_dir/"selection.json"),
              "claim_status": "pilot_only_no_eigencircuit_hypothesis_test",
              "analysis_manifest_sha256": sha256(analysis_dir/"analysis_manifest.json")}
    atomic_json(pilot/"report/summary.json", result)
    lines = ["# Local P/D/C/R pilot", "", f"Generated: {result['created_utc']}", "",
             "Five independent selection baselines; one repeated seed; one undriven control; one E and one I lesion.",
             "", "- Same-seed replay: identical spikes and recorded external input events.",
             "- Input protocol: fixed_binomial_tape_v1; scheduled input is identical within each baseline/lesion pair. Delivered voltage jumps retain refractory gating.",
             "- No input: zero spikes.",
             f"- Recruited non-input neurons per trial: {min(r['recruited_noninput'] for r in baseline)}–{max(r['recruited_noninput'] for r in baseline)}.",
             f"- MN9 mean across selection trials: {np.mean([r['mn9_hz'] for r in baseline]):.1f} Hz.",
             "", "## Individual lesion checks", "",
             "| Model sign | Root ID | MN9 ΔHz | Total motor ΔHz |", "|---|---|---:|---:|"]
    lines += [f"| {r['role']} | {r['support_ids'][0]} | {r['mn9_delta_hz']:.1f} | {r['motor_total_delta_hz']:.1f} |" for r in results]
    lines += ["", "These are one-pair software/pilot observations, without confidence intervals or significance claims.",
              "The sign of an outgoing synapse does not prescribe the sign of a downstream population response.",
              "", "## Correlation checks", "", "| Bin width / minimum count | Neurons | Groups | Largest group |",
              "|---|---:|---:|---:|"]
    lines += [f"| {r['analysis']} | {r['n_neurons']} | {r['n_clusters']} | {r['largest_cluster']} |" for r in correlations]
    lines += ["", "Groups include singletons. The cut at 1-r = 0.7 is exploratory, not a significance threshold.",
              "Different bin widths change the grouping. The saved surrogates and split-trial comparison describe this uncertainty.",
              f"Split-trial adjusted Rand index: {correlations[0].get('split_trial_ARI'):.3f} across {correlations[0].get('split_common_cells')} common cells.",
              f"Observed mean within-group correlation: {correlations[0]['within_group_mean_r']:.3f}.",
              *[f"{kind}: median reclustered within-group correlation {values['median']:.3f}, range {values['range'][0]:.3f}–{values['range'][1]:.3f}." for kind, values in null_summary.items()],
              "These surrogate summaries recompute groups in each surrogate and are descriptive, without a prespecified significance test.",
              "", "## Reproduce", "", "Run from the repository root with the recorded environment:", "", "```text",
              f"python -m eigencircuits.report --pilot {pilot.relative_to(Path(__file__).resolve().parents[1]).as_posix()} --analysis {analysis}",
              "```", "", "Source trial manifests, hashes, complete rate tables, and full response footprints are linked by summary.json.",
              "No eigenmode lesion or CCR confirmation has been run."]
    (pilot/"report/REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("Pilot report: "+str(pilot/"report/REPORT.md"))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", required=True)
    p.add_argument("--analysis", default="analysis")
    a = p.parse_args()
    report(a.pilot, a.analysis)
