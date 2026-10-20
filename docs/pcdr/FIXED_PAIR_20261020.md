# One further fixed timestep pair — 20 October 2026

## Decision before new results

The user authorized one further baseline/mode pair at 0.0000125 ms after completing verification of the existing pilot. Select seed 631401 because it is the first original seed and fails the finest completed comparison. This selection uses earlier results and is diagnostic, not an independent confirmatory sample. No seed substitution, intervention sweep, solver change or full-panel expansion is authorized by this protocol.

Keep the one-second duration, source matrix, simulator equations and scheduling, physical input schedule, lesion membership and numerical tolerances unchanged. Preserve the frozen original package. Record the extension separately. Compare against the completed seed 631401 pair at 0.000025 ms. Report every readout and failure; one passing comparison cannot establish the original two-successive-halving, 30-seed requirement.

## Completed evidence

All six pair archives passed local frozen-record, output-hash, input-schedule, spike-derived rate and population-bin checks. Supplemental checks passed for 36 process records, 12 reference prefixes and 12 full-trial refractory-spacing checks. Records: `results/pcdr/pairs_verified_20261020/verification.json`, `comparisons.csv`, `supplement_20261020.json`. The previous dated verification remains preserved.

The final archive SHA256 is `f3102d3a992f4b32f0edf3fae3e9bf1026e16483f6fb4f8d20e5bf70b775f52f`; downloaded as `ef07e175-78b0-494f-9e9c-63918b89143f.tmp`. Its last-halving response L1 is 0.1429709279 and worst population L1 is 0.2032875118. Both fail 0.05. All three seeds fail the finest completed halving.

Three additional local checks passed at 0.0000125 ms: physical input/delay/refractory-grid representation, exact tiny-network comparison with the unwindowed implementation, and the linear subthreshold known solution (30.46 seconds). These do not establish full-network agreement.

## Execution requirements and stopping rule

Inspect queue and avoid duplicate work. The October 20 live queue inspection returned no jobs for cbaker4. No new scientific trial has been submitted yet.

Use the existing frozen CCR environment and a separate extension controller/output directory. Require a real compute allocation, same-step reference reproduction, two concurrent short-prefix capacity probes, a conservative runtime screen, memory checks, exclusive ownership and recorded time limits. Do not launch full trials if the screen exceeds the allocation. Preserve all refusal/failure evidence. Do not loosen the gate to force a run.

After the one pair, download and independently reconstruct the saved readouts, compare every unchanged criterion, update the meeting records and stop. If access or capacity blocks execution, report that precise limitation instead of claiming a launch. No automatic additional halving follows.

## Implementation validation

Separate controller scripts/pcdr_fixed_pair.py and launcher scripts/pcdr_fixed_pair.sh reuse frozen simulator and owned-process runner. Five extension tests passed, covering exact spec preservation, wrong/missing pair rejection, capacity boundary and invalid measurements, exact allocation identity, and unknown prefix rejection. Together with three saved-readout tests, eight passed in0.71seconds. The new-step three tests passed separately as recorded above. No new full network result exists yet.


## CCR submission — 20 October, 11:27 Eastern

Job 26566063 accepted and observed RUNNING on cpn-d02-06, 4 CPUs, 64000 MB, CPU-Gold-6448Y, no requeue. Allocation starts 20 October 11:27:20 and ends 23 October 11:27:20 Eastern. Controller additionally limits work to at most 70 hours and reserves allocation time. This is a launched batch job, not yet a confirmed full scientific launch. Initial log shows module loading; progress.json was not yet present at the immediate startup checks.

Transferred source from commit 1e35c14 matched SHA256: controller 5e7ba43fa9770c6e5e803cc20c94c768af271abb98b2b11c951e8447bce0da98; launcher fa3ffa23577865133f030d8fb168d3f3e346e82c701667136da393f477f2f597. Bash syntax passed. The test-only scheduler estimate differed from actual immediate start, so it was not used as a promise.

Remote directory /user/cbaker4/connectome_four_trial; progress fixed_pair_20261020/progress.json; log fixed_pair_26566063.log; eventual archive CCR_fixed_pair_20261020.zip. Submission ID saved in fixed_pair_submission_20261020.txt. Do not resubmit. Thirty-minute follow-ups are active. Screenshot capture timed out; the returned terminal state confirmed the Slurm record.
