# Four full-duration smaller-step trials — execution protocol, 10 October 2026

This is the newly authorized first wave for an8-core,92000-MB,72-hour CCR allocation. It is separate from the earlier two-hour probe and the future16-core allocation. The old scientific plan and model/data remain frozen; only execution scope and deadline handling change prospectively here.

## Fixed work

| Seed | Condition | Timestep (ms) | Simulated duration |
|---|---|---:|---:|
|631401|Baseline|0.00005|1second|
|631401|Mode output lesion|0.00005|1second|
|631401|Baseline|0.000025|1second|
|631401|Mode output lesion|0.000025|1second|

One process per trial, four concurrently. No additional seeds or interventions. These four belong to the existing twelve-trial panel; completed, independently verified outputs should be reused later. The eight trials for631402/631403 are not launched. A single seed cannot establish the original30-seed convergence criterion.

## Order and resource gates

The launcher requires a CCR compute node and Slurm allocation, loads Python3.11.5 and archived pinned requirements, verifies all package files and runs local implementation tests. Two concurrent10-ms baseline/mode references must reproduce the archived0.0001-ms events. Next four10-ms baseline probes run concurrently, two at each new step, to measure contention. The original seed/input/model are unchanged; duplicated prefixes are calibration, not scientific replication.

Before full runs, the slowest probe at each step is scaled100× and multiplied by2. All four estimated concurrent durations must fit remaining time. Each prefix must finish successfully and stay at or below16GB observed peak memory. The allocation must have at least8CPUs and92000MB. Each worker has a20GB virtual-address-space cap, leaving12GB for the controller/session when four are active. This can stop a memory-hungry worker; its failure is retained, not interpreted as a scientific result. The cap is an execution guard, not a measured full-duration memory requirement.

The controller runs at most70hours and stops15minutes before its observed Slurm expiry, whichever is earlier. Installation and tests consume allocation time before that calculation. References have a1-hour cap; concurrent calibration has a2-hour cap. All scientific trials then start together. Runtime screens are estimates, not guaranteed speed or completion. A calibration refusal preserves evidence and starts no full trial. More CPU/RAM does not automatically accelerate each single-threaded worker.

## Run once

Upload CCR_Four_Trial.zip to /user/cbaker4 and extract into its new connectome_four_trial directory. The final delivery includes the archive checksum and copy/paste commands. Use a terminal inside the running allocation, never the login node. The launch command uses nohup so closing the terminal does not itself interrupt the controller; the allocation must remain active. Do not delete the Jupyter session while work runs.

The launcher uses a folder lock and refuses any existing four_results directory. Do not launch a second copy in another folder or another allocation. Logs and process IDs are recorded per worker. An interrupted controller stops only its owned worker groups. A failed worker does not silently erase other completed workers. Full simulations are not checkpoint-resumable: killed workers can lack final spike/rate outputs, and a new attempt must preserve the old directory and be explicitly planned.

Read four_results/progress.json for phase and status; logs are under four_results/logs. While running, process exit codes can update before the final scientific_completed count is recomputed. That count is based on checked trial manifests/hashes, not just a process exit. Zero complete trials during the scientific phase does not mean no workers are active.

Final output: CCR_four_trial_results.zip beside run_all.sh, created after the controller ends normally or handles failure/interruption. A forced node/allocation kill may prevent archive creation; the raw output directory still matters. ZIP existence is not scientific success. Require four checked completed trials plus independently retrieved/checked outputs before interpretation. Agreement summaries use single_seed labels and explicitly retain original_30_seed_requirement_established=false. Partial results are kept without a full-panel convergence label.

## Scientific interpretation

The same signed matrix, model equations, NumPy backend, input schedules,51-cell support,1-second duration and original tolerances are retained. The first wave uses one previously inspected seed chosen by the pre-existing plan, not a favorable new outcome. Both adjacent comparisons against existing0.0001-ms anchors are reported. Do not loosen thresholds, shorten trials, call repeated prefixes independent samples or claim that these results validate biological function.

Implementation and validation provenance remain in repository technical records. No new scientific result is claimed at package preparation.

## Validated release

Current upload exports/CCR_Four_Trial.zip:92,686,149bytes; SHA256 `30b9fe43e1aac70a4dc88b392e28b1e5d221de8b2544b51af06d207af01425f4`. All102manifest entries checked. All original package members remain byte-identical except the active launcher/guide, whose originals are retained inside. Scientific plan/data/source/anchors unchanged. Final extracted-package verification passed;38tests passed in25.31s with52dependency warnings. Bash syntax passed. Tests include concurrent screening, resource rejection, fixed seed selection, real success/failure/timeout, controller interruption and partial-launch cleanup. Remote Linux execution and concurrent performance remain pending. New orchestration uses Codex assistance; no scientific result claimed. Prior upload preserved at results/pcdr/four_trial_validation_20261010/source_pilot.zip, replacing it as the current export only after validation.
