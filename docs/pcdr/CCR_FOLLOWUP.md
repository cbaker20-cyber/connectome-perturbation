# Running the follow-up

Completed-run update: all 101 trials finished and the full files passed the local checks. All 25 replays matched. Smaller time steps changed several large responses, with the MN9-only case still inconsistent across steps. This package's planned run is complete; the instructions below are retained for reproducibility, not a request to rerun it. See CCR_RESULTS_20260927.md for the verified findings and remaining questions.

This package adds 101 trials to the existing study without changing its files. The stages are 25 exact replays, 46 trials at 0.05 and 0.025 ms, and 30 lesions of the 29 mode cells active in at least one default baseline. Selection and IDs are recorded in CCR_FOLLOWUP_PLAN.json. This is a follow-up to observed results, not a new confirmation of the eigencircuit claim.

For each of the six lesion conditions at weight 1.2/inhibitory multiplier 0.8, the plan selects the seed with the largest total rate change and the seed nearest the median total change, breaking ties by smallest seed. It includes the paired baselines and removes duplicate trial selections. Two default replay trials are also included. Each finer-step trial uses the original physical input times, with zero input on the intervening finer ticks. It does not generate a new Bernoulli input sequence or interpolate the old input into repeated jumps. Delivered inputs remain voltage dependent.

The run stops if a replay's spikes or delivered inputs differ from the original. A CPU change is recorded, but cannot silently excuse a replay mismatch. Python and package versions must match the original environment. Finer-step trials are checked for valid inputs and spike timing; they are collected without declaring convergence from an arbitrary cutoff. The reduced lesion uses the same 30 seeds as the original default runs, so it is a retrospective comparison. Its footprint is reported on the original fixed 51-cell support. Reference-set design remains separate and is not fixed by this package.

## CCR settings

| Field | Value |
| --- | --- |
| App | JupyterLab, Advanced Options |
| Cluster | UB-HPC |
| Account | smuldoon |
| Partition | general-compute |
| QOS | general-compute, matching the partition |
| Hours | 6 |
| Cores | 24 |
| Memory per node | 192000 MB |
| GPUs | None; leave blank |
| Extra modules | Leave blank; reuse ccr_python.json |
| Node features | Leave blank for the supported Jupyter app |

The runner uses up to 16 single-thread workers, limited by the allocated CPUs and memory. It budgets 8 GB per worker plus 8 GB for the controller and notebook. This is a resource allowance, not a measured memory requirement. More than 24 allocated cores will not accelerate this implementation's 16-worker limit. The notebook allows five hours for workers, leaving time within the six-hour allocation for setup and collection. Actual CCR duration has not been measured for this package. A full-network local replay took about 19 seconds and a selected 0.025 ms trial about 57 seconds, excluding validation and collection; those timings are not a cluster runtime promise.

## Upload and run

Upload CCR_Followup.zip to /user/cbaker4 using OnDemand Files. Use the existing home-directory project, not the full shared smuldoon directory. In a CCR terminal, run this as one line:

```bash
unzip -n /user/cbaker4/CCR_Followup.zip -d /user/cbaker4/connectome
```

Start the Jupyter allocation above. Open /user/cbaker4/connectome/CCR_Followup.ipynb and select Run All once. The notebook may keep its Python 3.9 kernel. It launches simulations through the existing .ccr-venv/bin/python, using the saved ccr_python.json module environment and MPLBACKEND=Agg. No pip installation is needed. Dependencies remain the installed NumPy, pandas, PyArrow, Brian2, SciPy and their recorded dependencies; the runner also imports existing project helpers. It rejects a changed recorded package environment rather than silently installing different versions.

The controller writes to a file rather than the browser connection. Closing the browser does not stop the separate process while the allocation remains alive. Do not launch a second copy. In a terminal, check:

```bash
tail -n 20 /user/cbaker4/connectome/followup_20260927_controller.log
cat /user/cbaker4/connectome/results/followup_20260927/progress.json
```

The status must be complete and the completed count must be 101. Collection and packaging happen automatically after the trials. Download /user/cbaker4/connectome/results/followup_20260927/CCR_followup_results.zip and the controller log. The ZIP contains sparse rates, the neuron universe, population traces, summaries, manifests, source files and worker logs. The much larger spike and delivered-event tables remain in the new trial directories on CCR. Keep them until review is finished.

If a worker fails or reaches its limit, subsequent stages stop and the runner tries to package the completed and failed records. Send that ZIP and log rather than changing versions or deleting outputs. A preflight failure appears in the controller log before an output folder is made. A hard allocation termination can prevent final packaging; the per-trial files remain. This version preserves partial runs but does not automatically resume them. Existing output folders are refused; do not delete them to restart. Reopening a completed run shows its download location without rerunning trials.

## Local verification before upload

The default full-mode replay at seed 631401 matched the original CCR spike and delivered-event digests exactly on the local PC. A full-network test of comparison 004, seed 631427, at 0.025 ms completed with the saved physical input times and valid spike spacing. It produced 18,762 spikes and MN9 at 109 Hz, compared with 739,680 spikes and MN9 at 26 Hz in the saved 0.1 ms trial. This single development test raises a time-step concern; its finer-step paired baseline has not been run locally, and it does not establish convergence or explain every exceptional trial. The recorded 101-trial selection was prepared before inspecting this result and was not changed afterward. The CCR package reruns it under the recorded CCR environment along with the other selected cases.

Thirty-four focused tests passed, including saved-time mapping, invalid event rejection, same-step agreement on a small network, stage order, stopping after replay failure, output-folder protection, failure packaging, paired-step collection and changed-output rejection. The full 101-trial CCR sequence has not run yet. Historical trial evidence and simulation source files remain unchanged.
