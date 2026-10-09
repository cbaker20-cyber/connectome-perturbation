# Joint comparison-family construction — 8 October 2026

The first bounded joint search reached its internal time limit without an integer candidate pair. It did not establish feasibility, infeasibility or an optimal matching gap. The attempt and its unchanged protocol are preserved. No simulation or retry was launched.

## Logic review and declared question

The [saved-family audit](FAMILY_CAPACITY_20261008.md) exhaustively limits combinations of nineteen existing memberships. It does not constrain every possible membership in the 999-cell pool. The individual distribution searches capped overlap against fifteen older references, but not against each other. Thus neither analysis answers whether jointly choosing new memberships can yield a better mutually diverse family.

The new question is whether two sets chosen simultaneously can improve that design tradeoff. Two is the smallest family that introduces a mutual-overlap constraint. This is an exploratory construction question informed by earlier outcomes, not an independently confirmatory test of eigencircuit specificity.

Recorded before execution:

- Use exactly the frozen 999-cell pool and the fifteen reference memberships from the verified expansion study.
- Select two binary 51-cell sets. Preserve target/input exclusions, exact sign/recruitment/motor counts and the existing conservative sufficient mean constraints for each set.
- Each new set shares at most thirty cells with every old reference and with the other new set. This retains the earlier reference constraint and adds mutual diversity; thirty is a design contrast, not a biological acceptance standard.
- Minimize the largest empirical-CDF gap across all six fixed features and both sets. There is no newly selected distribution-gap cutoff.
- Run one worker with sixty seconds inside the solver and a one-hundred-second external deadline. No retry, changed cap, expanded pool or simulation within this attempt.

These requirements are stronger than the earlier saved-family audit, which only required pairwise overlap within a chosen subset. Its three-set witness is therefore not a starting feasible solution for this joint problem. Failure here cannot invalidate that earlier witness.

## Formulation and implementation checks

For cell i, binary x_i and y_i indicate membership in each set. A continuous z_i lies in [0,1] with z_i >= x_i+y_i-1, z_i <= x_i and z_i <= y_i. At binary memberships these inequalities force z_i to equal their product. Therefore sum(z_i) <= 30 is exactly the required shared-cell cap; it does not merely constrain an approximation to overlap.

A common continuous t bounds both signs of every target-versus-comparison CDF difference at all combined observed feature thresholds, for each set separately. CDFs are constant between those thresholds, so minimizing t minimizes the stated worst gap. Both sets retain the original exact strata and sufficient mean rows. These sufficient bounds are stricter than the original pooled-SMD rule; any later full-pool or impossibility statement must retain that qualification.

Rows were assembled as sparse coordinates and converted to the solver's CSC format. The model has 2,998 variables, 16,614 constraints and 7,864,962 nonzero coefficients. Installed SciPy signatures were inspected; execution used SciPy 1.17.1, NumPy 1.26.4 and Python 3.11.9, with the full environment saved. Older frozen optimizer sources were not edited.

Fourteen formulation tests passed. Small known-answer problems compare the optimum with exhaustive pairs under several caps, including a jointly infeasible problem caused by the reference constraints. Failure tests reject fractional memberships, wrong intersection variables, excessive mutual overlap, understated CDF objectives, nonfinite values, malformed masks, invalid strata and invalid budgets/caps. Ten existing family-capacity tests also passed in that invocation (24 tests, 1.51 seconds).

Thirteen separate checker tests passed in 0.74 seconds. They distinguish verified optima, feasible time-limited incumbents, no-incumbent time limits, solver-reported restricted infeasibility and solver errors, and reject contradictory status/objective/bound records. This is algorithmically separate checking with Codex assistance, not independent human review.

## Completed attempt

The solver returned status 1, time limit reached, with no integer incumbent. Objective, dual bound and relative gap were all absent. The worker completed normally in 64.375 seconds including loading and construction, before its one-hundred-second external deadline. Stderr was empty. No candidate or solution-vector file was produced.

The independent status checker verified frozen inputs, protocol dimensions, process completion and consistency of the result/candidate inventory. Its outcome is `time_limit_without_incumbent`. There are no memberships whose scientific properties can be validated, and no new solver bound to report. A successful process exit here means the bounded attempt completed and saved its outcome; it does not mean the research construction succeeded.

Full evidence is in results/pcdr/joint_family_20261008. The [compact snapshot](evidence/2026-10-08/joint_family/snapshot.json) preserves the [protocol](evidence/2026-10-08/joint_family/protocol.json), solver/process records, environment and [status verification](evidence/2026-10-08/joint_family/verification.json), with hashes and test counts. The date is local 8 October; recorded UTC timestamps fall on 9 October.

## Decision and remaining work

Retain the attempt as unresolved computational evidence. Do not call the design impossible, imply a feasible pair exists, or launch lesion simulations. Do not automatically extend the original budget after seeing this outcome. The earlier saved-family limits, matching results and eighteen failed numerical convergence groups remain unchanged.

Before allocating more compute, a separate plan should assess whether a computational reformulation or a CCR run is justified. Relevant options include removing the exchange symmetry between the two sets, establishing a validated feasible starting pair, or deriving a relaxation bound. Those options are proposed, not implemented or executed here; none justifies silently changing the scientific constraints. Heavy computation belongs on CCR under a recorded resource budget.

The original eigencircuit question remains open. Matching and diversity are necessary design concerns, but an optimized pair alone would not establish adequate confounder control, a random-reference significance claim, numerical convergence or behavioral relevance. The [current evidence boundaries](FAMILY_CAPACITY_20261008.md#research-decision-and-evidence-boundaries) remain applicable.

## Reproduction and assistance

Use unused output paths; the runner refuses an occupied study directory:

```text
.venv/Scripts/python.exe -m pytest tests/test_pcdr_joint_family.py tests/test_pcdr_family_capacity.py -q
.venv/Scripts/python.exe -m pytest tests/test_pcdr_verify_joint_family.py -q
.venv/Scripts/python.exe scripts/pcdr_joint_family.py --out <unused-directory>
.venv/Scripts/python.exe scripts/pcdr_verify_joint_family.py --study <directory> --out <unused-verification.json>
```

Code, formulation review, tests, execution, status checks and documentation used Codex assistance. These checks support the recorded calculation and reporting logic; they do not certify that every aspect of the broader research is correct or that an eventual competition submission meets all requirements.

The subsequent [fixed-anchor alternative and overlap-bound check](ANCHOR_FAMILY_20261008.md) is complete. Both existing capped anchors require overlap above 31 under the retained constraints, so neither extends at cap thirty. This resolves those conditional problems, not the general joint search above.
