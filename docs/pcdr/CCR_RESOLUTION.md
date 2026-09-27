# Further time-step comparisons

The completed follow-up established exact replay for the selected trials, but not convergence across time steps. Four selected large responses became much smaller at 0.05 and 0.025 ms. The MN9-only response at seed 631430 became smaller at 0.05 ms and large again at 0.025 ms. The default-setting conclusions were not tested at finer steps in that package. These are separate gaps, and both are addressed here.

The equations use Brian2's linear method. That solves the between-event linear equations; it does not remove the clock's role in spike detection, propagation and resets. Brian2 2.9.0 documents both the linear/exact method and the time grid used for spikes and scheduling. This is why successful exact replay is insufficient as a numerical check. The current work changes the clock step while preserving the equations, physical input times and scheduling slots. [Numerical integration](https://brian2.readthedocs.io/en/2.9.0/user/numerical_integration.html), [simulation clocks and scheduling](https://brian2.readthedocs.io/en/2.9.0/user/running.html).

## Recorded scope

| Stage | Trials | Purpose |
| --- | ---: | --- |
| Replay | 4 | Check paired default baseline/mode and high-weight baseline/MN9-only against the original outputs before proceeding |
| Finer selected cases | 46 | Reuse all 23 source trials selected in the previous follow-up, including paired baselines, at 0.0125 and 0.00625 ms |
| Default setting | 480 | Run all 30 original seeds at 0.05 and 0.025 ms for baseline, mode, mode without MN9, MN9 only, three comparison sets and active29 |
| Total | 530 | Retrospective numerical follow-up |

The high-weight source selection is unchanged from the previous package. The added default trials use every original default seed, not seeds chosen for a favorable response. Active29 keeps the original 29 IDs rather than selecting a different set after each time-step change. These are reused input realizations, not held-out validation or new animals. All groups are retained regardless of their responses.

Input events stay at the original physical times. A finer tape places the original jump on every corresponding fine tick and zeros on intervening ticks; it does not repeat each jump across several ticks. The old input reader validates the original event table. The time steps divide the original 0.1 ms grid exactly. Tests compare the new and previous tapes at all previously used steps and verify the new mappings.

The collector reports both each lesion's own-support footprint and its fixed-51-support footprint. Use the own-support mode/comparator endpoints to compare with the original primary question; use the common 51-cell support when comparing active29 with full51. Mean-vector results average signed changes before taking absolute values. Every lesion is paired with a baseline at the same step, variant and seed. Changes in the number of active cells at a finer step do not silently redefine the lesion.

No universal pass threshold for convergence has been invented. Review the rate differences, population trajectories and the direction and size of the mode/comparator contrasts across steps. Stable aggregate results and exact agreement of every spike are different claims. If the smallest steps still disagree, report unresolved step dependence. If the default comparison changes, retain both estimates and revise the claim; do not choose a preferred step by the size of the effect. This batch does not repair the comparison sets' distributional imbalance or establish biological circuit independence.

## Upload and run

Use the existing CCR session if enough time remains. Upload CCR_Resolution.zip to /user/cbaker4 and run this as one terminal line:

```bash
unzip -n /user/cbaker4/CCR_Resolution.zip -d /user/cbaker4/connectome
```

Open CCR_Resolution.ipynb in /user/cbaker4/connectome and select Run All once. Keep the existing original study, followup_plan.json, simulator helper, .ccr-venv and ccr_python.json. The package includes the unchanged simulator helper in case it is needed; it does not replace the earlier runner or completed outputs. No package installation is requested. The notebook reuses the recorded Python 3.11 module environment, excludes PYTHONPATH/PYTHONHOME, and sets MPLBACKEND=Agg. Its own kernel may stay at Python 3.9.

For a new allocation use UB-HPC, smuldoon, general-compute with matching QOS, 24 cores, 192000 MB RAM, six hours and no GPU. Leave extra modules and node features blank. At most 16 simulation workers run concurrently, limited further by available CPUs and an allowance of 8 GB per worker plus 8 GB for the controller. This is a resource budget, not a claim about measured peak usage for every new trial.

The notebook requests at most 3.5 hours of worker time. The controller reads the remaining Slurm time and reduces that budget if needed, reserving 30 minutes for collection and packaging. It refuses to start if less than an hour remains. The full 530-trial runtime has not been measured. A six-hour allocation is an allowance, not an expectation that the work must use all of it. A worker has an external time limit of at most one hour or the remaining controller budget. A failure stops later stages.

The process writes a log independently of the browser. Check it with:

```bash
tail -n 20 /user/cbaker4/connectome/resolution_20260927_controller.log
cat /user/cbaker4/connectome/results/resolution_20260927/progress.json
```

When status is complete and the count is 530, download /user/cbaker4/connectome/results/resolution_20260927/CCR_resolution_results.zip and the controller log. This results ZIP includes the full spike and delivered-event files, so a separate tar download should not be needed. It also contains the plan, sources, sparse rates, neuron universe, traces and summaries.

Existing output folders are refused. Partial runs are preserved but not automatically resumed. Do not launch another copy while it is running or delete failed results. If a worker fails, send the available ZIP and log. A failure before worker startup is recorded in the controller log. A hard allocation termination can interrupt packaging, although per-trial files remain. Closing the browser does not stop the separate process while the allocation stays alive.

## Verification before upload

The tests cover event timing at all five steps, agreement with the old tape at the three previous steps, invalid remaining-time responses, full job and paired-baseline coverage, stage ordering, failure stopping, full-evidence packaging, overwrite refusal and the distinction between lesion support and the fixed mode support. Previously used checks are also rerun. The local finest-step worker test and its measured result are recorded in the lab notebook. It is a development run, not an additional member of the planned CCR sample.

All 51 focused tests passed. The local 0.00625 ms MN9-only test at seed 631430 completed in 226.97 seconds with a recorded peak RSS of 2.83 GB. It produced 21,172 spikes, 478 recruited non-input neurons and MN9 at 119 Hz. The paired finer-step baseline has not been run locally. The 530-trial plan was recorded before this result was inspected and remains unchanged. The complete CCR batch has not yet run.
