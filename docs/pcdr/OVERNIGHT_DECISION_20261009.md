# Overnight decision memo — 9 October 2026

Convergence has not been established. The overnight work strengthens a selected-case local mechanism explanation; it does not resolve the original eigencircuit question or replace the failed numerical criteria.

## Completed local replay

The pending check in [conditional crossings](DOWNSTREAM_CROSSINGS_20261009.md) is now complete. A separately recorded local replay starts each downstream neuron from resting voltage -52 mV and zero g, uses archived presynaptic spikes and effective incoming weights, and generates its own threshold crossings and resets. It does not receive observed postsynaptic reset times.

The recurrence evaluates exact linear dynamics between incoming event ticks, checks v > -45 mV before delivery, clears voltage/g on spikes, rejects refractory arrivals and releases at the recorded 2.2-ms boundary. Delays are 1.8 ms. Computation stops at the first outside difference inclusive. Four distinct target/step situations produce twelve reference/intervention prefixes across six comparisons, with repeated joint/G cases; these are not twelve independent scientific replicates.

All twelve prefixes reproduce every archived target spike at exactly the same integer clock tick, including the missing first outside spike under intervention. The single worker took 8.812 seconds, exited normally with empty stderr and stayed within its recorded 120-second deadline. No full-network simulation, new input tape, intervention or CCR job was run.

Six focused tests passed in 2.22 seconds with 26 dependency deprecation warnings. A separate sequential tick recurrence agrees on known-answer cases; a tiny installed Brian2 2.9.0 model agrees using the actual threshold/synapse/reset scheduling and refractory rules. Invalid-arrival/weight/time cases are rejected. A second archive read independently reproduces the expected target spike arrays and verifies all saved output hashes. The implementation's aggregation of simultaneous inputs and closed-form propagation changes floating-point arithmetic relative to the original network; exact observed tick agreement is reported for these prefixes only, not assumed elsewhere.

The replay is free-running for each postsynaptic neuron, but conditioned on recorded presynaptic network inputs. It is not a free-running network counterfactual. It stops at first divergence; it does not reproduce the full 750-ms aftermath. A saved-target-spike comparison verifies local output, not absolute state samples, which are unavailable for these four targets in this archive.

Full records: results/pcdr/local_replay_20261009. [Compact evidence](evidence/2026-10-09/local_replay/snapshot.json) preserves the protocol, results, process, environment and verification; predicted/actual tick arrays are retained locally with hashes. Runner: `.venv/Scripts/python.exe scripts/pcdr_local_replay.py --out <unused-directory>`. Tests: `tests/test_pcdr_local_replay.py`. Failed attempts would have been retained; none of these twelve prefixes failed.

## What this adds

Earlier route checks found exactly one changed incoming presynaptic emission capable of arriving before each first outside spike difference: the missing G/H spike. The conditional calculation showed the reference above threshold and intervention below. Generating the reset histories independently now reproduces all earlier spikes through that difference. Together, these support a local account of how the selected intervention first changes a downstream spike.

They do not identify the complete route to the late population burst, prove a shared burst mediator or show biological relevance. The same kind of direct propagation occurs at the finer step where the broad reference burst is absent. More selected-case tracing can refine the explanation but does not repair default-network convergence or confounded support comparisons.

## Convergence audit: retain the failed decision

Revisited the original [fine-step report](FINE_TIMESTEP_RESULTS_20261005.md) and machine-readable agreement-breakdown records. All eighteen full condition-by-halving groups failed. The selected default support at the final halving, 0.0002 to 0.0001 ms, has:

| Criterion | Passing paired trials |
|---|---:|
| A amplitude | 24/30 |
| F concentration | 28/30 |
| Full neuronwise response | 1/30 |
| Both population time courses | 1/30 |
| All requirements jointly | 1/30 |

The group rule requires at least 29/30 joint passes plus a passing mean response, and both final halvings must pass. Median individual relative L1 differences are 13.73% for the response and 15.41% for population activity, versus the declared 5% tolerance. Those criteria permit nonidentical spike times; they are not an exact-spike requirement. Exact ticks in this local replay are an implementation check, not a replacement scientific criterion.

The selected support's mean vector differences across halvings are 2.95%, 2.91% and 2.21%; these descriptive mean comparisons pass. Stable means and persistent ordering against three fixed comparisons are useful but do not establish convergence of individual responses or a continuous-time limit. No tolerance, seed, support or failed result was removed.

## Research decision

Do not claim a converged functional eigencircuit. Retain two separate findings: descriptive localized response/order at stated model resolutions, and a selected-case demonstration of timing-sensitive downstream propagation. Present them with their unresolved numerical and comparison limitations.

The next priority should return to the numerical question with the advisers, rather than another comparison optimizer or burst intervention. Prepare a proposal that states whether the desired claim requires paired-trajectory convergence or a separately defined distribution-level stability question. A distribution-level study would be a new estimand and design, not a retrospective rescue of the failed paired study. Existing seeds can support exploratory descriptions but not an unacknowledged fresh confirmation.

If pursuing paired convergence, another smaller timestep alone has no guaranteed value. Any new CCR proposal should specify which failed quantities are targeted, fixed inputs/seeds/supports, bounded resources, recording sufficient to diagnose disagreement, and unchanged criteria or an explicitly justified prospective amendment. This memo does not select a new timestep, allocate resources or authorize a run.

For eigencircuit specificity, better comparison design remains independently necessary. Optimized sets are not random null samples; mutual-only pairs can meet a CDF gap while having incoming-degree variance ratios above nine. More seeds cannot fix that structural imbalance. The original support question remains open even if a numerical follow-up succeeds.

## Status for the morning

The bounded overnight deliverables are complete: source/reconstruction audit, conditional crossing calculation, free-running local-prefix replay, separate checks, and a convergence/next-experiment memo. No new full-network run or upload is pending from this work. The automation should now pause rather than manufacture additional searches until its morning deadline.

Code, methods, tests, analysis and documentation used Codex assistance. Separate algorithms and archived-output checks do not constitute independent human review or competition compliance certification.
