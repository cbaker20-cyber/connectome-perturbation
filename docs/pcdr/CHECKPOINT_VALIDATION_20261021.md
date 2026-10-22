# Checkpoint execution validation — 21 October 2026

Purpose: complete the same seed631401 baseline/mode pair at0.0000125ms through bounded allocations, retaining the frozen simulator equations, input schedule, support, and convergence criteria. No new scientific result is established by these tests.

## Implementation and review

The separate pcdr_checkpoint_sim.py follows the frozen fine simulator loop. It saves Brian network state, including delayed arrivals and spike-monitor history, plus accumulated delivered-input events. Each restart checks source/model/data hashes, input tape, numerical settings, Python/Brian/NumPy versions, and restored clock. Exclusive ownership prevents simultaneous writers. Foreign/stale locks fail closed; they are not removed automatically.

Review identified an interrupted-save defect: a partially written tick directory could prevent retry. Each attempt now uses a unique generation, leaving incomplete generations intact. Both payload files are flushed before an atomic latest-pointer replacement. A completed checkpoint can reproduce final outputs if output writing was interrupted. This still requires process-kill testing and filesystem durability review before production.

Prototype two-cell fresh-process equality passed including delayed events and refractory states. Integrated tests use the actual model constructor and frozen simulator as the comparator, baseline and output lesion, both0.0001 and0.0000125ms, two restarts, no inputs, changed configuration, corrupted files, conflicting locks, invalid boundaries and orphan-save recovery. Current execution log: results/pcdr/checkpoint_feasibility_20261020/integrated_tests.log; JUnit file is written only when the suite finishes. Do not infer a passing suite from its launch.

## Remaining production requirements

The full1s tape has80million rows and21 input columns. Input arrays and Brian float64 copies alone can require roughly15.12GB per worker before network and serialization memory. Measure full-network peak RSS, save/restore cost, checkpoint size, filesystem quota and retained-generation growth on CCR before scientific segments. Earlier10ms probes do not establish this full-tape memory requirement.

pcdr_checkpoint_worker.py is a draft adapter for100ms segments and the original final-output verifier; it is not yet released. No checkpoint production job has been launched. Prior job26566063 remains a preserved capacity refusal, with zero new full scientific trials.

Integrated initial suite:12failed/3passed128.51s, all checkpoint creation failures due Windows fsync on read-only payload handle (Bad file descriptor). Preserved integrated_tests.log/xml. Corrected open mode to r+b; full repeat running as process57384, logs integrated_tests_v2.log/xml. Do not claim pass before XML/log complete. No CCR production launched.

## CCR storage inspection, 21 October

The live queue was empty at the inspection (remote clock 04:50:39 UTC). `rquota` reported home usage 14 GB of 25 GB, and project usage 654 GB of 1.0 TB. `/projects/academic/smuldoon` is writable by this account, which belongs to grp-smuldoon. No files were created there. The earlier `quota -s` attempt failed because that command is absent; the documented `rquota` command succeeded. Filesystem-wide `df` availability is not the user's quota.

Use a dedicated project subdirectory for the bounded checkpoint capacity validation, subject to an actual size estimate and a fresh quota check. Do not place retained full-network generations in the home directory without demonstrating they fit. No production allocation or simulation was submitted during this inspection.

CCR documents local `/scratch` as allocation-local and deleted at job end, so it cannot be the only checkpoint location between jobs. The `/vscratch` service is scheduled to become read-only on October 27 and is not an appropriate new dependency. Sources: https://docs.ccr.buffalo.edu/en/latest/hpc/storage/ and https://docs.ccr.buffalo.edu/en/latest/changelogs/scratch-shutdown/ (consulted 21 October).

## Follow-up failure checks

The corrected initial implementation passed all15 integrated tests in223.76s (integrated_tests_v2.log/xml). Separately, the injected latest-pointer failure passed in19.24s and abrupt process exit passed in7.90s. Previous-pointer bytes stayed unchanged; incomplete save evidence remained. Abrupt exit deliberately retains its owner lock and subsequent execution refuses it. This tests safe refusal, not automatic recovery after termination.

A final ownership change closes the lock file through a context manager and only removes a lock whose complete ownership record matches the current attempt. A replacement-owner test was added. The complete18-test suite is being repeated as integrated_tests_v3; its result must be recorded before releasing this source revision. Production still requires segment-controller validation, explicit dead-owner recovery with Slurm evidence, full-network reference equivalence and measured memory/storage/save/restore timing.

## Next bounded CCR validation (proposed; not launched)

Before either scientific condition advances, validate the checkpoint extension on the actual frozen network and full-length input schedule. The test must reconstruct the full one-second input tape at the authorized step so its memory use is representative. Compare a short uninterrupted prefix with the identical prefix reached through two separate processes, retaining exact spike times/IDs, scheduled and delivered input records. Include baseline and output-lesion reference reproduction at the saved reference step. Record elapsed time, maximum RSS, checkpoint bytes, save time and fresh-process restore time separately.

Use the same frozen environment and backend, source/data/input hashes, explicit stage ownership, bounded process timeouts and actual Slurm limits. No simulation on the login node. Choose the probe walltime from the existing measured prefix costs with margin, then reject if the actual allocation is insufficient. The production segment gate must include twice the measured simulation estimate plus measured setup/save/restore costs and a termination reserve; the previous capacity refusal must remain in the record. Do not infer a whole-pair completion guarantee from a short probe.

The draft worker also needs restart-safe attempt directories: its current `segments/<condition>/<stop>` directory is exclusive and a failed attempt would prevent a retry. Preserve each attempt rather than deleting its records. An abruptly terminated owner requires checking the recorded Slurm job and process identity before archiving its lock; the current simulator intentionally does not perform that recovery automatically. These are unfinished implementation tasks, not a reason to weaken the capacity or numerical checks.

Local validation environment: Windows, Python3.11.9, Brian2 2.9.0, NumPy1.26.4, pandas3.0.3. The frozen CCR environment requires Python3.11.5; local passes do not replace running equivalence checks in that environment. The checkpoint configuration rejects cross-version continuation.

## Final local result

The final18-test suite passed in250.41s with zero failures (integrated_tests_v3.log/xml). This includes the replacement-owner cleanup test and all earlier equivalence/failure cases. Source and evidence hashes, exact local versions, and limits are recorded in results/pcdr/checkpoint_feasibility_20261020/integrated_validation.json. The initial failed run is preserved. This releases the local simulator component for further CCR validation only; the draft segment worker and production execution remain unfinished. No convergence result changed.

## Bounded full-network validation prepared, 21 October

New comparator checks every saved Brian state value recursively, including array dtype/shape and RNG/delayed-arrival state, after checkpoint hashes and endpoint/configuration match. Five comparator tests passed (17.62s), including actual-model fresh-process equality and a one-bit numeric difference refusal. The worker constructs the full one-second input tape for short10/20ms checkpoint prefixes and records peak RSS, tape bytes, checkpoint bytes, store/restore timings, provenance and failures. Eight worker tests passed; four controller workflow/guard tests passed. The tests include an actual three-cell checkpoint plus changed-input refusal; controller workflow tests use synthetic workers and do not establish CCR performance.

One combined test attempt failed because Windows monotonic-clock resolution reported a submillisecond toy save as0seconds. Evidence is preserved in probe_controller_tests.log/xml. Measurement timing now uses perf_counter; the repeated10-test combined set passed in5.08s, and the two added controller workflow cases passed with the two guard cases (4passed0.72s). This correction changes timing measurement only. Probe Python compilation and launcher bash syntax passed locally.

Proposed single validation allocation:4CPUs,64000MB,12hours, CPU-Gold-6448Y, no requeue. Its controller allows at most10hours and reserves300seconds of the actual allocation. It runs two archived-step references, then uninterrupted20ms and fresh-process10+10ms prefixes for each condition using the full input tape. Workers are serial to measure full-tape memory before choosing concurrency. This is eight bounded validation processes, not eight scientific trials. Exact full-state and delivered-history comparisons are required. The controller cannot start production and stops after a failed process. A dedicated project directory is planned; no frozen package files or prior results are replaced.

## CCR submission

Job26580158 accepted21October2026 at06:13:09Eastern. Initial state PENDING/Priority,4CPUs,64000MB,12hours,CPU-Gold-6448Y,no requeue. Exact committed sources aa8b327bcdfde6d66456224c3ee8061987eb4d47 transferred and all five remote SHA256 values matched Git blobs; remote bash syntax passed. Project directory /projects/academic/smuldoon/cbaker4_checkpoint_validation_20261021 contains submission.txt; log validation_26580158.log and run/progress.json will appear after startup. No allocated node or completed validation was yet observed. Do not duplicate this job. No full scientific trials launched.

### Completed remote validation, 21 October

Slurm job26580158 completed with exit0:0 after4:59:36; recorded batch peak RSS18375824K. All eight short validation processes finished. The remote comparator reported exact full-state and delivered-input agreement at20ms for both conditions, comparing uninterrupted execution with a fresh-process restart at10ms. These checks used the full one-second input tape. They do not establish a completed one-second trial or timestep convergence.

The completed archive is `CCR_checkpoint_validation_20261021.zip` in the project validation directory, SHA256 `56c0352d3696dbc730f90d0f038ea6e5703746831b7f2103a105acf34c739339`. Local retrieval has not succeeded; independent verification remains outstanding. Production remains gated on that verification and a documented resource decision. No scientific trial was launched.

### Local verification after download

The downloaded archive matched the remote SHA256. Local checks passed for all eight process outcomes, all eight recorded checkpoint payload hashes/endpoints, deployed source hashes, and both reference spike/input prefixes against the frozen upload anchors. Rerunning the tested comparator locally confirmed exact saved-state and delivered-input agreement for both conditions. This uses the same comparator implementation as CCR. The local verification script and report are preserved under `results/pcdr/checkpoint_verified_20261021`.

Peak worker memory was16.854GB; checkpoint payloads were approximately242.56MB. Measured save/restore costs were approximately0.51/0.21seconds for the tested fine-step prefixes. These measurements support continuing production implementation, but do not establish full-duration runtime, later checkpoint sizes, or convergence. Production has not launched; complete provenance crosschecks and worker/controller resource and failure tests remain.

### Production execution preparation

Additional local checks passed for all eight physical-input digests, package/Python versions, input/support index mappings, dataset hashes, backend and weight scales. The production worker draft now preserves failed attempts, refuses conflicting ownership and skipped segment boundaries, and blocks login-node or undersized execution. Eighteen component tests passed. Controller integration and end-to-end production workflow tests remain unfinished; these components have not been deployed.

The proposed screen uses one serial worker,100ms segments, twice the slowest measured rate plus one hour reserve, twice measured peak memory, and a storage allowance four times20 observed checkpoints. These are conservative planning rules rather than guarantees of later runtime or checkpoint growth. Actual allocation and available storage must be checked before launch and each continuation.

### Controller component tests, 22 October

A draft allocation controller now advances the fixed pair through100ms segments, preserves per-allocation attempts, checks completed output hashes, and refuses changed execution sources or unresolved ownership. Twenty-segment progression, allocation-budget stop/resume, completed-run refusal to repeat, worker failure, and corruption paths were tested with simulated workers. The combined24 component tests passed. This does not test the full production workflow: real worker integration, validation binding, later-segment resource growth checks, and live allocation/quota checks remain required before deployment. No production job was submitted.

### Resource growth and validation binding

The draft controller now increases its resource screen when successful later segments show larger elapsed time, memory, or checkpoints. It also refuses production if the simulator/model bytes or Python/package environment differ from the validated records. The26 component tests passed, including changed-source/environment refusal and resource-growth checks. Real worker integration and live CCR resource checks remain outstanding; no production launch occurred.

### Final-output checks, 22 October

The actual output writer was exercised with synthetic frames: sparse rates and population counts matched known values, while changed input timing, invalid delivered events, and refractory violations were rejected with preserved failed manifests. The controller also stops before launch when less than its one-hour reserve remains.31 component/output tests passed. These checks do not yet constitute a real simulator-to-controller fresh-process integration test; production remains unlaunched.

### Fresh-process final-output recovery

A bounded three-cell test at0.0000125ms passed across three fresh processes: save at3ms, finish6ms and inject an output failure, then restore the completed checkpoint and produce validated outputs. Checkpoint metadata remained byte-identical during final recovery, establishing that recovery did not advance or replace the completed checkpoint. The failed attempt was retained. This tests the real simulator/output writer, not the full production controller or a scientific-duration trial. The test passed in35.84seconds; production integration and CCR resource checks remain.

### Production worker path

The production worker execution path passed a bounded three-cell integration test at0.0000125ms through the actual simulator, output validation and final-directory promotion. A second attempt refused the existing trial and preserved its manifest. Test adapters reduce duration to6ms and substitute local allocation/package metadata; this is not a full-duration production run. The test passed in30.80seconds. Controller subprocess integration and live deployment checks remain.

### Subprocess handoff and live resources

The controller passed its real subprocess handoff test using fixture payloads:20 child processes advanced the declared endpoints, and a completed rerun launched none. This complements the actual simulator/worker tests; it is not another neural simulation. Nine controller tests passed in4.49seconds. Live CCR inspection showed no queued/running user jobs, project usage656GB/1TB, and a72-hour general-compute limit. Deployment preparation is underway; no production job has been submitted.
