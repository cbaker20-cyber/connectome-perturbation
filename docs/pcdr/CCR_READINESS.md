# CCR readiness gates

Recorded 22 September 2026. This is a launch checklist, not evidence that CCR has been tested.

Afternoon update: joint motor/sign/recruitment plus original six-feature mean-balance feasibility is now established by nine independently verified binary sets. Their distributions and diversity remain problematic (see MOTOR_SET_AUDIT_20260922.md). The older feasibility gate below is historical; confirmation still requires a defensible comparison design as well as technical CCR validation.

1. Obtain actual account, partition, project directory, Python/module environment and node limits. No credential should be stored in a report or repository. No CCR connection or submission has occurred in this continuation.
2. Copy the frozen input/source bundle, verify hashes and recreate the recorded package versions. Keep local historical files unchanged. The existing worker rejects changed sources or packages; prepare a new cluster manifest after documenting any environment amendment, rather than editing an existing manifest to bypass this check.
3. Run one NumPy baseline, its identical-seed replay, a no-input trial and an output-only lesion. Verify scheduled-input equality, deterministic replay, zero undriven spikes, all-neuron outputs and lesion support. Measure construction plus simulation plus output time, peak memory and bytes per trial. Account/partition and resource requests remain unresolved until access exists.
4. Use NumPy by default. For a proposed Cython switch, run the existing full benchmark, then require both benchmark.json passed=true and `python scripts/pcdr_backend_input_check.py --benchmark PATH` to pass. The new read-only check verifies exact input schedule identity across all60 baseline/lesion backend pairs; equal input counts alone are insufficient. Do not claim backend readiness from the unit test or an unrun certificate. Delivered input events may differ with state and are not required to match.
5. Before a large array, test a small array, a failed/missing job and resume/collection. Each array index owns one frozen condition/seed; no nested parallelism. Keep unique directories and locks. Reject partial confirmation summaries. Set concurrency from measured memory and actual allocation rather than the template example.
6. Freeze the scientific comparison design separately from technical deployment. Existing optimized controls do not justify the original random-reference p-value. More seeds or sets cannot fix this by themselves. The next baseline-only gate is joint motor/sign/recruitment plus continuous-feature feasibility.

## New check and validation

- scripts/pcdr_backend_input_check.py was created with Codex assistance. It reads benchmark manifests, checks completed status and equal seed, schedule digest, drive, duration, timestep, support and model variant across NumPy/Cython, and returns a machine-readable list or an error. It modifies no benchmark or simulation files.
- Test: tests/test_pcdr_backend_input_check.py constructs all60 synthetic pairs, verifies acceptance, then alters one schedule digest and requires rejection. This validates the guard, not real backend equivalence.
- Current scripts/pcdr_array.sh remains a submission template. Cluster account/partition, transfer/environment setup, integration of certificates into automated dispatch and scheduler fault tests are still pending. No automatic large dispatch is enabled by this checklist.
