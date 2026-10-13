# Smaller-step recovery, 13 October UTC

The four-worker package stopped on 10 October at its scheduling gate. It did not start any of the four full scientific trials. Its four concurrent short probes produced twice-scaled screens of 185867.81 seconds (51.63 hours) at 0.00005 ms and 346400.43 seconds (96.22 hours) at 0.000025 ms, against 249865.35 seconds (69.41 hours) available. These are scheduling estimates, not measured full-trial durations. The completed stop record and all outputs remain in `four_results` on CCR.

## Prospective execution amendment

The user authorized recovery using the existing allocations. The long allocation is job26427314 on cpn-c04-18, with16CPUs and256000MB reported by Slurm. The four2CPU allocations share cpn-b04-12-02 and had approximately15.6hours remaining at inspection; the8CPU allocation had approximately15.3hours. None is a suitable basis for knowingly starting the previously screened long trials. The long allocation had over54hours remaining and no research workers at inspection.

Prioritize seed631401 baseline and selected mode-output lesion at0.00005ms, each for the original full1second. Both jobs are selected from the frozen twelve-trial plan. The scientific source, input schedules, supports, readouts and agreement criteria are unchanged. This is one seed and one additional halving; it cannot establish the original30seed/two-successive-halving requirement. The0.000025ms full trials and other two seeds remain unstarted.

`scripts/pcdr_recover_pair.py` is a separate execution controller. It verifies the frozen package and environment, uses two concurrent archived-reference checks at0.0001ms, then two concurrent10ms capacity probes at0.00005ms. Both references must match exactly. The pair can start only if twice the slowest measured prefix scaled to1second fits the remaining budget. The controller allows at most54hours and reserves20minutes before allocation expiry. Each worker retains the existing20GB address-space limit. Existing result directories are refused, child cleanup is limited to owned processes, and failures remain archived.

## Launch evidence

The controller was transferred separately without modifying the frozen package. Local and remote SHA256 matched:
`21f208a5ac117e1cb4b85f00fc1cc55a24c3f6e5f8a9252ab7db0980f92cf489`.

Dispatch uses `nohup srun` from the CCR login shell, with all simulation execution on the allocated compute node. This avoids making the new run depend on the shorter8CPU interactive allocation. Dispatch PID1885034; Slurm step26427314.3. The step receives4CPUs; two workers execute concurrently with numerical library thread counts fixed to one.

At03:45:12UTC, reference workers255604 and255605 started on cpn-c04-18. Python3.11.5,4CPU affinity and256000MB were checked before dispatch. At03:46:47UTC both reference workers were still running. No full scientific trial was yet started at that observation.

At03:50:23UTC both references were complete and exact, with measured simulation times300.73538083501626 and301.17886948399246seconds. The controller had advanced to the two concurrent0.00005ms capacity probes. Full scientific trials were not yet started at this observation.

Remote root: `/user/cbaker4/connectome_four_trial`.
Recovery output: `recovery_pair_20261013/`.
Dispatch log: `recovery_dispatch_20261013.log`.
Final archive when the controller exits: `CCR_recovery_pair_20261013.zip`.

## Validation and preserved failures

Eleven local controller tests passed in1.17seconds. They cover the capacity boundary, invalid/incomplete probe records, exact pair selection, refusal without scientific launch, reference failure, duplicate-output refusal, archive readability and explicit one-pair interpretation. The controller-flow tests use simulated process results; they do not establish network reproduction. Actual reference reproduction is checked separately on CCR.

A preliminary read-only Slurm command using bare `bash` failed because the remote executable could not be resolved. Repeating with absolute `/bin/bash` succeeded. No simulation ran in that failed command. The final dispatch uses absolute `/bin/bash` and explicit modules.

Convergence remains unestablished; all eighteen original full agreement groups remain failed.

## Full scientific pair confirmed running

At2026-10-13 12:39UTC, the capacity gate was allowed:122231.84648839524seconds (33.95hours, including the2x margin) versus193481.91692105698seconds (53.74hours) remaining at the decision. Full baseline and mode-lesion workers started at04:00:30UTC (00:00:30Eastern), PIDs256229 and256231, for seed631401 at0.00005ms. Both scientific trial manifests were running, and the controller remained in scientific phase after8.64hours. This confirms full-trial launch, not completion or convergence. The0.000025ms pair remains unstarted.

Live process inspection at12:39UTC showed both scientific workers at99.9% CPU, approximately5.86GB RSS each, with8h38m CPU time and empty stderr logs. This is active execution evidence, not a completed-output check.
