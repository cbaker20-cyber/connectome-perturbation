# Incoming timing and surplus-history sensitivity — 9 October 2026

Changing paired event times while holding per-source incoming event counts fixed changes the selected target's count in many local replays. However, the numerical attribution depends strongly on how events are paired, and many constructed histories violate source refractory spacing. This analysis does not establish a unique timing-versus-count decomposition or a physically realizable network mechanism.

## Recorded comparison

Kept the same 26 count-selected cases and four absent seeds from [baseline replays](BASELINE_REPLAY_20261009.md). Recorded the design before calculation. For each presynaptic neuron, pair the first min(coarse count, fine count) arrivals by order and retain each history's remaining events as surplus. Repeat using the last arrivals as a matching-rule sensitivity check. Pairing describes a construction; it does not identify the same physical spike across simulations.

For each rule, replay four histories at the same fine timestep through the original selected checkpoint:

| History | Paired event times | Surplus events and their times |
|---|---|---|
| cc | Coarse | Coarse |
| cf | Coarse | Fine |
| fc | Fine | Coarse |
| ff | Fine | Fine |

The cc and ff histories reconstruct the original coarse and fine inputs. Every reconstructed endpoint replay reproduced the prior verified target spike list exactly. Changing paired times holds each source's event count fixed. Changing surplus history alters both counts and the times of unmatched events, so it is not a pure count intervention. All histories are conditional inputs to a single target; target output does not feed back into them.

## Completed findings

| Count changes among 26 cases | Pair from beginning | Pair from end |
|---|---:|---:|
| Change paired times, hold coarse surplus | 21 | 24 |
| Change paired times, hold fine surplus | 23 | 22 |
| Change surplus, hold coarse paired times | 22 | 22 |
| Change surplus, hold fine paired times | 23 | 17 |
| Nonzero interaction: cc − cf − fc + ff | 14 | 21 |

At least one mixed-history count differs between the two pairing rules in 21 of 26 seeds. Effects therefore cannot be assigned a unique percentage using this construction. Interaction also prevents treating the two changes as independent additive causes. These selected cases are not an unbiased sample of neurons, and the two contrasts within a case are not independent observations.

The feasibility check is an additional substantive limitation. Among 52 mixed histories per rule, 30 beginning-paired histories and 51 end-paired histories contain at least one consecutive same-source interval shorter than 2.2 ms for a non-input neuron. Five end-paired mixed histories contain exact same-source/time duplicates (ten duplicate events total); beginning-paired mixed histories have none. The algorithm retained multiplicities, as declared, rather than silently deleting collisions. Even a construction without these violations is not proven realizable by the full network.

Thus the mathematical replay demonstrates sensitivity to event timing under fixed incoming counts, but many histories cannot be emitted by the original non-input source cells. It would be incorrect to present these as verified network interventions or as evidence that a particular fraction of the original discrepancy is caused by timing alone.

## Verification and provenance

Seven known-answer/failure tests passed in 0.52 seconds, covering both pairing directions, missing sources, exact endpoint reconstruction, and malformed event lists. The single worker completed in 27.953 seconds within its 180-second deadline. All consumed saved spikes and prior arrival arrays were hash-checked; model connectivity and replay source match the previous verified provenance. No network simulation, CCR job or upload was launched.

A separate dataframe implementation paired by ascending/descending within-source ranks and outer joins. It reproduced all 208 input histories and partition totals, checked collisions, and recorded source refractory-spacing violations. A separate sequential tick recurrence matched every predicted spike for eight mixed histories: both pairing rules and both mixtures for the smallest and largest selected seeds, chosen before that verification. It completed in 11.421 seconds under a 60-second bound. This checks those eight numerical trajectories, not all mixed histories independently.

Full output: results/pcdr/history_parts_20261009. [Compact evidence](evidence/2026-10-09/history_parts/snapshot.json) retains protocols, every target spike list, per-source partition, verified-history table, verification/process records and local input-array hashes. Reproduction: `.venv/Scripts/python.exe scripts/pcdr_history_parts.py --out <unused-directory>`; tests: `tests/test_pcdr_history_parts.py`. Existing outputs cannot be overwritten by the runner.

## Decision

Stop this branch of arbitrary event-pairing mixtures. It has answered the bounded question and exposed why a clean numerical attribution would not be defensible. Preserve the stronger earlier result: actual archived incoming histories reproduce selected count differences at a common target timestep.

The next useful mechanistic question concerns actual saved events: where does refractory acceptance or threshold crossing first differ along the selected targets' incoming histories? A recorded state/event comparison can use valid archived trajectories and avoid interpreting nonphysical mixtures as network interventions. It will still need to distinguish local propagation from the initiating network cause. More diagnostic tracing must not become a substitute for a numerical-study decision with the advisers.

All eighteen original full convergence groups remain failed. No converged functional eigencircuit or eigencircuit-specific effect is established. Code, analysis, checks and documentation used Codex assistance; separate computations are not independent human review.
