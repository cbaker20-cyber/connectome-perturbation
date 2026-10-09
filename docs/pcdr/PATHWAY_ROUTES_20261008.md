# Direct routes to the first outside spike changes — 8 October 2026

All six intervention comparisons have a direct, positive-weight connection from the affected G/H target to the earliest changed outside neuron. In every case, exactly one changed presynaptic emission can arrive on an incoming connection by that outside neuron's first changed spike: the missing G or H spike. This localizes the first downstream input difference. It does not establish the route responsible for the later population burst.

## Recorded check

Continued the [early divergence analysis](PATHWAY_DIVERGENCE_20261008.md) using saved outputs only. Before calculation, recorded all six earliest-outside targets, both G/H connections to each, scaled weights and possible arrivals through the first outside change. Rechecked the earlier analysis's input/output hashes and all original model/data hashes in the archived plan.

The archived model specifies a 1.8-ms synaptic delay and `g += w` on a presynaptic arrival. Delay is an integer number of clock ticks at both tested steps. Connectivity weights use 0.275 mV per signed connectivity unit, the recorded 1.2 weight scale and 0.8 inhibitory scale for negative weights. Existing outgoing-lesion identities were checked when calculating effective weights. None of the routes below has a zeroed weight.

The values below describe predicted changes in the synaptic state variable g, not instantaneous membrane-voltage jumps. They do not report newly measured conductance or voltage.

## Results

| Step (ms) | Removal | Missing upstream spike | Predicted arrival (ms) | First outside change (ms) | Missing positive g increment (mV) | Arrival-to-change interval (ms) |
|---|---|---|---:|---:|---:|---:|
| 0.0004 | G | G at 616.7112 | 618.5112 | 618.9360 | 0.33 | 0.4248 |
| 0.0004 | H | H at 618.6280 | 620.4280 | 620.4536 | 0.33 | 0.0256 |
| 0.0004 | Both | G at 616.7112 | 618.5112 | 618.9360 | 0.33 | 0.4248 |
| 0.0002 | G | G at 603.6980 | 605.4980 | 606.9870 | 8.25 | 1.4890 |
| 0.0002 | H | H at 605.6464 | 607.4464 | 608.8404 | 0.33 | 1.3940 |
| 0.0002 | Both | G at 603.6980 | 605.4980 | 606.9870 | 8.25 | 1.4890 |

The outside neurons are, respectively, 720575940619397797 and 720575940635451546 at the coarser step, and 720575940605420902 and 720575940629489260 at the finer step. Joint removal first changes the same outside neuron as G-only removal at each step. Every first outside event is a spike present in the reference but absent at that exact tick in the intervention.

Some cross-connections also exist: G connects to the coarser H-first neuron, and H connects to the finer G-first neuron. However, neither supplies a changed emission early enough in the relevant comparison. Edge presence alone would therefore give a less specific account than combining connectivity with event timing.

## Independent check and limits

A separate check joined connectivity by original exact root IDs rather than neuron indices, independently reconstructed event-set differences from archived raw spikes, and examined every presynaptic neuron with an incoming connection to each earliest-outside target. In each comparison, the only changed emission scheduled to arrive by the outside change is the one listed above. All other incoming presynaptic spike events capable of arriving by that deadline match. Input delivery was already verified identical in the original review.

This rules out another changed recurrent presynaptic emission as an earlier competing explanation at these first outside targets, within the recorded model and time window. It is stronger than an anatomical-edge observation. It does not by itself establish the target's exact voltage, how close it was to threshold, whether synaptic state was gated or reset, or how this first change propagates to the later burst. Those require state/scheduling evidence or a validated local reconstruction.

In particular, the 0.33-mV values must not be compared directly with a membrane threshold as if they were voltage jumps. The model adds them to g; membrane integration and other state affect the resulting response. The 94.38/78.21-mV connections originally removed are source-to-G/H connections, whereas this table concerns subsequent G/H-to-outside connections. They are different edges.

## Decision

The first local propagation step is now supported by both timing and direct connectivity, with no competing changed incoming emission before the first outside spike difference. The next useful question is whether a local state reconstruction can reproduce that first missing spike from the saved inputs and exact archived equations. That is proposed, not completed; no new simulation, rescue or intervention was run here.

Do not extrapolate this first step into a complete burst mechanism. The finer case also shows direct propagation despite lacking the broad reference burst. The original eigencircuit question, comparator imbalance and eighteen failed convergence groups remain unresolved. These selected-case findings support a narrower account of timing-sensitive recurrent propagation.

## Reproduction and records

Two focused tests pass in 0.43 seconds, covering signed missing/added increments, arrival boundaries, zero weights, invalid delay and duplicate events. Independent ID joins, raw-spike set differences and all-incoming emission checks agree across all six comparisons. Full evidence: results/pcdr/pathway_routes_20261008. The [compact snapshot](evidence/2026-10-08/pathway_routes/snapshot.json) preserves the protocol, results, source delay record and independent checks.

```text
.venv/Scripts/python.exe -m pytest tests/test_pcdr_pathway_routes.py -q
.venv/Scripts/python.exe scripts/pcdr_pathway_routes.py --out <unused-directory>
```

Previous frozen evidence and uploads were preserved. Code, analysis, separate recalculation and documentation used Codex assistance; no independent human review is implied.
