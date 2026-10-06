# Two-connection test at CCR

Upload `CCR_Pathway.zip` to your home directory and extract it into a new folder. Open `connectome_pathway/CCR_Pathway.ipynb` in a compute session and select Run All. The notebook starts setup and four simulations, shows progress, and links the results ZIP when collection finishes. No Git checkout or separate dataset upload is needed.

Use account `smuldoon`, UB-HPC, `general-compute`, the permitted QoS, 4 CPU cores, 32000 MB RAM and 8 hours. Leave GPUs blank. Four independent trials use the four cores; extra cores would not speed up these single-threaded workers. The shell loads `ccrsoft/2024.04`, `gcccore/13.2.0` and `python/3.11.5` for simulation. The notebook kernel can stay on its existing Python version.

These module names worked in the previous CCR sessions. A module or package error stops the run; do not silently change versions. The package pins the recorded dependencies: NumPy, SciPy, pandas, PyArrow, Brian2, Cython, matplotlib, joblib, pytest and statsmodels, plus their recorded dependencies. It creates a separate `.pathway-venv` in the extracted folder.

## What runs

The experiment retains seed 631430, saved sugar stimulation, weight scale 1.2, inhibitory scale 0.8 and the MN9 outgoing lesion. At each of 0.0004 and 0.0002 ms, run an unchanged reference and a version with two connections removed from source 720575940628695043 to targets 720575940629667639 and 720575940623862015. Each trial starts at time zero and ends at 750 ms.

Measure non-input spikes and newly recruited non-input cells in [650,730) ms. Newly recruited cells have no earlier spike before 650 ms. Keep the source and two target spike histories. References must reproduce archived spikes exactly, and all four trials must reproduce archived delivered stimulation. A failed check stops successful collection. This selected-case experiment tests the pathway's contribution; it does not establish convergence or eigencircuit specificity.

## Reconnect and download

The launch cell starts a separate process. Closing the tab or losing the VPN should not stop it while the allocation remains active. After reconnecting, run only the status cell to check progress. Do not launch another copy in another extracted folder. Download `CCR_pathway_results.zip` after status says `complete`. It contains spikes, stimulation events, endpoints, checks, source code and logs. State recordings and duplicated model datasets are omitted.

From a terminal in the extracted folder:

```bash
tail -n 40 run_all.log
cat pathway_results/progress.json
cat pathway_results/*/simulation_progress.json
```

Before the simulation starts, package installation and tests appear in `run_all.log`. During simulation, progress is recorded every 10 ms of model time. Each trial has its own log under `pathway_results/logs`. The first 10 ms can take a while. The requested eight hours is an allowance; earlier two-trial diagnostic runs took about 74 and 147 minutes, but four-way concurrency may change timing.

Completed trials can be reused only after their hashes, specifications and sources pass verification. Interrupted trials cannot resume from a partial simulated time: delayed events and network state are not checkpointed. The controller preserves those folders and stops for review. Do not delete a lock while another process may be using it. An allocation ending can leave a stale lock; confirm the old job has ended before handling it. Preserve failed outputs before retrying a trial from time zero.

The working notes and code include assistance; this package is not an independently student-written submission.
