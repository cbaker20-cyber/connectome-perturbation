# Distribution matching and unavoidable imbalance — 8 October

Two bounded local searches produced independently verified 51-cell comparison candidates with better feature-distribution matching than the recently found twelve-set family. A separate full-pool bound shows that the existing exact composition rules themselves prevent perfect distribution matching. No lesion simulation or new CCR upload was run.

This continues the [fine-step contrast and diversity analysis](RESEARCH_CONTINUATION_20261008.md). That analysis established persistent response ordering against three fixed comparisons, while documenting their narrow membership diversity. The work here concerns the comparison design, not new evidence for an eigencircuit-specific response.

## Declared design

The objective minimizes the largest empirical cumulative-distribution gap across the same six baseline log1p features: incoming/outgoing degree, incoming/outgoing strength, baseline firing rate and strong outgoing mass. For each feature, the gap is the largest difference in the fraction of cells at or below a value. It is a descriptive matching quantity, not a significance test.

Retained the 51-cell target, target/sugar-input exclusions, exact model-sign/recruitment/motor counts, and the existing conservative sufficient mean constraints. Those constraints imply the original pooled-SMD rule but are stricter; they are a computational restriction, not a redefinition of earlier accepted sets. Recruitment labels remain from the original frozen baseline feature table, not newly recalculated at the finer steps.

The candidate pool contains the union of all three original comparisons, all twelve newer witnesses, and the twenty nearest eligible cells to each target cell within its exact stratum. Distance is squared Euclidean distance across the six log1p features divided by their full-feature-table standard deviations. Exact root ID breaks ties. This baseline-only construction yields 538 candidate cells; it does not cover all 126,935 eligible cells. No lesion outcome enters candidate selection.

Recorded two binary optimization problems before execution:

1. Minimize the maximum distribution gap without an overlap cap.
2. Minimize the same gap while sharing at most 30 cells with each of the fifteen existing comparisons. This requires at least 21 changed members relative to each existing set. Thirty is a declared design contrast, not a biological standard or retrospectively chosen outcome threshold.

Each worker had a 60-second internal limit and a 100-second external deadline including loading and validation. No retry, enlarged pool or altered objective was allowed in this run. The objective was optimized directly; no distribution cutoff was chosen after inspecting the results. Continuous objective value accompanies binary cell memberships; fractional neurons are never accepted.

## Results

| Search | Maximum CDF gap | Largest pooled SMD | Incoming-degree variance ratio | Overlap with existing sets | Worker time |
|---|---:|---:|---:|---|---:|
| No overlap cap | 8/51 = 0.156863 | 0.070704 | 3.438 | 34–35 with original three; 29–30 with newer twelve | 9.17 s |
| At most 30 shared cells | 11/51 = 0.215686 | 0.070098 | 4.522 | 29–30 with original three; 30 with newer twelve | 18.05 s |

Both workers exited successfully with empty stderr. HiGHS reports an optimal solution with zero relative gap and matching primal/dual objective bounds for each restricted problem. This is numerical solver optimality within this candidate pool and these constraints, not a proof of the best possible full-pool comparison. The two new candidates share 39 cells with each other; the cap was against the fifteen previous sets, not against one another.

An independent checker reconstructed the candidate pool from original features and exact IDs, checked frozen hashes, and recalculated membership eligibility, size, exact strata, conservative mean bounds, original SMD, overlaps and all six CDF gaps. Its CDF calculation directly counts both sets at each observed threshold, separately from the optimizer's linear constraints. Recorded objectives agree with those calculations. Both candidates have complete source and environment provenance.

| Feature | No-cap CDF gap | Capped CDF gap | No-cap variance ratio | Capped variance ratio |
|---|---:|---:|---:|---:|
| Incoming degree | 0.1569 | 0.2157 | 3.438 | 4.522 |
| Outgoing degree | 0.1569 | 0.1961 | 2.724 | 3.389 |
| Incoming strength | 0.1373 | 0.1373 | 1.920 | 2.277 |
| Outgoing strength | 0.1569 | 0.1961 | 1.527 | 1.715 |
| Baseline firing rate | 0.1569 | 0.1569 | 0.926 | 0.924 |
| Strong outgoing mass | 0.1373 | 0.1176 | 1.106 | 1.117 |

The earlier twelve-set family had incoming-degree variance ratios 6.895–7.182 and maximum CDF gap 0.353. These new candidates improve those descriptions, but still have unequal feature distributions. The larger minimum gap in the capped problem quantifies a tradeoff between distribution matching and membership diversity in this restricted pool. No acceptance cutoff or biological equivalence claim follows.

## A full-pool limitation from exact strata

For each feature threshold, let N be a stratum's eligible population, L the number at or below the threshold, and k the required membership. Any valid set must select between max(0,k−(N−L)) and min(k,L) cells below the threshold. Sum these limits across strata and divide by 51. If the target CDF lies outside that possible interval, its distance to the interval is an unavoidable discrepancy at that threshold.

Calculated these bounds at every observed feature value for both the restricted pool and the full eligible pool. This uses sorted lookup operations, not enumeration of all cell subsets. It ignores mean constraints and overlap limits, so it provides a lower bound on achievable mismatch, not an achievable joint optimum. All features must ultimately be matched by the same cell set.

| Feature | Stratum-only lower bound on its maximum CDF gap, full eligible pool |
|---|---:|
| Incoming degree | 2/51 = 0.039216 |
| Outgoing degree | 5/51 = 0.098039 |
| Incoming strength | 4/51 = 0.078431 |
| Outgoing strength | 5/51 = 0.098039 |
| Baseline firing rate | 2/51 = 0.039216 |
| Strong outgoing mass | 0 |

The same bounds hold in the restricted pool; equality of these bounds does not establish equal optimization possibilities. Zero lower bound for strong outgoing mass does not prove exact matching is possible together with all other requirements.

The outgoing-degree bound has a direct explanation. There are exactly eight eligible recruited excitatory motor cells and every comparison must contain all eight. Six have outgoing degree at most 20, while only one target cell meets that threshold. Every admissible comparison therefore has at least 6/51 of its cells below that threshold versus 1/51 in the target: a gap of at least 5/51. The same forced six have outgoing strength at most 25, compared with one target cell. A separate raw-feature count reproduced both statements without the log1p CDF helper.

Thus searching harder cannot produce a zero-gap comparison under the existing exclusions and exact composition counts. The full-pool lower bound of 0.098 is below the observed optima of 0.157 and 0.216; additional improvement might be possible. The current calculations do not identify how much of that remaining difference comes from pool restriction, conservative mean bounds, overlap limits, or joint feature compatibility.

## Completed pool expansion

A separately recorded continuation increased the nearest-neighbor count from twenty to fifty per target. The pool grew from 538 to 999 cells and strictly contains the original pool. The original optimizer source, six features, sufficient mean constraints, exact strata, fifteen reference sets, overlap cap and 60/100-second budgets were unchanged. The two original optimized solutions were not added as new reference sets. The expansion protocol and source hashes were saved before either solve.

| Search in 999-cell pool | Maximum CDF gap | Largest pooled SMD | Incoming-degree variance ratio | Worker time |
|---|---:|---:|---:|---:|
| No overlap cap | 8/51 = 0.156863 | 0.070704 | 3.438 | 47.125 s |
| At most 30 shared cells | 10/51 = 0.196078 | 0.070955 | 4.741 | 52.594 s |

Both workers finished successfully with empty stderr, matching primal/dual bounds and zero reported relative gap. Independent reconstruction and direct CDF/count checks pass. The expanded models have 1,000 variables; the capped model has 6,808 constraints and 3,928,485 nonzero entries. The original 538-cell study also reproduces its previous verification fields with the updated checker.

The capped optimum improves by 1/51, establishing that the original restricted pool limited that objective. However, incoming-degree variance ratio worsens from 4.522 to 4.741 and baseline-rate CDF gap rises from 8/51 to 9/51. Optimizing the largest CDF discrepancy does not improve every feature measure. The uncapped optimum is unchanged; this does not establish a plateau across the full eligible pool.

Each expanded candidate selects one cell outside the earlier pool. The uncapped candidate shares fifty members with its predecessor; the capped candidate shares forty-seven. The two expanded candidates share thirty-nine members with each other. Their overlaps with the fifteen frozen references still meet the stated conditions. They remain unsimulated, highly overlapping optimized candidates, not independent draws. The stratum-only bounds are unchanged, including the unavoidable 5/51 full-pool bound.

The [expanded evidence snapshot](evidence/2026-10-08/distribution_expand/snapshot.json) records membership comparisons and hashes. Full evidence is retained in results/pcdr/distribution_expand_20261008. No earlier protocol or result was overwritten.

## Decision and next research step

Retain both candidates as unsimulated, optimized design results. They show that mean and distribution matching can improve while changing more memberships, but they do not form a random reference ensemble. Two mutually overlapping candidates and persistent variance differences do not establish adequate control of degree/strength or recruitment.

The bounded expansion is now complete. Retain both pool studies rather than selecting a candidate solely because its largest CDF gap improved. Further pool expansion is not automatically justified by the modest capped improvement, persistent variance imbalance and nearly unchanged memberships. Before another lesion experiment, the next design question is whether a family can achieve explicitly declared distribution and membership-diversity requirements simultaneously; that question remains proposed, with no acceptance thresholds or new runs chosen here. Allowing shared target motor identities would instead change the perturbation question and requires a separate design amendment.

The persistent fine-step ordering remains a descriptive result; all eighteen original convergence-group criteria remain failed. These baseline-only results supply no new lesion response, no behavioral measurement, no convergence claim and no eigencircuit-specific confirmation. Any later simulation must use a frozen candidate selection and explicit scientific question, and should not treat an optimized comparison as a random sample.

## Reproduction and evidence

Run with the recorded local `.venv/Scripts/python.exe`, using unused output paths:

```text
scripts/pcdr_distribution_match.py --out <new-study-directory>
scripts/pcdr_verify_distribution_match.py --study <study-directory> --out <new-verification.json>
-m pytest tests/test_pcdr_distribution_match.py tests/test_pcdr_verify_distribution_match.py -q
```

Twenty-four focused tests pass, with 26 dependency deprecation warnings. Tests compare solver results with exhaustive subset optima, check forced CDF bounds and infeasibility, and reject fractional candidates, invalid IDs, wrong counts, changed strata, insufficient pools, nonfinite inputs, incorrect mean/overlap constraints and understated CDF objectives. The installed SciPy 1.17.1 `milp` signature and supported options were inspected before implementation. Simulation code and its environment were not changed; the full simulation suite was not repeated.

The optimization has 539 variables and 4,441 constraints without the overlap cap (4,456 with it), with approximately 1.37 million nonzero matrix entries. Measured local runtimes stayed well inside the declared limits, so CCR was not needed for these design calculations.

Full evidence is in results/pcdr/distribution_match_20261008. The [compact snapshot](evidence/2026-10-08/distribution_match/snapshot.json) links hashes to the declared [protocol](evidence/2026-10-08/distribution_match/protocol.json), both candidates, solver/process records, and [independent verification with full-pool bounds](evidence/2026-10-08/distribution_match/verification.json). Original solution vectors and logs remain locally preserved. Code, analysis and documentation used Codex assistance; this is not an independently student-written submission.


Expansion reproduction uses `.venv/Scripts/python.exe scripts/pcdr_expand_distribution_pool.py --out <unused-directory>`, then the same independent verifier with `--study <directory> --out <new-verification.json>`. Thirty focused tests pass across `test_pcdr_expand_distribution_pool.py`, `test_pcdr_distribution_match.py` and `test_pcdr_verify_distribution_match.py` (26 dependency deprecation warnings). Added checks cover nested pools, deterministic exact-ID ties, stratum exclusions, invalid neighbor counts, duplicate IDs and ineligible reference members. No simulation suite was repeated because simulation code was unchanged. The expansion and its documentation also used Codex assistance.

The subsequent [saved-family capacity audit](FAMILY_CAPACITY_20261008.md) is complete. Across all nineteen saved candidates, no pair simultaneously meets a CDF gap allowance of 11/51 and a thirty-cell overlap cap. This is an exhaustive audit of existing memberships; construction of a new family remains proposed.
