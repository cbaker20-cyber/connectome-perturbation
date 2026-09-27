# CCR run, 27 September 2026

The downloaded controller records report all 3,390 planned indices complete, with no missing or duplicate indices. There were 3,337 new worker processes, all with exit code zero and no timeout, and 53 reused trials. The controller log contains the complete sequence from 1 through 3,390 without other messages. The last progress update was 05:26:30 UTC, or 1:26:30 a.m. Eastern. This is the controller's completion record, not the time the user saw the disconnected notebook.

Fresh workers took a median 58.57 seconds, with a range of 44.14 to 78.85 seconds. Their summed durations are overlapping worker wall times, not the duration of the study or measured CPU usage. These two files do not establish the selected worker count or when the controller started.

The original downloads remain under results/pcdr/results_ccr_20260927. Their SHA256 hashes and the status audit are in evidence/2026-09-27/controller_audit.json. The audit checked index coverage, each fresh worker's command index and exit status, timeouts, and the controller's numbered completion sequence. This is execution evidence. It does not independently verify the trial files or establish an eigencircuit effect.

## Collection before interpretation

Use a new CCR Jupyter allocation for collection only; an initial request of four cores, 16000 MB and two hours is reasonable but has not been benchmarked for this collector. Open the existing notebook in /user/cbaker4/connectome and run its first two setup cells with the saved Python-module configuration and MPLBACKEND=Agg fix. Keep all simulation files and package pins unchanged. Do not run the study launch cell. The collection command is the existing pcdr_ccr_sensitivity.py collect action on results/expanded_sensitivity.

The collector requires the prepared environment and source/data fingerprints, checks all trial output hashes and rate tables against spikes, and checks baseline/lesion input pairing before computing descriptive summaries. If a lock or provenance error appears, investigate it rather than deleting locks or relaxing validation. Successful collection produces results.json and per_seed.csv. Retrieve those with jobs.json, capacity.json, the smoke certificate, installed library list and controller records. Retain the underlying trials on CCR.

## Analysis order

Keep the frozen 3,390-job design. First verify the nine parameter settings, 30 seeds, condition memberships and expected 104 condition-by-network summaries and 3,120 per-seed comparisons. Check the all-neuron rate universe, own-network baselines and input pairing before interpreting any effect.

Then describe the 51-cell mode's footprint at the default setting and its paired differences from each of the three existing comparison sets. Report A (mean absolute change within the lesioned set), F (fraction of total absolute change within that set), total change and off-set change together. A high within-set change is not by itself evidence of confinement.

Compare the full mode with mode-without-MN9 and MN9 alone, then examine all 51 individual lesions at the default setting. Do not treat individual effects as additive. If neuron-level combined-versus-single comparisons are needed, calculate them from retained rate tables under a recorded analysis procedure; aggregate A and F alone do not establish interaction or synergy.

Report every setting in the full 3 by 3 parameter grid, including reversals or weak responses. Do not choose a new mode, remove a comparator or select a favorable setting based on these outcomes. Bootstrap intervals describe variation across simulated input seeds for this model. The optimized comparison sets do not support random-reference p-values or claims of biological replication. Decide further experiments only after this collection and review.

This note and the audit were prepared with Codex assistance. Scientific outcomes have not yet been supplied or analyzed.
