# Capacity of the saved comparison family — 8 October 2026

The nineteen saved comparison sets cannot provide two sets that both have maximum feature-CDF gap at most 11/51 and share at most thirty cells. At that overlap limit, a three-set family requires a gap allowance of at least 16/51. These are exact statements about the saved sets, not impossibility results for the full eligible cell population.

## Question and recorded design

The [distribution-matching searches](DISTRIBUTION_MATCHING_20261008.md) improved individual candidates but left substantial overlap. This continuation asks how many existing candidates can coexist under simultaneous distribution and pairwise-overlap requirements. It does not construct new memberships or inspect additional lesion outcomes.

Included all three original comparisons, all twelve accepted diverse-search witnesses, and all four candidates from the 538- and 999-cell distribution searches. All nineteen memberships are distinct. Original source/input hashes and completed verification records were checked. A separate protocol recorded the exact memberships, source hashes and complete threshold grid before enumeration. This is a retrospective design audit of existing results, not a prospective biological experiment.

For each set, recomputed the largest empirical-CDF gap across the six baseline log1p features. Because both groups contain 51 cells, each gap is an integer count divided by 51. Examined every gap allowance from 0/51 through 51/51 and every shared-cell cap from zero through 51. No favorable acceptance threshold was selected after inspecting the family results. The thirty-cell cap below is highlighted because it was already used in the previous design, not because thirty is a biological standard.

Enumerated all 524,288 subsets. Each subset has a largest member CDF gap and a largest pairwise overlap. For each of the 2,704 threshold combinations, retained the maximum family size and a witness. A separate graph search checked every maximum: candidate sets are vertices and an edge joins pairs whose overlap meets the cap. Its largest complete subgraph gives family capacity. A singleton has no pairwise-overlap requirement; its reported minimum cap is zero.

## Completed results

| Maximum allowed CDF gap | Largest saved family with every pair sharing at most 30 cells |
|---|---:|
| 8/51 = 0.156863 | 1 |
| 10/51 = 0.196078 | 1 |
| 11/51 = 0.215686 | 1 |
| 14/51 = 0.274510 | 2 |
| 16/51 = 0.313725 | 3 |
| 17/51 = 0.333333 | 3 |
| 18/51 = 0.352941 | 3 |

These are the observed candidate gap levels; capacity is constant between them. No candidate has a smaller gap than 8/51 or a larger gap than 18/51. Even allowing all nineteen candidates, no four-set family satisfies the thirty-cell pairwise cap.

Among candidates with gap at most 10/51, the least possible overlap for a pair is 38 cells. A three-set family at gap at most 11/51 requires allowing 47 shared cells. At gap at most 16/51, one three-set witness under the thirty-cell cap is motor_003, new_1 and pool_538_cap_30. This witness mixes an original simulated comparison with unsimulated candidates; it is not a recommendation to run them or a new response result.

The individual capped optimizations constrained overlap against fifteen previous references. They did not constrain overlap against other solutions from those optimizations. Therefore their success never established a mutually diverse family of well-matched candidates. The completed audit measures that distinction directly.

## Checks and limits

All nineteen sets pass exact ID, size, target/input exclusion, sign/recruitment/motor composition and original pooled-SMD checks. This audit uses the original pooled-SMD rule for the mixed collection; it does not retroactively impose the newer sufficient mean bounds on the three original sets. All comparisons use the same frozen baseline features and recruitment labels.

Ten focused tests passed in 2.85 seconds. They compare all thresholds on a small example against direct subset enumeration and check empty collections, singletons, invalid counts, asymmetry, invalid diagonals and the exhaustive-search size limit. Research execution completed locally in about 7.4 seconds. All 2,704 research maxima agree with the independent graph algorithm. Additional checks reproduced all CDF maxima using raw-feature integer counts, all overlaps using a membership-incidence matrix product, and every saved frontier witness's requirements. All frozen-input and snapshot-copy hashes match.

This is exhaustive over nineteen saved sets only. They were optimized through related searches, use overlapping cells, and are not a calibrated random ensemble. The thresholds describe a tradeoff; they do not certify adequate confounder control. Full-pool feasibility, behavior and numerical convergence were not tested here.

## Research decision and evidence boundaries

Do not launch another lesion batch using these candidates merely because individual matching improved. The collection does not meet the previously used thirty-cell diversity contrast at the better observed gap levels. The next construction question is whether new memberships can satisfy family-wide constraints simultaneously. A future design must specify the number of sets, matching requirements, exclusions, pairwise constraints, solver budget and treatment of time-limited or infeasible results before execution. No such new search or simulation has been launched, and no cutoff is promoted here to a scientific acceptance standard.

The original question remains whether concentrated eigenvector supports predict localized output-lesion response beyond degree/strength, strong connections and recruitment. Keep the following boundaries in research explanations and any later submission draft:

| Evidence | Completed conclusion | Unresolved claim |
|---|---|---|
| [Fine-step contrasts](RESEARCH_CONTINUATION_20261008.md) | Selected support exceeds three fixed comparisons in the audited same-step paired A/F summaries | Eigenvector membership uniquely explains the difference |
| [Numerical study](FINE_TIMESTEP_RESULTS_20261005.md) | Group means are relatively stable; all eighteen full agreement criteria failed | Individual responses have converged |
| [Separate G/H intervention](SEPARATE_PATHWAY_RESULTS_20261008.md) | Either single removal interrupts broad recruitment in the selected coarser-step case; references reproduce | Generality, sufficiency, biological bursting or eigencircuit specificity |
| [Matching and pool expansion](DISTRIBUTION_MATCHING_20261008.md) | Better individual CDF matching is feasible, with remaining variance and overlap limits | Adequate control or a random-reference significance test |
| This family audit | Exact capacity of the nineteen saved candidates under every threshold pair | Full-pool impossibility or a validated new comparison ensemble |

Code, analysis, independent recalculation and documentation used Codex assistance. These records do not establish independent student authorship or certify competition compliance. They preserve what was done and what remains to be explained and defended by the researcher.

## Reproduction

Use the recorded local environment and an unused output directory:

```text
.venv/Scripts/python.exe -m pytest tests/test_pcdr_family_capacity.py -q
.venv/Scripts/python.exe scripts/pcdr_family_capacity.py --out <unused-directory>
```

The runner rejects occupied output directories and verifies the earlier evidence before recording its protocol. Full records are in results/pcdr/family_capacity_20261008. The [compact snapshot](evidence/2026-10-08/family_capacity/snapshot.json) preserves hashes for the protocol, exact frontier witnesses, environment and completion record. Earlier frozen studies and the current upload artifact were preserved.
