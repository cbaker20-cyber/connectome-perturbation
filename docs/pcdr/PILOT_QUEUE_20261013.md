# Remaining smaller-step pilot queue, 13 October 2026

The user authorized additional runs and compute requests. This schedules only the ten unstarted trials in the existing twelve-trial pilot. It excludes the running seed631401 baseline/mode pair at0.00005ms, job26427314. No30seed expansion or new intervention is included.

| Array task | Seed | Step (ms) | Full trials |
|---:|---:|---:|---|
|0|631401|0.000025|Baseline and mode output lesion|
|1|631402|0.00005|Baseline and mode output lesion|
|2|631402|0.000025|Baseline and mode output lesion|
|3|631403|0.00005|Baseline and mode output lesion|
|4|631403|0.000025|Baseline and mode output lesion|

Each task requests4CPUs,64000MB and72hours on general-compute, accountsmuldoon, with two concurrent simulation workers. Array concurrency is one task, so the new queue does not place multiple pilot pairs on one node at the same time. The current recovery node cpn-c04-18 is excluded from the new allocation request. Other users' node activity is not controlled; measured performance may vary. Pending jobs request future capacity without holding idle running interactive sessions. Start time is controlled by Slurm and is not guaranteed.

Each task checks the frozen package and Python environment, reproduces both archived10ms references at0.0001ms, and measures two concurrent10ms baseline probes at its assigned step. Calibration uses the fixed seed631401; probes are repeated timing measurements, not scientific replicates. Twice the slower measured prefix scaled to1second must fit remaining time. This margin is a scheduling screen, not a guarantee across seeds or later activity. The controller stops after at most70hours or20minutes before allocation expiry. Existing20GB per-worker address-space limits remain.

The new execution source is separate from all frozen simulation/package files. Per-task locks and refusal of existing output directories prevent repeated execution in this queue. Failed records and partial results are preserved. Full results are hash-checked before being marked complete; the final archives require separate local verification. Combined adjacent-step analysis waits for the appropriate completed pairs. No task independently claims convergence; the original thirty-seed requirement remains unmet by a three-seed pilot even if all twelve trials complete.

Validation:14local tests passed in1.24seconds, covering exact remaining-pair selection, exclusion of the active pair, duplicate records, scheduling boundary, invalid measurements, output hashes, missing expected outputs, controller refusal/failure, archive CRC and rerun refusal. Controller-flow tests use simulated process results; remote reference checks provide separate numerical reproduction evidence.

Remote filenames: `queued_pilot_20261013.py`, output directories `queued_pair_0_20261013` through `queued_pair_4_20261013`, and final `CCR_queued_pair_<task>_20261013.zip` archives. No frozen source/data replacement and no input schedule changes.

At preparation, the current recovery pair was still running and all five new tasks were not yet submitted. Submission and actual execution are recorded below once observed.

## Submission verified

Submitted2026-10-13 at08:46:59Eastern (12:46:59UTC), array26469967, tasks0–4, concurrency1. At12:47:06UTC all five tasks were PENDING with unknown start times. Slurm confirmed4CPUs,64000MB (displayed62.50G),72hours, accountsmuldoon, QOSgeneral-compute, no automatic requeue, and excluded nodecpn-c04-18. The earlier `sbatch --test-only` estimate suggested18October04:01:19 in the scheduler's displayed timezone; this was an estimate from a validation request, not a confirmed reservation or actual start. Actual accepted jobs had StartTime=Unknown.

The active recovery remained in scientific phase at12:47:06UTC. No new full trial has been claimed started from this array. Submission identity is saved remotely in `pilot_queue_submission_20261013.txt`. Do not resubmit or duplicate the array.

Versioned controller commit6b0255175dfb4f95d16582073576b4e2da53c2a8. Local/remote controller SHA256f2105d2e328599f5cca44890c908f7adae54cd983bef9e65412d7131c6181757; launcher SHA25680254e8877a62a1a986fdbc9a21c1f60759b53fad1aed7c233ff81ec731b705a. Both remote hashes matched; Bash syntax and Slurm test-only validation passed before submission. Source was transferred from this exact repository commit. No package/data/source replacement occurred.

## Finest-step hardware amendment

At16:29UTC, task0 had stopped before scientific launch:298662.83742199885seconds (82.96hours) including the2x margin, versus250127.41637589107seconds available. Both archived references matched exactly. Its nodecpn-b04-04-01 reports Gold6230/Cascade Lake. The successful recovery calibration nodecpn-c04-18 reports Gold6330/Ice Lake. This difference motivates a hardware request; it does not isolate processor type from node load or prove that newer hardware will finish the finest step.

General-compute is capped at72hours. Account associations were inspected; no lab-specific smuldoon faculty partition was found. Industry partitions list longer times but the account did not list industry QOS, so no unsupported longer request was made.

Pending array tasks2and4 now require CPU-Gold-6448Y (Sapphire Rapids), verified by scontrol. Only pending jobs were changed. The stopped task0 gets a separately recorded retry using the same scientific workers, same72hour request, same2x gate and exact reference checks. New output sapphire_pair_0_20261013 preserves the refusal folder. Retry code requires prior budget_insufficient, zero scientific completions and no prior scientific-launch log directory, and retains the same per-task lock. All15controller tests pass, including these refusal/running/scope guards. A new versioned controller is uploaded under a separate filename so active and already-queued controllers are not replaced. This is an execution amendment, not a convergence result or a guarantee of successful capacity screening.
