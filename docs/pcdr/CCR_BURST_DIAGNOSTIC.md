# Two recorded replays at CCR

Use `CCR_Diagnostic.zip`, extract it into a new folder in your writable home directory, and open `connectome_diagnostic/CCR_Burst_Diagnostic.ipynb`. Select Run All. Do not extract over the completed fine-step study.

Request UB-HPC, account smuldoon, general-compute, a permitted QoS, 4 CPU cores, 32000 MB RAM, 12 hours, no GPU. Leave extra modules and node features blank. Only two simulation workers run; requesting dozens of cores would not accelerate this fixed pair. The extra cores allow the notebook and file collection to operate alongside them. Times are estimates based on the preceding full-network study, not a guaranteed completion time.

The shell loads ccrsoft/2024.04, gcccore/13.2.0 and Python 3.11.5. The notebook kernel can remain on its existing version. It installs pinned dependencies in `.diagnostic-venv`, verifies immutable package files, runs tests, launches both replays and collects `CCR_diagnostic_results.zip`. Notebook outputs and execution counters are excluded from byte hashes to avoid the previous autosave failure. Simulation code, reference files, parameters and data remain hashed. The full dependency versions are in `requirements-ccr.txt` and the installed list is included in the result archive.

The model, lesion and input schedules stay fixed. Steps are 0.0004 and 0.0002 ms; both start at time zero and stop at 750 ms. Voltage, drive and refractory state are recorded for 34 preselected cells during 600–750 ms in bounded chunks. Recording phases are before threshold detection (after integration), after synaptic events (before reset), and end of step (after reset). The diagnostic fails if spikes or delivered inputs differ from the exact saved prefixes. A completed job provides observations for a mechanism analysis, not an automatic conclusion about the cause.

The notebook prints simulated milliseconds for each worker. A quiet interval means the current 10 ms simulated chunk is still processing; each chunk can take minutes. From a Jupyter terminal:

```bash
cd /user/cbaker4/connectome_diagnostic
tail -n 30 run_all.log
cat diagnostic_results/0.0004/state/progress.json
cat diagnostic_results/0.0002/state/progress.json
```

Adjust the directory if you extracted elsewhere. The recorded state files begin only at simulated time 600 ms. Browser disconnection does not itself stop the detached launcher, but expiration of the CCR allocation does. Keep the notebook tab or reopen it to monitor files; do not click Run All again while a controller is active.

Download `CCR_diagnostic_results.zip` when the notebook reports success. Also retain the upload locally. If the kernel disconnects after completion, the ZIP remains accessible through OnDemand Files. A result ZIP is only made after both prefix checks and output hashes pass.

Completed matching trials can be reused. Failed trial directories and their logs are deliberately not overwritten. After confirming that the original job and processes have stopped, preserve any failed trial directory and its corresponding log directory under a dated attempt folder before rerunning. A hard kill can leave `diagnostic_results/.controller.lock`; remove only that stale lock after confirming its owner is no longer running. Never remove a live controller's lock. The shell's `.run_all.lock` uses an operating-system lock that releases when its owner exits. Setup and collection need allocation time in addition to the worker allowance of 11 hours.

This is a targeted replay, not a new control-set study or a replacement for the previous convergence test. The original raw results remain untouched.
