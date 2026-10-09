# Baseline differences before the endpoint — 9 October 2026

Default-baseline count disagreement is substantial well before the one-second recording ends. Its median summed absolute neuronwise count difference is 321 spikes by 600 ms and 500.5 by 900 ms, versus 578.5 for the full second. Removing the last 1 ms leaves a median of 577.5. A small shift at the final observation boundary cannot account for the bulk of the saved count disagreement under the suffix-deletion check below.

## Recorded analysis

Followed [the count partition](BASELINE_COUNTS_20261009.md) with all thirty default baseline pairs at 0.0002 and 0.0001 ms. No selected-case substitution, simulation or repeated simulator audit. Before calculating the new results, recorded prefix endpoints at 100-ms intervals through 1000 ms, plus 950, 980, 990, 995 and 999 ms. These descriptive windows were chosen after earlier count findings; they are not new convergence criteria.

Used the prior verified snapshot as the provenance chain, verified its file hashes and plan, and checked all sixty consumed spike-file hashes against its archived-output records. Converted on-grid native spike times to integer ticks on the common 0.0001-ms grid. Prefixes are half-open [0,end), with boundary spikes assigned to the next interval. Neuron IDs remain exact strings. Counts include stimulated neurons and are not divided by prefix duration.

For each prefix, computed the L1 norm of coarse-minus-fine counts across neurons. Also retained adjacent-interval and suffix count L1. These norms need not add because signed differences can cancel between intervals. A cumulative L1 can decrease; it is not a monotonic count of errors or a causal onset measure.

| Prefix end (ms) | Median count L1 | Seeds with nonzero count L1 |
|---|---:|---:|
| 400 | 2.0 | 15/30 |
| 500 | 167.0 | 21/30 |
| 600 | 321.0 | 22/30 |
| 900 | 500.5 | 26/30 |
| 980 | 587.0 | 26/30 |
| 990 | 575.5 | 26/30 |
| 999 | 577.5 | 26/30 |
| 1000 | 578.5 | 26/30 |

Every endpoint and seed is retained in the evidence, including those omitted from this compact table. Zero count difference does not imply identical spike times. Truncation introduces another endpoint, so the prefix comparison alone does not eliminate timing effects.

## Conservative endpoint bound

Let D be a neuron's full-second coarse-minus-fine count, and let T be the sum of its coarse and fine spike counts in the selected suffix. Removing any subset of those suffix spikes can change D by at most T. Therefore sum(max(abs(D) − T, 0)) is a lower bound on the remaining L1 after any such deletion. It is deliberately permissive and can be loose; it does not choose matching spikes or assume that every suffix spike is an endpoint artifact.

Across thirty seeds, full count L1 sums to 16,380. Even allowing arbitrary deletion of observed spikes in the final 1 ms, at least 15,963 (97.45%) remains under this bound. For the last 10 ms, at least 12,458 (76.06%) remains. These are pooled lower bounds, not causal fractions or mean per-seed percentages. The analysis concerns saved suffix spikes; it does not simulate missing future spikes, globally realign trains, or establish long-run rate stability.

Together, the prefix counts and bound rule out an explanation confined to deleting a few observed spikes at the very end. They do not rule out timing-dependent recurrent changes earlier in the trial. The previous finding that most count disagreement is in cells active at both steps remains relevant.

## Verification and research decision

Ten focused tests passed in 0.49 seconds. Tests cover exact boundaries, empty spikes, invalid times/indices, off-grid events, interval cancellation, and an exhaustive small-count check that the deletion bound never exceeds the best attainable distance over all permitted suffix deletions. Nine initial tests passed before execution; the exhaustive bound test was added afterward and the expanded file rerun, with both records preserved.

A separate calculation reread hash-checked spikes and used decimal-rounded physical times, pandas grouped counts and aligned series arithmetic instead of the producer's native ticks and bincount. It matched all 450 seed/endpoint rows for prefix, interval, suffix and deletion-bound quantities. Final distances also reproduce all thirty prior baseline totals. Separate implementations do not constitute independent human review.

Full outputs: results/pcdr/baseline_time_20261009. [Compact evidence](evidence/2026-10-09/baseline_time/snapshot.json) retains the prospective analysis record, every row, summaries, verification and test addendum. Reproduction: `.venv/Scripts/python.exe scripts/pcdr_baseline_time.py --out <unused-directory>`; tests: `tests/test_pcdr_baseline_time.py`.

The endpoint explanation is now sufficiently bounded to stop repeating this check. A next mechanistic study should select baseline events using a recorded rule across the seed panel and test how initially shifted events change subsequent counts. It should reuse existing scheduling checks rather than restart a general code audit. Such tracing remains diagnostic: all eighteen original full convergence groups still fail, and eigencircuit specificity is still unestablished. No new full-network experiment or CCR launch is prepared here.

Code, analysis, verification and documentation used Codex assistance.
