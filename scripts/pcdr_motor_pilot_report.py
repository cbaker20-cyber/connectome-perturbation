"""Build readable notes and a scientific figure from the committed evidence snapshot."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import sha256, atomic_json, now


def main():
    evidence = ROOT/'docs/pcdr/evidence/2026-09-22'
    manifest = json.loads((evidence/'manifest.json').read_text())
    for record in manifest['records']:
        assert sha256(evidence/record['published']) == record['sha256']
    study = evidence/'motor_composition_pilot_20260922'
    results = json.loads((study/'analysis/results.json').read_text())
    contrasts = json.loads((study/'paired_contrasts.json').read_text())
    audit = json.loads((study/'completion_audit.json').read_text())
    protocol = json.loads((study/'amendment.json').read_text())
    duplicates = json.loads((study/'response_duplicates/summary.json').read_text())
    mode = next(r for r in results if r['condition'] == 'mode')
    others = [r for r in results if r['condition'] != 'mode']
    n_a = sum(mode['A'] > r['A'] for r in others)
    n_f = sum(mode['F'] is not None and r['F'] is not None and mode['F'] > r['F'] for r in others)
    both = sum(mode['A'] > r['A'] and mode['F'] is not None and r['F'] is not None and mode['F'] > r['F'] for r in others)
    lines = ['# Motor-composition pilot: all results', '', '22 September 2026. Descriptive follow-up using all nine fixed motor-balanced comparison sets.', '',
             f'All {audit["trials_verified"]} trials and {audit["scheduled_input_pairs_verified"]} scheduled-input pairs passed independent verification. The ten complete 127,400-neuron mean footprints were recomputed from saved rates. Source and output hashes passed. No random-reference p-values were calculated.', '',
             f'The eigen-set had A = {mode["A"]:.6f} Hz and F = {mode["F"]:.6f}. It exceeded {n_a}/9 comparisons on A, {n_f}/9 on F, and {both}/9 on both. These are conditional descriptive orderings, not significance tests.', '',
             f'{100*(1-mode["F"]):.2f} percent of the absolute mean response was outside the eigen-support. This is inconsistent with describing the support as dynamically independent merely because its response is more concentrated than some alternatives.', '',
             '## Frozen question and comparison', '',
             'The question was whether the prior response ordering persists against these nine motor-count-balanced optimized sets. Every set has 51 cells and 13 annotated motor cells, with exact sign/recruitment/motor counts and the original six pooled SMDs <=0.1. The target is the unchanged exploratory rank 33 support. No set was replaced after seeing an outcome.', '',
             'The pre-lesion audit found incoming-degree variance up to 19.117 times the target and an ECDF gap up to 0.294118. All nine comparisons share 47 cells. MN9 is in the target and excluded from every comparison. Detailed cell types and some annotation availability differ. These facts prevent interpreting this as an isolated causal test of motor count, a representative random-control sample or confirmation of P over D/C/R.', '',
             'Five fresh seeds 631201-631205 were run separately from earlier studies. The model, inputs, timestep, duration and output-only lesion semantics were unchanged. Thirty-minute local limit, one serial worker, memory/disk guards and no automatic extension were recorded before simulation.', '',
             '## Every lesion set', '',
             '| Set | A (Hz) | F | MN9 change (Hz) | Motor total change (Hz) |',
             '|---|---:|---:|---:|---:|']
    for r in results:
        lines.append(f'| {r["condition"]} | {r["A"]:.3f} | {r["F"]:.4f} | {r["mn9_delta_hz"]:.1f} | {r["motor_total_delta_hz"]:.1f} |')
    lines += ['', 'The reported A and F are computed after averaging each neuron\'s signed paired response over seeds and then taking absolute values. The arithmetic mean of single-seed A/F is not the declared outcome. Motor changes are simulated rates, not feeding behavior.', '',
              '## Conditional paired-seed differences', '',
              'Differences below are eigen-set minus comparison, each scored on its own support. Intervals use 2000 shared whole-seed bootstrap resamples, seed 631250. The same resampled seeds are used for each pair of conditions. They describe uncertainty from five stochastic input seeds conditional on these fixed sets. They do not cover uncertainty in the connectome, mode selection, matching or model assumptions, and are not multiplicity-adjusted confirmatory intervals.', '',
              '| Comparison | A difference (Hz) | A 95% interval | F difference | F 95% interval |',
              '|---|---:|---|---:|---|']
    for c in contrasts:
        ai, fi = c['A_difference_95pct'], c['F_difference_95pct']
        lines.append(f'| {c["comparison"]} | {c["A_difference"]:.3f} | {ai[0]:.3f} to {ai[1]:.3f} | {c["F_difference"]:.4f} | {fi[0]:.4f} to {fi[1]:.4f} |')
    lines += ['', 'Per-set intervals, all 50 per-seed readouts and all ten sets are preserved in the evidence snapshot. No favorable set subset was selected. Paired-seed intervals do not make the nine largely overlapping sets independent.', '',
              '## Repeated responses checked after completion', '',
              f'The nine distinct membership sets produced only {duplicates["distinct_five_seed_spike_trajectories"]} distinct five-seed spike trajectories. This was noticed in the completed result table, so a separate post-result diagnostic was recorded before checking the full outputs. Within each group, every spike event and all 127,400 per-neuron rates were exactly equal for every seed. This is stronger than merely equal A and F.', '',
              'The repeated groups were motor_003/006/009, motor_004/007/010 and motor_005/008/011. Each group shared 49 cells. Four cells varied in membership across the group, and all four had zero spikes in all five baselines and all corresponding lesion conditions. Their recorded IDs and all inspected rates are saved in response_duplicates/varying_cell_rates.csv.', '',
              'This means part of the apparent set diversity consisted of substitutions among cells that were silent in these runs. It does not prove they stay silent in new seeds or another input/model condition. Keep all nine completed results in the record; do not count them as nine independent perturbation responses or reinterpret the three patterns as independent biological replicates.', '',
              '## What this changes and what remains', '',
              'This adds an actual lesion comparison after matching feasibility and distribution checks. It tests the ordering against fixed alternatives with matching motor counts. It does not establish that motor composition caused any difference from the earlier pilot, because the individual neurons and other distributional properties changed too.', '',
              'The next design problem is comparison quality and diversity. A prospective design could constrain distributional differences and deliberately seek more distinct eligible sets, then test its feasibility before new lesions. Neither a new numerical balance cutoff nor a different eigen-support should be chosen to improve these completed outcomes. The historical 199-control confirmation still lacks a justified reference-sampling design.', '',
              '## Code, checks and evidence', '',
              'Created scripts/pcdr_motor_set_audit.py, pcdr_motor_composition_pilot.py, pcdr_verify_motor_pilot.py, pcdr_motor_response_duplicates.py, pcdr_publish_evidence.py and pcdr_motor_pilot_report.py with Codex assistance. Function explanations are separate in CODE_GUIDE.md. The source model and existing simulator were not changed.', '',
              'The verifier rereads every saved trial, checks all output hashes, membership IDs, seeds, provenance and model parameters, verifies paired scheduled inputs, then recomputes all ten full footprints and A/F/MN9/motor summaries. The added contrast calculation uses common seed weights before taking absolute responses. Known-answer tests check identical paired contrasts, a constant-response example and undefined concentration for zero response.', '',
              f'Delivered-input digests match in {audit["delivered_input_pairs_equal"]}/50 pairs. Scheduled-input identity is required; delivered events can differ with network state. Every scheduled pair matched.', '',
              'Before launch: 31 focused tests passed. For the repository commit: 224 tests passed, 3 skipped, 40 warnings. These are software checks, not biological validation. Verification of the completed study is separate from the unit tests.', '',
              'Commands: .venv/Scripts/python.exe scripts/pcdr_motor_set_audit.py; scripts/pcdr_motor_composition_pilot.py --prepare; scripts/pcdr_motor_composition_pilot.py; scripts/pcdr_verify_motor_pilot.py; scripts/pcdr_publish_evidence.py; scripts/pcdr_motor_pilot_report.py.', '',
              'Full local evidence: results/pcdr/motor_composition_pilot_20260922. Compact committed evidence: docs/pcdr/evidence/2026-09-22, with original-source hashes. Trial spikes, delivered/scheduled input tapes, rate tables and source archives remain local. Earlier studies and PDFs remain unchanged.', '',
              'The distributional objection and supporting literature are recorded in MOTOR_SET_AUDIT_20260922.md. The feasibility method is in FULLPOOL_FEASIBILITY_20260922.md. This report is research support prepared with Codex assistance, not a student-authored STS submission.', '']
    report = ROOT/'docs/pcdr/MOTOR_COMPOSITION_RESULTS_20260922.md'
    report.write_text('\n'.join(lines), encoding='utf-8')
    plt.rcParams.update({'font.size': 13, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 3, figsize=(12, 7.5), gridspec_kw={'width_ratios': [1, 1, 1.3]}, layout='constrained')
    labels = [r['condition'] for r in results]
    ypos = np.arange(len(results))
    colors = ['#b33b30' if label == 'mode' else '#35648c' for label in labels]
    for ax, metric, label in [(axes[0], 'A', 'Mean absolute response\ninside set (Hz)'), (axes[1], 'F', 'Fraction of response\ninside set')]:
        for i, r in enumerate(results):
            interval = r['interval'][metric+'_95pct']
            ax.plot(interval, [i, i], color=colors[i], linewidth=2)
            ax.scatter(r[metric], i, color=colors[i], s=28, zorder=3)
        ax.set(yticks=ypos, yticklabels=labels if metric == 'A' else [], xlabel=label)
        ax.invert_yaxis()
        ax.grid(axis='x', alpha=.2)
        ax.set_title(metric+': conditional 95%\npaired-seed intervals', fontsize=13)
    distributions = pd.read_csv(evidence/'motor_set_audit_20260922/distributions.csv')
    rows = distributions[distributions.feature == 'in_degree'].set_index('condition')
    stats = [{'med': rows.loc[label, 'sample_q50'], 'q1': rows.loc[label, 'sample_q25'], 'q3': rows.loc[label, 'sample_q75'],
              'whislo': rows.loc[label, 'sample_q0'], 'whishi': rows.loc[label, 'sample_q100'], 'fliers': []} for label in labels]
    boxes = axes[2].bxp(stats, positions=ypos, orientation='horizontal', patch_artist=True, widths=.55)
    for box, color in zip(boxes['boxes'], colors):
        box.set_facecolor(color)
        box.set_alpha(.65)
    axes[2].set(yticks=ypos, yticklabels=[], xlabel='log(1 + incoming degree)')
    axes[2].invert_yaxis()
    axes[2].set_title('Baseline spread\nMin/max and quartiles', fontsize=13)
    axes[2].grid(axis='x', alpha=.2)
    fig.suptitle('Motor-balanced comparisons: five fresh paired seeds\nEach set: 51 neurons, 13 motor cells. Comparisons share 47 neurons.', fontsize=14)
    directory = ROOT/'docs/pcdr/figures'
    directory.mkdir(exist_ok=True)
    figure = directory/'motor_composition_20260922.png'
    fig.savefig(figure, dpi=180)
    plt.close(fig)
    atomic_json(directory/'motor_composition_20260922_manifest.json', {'created_utc': now(), 'script_sha256': sha256(Path(__file__)),
                'evidence_manifest_sha256': sha256(evidence/'manifest.json'), 'report_sha256': sha256(report), 'figure_sha256': sha256(figure)})
    print(json.dumps({'report': str(report), 'figure': str(figure), 'A_greater': n_a, 'F_greater': n_f, 'both': both}))


if __name__ == '__main__':
    main()
