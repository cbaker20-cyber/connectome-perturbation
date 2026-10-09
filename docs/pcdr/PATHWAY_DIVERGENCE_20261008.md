# Early divergence after separate G/H removal — 8 October 2026

The interventions first alter different neurons outside the selected source and targets, then affect many of the same neurons before 650 ms. Most early event differences occur in neurons whose spike count over [600,650) is unchanged. The finer-step case has more early changed neurons despite lacking the broad reference burst. Early event-difference counts alone therefore do not explain the coarse-only burst.

This is a descriptive analysis of the [verified eight-trial experiment](SEPARATE_PATHWAY_RESULTS_20261008.md), not another intervention, an independent seed replication or an eigencircuit comparison.

## Recorded analysis

Checked the returned archive against its successful independent review hash. Before extracting divergence results, recorded all six intervention-versus-reference comparisons, exact neuron/tick symmetric differences, first changed event per neuron, and windows [600,610), [610,620), [620,650), [650,730), [730,750) ms. Also recorded shared changed-neuron sets before 650 ms, excluding the source and G/H targets. These supplementary choices were made after the primary experiment; its original endpoints and numerical convergence rules were retained.

Every pre-600 spike prefix again matches. A keyed table merge and a separate event-set symmetric difference agree for every comparison. A shifted spike is represented as a reference-only event plus an intervention-only event; these are not necessarily two changes in spike count. Event order cannot locate the first membrane-state difference or prove a synaptic transmission route.

## First changes

| Step | Removal | First changed event (ms) | First changed event outside source/G/H (ms) | Outside neuron |
|---|---|---:|---:|---|
| 0.0004 ms | G | Missing G spike, 616.7112 | 618.9360 | 720575940619397797 |
| 0.0004 ms | H | Missing H spike, 618.6280 | 620.4536 | 720575940635451546 |
| 0.0004 ms | Both | Missing G spike, 616.7112 | 618.9360 | 720575940619397797 |
| 0.0002 ms | G | Missing G spike, 603.6980 | 606.9870 | 720575940605420902 |
| 0.0002 ms | H | Missing H spike, 605.6464 | 608.8404 | 720575940629489260 |
| 0.0002 ms | Both | Missing G spike, 603.6980 | 606.9870 | 720575940605420902 |

All listed outside first events are reference-only spikes. Each row has one earliest outside event; the analysis retains ties if present. The shared first event for G-only and joint removal does not establish identical subsequent trajectories. G-only and H-only have different earliest outside neurons at both steps. Thus the saved spike records do not identify one common first outside mediator.

Before 650 ms, excluding the selected three neurons, G-only/H-only/joint removal changes events in 193/179/227 neurons at 0.0004 ms and 304/300/311 at 0.0002 ms. The single-removal changed-neuron intersections contain 179 and 300 neurons, respectively: the H-only early changed-neuron set is contained in the G-only set. All-three intersections contain 177 and 296 neurons. Set inclusion does not mean identical changed spikes, order, magnitude or causal roles.

## Timing differences versus count differences

After observing the event counts, a separately labeled diagnostic compared each neuron's total count over [600,650). This includes the source and targets, unlike the shared-set counts above.

| Step | Removal | Neurons with changed events | Of these, unchanged window count | Neurons with changed count | Net window spike change |
|---|---|---:|---:|---:|---:|
| 0.0004 | G | 196 | 173 | 23 | -14 |
| 0.0004 | H | 182 | 160 | 22 | -15 |
| 0.0004 | Both | 230 | 198 | 32 | -16 |
| 0.0002 | G | 306 | 291 | 15 | +3 |
| 0.0002 | H | 301 | 286 | 15 | +3 |
| 0.0002 | Both | 313 | 296 | 17 | +1 |

Equal counts with different event times describe temporal rearrangement within this window. They do not imply that individual spikes can be uniquely paired across trajectories. Count changes can also reflect events moving across a window boundary. No per-spike correspondence or continuous state reconstruction was inferred.

The finer case has more neurons with changed early events but fewer with changed counts. This reinforces the distinction between propagation of timing differences and growth in population spike counts. It does not demonstrate which temporal pattern produces the later coarse reference burst.

## Decision and limits

The narrow causal intervention result remains: either single connection removal after identical earlier spike histories interrupts broad recruitment in this selected coarser-step case. This analysis adds a chronology and shows substantial early temporal rearrangement, but cannot establish a common causal mediator, sufficiency, generality or biological bursting.

Do not select another intervention solely from an earliest-event or shared-neuron list. A next mechanistic analysis would need connectivity and delivered-event/state evidence to distinguish a direct downstream effect from recurrent timing changes. That remains proposed; no route or initiating numerical mechanism was verified here. The outcome also supports avoiding a simple score based on how many neurons diverge early.

For the original eigencircuit question, there is no new support-specific response comparison. All eighteen full numerical agreement groups remain failed, and the matching-design limitations remain. The useful advance is narrowing the interpretation of the already observed suppression rather than generating another simulation or claiming a general mechanism.

## Reproduction and verification

Four focused tests pass (0.53 seconds): known shifted-event output, ties, identical trajectories, duplicate events, invalid ID types and noninteger ticks. All six research differences agree with independent set algebra; grouped minima reproduce every saved first-change record. Archive CRC, duplicate paths, hash, tick grid and pre-switch prefix checks pass. Full evidence is in results/pcdr/pathway_divergence_20261008; the [compact snapshot](evidence/2026-10-08/pathway_divergence/snapshot.json) records hashes for retained event/first-change tables and copies the protocol, results and post-result count diagnostic.

```text
.venv/Scripts/python.exe -m pytest tests/test_pcdr_pathway_divergence.py -q
.venv/Scripts/python.exe scripts/pcdr_pathway_divergence.py --out <unused-directory>
```

Output directories cannot be overwritten by the runner. Earlier scientific evidence and the upload remain unchanged. Code, analysis, separate recalculation and documentation used Codex assistance; these are not independent human reviews.
