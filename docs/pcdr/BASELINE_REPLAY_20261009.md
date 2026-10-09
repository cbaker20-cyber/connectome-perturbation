# Baseline timing and count replays — 9 October 2026

The selected cells' count differences persist when their saved incoming histories are replayed at a common timestep. In all 26 count-selected cases, the coarse incoming history replayed at the fine step retains the coarse target count, while the fine incoming history produces the fine count. This supports a local contribution carried by the incoming network activity. It does not locate the initiating network event or explain the full population discrepancy.

## First recorded selection: early timing

For each of all thirty default baseline seeds, paired spikes by ordinal within each non-input neuron. Selected the earliest ordinal pair separated by more than one coarse step (0.0002 ms), ordering by earlier event time, root ID, then ordinal. The rule and exclusions were recorded before results. Ordinal pairing is descriptive and does not prove event identity; unmatched terminal spikes are not selected by this rule.

All thirty seeds selected a target, representing fourteen distinct neurons. Selected pairs occurred between 10.3369 and 21.8725 ms; every separation was 0.0003 ms, with the coarse event later. Replayed each cell from rest through one additional 2.2-ms refractory duration after the pair, rounding the common stop upward to a coarse tick. The existing local replay generates its own threshold crossings, resets and refractory state, with 1.8-ms delayed incoming events and the original default weights.

All sixty native-step prefixes reproduced every saved target tick exactly. At a fixed fine step, replacing fine incoming history with coarse incoming history changed spike timing in all thirty cases but changed no counts in these short prefixes. This selection therefore did not explain the later count gaps. It is preserved rather than presented as a count mechanism.

## Recorded amendment: count differences

After that result, recorded a second selection rule. For every seed, inspect the previously declared 100, 200, ..., 1000-ms checkpoints. At the first checkpoint where any non-input cell has an absolute cumulative count gap of at least two spikes, choose the largest gap, breaking ties by root ID. The two-spike rule targets a diagnostic case; it is not a new convergence tolerance or significance test. All trials and missing selections are retained.

Twenty-six seeds qualify, with fifteen distinct selected neurons and checkpoints between 200 and 900 ms. Seeds 631403, 631404, 631410 and 631423 do not qualify. Selection explicitly favors count-disagreeing cells and cannot estimate the proportion of all neurons with this mechanism.

Replayed each selected target from initial rest through its half-open checkpoint. All 52 native-step target prefixes match every saved tick exactly. Then held target integration, threshold checking, reset, refractoriness and weights fixed at 0.0001 ms and replaced its fine-run presynaptic history with the coarse-run history at the same physical times. No new external drive was applied to these non-input targets.

| Local replay result | Count-selected cases |
|---|---:|
| Both native histories reproduce exact saved target ticks | 26/26 |
| Coarse history at fine step retains the coarse target count | 26/26 |
| Coarse versus fine history at the same fine step changes target count | 26/26 |

For example, seed 631401 selects neuron 720575940630868793 at 300 ms: coarse and fine counts are 29 and 21. Coarse history at the fine step still produces 29. Seed 631430 selects neuron 720575940615671106 at 400 ms: counts are 31 and 29; coarse history at the fine step produces 31. These examples illustrate the complete panel rather than substituting for it.

The comparison changes the entire saved incoming spike history. That history may differ in both event times and event counts. It does not isolate one synapse, prove that the earliest timing-selected neuron drives the later count-selected neuron, or separate all upstream timing from upstream count effects. Changing one target's output does not feed back into the fixed recorded inputs. This is a conditional single-neuron replay, not a network intervention.

The result rules out a need to retain the selected target's coarse update grid to retain its coarse count in these specific replays. It does not rule out upstream discretization effects, refractory feedback, other coding issues, or target-grid effects in other cells/windows. Neither trajectory convergence nor eigencircuit specificity follows.

## Verification and execution

Reused the previously tested replay algorithm rather than repeating the scheduling audit. Checked source/model/connectivity provenance against the original archived trial manifests, all consumed spike hashes, and exact input IDs. Twelve new selection known-answer/failure tests passed: six early-selection tests in 0.49 seconds and six count-selection tests in 0.51 seconds. Tests cover exclusions, ties, selection boundaries, missing selections and malformed event histories.

The early and count workers completed in 18.062 and 19.781 seconds, respectively, each within a separately recorded 180-second deadline. No native replay failed; no hybrid was interpreted without both native matches. No full-network simulation, new CCR run or upload occurred.

A separate dataframe calculation reproduced all sixty selection decisions, all saved target prefixes and all incoming arrival/weight arrays by ID joins. For the smallest and largest count-selected seeds, a separate sequential tick recurrence reproduced every hybrid spike tick exactly (29 and 31 spikes). That two-case numerical check does not independently validate every hybrid trajectory, although all native target trajectories match saved simulations.

The first invocation of the sequential verification failed before executing: `python -m runpy` interpreted the filename as a module. Its failed process record and stderr are preserved. A documented invocation-only correction used explicit `run_path`; it completed in 3.078 seconds. No scientific code or inputs changed to obtain agreement.

Full records: results/pcdr/baseline_events_20261009 and results/pcdr/baseline_count_replay_20261009. Compact [early evidence](evidence/2026-10-09/baseline_events/snapshot.json) and [count evidence](evidence/2026-10-09/baseline_count_replay/snapshot.json) preserve protocols, all selection/replay records, checks, process results and input-array hashes. Full arrival arrays remain local. Scripts: `pcdr_baseline_events.py` and `pcdr_baseline_count_replay.py`; each accepts `--out <unused-directory>` and refuses overwriting an existing analysis directory.

## Next uncertainty

We now have a local explanation for selected count differences in terms of differing incoming histories, not a complete chain from the earliest timing shift to the later count gap. The next bounded analysis should partition those incoming-history differences into timing shifts versus changed event counts, retaining every selected case and missing case. Any replacement-history experiment must record its matching rule before results and distinguish constructed histories from physically realizable network trajectories. Do not launch another whole-network sweep on the strength of this result.

All eighteen original full convergence groups remain failed. The original eigencircuit question and comparison-design limitations remain unresolved. Code, analysis and documentation used Codex assistance; separate computational checks are not independent human review.
