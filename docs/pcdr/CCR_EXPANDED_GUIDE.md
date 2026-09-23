# Expanded CCR study

Upload and extract this ZIP, then open `connectome/CCR_Expanded_Study.ipynb`.

Request **32 cores, 128000 MB RAM, 8 hours, no GPU** in OnDemand. Use UB-HPC, account smuldoon, general-compute and the valid QoS offered for that allocation. Keep the Jupyter application's supported architecture. This is an initial reservation; close the session when the work finishes. Availability and queue time depend on the allocation. CCR supports custom single-node OnDemand resource requests: [OnDemand](https://docs.ccr.buffalo.edu/en/latest/portals/ood/), [job resources](https://docs.ccr.buffalo.edu/en/latest/hpc/jobs/).

This replaces the earlier undersized two-worker recommendation. It prepares 3,390 one-second whole-brain trials:

- 1,890 trials: nine joint overall-weight/inhibitory-multiplier settings, seven conditions, 30 paired seeds.
- 1,500 additional trials: individual lesions of the other 50 mode cells, 30 paired seeds, default network only. MN9-only and the shared baseline are already in the first group.

The full 3 x 3 grid tests parameter interactions that the earlier one-factor design could not. Individual lesions map the contribution of every mode neuron, rather than assuming the combined support is functionally uniform. Inhibitory weights receive the product of the overall scale and inhibitory multiplier. These are model sensitivity settings, not measured biological uncertainty. No new mode is chosen from these outcomes.

The notebook first runs the four technical checks. It then measures throughput on real pending study jobs at 1, 4, 8, 16 and up to 24 workers, capped by allocated CPUs and measured memory. It reserves two CPUs and 12 GB for the notebook/analysis, with 50% extra memory per worker beyond the observed peak. It chooses the smallest tested concurrency within 90% of the best observed throughput. Those calibration trials remain part of the fixed study. Outcomes do not determine concurrency or membership.

The controller runs within the existing allocation and submits no extra Slurm jobs. It has a seven-hour limit after calibration; the scheduler's eight-hour allocation remains the outer limit. Completed trials are checked and reused on restart. A STOP file prevents new trials. After a killed session, confirm the old processes ended before removing stale locks. Calibration must be repeated in a new allocation. Short calibration waves are approximate and cannot guarantee every later memory peak.

The archive remains about 95 MB because it contains the same three input datasets and no old simulation results or virtual environment. Exact libraries and dependencies are in `requirements-ccr.txt`; Python 3.11 is the simulation target. NumPy, SciPy, pandas, PyArrow, Brian2, Cython, matplotlib, joblib, pytest and statsmodels are pinned along with their dependencies. Linux installation and actual CCR scaling remain untested locally.

This is an explicit exploratory amendment after the user asked to use CCR more substantially. The original 350-job design is retained in the repository. More computation does not fix the distributional mismatch of the optimized controls. Report all conditions, individual cells and variants, conditional seed intervals, and no random-reference p-values. Single-cell effects are not additive in this recurrent model.
