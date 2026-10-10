# Numerical-study decision proposal — 10 October 2026

**Status: proposal for adviser discussion. No new simulations, seeds, solver or upload have been prepared or launched.** Keep the original eigencircuit question and the failed numerical results. The next run should answer a stated numerical question rather than merely produce a finer trace.

## The decision

The original result concerns localized paired lesion responses. The frozen study required both final adjacent timestep comparisons to pass its mean and individual-response criteria. All eighteen full groups failed. Stable averages and locally reproducible mechanisms do not change that result.

Ask the advisers to choose the numerical requirement before approving further compute:

| Route | Question it answers | What it cannot rescue |
|---|---|---|
| Extend paired-response resolution study | Do the same-seed lesion-response vectors and population traces agree over two additional halvings? | Earlier failures; comparison-set imbalance; biological validity. |
| Develop an independently validated event-handling reference | Does another well-specified treatment of thresholds, resets, refractory release and delayed arrivals agree on small networks, then selected full trajectories? | No reference implementation exists yet. Subthreshold exact integration alone is not this reference. |
| Separately designed ensemble study | Are explicitly chosen response summaries/distributions stable over resolution for a defined input ensemble? | It answers a different question and must not be described as passing the failed individual-response study. |

Recommendation: decide between these claims first. Do not automatically spend another allocation on the whole panel, and do not treat a CB4058 lesion as a numerical fix. That source supplies a mechanistic lead and a comparison-confounding alternative; it does not establish which numerical definition is appropriate.

## Concrete paired-resolution option to discuss

This is an explicit candidate extension, not an authorized launch design. Add 0.00005 and 0.000025 ms, retaining the existing 0.0001-ms outputs as the anchor. Evaluate both new adjacent comparisons. Preserve the one-second duration, saved physical external-input tapes, default parameters, outgoing-lesion semantics and frozen supports. No fresh eigenvector selection, time alignment, endpoint trimming or exclusion of problematic seeds.

**First gate: feasibility only.** Use baseline and mode for the first three original seed IDs, 631401–631403, at both new steps: twelve new trials. This deterministic small panel is a prospective restriction of already inspected seeds, not held-out confirmation or a representative sample. Its purposes are measured runtime/memory, output integrity and identifying continued disagreement. It cannot establish the thirty-seed criterion. One failed seed need not preclude 29/30; at least two failures within a condition and halving would preclude that original threshold for the full fixed panel, if those failed results are valid.

Record before execution a hard allocation/worker-hours cap and per-worker timeout based on actual new-step capacity probes; those caps are deliberately not invented here. Preserve partial outputs and stop after the twelve planned trials or any integrity/resource failure. No automatic expansion, retry with changed numerics, or extra seeds. A timeout is a technical incomplete result, not evidence of convergence or divergence.

**Second gate: scientific panel only if justified.** Extending baseline/mode across all thirty original seeds requires 120 new trials. That could address those two conditions over the added range, not every comparator or altered-weight group. Extending all five default conditions requires 300 new trials. Existing verified anchor outputs can be reused; reproduction checks for the new package must precede interpretation. The separate altered-weight cases need an explicit inclusion decision if the claim is to cover them. Do not silently redefine the original all-group result as a mode-only success.

Retain the actual criteria and averaging order from [the frozen plan](CCR_FINE_PLAN.json): A difference at most max(1 Hz, 5% of finer A), F difference at most 0.01 with undefined fractions failing, full paired-response relative L1 at most 0.05, and 10-ms population relative L1 at most 0.05 for both baseline and lesion. Group decisions require the passing mean and at least 95% of individual pairs under the implemented joint rule; at thirty seeds that means 29. Both new successive comparisons must pass for a claim of agreement over the added range. That would still not prove a continuous-time limit.

Keep complete spikes, rates, delivered inputs, manifests, source/environment records and process outcomes. For additional diagnostics, use bounded state recording of the already selected targets/source with exact replay checks. A state recorder must not change the reference trajectory. Choose its cells/windows before new outcomes and keep diagnostic recording separate from the scientific pass/fail decision.

## Recorded compute evidence

Read all 600 completed default fine-study manifests from the already hash-verified archive and calculated finish-minus-start elapsed duration. These are worker wall-hours under the prior concurrency/node/setup conditions, not guaranteed CPU-hours or future allocation time.

| Step (ms) | Trials | Median elapsed hours/trial | Range (hours) |
|---|---:|---:|---:|
| 0.0008 | 150 | 1.896 | 1.843–1.976 |
| 0.0004 | 150 | 3.785 | 3.689–3.899 |
| 0.0002 | 150 | 7.540 | 7.356–7.720 |
| 0.0001 | 150 | 15.121 | 7.364–15.408 |

Under the illustrative assumption that elapsed time scales inversely with dt while execution conditions remain unchanged, the two proposed steps cost 2+4 times each corresponding saved finest-step duration:

- Twelve-trial, three-seed baseline/mode pilot: approximately **545 worker-hours**.
- Thirty-seed baseline/mode extension: approximately **5,178 worker-hours**.
- All-five-condition default extension: approximately **12,940 worker-hours**.

These are scenario estimates, not a measured request or commitment. Concurrency, node differences, backend overhead, scheduling and activity can change them. In particular, the finest-step range already shows heterogeneous timing. Dividing by a nominal worker count does not establish allocation completion: individual long trials, memory and walltime limits still matter. Finer dense input tapes also increase memory; no new-step memory peak has been measured.

All 600 intervals match a separate timestamp calculation; four medians match separate order statistics, and the pilot sum matches a separate 2×+4× calculation. [Evidence](evidence/2026-10-10/numerical_proposal_capacity/snapshot.json) includes every duration, protocol, estimates and checks. Runtime summaries do not constitute new scientific simulations.

## Other routes need their own design

An event-handling reference needs explicit conventions for simultaneous arrival/crossing/reset, refractory release, discarded inputs and strict threshold inequalities. Validate known analytical cases, boundary/failure cases and saved short trajectories before using it on a network. A local replay conditioned on archived inputs does not test the free-running network. No implementation timeline or performance claim is established here.

An ensemble study would need a defined seed/input-generating population, primary summaries and averaging order, prospective equivalence margins, a resolution range, a sample-size/precision calculation, multiple-comparison handling and a confirmation panel independent of exploratory design choices. Repeated baseline/comparator rows sharing seeds cannot be counted as independent samples. Failure to reject a difference is not equivalence. Existing stable means are a reason to discuss this route, not its result.

For eigencircuit specificity, numerical agreement and comparison design are separate requirements. CB4058 is included in the mode lesion and absent from the three fixed comparators; prior single-cell effects and the current inhibitory histories make influential-cell explanations concrete. Any follow-up must separate those explanations with a recorded design rather than call concentrated eigenvector support causally special because one group differs from imperfect controls.

## Outcome to leave the meeting with

Record the chosen scientific/numerical claim, the next bounded experiment or development task, its completion and stop conditions, and who will review the design before compute. If these cannot be agreed, present current results as descriptive numerical sensitivity and selected propagation evidence, with the original eigencircuit claim unresolved. No tolerance change, result deletion or automatic new run follows from this proposal.

Prepared with Codex assistance from saved research records; no independent human review is implied.
