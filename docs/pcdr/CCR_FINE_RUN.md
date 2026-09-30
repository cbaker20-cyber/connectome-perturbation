# CCR fine-step run

30 September 2026. This package tests numerical agreement. It does not repair the earlier comparison-set imbalance or make this a confirmatory eigencircuit experiment.

## Upload and launch

Use one upload: CCR_Fine_Steps.zip. It contains the connectivity data, the necessary original trial evidence, exact input schedules, code, dependencies and notebook. No previous remote folder is required. Keep the ZIP and extracted files in your home directory while the smuldoon project quota is full. Before starting, check your remaining home quota with rquota from a login terminal. Results retain full spikes; allow several GB beyond the extracted package and environment. Reported filesystem free space is not your personal quota.

Upload through OnDemand Files to /user/cbaker4. From its terminal, run these as separate complete lines:

```bash
cd /user/cbaker4
unzip -n CCR_Fine_Steps.zip
```

A fresh package creates /user/cbaker4/connectome_fine. Do not extract a changed package over an existing run. Keep the existing folder to resume that exact run.

Request the Jupyter Advanced application with these settings:

| Field | Value |
| --- | --- |
| Cluster | UB-HPC |
| Account | smuldoon |
| Partition | general-compute |
| QoS | The permitted general-compute option in your form; do not type an unavailable value |
| Cores | 64 |
| Memory, MB | 512000 |
| Hours | 72 |
| GPUs | None |
| Extra Jupyter modules | Blank |
| Node features | Blank; retain the application's supported architecture |

These are resource requests, not guaranteed queue availability. More cores shorten independent trials; one NumPy simulation remains single-process. The controller tests 1, 8, 32 and up to 60 workers within the allocation. It chooses the smallest tested count within 90% of the best measured throughput. Two CPUs and 16 GB are reserved; at least 8 GB per worker is allowed, or 1.5 times measured peak memory if larger. Whole-trial input arrays use more memory than the previous 10 ms prefixes, so this allowance exceeds their measured 2.68 GB. Short probes cannot establish every later memory peak.

Open connectome_fine/CCR_Fine_Steps.ipynb. Choose Cell → Run All in classic Notebook, or Run → Run All Cells in JupyterLab. The notebook kernel may remain Python 3.9: the shell separately loads the previously working ccrsoft/2024.04, gcccore/13.2.0 and python/3.11.5 modules. It creates .fine-venv and uses that interpreter for every simulation. It does not modify the Jupyter server's module environment or ask you to paste an absolute Python path.

Run All installs pinned libraries, runs focused implementation tests, verifies package hashes, runs four one-second exact replays, measures concurrency, runs the 616 fine-step trials, verifies output hashes, computes summaries and creates CCR_fine_results.zip. Use either the notebook or the terminal launcher, not both. A file lock prevents two launchers in the same folder.

An equivalent command inside the allocated Jupyter terminal is:

```bash
cd /user/cbaker4/connectome_fine
bash -lc 'bash run_all.sh' > run_all.log 2>&1
```

Do not start simulations on login1/login2. The controller requires a Slurm allocation. Closing the browser does not cancel the notebook-launched subprocess, but ending the allocation stops it. Re-running the launch cell while it is active is unnecessary and rejected by the lock.

## Progress and download

From a terminal:

```bash
tail -n 30 /user/cbaker4/connectome_fine/run_all.log
cat /user/cbaker4/connectome_fine/fine_results/progress.json
squeue -j YOUR_JOB_ID -o "%.18i %.10M %.10L %t"
```

Replace YOUR_JOB_ID with the number printed by the notebook. During a long trial the completed count can remain unchanged for hours; updated_utc and active reflect the controller. Before production, replay and capacity logs appear in run_all.log and fine_results. Worker stderr and process records are kept under fine_results/logs.

Download connectome_fine/CCR_fine_results.zip through the notebook's final link or OnDemand Files. It includes raw spikes, rates, delivered inputs, population timing, per-seed and mean results, agreement checks, logs and source files. A complete run has status complete and completed equal to total (620). A result ZIP can also contain a stopped run; its existence does not mean the experiments completed.

The simulation budget is at most 70 hours, additionally limited by actual Slurm time remaining minus 30 minutes for collection. Local timing gives roughly 1,000 CPU-hours for the fine-step set by simple scaling, before concurrency contention and CCR differences. This is not a measured completion prediction. More memory cannot eliminate per-trial sequential work.

## Interrupted runs

Completed trials are hash-checked and reused on another Run All in the same folder. An incomplete trial is moved into an interrupted subfolder before restarting; it is never reported as complete. Corrupted complete outputs stop the run rather than silently being replaced. Every new allocation repeats the replay and throughput checks. The source plan and package must remain unchanged.

The outer shell lock releases when its process ends. If Slurm kills the job, fine_results/controller.lock can remain because cleanup did not execute. First confirm the recorded Slurm job has ended and there are no active workers. Only then remove that one stale controller.lock file, and Run All in a new allocation. Do not remove a lock while its job is active. A hard Slurm termination may also prevent the result ZIP from being written; the unarchived trial directories remain resumable.

## Fixed design and interpretation

Four exact replays precede 616 new one-second simulations. The default panel has 30 previously used seeds, baseline, the unchanged 51-neuron mode and motor_003/004/005 at 0.0008, 0.0004, 0.0002 and 0.0001 ms: 600 trials. The other 16 trials retain w120_i080 mode-without-MN9 seed 631405 and MN9-only seed 631430, each with its baseline at all four steps. No new eigenvector selection or outcome-based seed substitution occurs. All scheduled physical input times are retained from the saved 0.1 ms input process; this tests time discretization conditional on that input process, not a continuous-time Poisson limit.

For adjacent steps, the declared checks are A difference at most max(1 Hz, 5% of finer-step A), F difference at most 0.01, relative L1 difference of the full paired response vector at most 0.05, and relative L1 difference of 10 ms population counts at most 0.05 for both baseline and lesion. Undefined F does not pass. A group requires the mean paired response criteria and at least 95% of its individual pairs; a single altered-weight case must pass itself. Both final successive halvings must pass before describing agreement over the tested range. These are chosen practical numerical tolerances, not literature-established biological thresholds. All differences remain available if they fail; do not loosen criteria after viewing outcomes. Spike-by-spike identity is required for exact same-step replays, not for comparisons across different time grids.

The batch retains NumPy execution and the tested windowed recorder. Changing to a compiled backend might help later, but would require its own event-equivalence evidence. There are no GPU tasks in this package. No full-duration fine-step results are claimed before CCR execution.

## Libraries and sources

Python 3.11; NumPy, SciPy, pandas, PyArrow, Brian2, Cython, matplotlib, joblib, pytest and statsmodels, plus their pinned dependencies in requirements-ccr.txt. psutil and NetworkX are not required by this run. Installed versions are saved in the results.

CCR documents resource selection and Slurm limits at https://docs.ccr.buffalo.edu/en/latest/hpc/jobs/ and OnDemand at https://docs.ccr.buffalo.edu/en/latest/portals/ood/. The module sequence above was previously verified in this user's CCR terminal; local packaging does not re-test remote module availability.

Brian2 linear/exact integration solves the linear subthreshold equations, while network scheduling still uses the clock: https://brian2.readthedocs.io/en/2.9.0/user/numerical_integration.html and https://brian2.readthedocs.io/en/2.9.0/user/running.html#scheduling. Reducing this clock step addresses event timing; it does not add biological detail to the model.
