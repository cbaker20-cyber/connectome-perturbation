# Meeting brief — 20 October 2026

## Quick recap

My original question is unchanged: do concentrated eigenvector supports of the materialization-630 Shiu matrix predict localized firing-rate responses to output lesions, beyond connectivity, strong connections and recruitment? The output-lesion footprint is the cell-by-cell change in firing rate between matched lesion and baseline runs.

Since the last update, I have ten completed full-duration trials at smaller timesteps downloaded and checked. These results do not establish numerical convergence. One of three available comparisons from0.0001 to0.00005ms passes all individual criteria; neither of the two available comparisons from0.00005 to0.000025ms passes. CCR's completion record now confirms that the last seed's finest-step pair finished on 18 October at 15:01 UTC, with both processes returning zero. All 12 trials have therefore finished remotely; ten are locally verified. The final archive has not yet transferred successfully, so its numerical comparison remains unevaluated.

## Evidence to show

| Work | What was changed or checked | What the evidence supports | Convergence status / limitation |
|---|---|---|---|
| Original fine-step study |620 trials, reaching0.0001ms|Selected-support mean summaries can remain similar while individual responses differ|All18 full agreement groups failed|
| Saved-output localization diagnostics |Baseline/lesion differences and shared active cells examined|Differences are present in baseline too and are not restricted to the final recording boundary|Diagnostic; not a convergence test or a complete initiating cause|
| Selected local state replays |Saved inputs, spike/reset histories and states reconstructed|Selected saved spikes can be reproduced locally|Selected-case reproduction does not validate every network trajectory|
| Separate G/H connection experiments |Eight completed altered-connection trials|Either removal interrupts recruitment in the selected coarser-step case|Conditional intervention result; no general eigencircuit/convergence claim|
| CB4058 history analysis |Actual arrivals and reset/refractory histories in selected cases|Specific timing/reset interaction worth discussing|Reset-history confounding and repeated targets; not a controlled causal result|
| Smaller-step full pilot |Baseline and mode lesion, first3 fixed seeds,0.00005 and0.000025ms;10/12 downloaded|Some changes shrink, but agreement is not consistently monotonic across seeds|Available comparisons fail the joint requirement; see table below|
| Local verification of downloaded pilot |Hashes, frozen records, input schedules, spike-derived rates/bins, reference reproduction, exit records, refractory spacing|No failure found in these checks for the10 downloaded trials|Does not independently validate all equations or establish biological validity|

## New numerical results

| Seed | Step change (ms) | Response difference | Population difference | Joint individual result |
|---|---|---:|---:|---|
|631401|0.0001 →0.00005|14.84%|19.34%|Fail|
|631401|0.00005 →0.000025|12.49%|11.64%|Fail|
|631402|0.0001 →0.00005|0.00%|0.00%|Pass|
|631402|0.00005 →0.000025|7.55%|12.00%|Fail|
|631403|0.0001 →0.00005|18.70%|22.91%|Fail|
|631403|0.00005 →0.000025|Not available|Not available|Not evaluated|

Response difference measures changes in the entire signed lesion-minus-baseline vector. Population difference compares total spike counts in10ms bins, taking the worse of baseline and lesion. Both must be at most5%. The joint test also requires close agreement in A (average absolute response within the fixed51-cell support) and F (fraction of the absolute network response inside it). All five available F comparisons pass; A fails the first631401 comparison. Passing A/F alone does not meet the original rule.

Convergence here means that further timestep refinement leaves the declared measurements sufficiently unchanged under the frozen tolerances. It is not equivalent to successful code execution, similar total spike counts, statistical significance or biological truth. The three-seed pilot cannot satisfy the original30-seed study requirement even if its individual results were all favorable.

## Decision for the remaining week

My proposed priority is to finish verification/reporting of the already-launched panel and retain the original question as unresolved where numerical reliability prevents a claim. I do not propose an automatic full-panel expansion or another intervention sweep. A further timestep halving has no established likelihood of resolving the discrepancy, and the completed full pair runs took many hours.

If another numerical experiment is essential, I propose first agreeing on one fixed failing baseline/lesion pair, one additional halving, unchanged inputs/support/readouts, reference checks and a measured capacity gate. Both trials must finish within the authorized walltime. Stop after that comparison and report every criterion, whether it passes or fails. This would be a diagnostic for that case only, not confirmation across seeds. It is a proposal, not a prepared or launched job. A different solver would require separate validation and is not ready as a quick substitute.

Questions I forgot to ask: What level of numerical agreement is needed for the original lesion-footprint claim? Would one additional fixed-case comparison change the research decision, given that one seed already passes a halving and fails the next? If the original criteria remain unmet, what descriptive claim is appropriate for the remaining week? A separately designed ensemble question could be discussed, but it would not erase these failed criteria or count as fresh confirmation using the same data.

## Records

Detailed numerical table and definitions: SMALLER_STEP_RESULTS_20261019.md. Local comparison data: results/pcdr/pairs_verified_20261019/comparisons.csv. Supplemental checks: supplement_20261020.json in the same folder. Earlier diagnostic context: MEETING_BRIEF_20261010.md and the records linked there. No new scientific simulation was launched for this brief.
