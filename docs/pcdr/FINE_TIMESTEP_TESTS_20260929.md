# Smaller time steps: implementation and local checks

29 September 2026. Follow-up to the [meeting recommendation](MEETING_REFLECTION_20260929.md). This stage tests the implementation and measures cost; it is not the one-second convergence study.

## Change and purpose

Added a separate simulator, scripts/pcdr_fine_sim.py. It preserves the model equations, threshold, reset, delay, refractory behavior, outgoing lesions, input jump and scheduling slot. It takes a saved input schedule on the original 0.1 ms grid and maps it to integer ticks at finer resolution. It rejects incompatible intervals rather than rounding arbitrary times into different inputs. The completed-study simulators remain unchanged.

The new recorder divides execution into recording windows. In each window it measures input-neuron voltage immediately before and after the synaptic slot, checks that jumps are valid and present in the saved schedule, retains delivered-event rows, and releases the window's monitors. The network state and delayed events continue across windows. This retains the existing method for measuring input delivery while bounding trace memory. It still uses a dense binary input tape; it is not a sparse event-generator replacement.

For 21 inputs and a 10 ms recording window at 0.0001 ms, the two raw float64 voltage arrays occupy 33.6 MB instead of 3.36 GB for a whole second. Temporary differences, timestamps, network state and the full input tape require additional memory. Actual process memory is measured separately. No claim that windowing is automatically event-preserving was made before testing it.

## Verification completed before full-network benchmarks

Small recurrent test networks compare the new recorder against the previous complete-trace implementation at 0.1, 0.00625 and 0.0001 ms, with and without an outgoing lesion. Spikes, scheduled inputs and delivered events agree exactly after explicitly normalizing the older Windows index column from int32 to int64. No floating-point neuron IDs are used. A directly stimulated input's first spike occurs at the next threshold-check tick, a known-answer scheduling check. A network without drive remains silent at 0.0001 ms.

An independent analytical subthreshold test uses the linear two-state solution with a decaying initial drive; both voltage and drive agree within 1e-9 mV at 0.0001 ms. This validates that test case, not all network dynamics. Other tests check exact input times through the new halving sequence and reject noninteger timing, invalid units, duplicate events, unknown IDs and out-of-duration events. Duplicate input IDs are rejected in code but were not a new dedicated test here. The original failure in six equivalence tests was solely the int32/int64 index representation difference; exact event values matched. Tests now explicitly compare the integer representation.

The full suite passed 348 tests with three unsupported-symlink skips and 183 warnings in 34.43 seconds. Five further invalid-event cases were then added; the expanded fine-step test file passed all 23 cases with 97 warnings in 11.51 seconds. The earlier full-suite count does not include those five new cases.

## Full-network implementation check

The first saved default baseline seed, 631401, was used without lesions. At 0.1 ms, the first 20 ms was run with both implementations. All spikes, scheduled inputs and delivered events matched exactly. Both runs produced 83 spikes. A separate 1 ms full-network run at 0.0001 ms completed in 17.094 seconds inside the simulator, including model construction, with three spikes. This is a short timing observation and not an estimate of the full one-second response.

Evidence: results/pcdr/fine_benchmark_20260929. Its prior protocol, source hashes, completion files, output hashes and subprocess logs are retained. Each subprocess had a 180-second deadline. Neither timeout nor a failed worker is treated as success.

## Longer resource measurements

A second recorded protocol ran the first 10 ms of the same baseline at 0.0008, 0.0004, 0.0002 and 0.0001 ms with 1 ms recording windows. It preserved input times, recorded full spikes and delivered events, checked output grids, and measured peak resident process memory. All cases completed within their 240-second external deadlines. These short prefixes omit most of the scientific trial and cannot establish late response behavior or convergence.

| Step, ms | Simulator elapsed seconds, including construction | Peak process memory, decimal GB | Spikes in first 10 ms |
| --- | ---: | ---: | ---: |
| 0.0008 | 19.578 | 2.675 | 26 |
| 0.0004 | 34.937 | 2.675 | 26 |
| 0.0002 | 66.532 | 2.675 | 26 |
| 0.0001 | 126.125 | 2.675 | 26 |

All four schedules contain the same 23 physical input events, and every scheduled event was delivered in these prefixes. All output hashes were independently rechecked. Identical counts do not imply identical spike times or full-duration convergence. A naive hundredfold scaling of the final runtime is about 3.5 hours for one second of simulated time, but initialization, activity, recording overhead and platform performance make that an estimate, not a measured duration. Whole-trial memory will also include a larger input tape and potentially many more spikes. These measurements support moving the full-duration work to CCR and benchmarking its backend before setting concurrency and wall time.

The compact [verification record](evidence/2026-09-29/fine_steps/record.json) retains measured results and source-record hashes. Full protocols, subprocess logs and event files are under results/pcdr/fine_ramp_20260929 and results/pcdr/fine_benchmark_20260929. No peak-memory claim is made for the earlier uninstrumented benchmark.

## Next scientific comparison

Use CCR for the full-duration sequence after measuring costs there. Retain the existing full51 candidate, baseline and three fixed comparison sets; use the same physical inputs at every step. Include the two previously divergent altered-weight examples with their baselines. A fixed small seed panel can establish feasibility, followed by the declared thirty-seed default comparison; the small panel must not replace that comparison silently. Record practical absolute and relative agreement criteria before seeing new one-second results, and assess full response vectors and population timing as well as A/F. A smaller step alone does not establish convergence or resolve comparator imbalance.
