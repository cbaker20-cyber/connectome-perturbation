# Alternative construction and constraint review — 8 October 2026

Neither of the two existing capped comparison sets can be extended by a partner sharing at most thirty cells under the recorded 999-cell design. Two conditional integer searches reported infeasibility. Separate fractional overlap minimizations and independently evaluated lower bounds support that result: the required overlap exceeds 31 cells for either anchor. This does not establish that a different jointly chosen pair is impossible.

## Why try fixed anchors?

The [joint two-set attempt](JOINT_FAMILY_20261008.md) reached its time limit without a candidate or bound. A smaller conditional problem fixes one set and searches for its partner. It removes the need to optimize two memberships and their intersections simultaneously, but restricts the search: failure applies to the fixed set only.

Before execution, recorded both available old-reference-capped anchors: the 538-pool solution with CDF gap 11/51 and the 999-pool solution with gap 10/51. Both were already verified and lie in the 999-cell pool. The uncapped optimized sets are excluded because they fail the fifteen old-reference caps. No anchor was selected based on a new lesion outcome.

Each case retained the 999-cell pool, exclusions, exact sign/recruitment/motor counts, conservative sufficient mean bounds and fifteen old-reference caps. Adding the fixed anchor as a sixteenth capped reference enforces mutual overlap <=30. The original frozen single-set optimizer minimized the partner's maximum CDF gap. If solved, this would also minimize the pair's worst gap conditional on that anchor, after taking the maximum with the anchor's fixed gap. It would not establish the global joint optimum.

Both case protocols were recorded before either search. Each had sixty seconds internally and one hundred seconds externally, with no retry or altered constraints.

| Fixed anchor | Worker time | Solver outcome | Candidate |
|---|---:|---|---|
| Capped 538-pool solution | 27.031 s | Restricted conditional problem infeasible | None |
| Capped 999-pool solution | 26.469 s | Restricted conditional problem infeasible | None |

Both workers returned normally, before either deadline, with empty stderr. Each model had 1,000 variables, 6,809 constraints and 3,928,536 nonzero coefficients. The result inventories and frozen inputs were checked. Solver reports alone are not treated as independent mathematical evidence; the following diagnostic addresses that limitation.

## A separately recorded overlap-bound diagnostic

After those reports, recorded a second diagnostic before running it. Minimize overlap with each anchor while allowing membership weights between zero and one. Retain exact stratum totals, sufficient mean bounds and caps against the fifteen older references. Remove all CDF rows and the new anchor cap. Every valid integer partner would be feasible in this less restrictive problem and have the same overlap objective.

This diagnostic cannot produce a lesion set: its solutions contain fractional memberships. Its purpose is a lower bound. Two LPs had ten seconds each inside a single worker with a forty-second external deadline. The worker completed in 2.953 seconds with return code zero and empty stderr. Both primal solutions satisfy the recorded constraints to below 3e-15 and each has ten fractional cells.

| Fixed anchor | Fractional minimum overlap | Conservatively adjusted numerical lower bound | Exact rational evaluation of saved-coefficient dual bound |
|---|---:|---:|---:|
| Capped 538-pool solution | 31.993578724 | 31.993096894 | 31.993578724 |
| Capped 999-pool solution | 31.362362134 | 31.362020152 | 31.362362134 |

Thus both integer partner problems require at least 32 shared cells under these constraints. A cap of thirty fails even when CDF matching is removed. Allowing a larger CDF gap alone cannot rescue either fixed-anchor construction.

### How the bound was checked

Write the fractional problem as minimizing c'x with Ax <= b, Ex = d and 0 <= x <= 1. For any inequality multipliers y <= 0 and unrestricted equality multipliers z, a lower bound is

```text
b'y + d'z + sum_i min(0, c_i - (A'y)_i - (E'z)_i).
```

For every feasible x, the Lagrangian is no greater than c'x. Minimizing its residual linear expression over the unit box gives the formula. This avoids relying on an approximately zero stationarity residual. Positive inequality multipliers are clipped to zero before evaluation. The numerical calculation subtracts an explicit guard proportional to accumulated term magnitudes; its values are reported, not hidden.

A separate checker rebuilt the intended feature, count and reference rows directly from the feature table, agreeing with the saved matrices within 1e-14. It then converted each saved binary floating-point coefficient and multiplier into an exact rational number and evaluated the formula without floating-point summation. Exact numerators and denominators are preserved in verification.json. The exact result applies to the encoded numerical LP; it is not a claim of exact real arithmetic for underlying logarithms or biological quantities. Both adjusted numerical margins above thirty are large compared with the reported guard.

The additional bounds are diagnostic follow-up work, not a retrospectively changed criterion for accepting a candidate. The original integer attempts and joint timeout remain preserved.

## Flaws and alternative approaches

| Approach or concern | What it can establish | Limitation and current decision |
|---|---|---|
| Reusing these two individually optimized anchors | A conditional partner if one exists | Completed: both cannot meet the thirty-cell cap under this design. Stop repeating these anchored searches. |
| Simultaneously choosing two new sets | Existence or an optimum within the recorded joint design | Still unresolved. Both memberships may need to move away from individual optima. The previous timeout establishes neither success nor impossibility. |
| Removing exchange symmetry in a joint model | Potentially reduce duplicate search over the same unordered pair | Proposed. A safe ordering must retain at least one orientation of every feasible pair and pass equivalence tests before use. It does not repair scientific confounding. |
| Continuous relaxation of a joint model | A lower bound on its objective | Proposed. Fractional memberships are not sets; relaxed intersection variables can substantially understate physical shared memberships. Never round them into an accepted pair without checking every constraint. |
| More CCR time | A larger computational allowance | Not automatically justified by a timeout. First record a revised computational plan and expected diagnostic value; no new CCR run was launched. |
| Caps against all fifteen older references | Enforces novelty relative to earlier memberships | This is a design choice, not a requirement derived from the eigencircuit hypothesis. Keeping it may make construction unnecessarily restrictive. Removing it would be a separately declared design amendment, not an invisible implementation fix. |
| A thirty-cell mutual cap | Requires at least twenty-one different cells in a pair | Does not imply independent responses, especially if substituted cells stay silent. No biological adequacy threshold has been established. |
| Six-feature marginal CDF matching | Describes each feature's marginal distribution | Does not match joint feature dependence, exact motor identity or all structural causes of response. Persistent variance differences remain relevant. |
| Sufficient mean bounds and restricted candidate pool | Make a bounded construction possible | Stricter than the original pooled-SMD criterion and smaller than the full eligible population. Infeasibility cannot be generalized beyond those restrictions. |
| Original baseline recruitment labels | Preserves a common frozen design | They were not recalculated at finer time steps. Apparent baseline balance does not resolve numerical sensitivity of lesion responses. |
| Optimized comparison families | Can test specified alternatives descriptively | They are not a calibrated random ensemble. More optimized sets or more seeds alone cannot justify random-control significance. |

A simple relaxation example explains one computational caution. With eligible feature values [0,1,1,2], target [0,2] and two disjoint two-cell sets, assigning weight 0.5 to every cell in both sets allows relaxed intersections of zero. Those are fractional weights, not disjoint neurons. The two integer sets have a worst CDF gap of 0.5, while those relaxed weights achieve 0.25. A relaxed bound can therefore be useful without being an attainable integer design.

## Decision and research direction

The anchored approach provided useful negative evidence and a reason to stop that branch. Do not spend more time on the same two anchors. The general pair construction remains unresolved; the existing capped single-set optimum of 10/51 is a numerical lower bound on its worst gap because each member must satisfy those same single-set constraints. No feasible pair or new upper bound was found here.

The next design review should separate the scientific goal of mutual diversity from the additional requirement of novelty against every old reference. A separately declared mutual-only construction would answer a different, potentially more direct question; it must not be reported as solving the original stronger problem. Alternatively, retain the stronger problem and test a symmetry-reduced formulation before allocating CCR resources. Neither alternative was implemented or run here.

The original question remains whether concentrated eigenvector supports predict localized outgoing-lesion responses beyond degree/strength, strong connections and recruitment. These construction results do not supply new lesion effects, resolve the eighteen failed convergence groups, generalize the selected G/H intervention, or establish eigencircuit specificity. Numerical and comparison-design limitations remain separate obstacles.

## Evidence and checks

Thirty-five focused tests passed across the anchored wrapper, frozen single-set solver, status interpretation, numerical lower-bound evaluator and rational verifier. Known-answer tests include exact small partner selection, exhaustive small optima, inconsistent solver records, invalid anchors, invalid multipliers and a residual correction that prevents a false dual bound. Tests supplement the direct research-output checks; they do not certify the entire study.

Full records are in results/pcdr/anchor_family_20261008 and results/pcdr/anchor_bound_20261008. Compact snapshots preserve [conditional-search evidence](evidence/2026-10-08/anchor_family/snapshot.json) and [overlap bounds with independent verification](evidence/2026-10-08/anchor_bound/snapshot.json). Exact LP matrices and fractional vectors remain local, with hashes. Snapshot copies were checked against originals. Local date is 8 October; UTC records use 9 October.

Reproduction uses the recorded local environment and unused output paths:

```text
.venv/Scripts/python.exe scripts/pcdr_anchor_family.py --out <anchor-study>
.venv/Scripts/python.exe scripts/pcdr_anchor_bound.py --source <anchor-study> --out <bound-study>
.venv/Scripts/python.exe scripts/pcdr_verify_anchor_bound.py --study <bound-study> --out <new-verification.json>
```

No prior frozen optimizer, simulation source, result or upload was changed. Code, mathematical formulation, tests, analysis and documentation used Codex assistance; the separate implementations are not independent human review.
