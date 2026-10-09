# Reference-cap ablation and amended pairs — 8 October 2026

The combination of both old-reference groups obstructs extension of the two fixed anchors. Either group alone leaves fractional minimum overlap near 21–22 cells; together they require more than 31. Removing both groups allowed independently verified integer partners at exactly thirty shared cells. Those partners have substantial degree-variance imbalance and are not ready-made biological controls.

## Recorded design

This follows the [fixed-anchor overlap bounds](ANCHOR_FAMILY_20261008.md). Before any calculation, recorded all four combinations of retaining the original-three and newer-twelve reference caps for each of the two anchors. Eight fractional minimum-overlap problems retain the frozen 999-cell pool, exclusions, exact strata and conservative sufficient mean constraints. No CDF rows enter these diagnostic LPs. This is complete over the declared two-factor design, not exhaustive over every reference subset or biological explanation.

Also recorded two integer partner searches before either diagnostic or integer run. These explicitly remove all old-reference caps, retain overlap <=30 with the fixed anchor, and minimize the partner's maximum six-feature CDF gap. Both anchors are used regardless of the diagnostic outcomes. This is an amended, weaker design; success cannot solve the original stronger problem.

Budget: eight LPs with ten seconds each in one worker with a one-hundred-second external deadline; two serial integer searches with sixty seconds each internally and one hundred seconds externally. No retries, threshold changes, pool expansion or simulation.

## Eight completed overlap diagnostics

| Reference caps retained | Minimum fractional overlap, 538 anchor | Minimum fractional overlap, 999 anchor |
|---|---:|---:|
| Neither group | 20.132002 | 20.195344 |
| Original three only | 21.305643 | 21.222819 |
| Newer twelve only | 22.022677 | 21.997464 |
| Both groups | 31.993579 | 31.362362 |

All eight LPs completed in a combined worker time of 3.234 seconds. Independently reconstructed rows agree within 1e-14, primal solutions pass the constraints, and exact rational evaluation reproduces the dual lower bounds for the saved floating-point coefficients. The explicit guarded bounds for the both-groups cases remain 31.993097 and 31.362020. The old results reproduce. Adding constraints never improves the minimum, as independently checked across the factorial design.

Both groups jointly create a stronger restriction than either group alone in this diagnostic. This does not establish which individual reference or cell causes the restriction. Fractional solutions below thirty with one group removed do not prove integer feasibility for those regimes; those integer cases were not run.

## Two independently verified amended pairs

| Fixed anchor | Partner CDF gap | Pair's worst CDF gap | Mutual overlap | Partner incoming-degree variance ratio | Worker time |
|---|---:|---:|---:|---:|---:|
| Capped 538-pool solution | 10/51 | 11/51 | 30 | 9.141 | 63.609 s |
| Capped 999-pool solution | 10/51 | 10/51 | 30 | 10.428 | 63.500 s |

Both integer solvers reached the internal time limit with valid incumbents. Their partner-objective lower bounds were 0.174646 and 0.173194, respectively; neither establishes optimality of the partner objective. Recorded relative gaps are about 10.93% and 11.67%. External deadlines were not reached, all workers exited normally and stderr was empty.

There is a separate conditional conclusion: each partner's gap is no worse than its fixed anchor's gap. Therefore each pair attains the fixed anchor's unavoidable floor for the pair maximum. The pair maximum is optimal conditional on that anchor and this amended feasible set, despite unresolved optimality of the partner-only objective. This does not imply optimality among all freely chosen pairs.

Independent checks validate exact IDs, pool membership, exclusions, 51-cell size, exact strata, sufficient means, original pooled SMD, direct threshold-count CDF gaps and mutual overlap. Largest partner SMDs are 0.069903 and 0.070459. The partners share 38–40 cells with original references and exceed thirty for some newer references. They explicitly fail the original stronger novelty requirement. No candidate membership or acceptance criterion was changed after the results.

## Why this is not yet adequate matching

CDF distance limits a fraction of cells at thresholds, but does not bound how far an extreme value lies beyond the target's range. Mean matching can also coexist with large dispersion. The new partners illustrate both limits.

A separately labeled post-result diagnostic inspected incoming-degree tails. Target incoming degrees range from 131 to 484, with log1p variance 0.062767. Both new partners include cell 720575940627712019 with incoming degree 5. It accounts for 47.40% and 41.53% of their respective total squared deviations in log1p incoming degree. Their degree ranges are 5–1,184 and 5–3,195. Their log variances are 0.573750 and 0.654538, explaining the ratios above. These contributions describe variance; they are not evidence that this cell causes a lesion response.

The anchors themselves remain imperfect: both include a cell with incoming degree 3,207, and their incoming-degree variance ratios are about 4.52 and 4.74. Finding a diverse partner therefore does not repair the anchor's imbalance. Silently removing extreme cells after inspecting them would alter the design and could select a favorable result; no such removal occurred.

## Decision

Retain the amended pairs as unsimulated feasibility witnesses. The obstruction was partly a consequence of enforcing novelty against old references, and the weaker mutual-only construction is feasible for both anchors. That is useful design evidence, not proof of eigencircuit specificity or adequate confounder control.

Do not launch a lesion batch on these witnesses merely because the mean/CDF and overlap conditions pass. The next matching question should address magnitude-sensitive imbalance directly, under a new recorded objective or constraint. Possible approaches include matching second moments or a distance sensitive to feature magnitudes. They have different tradeoffs and must not be chosen solely to remove a cell noticed in these results. No new metric, cutoff or search is declared or executed here.

The original stronger joint problem remains unresolved. The current eight-case diagnostic does not exhaust all pools, anchors, reference subsets, matching rules or mechanisms. The eighteen failed numerical convergence groups also remain a separate issue. An optimized pair cannot create a calibrated random ensemble, establish behavior or generalize the selected G/H intervention.

## Verification and records

Thirty-six focused tests passed in 2.68 seconds, with 26 dependency deprecation warnings. These cover the complete reference-group partition, no-reference matrix construction, invalid inventories, bound arithmetic, exact rational evaluation, membership failures and solver-status interpretation. The independent research checker completed all eight LP and both partner audits. Its status labels concern partner solver optimality; the conditional pair-floor deduction is recorded separately.

Full evidence: results/pcdr/reference_ablation_20261008. The [compact snapshot](evidence/2026-10-08/reference_ablation/snapshot.json) includes frozen protocols, processes, results, exact bound checks, memberships and the explicitly post-result degree-tail diagnostic. Large LP matrices, fractional vectors and integer solution vectors remain local with hashes. No older frozen source, result or current upload was replaced.

Reproduce with the recorded environment and unused paths:

```text
.venv/Scripts/python.exe scripts/pcdr_reference_ablation.py --out <unused-study>
.venv/Scripts/python.exe scripts/pcdr_verify_reference_ablation.py --study <study> --out <unused-verification.json>
```

Local date is 8 October; UTC timestamps fall on 9 October. Code, tests, formulation, separate recalculation and documentation used Codex assistance. Separate algorithms do not constitute independent human review.
