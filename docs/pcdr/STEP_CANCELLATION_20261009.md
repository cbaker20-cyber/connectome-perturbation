# Baseline and lesion contributions to cross-step disagreement — 9 October

Default baseline activity contributes substantially to the failed response agreement. At the final halving, its median neuronwise L1 difference is 578.5 Hz, compared with 309.5 Hz for the selected-support lesion. Only four of thirty seeds have a larger lesion than baseline difference. The selected altered-weight burst therefore cannot serve as an explanation of the entire default-network convergence failure.

## Recorded analysis

The earlier FINE_DIFFERENCES_20261005.md already established that disagreement is distributed across neurons; that analysis was not repeated. Instead, recorded a new paired decomposition over all thirty default seeds, four lesion conditions and three adjacent halvings, using all 600 relevant trials. The plan, archive, neuron inventory and each consumed rate file were checked against verified archived records. Read one seed at a time to bound memory. No new simulation, seed, exclusion, threshold or statistical test.

Let a = baseline_coarse − baseline_fine and b = lesion_coarse − lesion_fine. Then the change in the paired lesion-minus-baseline response is b − a. For each neuron,

```text
|b − a| = |a| + |b| − 2 min(|a|, |b|) 1[a and b have the same nonzero sign].
```

Summing gives the combined baseline/lesion difference minus same-direction cancellation. These are algebraic components, not independent causal effects. The same baseline is reused for four comparisons per seed. The thirty seeds, not the 120 condition rows, define the seed replication count at a halving.

## Completed findings

Selected-support lesion:

| Halving (ms) | Median baseline L1 (Hz) | Median lesion L1 (Hz) | Median paired-response L1 (Hz) | Pooled cancellation | Seeds with lesion L1 > baseline L1 |
|---|---:|---:|---:|---:|---:|
| 0.0008 → 0.0004 | 706.0 | 420.5 | 849.0 | 22.22% | 0/30 |
| 0.0004 → 0.0002 | 698.5 | 406.5 | 812.5 | 23.27% | 0/30 |
| 0.0002 → 0.0001 | 578.5 | 309.5 | 693.5 | 18.99% | 4/30 |

L1 here is the sum of absolute differences in each neuron's full-second firing rate. It is not a population net-rate difference, a per-neuron average or the original A metric. Pooled cancellation divides summed cancelled L1 by the summed baseline-plus-lesion L1 across seeds. Medians are computed separately and must not be added/subtracted as if they obeyed the per-seed identity.

At the final halving, the three fixed comparator lesions have median L1 differences 489.5, 528.5 and 420.5 Hz; paired-response medians are 748.0, 813.5 and 710.0 Hz. Pooled cancellation is 21.31%, 20.16% and 19.22%. Their lesion L1 exceeds baseline in 9, 11 and 8 of thirty seeds, respectively. Thus this is not unique to the selected support, although the baseline and related comparisons are shared and cannot be treated as independent confirmations.

Cancellation reduces the component sum but does not make the paired response converge. All eighteen original full agreement groups remain failed. Smaller component medians at the final halving do not prove a limiting rate, monotonic convergence for individual seeds or eventual convergence at an untested step.

## Decision for further numerical work

A next numerical proposal should include explicit checks of the unlesioned default baseline, as well as the paired lesion response and both population time courses. Diagnosing only lesion-specific propagation would leave a substantial baseline contribution unexamined. The altered-weight G/H result concerns a different configuration and cannot resolve these default-network failures.

Before any CCR run, identify whether the original trajectory-level question remains the goal or whether a separate distribution-level question is justified. Keep the original failed criteria. A new estimand or changed tolerance requires an explicit prospective design rather than reinterpretation of these outcomes. This analysis authorizes no new run and chooses no finer timestep.

The cancellation identity does not assign a unique percentage of the response error to baseline versus lesion: their signs and covariance matter. A larger baseline L1 is not proof that baseline error caused every observed response difference. Nor does a smaller lesion L1 establish that lesions stabilize the biological network. Those claims would require different evidence.

## Verification and evidence

Six focused known-answer/failure tests passed in 1.46 seconds, including complete cancellation, opposite signs, zero vectors and invalid shapes/values. All 360 response distances reproduce the original independently verified relative distances using their finer-step denominators, within 1e-12. All 120 final-halving absolute distances match the prior spike-derived analysis exactly. Every baseline-plus-lesion-minus-cancellation identity is exact in the saved outputs.

Full evidence: results/pcdr/step_cancellation_20261009. The [compact snapshot](evidence/2026-10-09/step_cancellation/snapshot.json) preserves protocol, all paired rows, summaries, hashes and verification/environment. Earlier source, simulations, criteria and uploads were unchanged. Reproduction: `.venv/Scripts/python.exe scripts/pcdr_step_cancellation.py --out <unused-directory>`; tests: `tests/test_pcdr_step_cancellation.py`.

Code, analysis, checks and documentation used Codex assistance. Separate arithmetic checks are not independent human review.
