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
