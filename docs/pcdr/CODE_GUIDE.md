# Notes on the P/D/C/R code

This explains the code separately from the implementation. Start with the small examples, then compare them to the saved files. Run commands from the repository root.

## Added 22 September: motor-composition audit and pilot

- `pcdr_motor_set_audit.py` reads the nine accepted memberships and original baseline features, verifies their evidence hashes, and checks original SMD and exact strata again. It saves ECDF gaps, variance ratios, min/quartiles/max and full annotation counts. ECDF gap is the largest difference in cumulative proportions. Categorical total variation is half the sum of category-proportion differences. Both are descriptive here; no new acceptance cutoff is introduced.
- `pcdr_motor_composition_pilot.py: prepare` records the question, every fixed set, fresh seeds, analysis definitions, known audit objections, source hashes and a thirty-minute deadline. It checks that the existing model/data/package versions agree with the earlier study. It creates 55 jobs: baseline plus ten lesion conditions for each of five seeds. `run` rechecks the frozen sources and reuses the serial queue. No model equations or simulation parameters change.
- `pcdr_verify_motor_pilot.py: main` verifies every completed trial's identity, parameters, membership and output hashes. It joins all 127,400 neuron IDs, checks all 50 input pairings, and independently rebuilds the ten mean footprints and summaries. The final audit is written only after all checks pass. It requires exactly the frozen 55 trials; partial studies cannot produce a completion record.
- `contrast_interval` bootstraps the same five paired seed indices for both conditions. It computes each mean neuronal response first, then absolute responses, then each condition's own-support A/F. Only then does it subtract the comparison from the mode. The intervals are conditional descriptions, not corrected inferential tests. If total response is zero, F is undefined and that bootstrap resample is counted rather than replaced with zero.
- `pcdr_motor_response_duplicates.py` is a separately recorded post-result diagnostic. It groups conditions by their five saved spike digests, then checks actual full spike tables and all-neuron rate tables for exact equality. It lists varying lesion memberships and checks those cells' counts in every baseline and relevant lesion trial. Three groups of three comparisons had identical trajectories; their varying cells were silent in these runs. This is not a claim about new seeds or model variants.
- `pcdr_publish_evidence.py` copies an explicit small list of completed records into docs/pcdr/evidence, checks byte-identical copies and writes a source manifest. Small parquet tables also get CSV views. It does not copy all spikes or full trial archives. A new snapshot directory is required, so a completed record is not silently rewritten.
- `pcdr_motor_pilot_report.py` verifies that compact snapshot and generates the all-set Markdown report and scientific figure. The figure shows A/F intervals and baseline incoming-degree spread, with every comparison retained. It can be regenerated from the committed evidence without running simulations.
- `pcdr_build_motor_record_pdf.py` appends the new research notes to a new PDF edition while retaining the prior 66-page record. It uses reportlab and pypdf in the document runtime, checks that old page text is unchanged and records source hashes. Rendered pages need visual review before delivery. It changes no research result.
- `pcdr_motor_record_qa.py` renders the complete new PDF with Poppler, compares all preserved pages pixel for pixel with the previous verified edition, and creates review images for every new page. It takes the actual pdftoppm executable path rather than assuming a particular installation.

All were created with Codex assistance. The local software suite passed 224 tests with 3 skipped before committing this research work. Archived trial source ZIPs retain original bytes; Git normalization of older tracked Windows files can change byte hashes across platforms, so use the archived source and recorded environment for exact frozen replays. New evidence files explicitly disable line-ending conversion in Git.

## Added 22 September: full-pool feasibility and small binary completion

These functions use baseline features and the selected mode's IDs. They do not run the brain model or read lesion responses. Full dated results are in FULLPOOL_FEASIBILITY_20260922.md.

- `scripts/pcdr_bounded_process.py: run_bounded` starts one owned worker, writes stdout/stderr to files and waits only to a specified deadline. Windows taskkill uses that process's PID with tree termination, so a venv launcher's child cannot keep solving after the launcher stops. Normal completion, worker failure and timeout have different recorded fields. The timeout test uses a sleeping child, not a real scientific solver.
- `scripts/pcdr_fullpool_relaxation.py: load_design` checks frozen feature/selection hashes, exact string IDs and finite nonnegative features. It creates the full eligible pool, exact sign/recruitment/annotated-motor strata and two mean tolerances. No target or input cell can enter the pool.
- `solve_relaxation` gives every eligible cell a weight between zero and one. Stratum rows require the right number of cells in weighted sums; feature rows constrain six log1p means. The objective is zero. The conservative version uses sufficient mean bounds; the outer version uses necessary bounds derived from maximum possible variance. Both are diagnostics. For example, half of a cell with feature 0 plus half of one with feature 2 can match a target mean of 1 when no single real cell can.
- `validate_fractional` recalculates stratum sums, feature means and membership bounds from the returned vector. A solver success flag alone is insufficient. It records how many entries are actually fractional, but does not round them into an accepted set.
- `main` records the LP method, budget and hashes before launching exactly two serial workers. `worker` checks hashes again, solves one formulation and saves the full vector and environment information. Timeouts preserve logs and process records. Existing study folders are not overwritten.
- `scripts/pcdr_fractional_completion.py: completions` fixes entries close to zero or one, then considers every binary assignment of at most twelve fractional entries. With seven such cells there are 128 assignments. It yields only assignments with exact stratum counts. The cap prevents an unnoticed exponential search.
- Its `main` records a separate follow-up protocol before enumeration, recalculates the original pooled-variance SMD for every count-valid assignment, and retains every passing set. It records the stricter sufficient bounds separately. A set can fail those sufficient bounds and still legitimately pass the original SMD; the comparison set's variance appears in the original denominator.
- `scripts/pcdr_verify_fractional_completion.py: main` independently rereads memberships and original features. It checks exact size, unique IDs, exclusions, strata, all six pooled SMDs, evidence hashes and set overlap. It does not call the search or shared SMD helper. It checks saved accepted witnesses; the exhaustive toy test checks enumeration behavior separately.
- `tests/test_pcdr_fullpool_relaxation.py` includes external timeout, normal/error exits, a fractional-only toy solution, a jointly impossible two-feature target despite overlapping separate intervals, outer-bound inclusion of all valid enumerated toy sets, and exact binary-completion enumeration with the cap.

All new code was created with Codex assistance. The tests and nine verified sets establish computational feasibility under the stated rules. They do not validate a random-control distribution or any biological effect.

## How one trial works

`trials.simulate()` calls the existing `model.create_model()`. It does not fit new physiology. The model gives each neuron a voltage and synaptic state, connects the supplied directed edges, and uses the existing spike threshold, reset and delays.

- `brian2.seed(seed)` sets the random stream before constructing the network.
- Sugar neurons receive a saved Bernoulli input schedule with probability 0.015 per 0.1 ms step. This matches N=1 PoissonInput's stepwise distribution at 150 Hz. A separate seeded NumPy generator produces the full schedule before simulation, so feedback cannot change which random numbers other inputs receive. TimedArray values drive voltage updates in the original synapses slot, with the original refractory gating and jump size.
- `model.silence()` changes outgoing synaptic weights to zero. It does not force the target's own firing to zero and does not delete its incoming connections.
- A monitor just before the synapses scheduling slot records the input neurons' voltage. A second monitor just after records it again. Their difference measures the external Poisson jump, because the recurrent synapses update g rather than v in that slot.
- `input_events.parquet` stores scheduled inputs; `delivered_events.parquet` stores observed voltage jumps. Each has the input neuron's root ID and integer simulation tick. With dt=0.1 ms, tick 20 is the step at 2 ms. A scheduled input can be blocked by refractory gating; this is why the two tables are separate. Paired trials must have identical schedules.
- `spikes.parquet` stores firing times in seconds, the trial name, root ID and context.
- `rates.parquet` contains all 127,400 neurons. At one second duration, a count of 12 spikes is 12 Hz; zero spikes is 0 Hz.
- `manifest.json` states that a trial happened even if the spike table is empty. Completion is written only after the outputs and checksums are present.
- `source_snapshot.zip` preserves the code available when the trial started. `environment.json` preserves versions. A different file/code/config signature cannot silently reuse an old completed trial.

Small lesion example: if A→B has weight +2 and B→C has weight -3, silencing B sets B→C to zero. A→B stays +2. B can still fire when A drives it.

`pilot.run_step()` launches one trial per subprocess. It times out at the shared deadline. An interrupted trial is not treated as completed evidence; completed earlier files remain available.

## IDs and matrices

`common.root_ids()` refuses floating-point IDs. A FlyWire ID is too large to pass safely through the usual floating-point representation. An integer index such as 17 means row 17 of this particular completeness table; it is not a FlyWire ID.

`graph.load_signed_matrix()` verifies the correspondence and builds W[post, pre]. For A→B, the weight belongs in row B, column A. Then multiplying W by an activity vector active only at A produces the input to B. Transposing W would answer a different question.

`graph.features()` calculates incoming/outgoing degree and absolute strength, strong outgoing mass, and actual model sign. It joins annotations without removing missing entries. The two transmitter maps are stored alongside the model sign.

`graph.strong_matrix()` uses each postsynaptic row's absolute input total. If B receives weights -95 from A and +5 from C, both survive a 5% cutoff; the negative edge stays negative. The original full-network matrix is not overwritten.

## Recruitment and spike-count correlations

`recruitment()` builds a complete neuron × declared-trial count table. Suppose A fires twice in trial 1 and not at all in trials 2 and 3. Its average over one-second trials is 2/3 Hz, and its recruitment fraction is 1/3. Dividing by only the observed trial would incorrectly give 2 Hz.

`bin_spikes()` makes neuron × trial × bin counts. At 10 ms, each one-second trial has 100 bins. Times are in seconds in the input table. Each trial retains its own boundary.

`cluster_matrix()` flattens the trial/bin axes for zero-lag Pearson correlation. It drops a row with no variation because its Pearson correlation is undefined. A cell that fires is not automatically variable: a perfectly constant count in every bin is also excluded.

- The raw matrix uses neuron order.
- The same values are reordered using average-linkage clustering of 1-r.
- The cut at 0.7 gives provisional groups. Reordering cannot create new correlations.
- `adjusted_rand()` compares two partitions without requiring their group numbers to match.
- `surrogate_checks()` circularly shifts counts independently within each trial, or permutes trial identity independently for each neuron. It recomputes the clustering rather than assessing only the best-looking observed grouping.
- The saved summary is descriptive. The surrogate comparison does not identify a synapse or establish causal direction.

`select_cells()` uses only baseline information. It excludes inputs, requires repeated recruitment, and requires both transmitter labels to agree with the matrix sign. It divides eligible rates into thirds within each E/I pool, then rotates through cluster/rate groups. The JSON records the seed, IDs, rates, model signs and group assignments before lesions.

## Eigenvectors and their supports

`solve()` finds vectors v satisfying Wv = λv. This is a property of the connectivity operator. It is not the full LIF solution: thresholds, synaptic dynamics, delays and the current drive also matter.

`power75()` ranks |v_i|² and takes the shortest prefix with at least 75% of the sum. Example: squared magnitudes [0.6, 0.2, 0.1, 0.1] select the first two cells because 0.6 is too little and 0.8 reaches the threshold.

For [1, i, 1, i], every squared magnitude is one. Three entries are needed. Taking only the real part would discard two entries and change the question.

`unique_modes()` groups complex-conjugate pairs. Equal magnitude alone is not sufficient: eigenvalues +2 and -2 are different real modes. An incomplete conjugate pair is recorded and excluded from selection.

`stability()` matches two seeded solutions. Near-repeated eigenvalues can have many equally valid bases. It marks them unresolved instead of interpreting the arbitrary basis from one solver run as a unique circuit.

`build()` saves eigenpairs, membership and all eligibility decisions before any mode lesion. It uses the first 20 stable complete modes in spectral order and the recorded recruitment rule. No eligible mode is a valid outcome; it does not automatically trigger a different context.

`cheap_diagnostics.diagnose()` calculates support/hub overlap and recruitment summaries. It applies no scientific stopping threshold to Jaccard values.

## Matching the control sets

`matched_sets()` receives the full feature table and focal support. Every proposed control must have the same number of distinct cells. Full matching also preserves counts in each model-sign/recruitment stratum.

- log1p reduces scale differences between small and very large degrees/strengths while retaining zeros.
- A nearest-neighbor proposal chooses similar cells, with a seeded random choice among up to 64 neighbors.
- The standardized mean difference compares target and control feature means using their pooled spread.
- If both spreads are zero, equal means count as a match and unequal means fail.
- Every continuous feature must meet the 0.1 limit. Too few acceptable sets produces an explicit incomplete result, not looser matching.
- Sets can overlap with each other, but not contain a neuron twice. Their overlap is saved.
- This proposal distribution is part of the model for the comparison. The resulting reference p-value is not a random-assignment test on living flies.

## Readouts

`paired_deltas()` checks seeds, exact scheduled inputs, network settings, dataset hashes and simulation code, then subtracts each baseline rate vector from its matched lesion vector.

For two seeds with changes [-2, 0] Hz at neuron A, the mean change is -1 Hz. The primary response uses |mean change| = 1, not a mean of arbitrarily pooled samples.

`footprint()` computes A and F. If mean changes are [-2, +1, 0] and the support is the first two cells, A=1.5 Hz and F=1. A zero whole-network response has no defined concentration.

`bootstrap_footprint()` resamples seed pairs together. It never resamples neurons as if they were independent experiments. One pair has no interval.

`reference_test()` compares the focal A/F to matched-set A/F. Both must exceed their references to support the conjunction. `paired_signflip()` and `bh()` provide the separate secondary E/I comparisons. Sign flipping assumes a symmetric paired-difference null; the test family is fixed rather than assembled from favorable results.

## Running and collecting CCR work

`ccr.prepare()` freezes conditions, seeds, code/data hashes and a timing estimate. It refuses mode work without the completed twenty-cell study and refuses confirmation without 199 valid full-match controls.

`ccr.worker()` runs one manifest row with a unique lock and output directory. Existing complete files are reused only if their signatures and checksums agree. Remove a stale lock only after verifying no worker still owns the job.

`ccr.collect()` requires all jobs before confirmation. It produces all response footprints, intervals, the full secondary family, or the mode's reference comparison. Sensitivity conditions use separate baselines and retain the original lesion set.

`benchmark.benchmark()` tests NumPy and Cython with a separate set of seeds. The saved criteria concern numerical compatibility, not biological validation. The current local workflow uses NumPy.

## Commands

Use `.venv/Scripts/python.exe` instead of `python` on this Windows checkout. Outputs under `results/` are intentionally not tracked by Git.

```text
python -m eigencircuits.audit --out results/pcdr/corrected_20260919/input_audit.json
python -m eigencircuits.pilot --out results/pcdr/corrected_20260919 --stage baseline
python -m eigencircuits.analysis --pilot results/pcdr/corrected_20260919
python -m eigencircuits.pilot --out results/pcdr/corrected_20260919 --stage lesions
python -m eigencircuits.report --pilot results/pcdr/corrected_20260919
python -m pytest -q
```

Frozen selections are not overwritten. For a changed analysis, supply a new `--out` directory and record the reason. Completed trial reuse also refuses changed simulation source. Use a new study directory when the protocol changes.

CCR preparation (no submission):

```text
python -m eigencircuits.ccr prepare --pilot results/pcdr/corrected_20260919 --out results/pcdr/ccr_singles
python -m eigencircuits.ccr worker --study results/pcdr/ccr_singles --index 0
python -m eigencircuits.ccr collect --study results/pcdr/ccr_singles --features results/pcdr/corrected_20260919/analysis/features.parquet
```

The worker command runs a real job; it is not a dry run. Transfer the required input files and pilot outputs intact. On CCR, check the environment, rerun the tests, and prepare the job manifest there if package versions differ. The existing local draft must not be submitted unchanged into a different environment.

After completing singles:

```text
python -m eigencircuits.build_modes --features results/pcdr/corrected_20260919/analysis/features.parquet --out results/pcdr/modes
python -m eigencircuits.cheap_diagnostics --modes results/pcdr/modes --features results/pcdr/corrected_20260919/analysis/features.parquet
python -m eigencircuits.controls --features results/pcdr/corrected_20260919/analysis/features.parquet --modes results/pcdr/modes --out results/pcdr/controls_pilot --pilot
python -m eigencircuits.controls --features results/pcdr/corrected_20260919/analysis/features.parquet --modes results/pcdr/modes --out results/pcdr/controls_confirm
python -m eigencircuits.ccr prepare --pilot results/pcdr/corrected_20260919 --out results/pcdr/ccr_modes --phase modes --mode-dir results/pcdr/modes --controls-dir results/pcdr/controls_confirm --singles-summary results/pcdr/ccr_singles/summary.json
```

Use `scripts/pcdr_array.sh` after supplying the real account, partition, memory/time limits and final array bound. No scheduler/account values are invented in this checkout.

The prepared local draft is `results/pcdr/ccr_singles_20260919/jobs.json`. It has 720 rows (array indices 0–719), including the two outside-group controls and one silent control. It has not been submitted. The generic paths above describe commands for a newly prepared study; substitute the actual study directory when using the draft.

## Supporting functions and records

| Function | Input → operation → output |
|---|---|
| `common.now`, `environment`, `provenance` | Current runtime and input/source files → read versions and hash bytes → timestamp or provenance dictionary. |
| `common.sha256`, `fingerprint` | File bytes or JSON-compatible values → SHA-256 → digest used to detect a changed record. |
| `common.atomic_json`, `atomic_parquet`, `read_json` | Path and data → temporary-file write followed by replacement, or JSON read → durable record or parsed values. |
| `common.neuron_ids`, `sugar_ids` | Completeness table or configured inputs → exact ID validation → ordered string IDs. |
| `common.load_trials` | Trial directories → require completion and spike checksums → combined spikes plus all declared manifests, including silent trials. |
| `memory.peak_rss` | Current process → operating-system peak-memory query → bytes. |
| `controls.standardized_difference` | Target/control feature arrays → absolute mean difference divided by pooled population SD → one balance value per feature. Equal constant features give zero; unequal constants fail. |
| `controls.generate` | Feature table and selected mode → match sets and save balance/overlap → ready or insufficient-matches manifest. |
| `analysis.coherence` | Correlation matrix and group labels → average upper-triangle values within groups → descriptive mean correlation. |
| `benchmark.equivalence` | Two sets of run measurements and an acceptance margin → Welch uncertainty interval → numerical agreement decision. |
| `audit.audit` | Exact local datasets → ID, weight, annotation and hash checks → input-audit JSON. |
| `report.report` | Completed pilot and frozen analysis → verify pairing, calculate readouts and draw figures → Markdown report, JSON summary and figures. |
| `freeze_record.freeze` | Final pilot directory → archive implementation/notes and hash all artifacts → research record and ZIP. Trial archives still identify the earlier code used by each trial. |

Each module's `main()` only parses its command-line arguments and calls the corresponding function. It does not define a separate scientific analysis.

## Local unattended controllers added 20 September

These scripts are outside `eigencircuits` so adding orchestration does not silently change the frozen scientific implementation.

- `pcdr_local_queue.stamp()` returns the current UTC time; `write()` atomically updates controller JSON.
- `available_memory()` reads native available physical RAM. It supplies an operational wait condition, not an analysis variable.
- `execute()` launches a child command, sends output to its log and propagates failure. On timeout it terminates the Windows child tree, including the virtual-environment launcher.
- `pcdr_local_queue.main()` reads the frozen manifest, acquires a controller lock, checks resources/deadline, runs each missing trial and calls the existing collector. The complete declared sample is unchanged by execution order.
- `pcdr_local_followthrough.create_pilot()` reads a selected support and five strict full-match controls, makes seven conditions (baseline, focal, five controls), and crosses them with five fresh seeds. Output: a 35-job manifest explicitly labeled `local_mode_pilot`.
- `summarize_mode()` reads completed A/F estimates, calls the existing conditional reference comparison, and writes an exploratory comparison record.
- The follow-through `main()` waits for singles, then executes report, mode selection, matching and pilot stages in order. Its nested `phase()` records each command, waits for sufficient memory and enforces timeouts. A failed eligibility/matching check does not trigger a relaxed substitute.
- `pcdr_local_findings.report()` requires a completed study and writes every condition plus the complete secondary-test table. It also hashes its source results and generated report. This gives a readable findings file without requiring a model call.
- Further rationale and failure behavior: [PROCESS_DETAILS.md](PROCESS_DETAILS.md). Current paths: `results/pcdr/ccr_singles_20260919` and `results/pcdr/local_followthrough_20260920`.

Matching audit functions and worked variance example: see MATCHING_AUDIT_20260921.md, Code guide commands and creation record. The original controls module was not modified; an instrumented copy logs rejected proposals without consuming random numbers.

Optimized pilot controller: scripts/pcdr_optimized_pilot.py prepare() validates the frozen audit sets and builds 35 explicit jobs; run() delegates to the existing serial queue and writes all-set findings after complete collection. The optimized_matching_pilot phase skips reference p-values. No model code was changed. See amendment.json and jobs.json for every input, ID and seed.

Completed pilot verification: scripts/pcdr_verify_optimized.py checks 35 frozen manifests and file hashes, reconstructs paired rates, independently recomputes all six aggregate summaries and full footprints, then writes per-seed diagnostics and a dated report. Single-seed A/F are explicitly distinguished from aggregate A/F. Exact command and script hash are in completion_audit.json.

## OnDemand notebook and preliminary closeout (22 September evening)

- `scripts/pcdr_distribution_feasibility.py`: builds a continuous feasibility problem from the existing baseline features. Exact strata and mean bounds stay fixed; target-centered second moments limit variance inflation. Fractional weights are diagnostic, never neurons to lesion. The solver reported infeasible for this new stricter program.
- `scripts/pcdr_ccr_transfer.py`: copies the required source/data files, records exact hashes and library versions, and builds the ZIP. On the destination it checks the payload, makes a labeled technical Git snapshot, freezes four smoke jobs, runs them with exclusive locks and validates their outputs. Notebook/config files are editable; their original hashes are recorded separately from immutable payload hashes.
- `scripts/pcdr_ccr_sensitivity.py`: prepares 350 fixed descriptive jobs after smoke validation. Runs two independent single-threaded processes within the existing allocation, logs progress, respects a deadline and STOP file, and rejects incomplete or corrupted analysis. It uses the existing output-only lesion simulator and paired readouts. It does not call a random-reference test.
- `scripts/pcdr_build_ccr_notebook.py`: creates the notebook and fixed follow-up design from previous memberships. Refuses to silently replace an existing different scientific design. The notebook uses a separate simulation environment and keeps large trial files on CCR.
- `scripts/pcdr_ccr_local_validate.py`: extracts the ZIP and exercises real entry points, including missing-job, lock, resume and disposable corruption checks.
- `scripts/pcdr_verify_ccr_release.py`: checks the final ZIP against the tested predecessor. This avoids repeating simulation for a prose-only correction while recording exactly what was and was not rerun.
- `tests/test_pcdr_ccr_transfer.py`: checks rejection behavior, resume preservation, the 350-job pairing, notebook code syntax, optional dependency recording and a known-answer sensitivity collection fixture.

These scripts and the notebook were created with Codex assistance. They prepare research computations and records; they do not establish a biological mechanism. See CCR_NOTEBOOK_GUIDE.md for operation and PRELIMINARY_CLOSEOUT_20260922.md for results and limits.

## Expanded CCR package

`pcdr_build_ccr_expanded.py` records a separate amendment and creates the larger notebook. It preserves the original design. `pcdr_ccr_sensitivity.py` now takes variants and seeds from the frozen design, restricts the extra individual-cell conditions to the default network, and requires a capacity certificate above two workers. `pcdr_ccr_capacity.py` benchmarks real pending jobs under allocated CPU/memory limits and chooses concurrency using throughput only. Completed calibration jobs are preserved. The capacity certificate is rejected after the study or Slurm allocation changes. Tests in test_pcdr_ccr_expanded.py verify the job grid, complete single-cell coverage and allocation safeguards with fixtures; actual CCR scaling remains untested.


## CCR summary analysis, 27 September

scripts/pcdr_analyze_ccr_summary.py reads the returned ZIP without unpacking arbitrary paths. It checks hashes linking the result files to the collection record and study, compares the job list with the frozen design, verifies expected condition/seed coverage and checks arithmetic identities in A and F. It distinguishes the footprint of the mean rate-change vector from the mean of per-seed footprints. Those operations are not interchangeable. Original scientific records and small derived tables are saved with one figure. It cannot reconstruct raw-neuron bootstrap contrasts from aggregate summaries and does not pretend to do so.

scripts/pcdr_collect_existing.py is a separate collection-only entry point for the observed CCR CPU change. It leaves deployed source and trial metadata untouched, checks that other environment fields match, and records simulation and analysis environments separately. Its temporary in-process loader binding applies only to the existing collector and is restored even after an error; simulation workers keep the strict original loader.


The 27 September continuation adds secondary_analysis to the same summary script. It aligns conditions by seed before subtracting signed MN9 responses. mean_interval resamples whole paired rows with fixed multinomial weights, so a shared input seed stays paired across every term of a contrast. The 51-single-cell sum includes MN9 once and the other 50 individually. The function also records per-seed ordering counts and each largest seed's share of summed absolute seed responses. These diagnose variability without replacing the primary footprint of the averaged neuron-level response. They are retrospective analyses and cannot reconstruct a spatial interaction pattern from scalar data.
# Saved-trial diagnostic added 27 September

`scripts/pcdr_resolution.py` adds a separate runner for further time-step work. It imports the unchanged simulator helper from the completed package and inserts the original 0.1 ms tape at integer-spaced fine ticks, with zeros between them. Its worker retains the earlier validation and output format and now records peak RSS. The controller checks Slurm time remaining, reserves 30 minutes for collection, limits concurrent processes to 16 within CPU/memory allowances, and returns the full trial files in one ZIP. The collector reports own-lesion support and fixed-51 support separately and pairs baselines by stage, time step, variant and seed. Existing folders cannot be overwritten. See CCR_RESOLUTION.md and its recorded JSON plan; no convergence threshold is silently applied.

`scripts/pcdr_check_followup.py` independently reads the downloaded follow-up events. It verifies the package plan, recorded sources, all worker files and original trial references; reconstructs counts and 10 ms population bins; and checks replay equality and delivered input membership at each physical time grid. It recalculates the published follow-up tables before adding shared-seed intervals for active29 versus full51. These new intervals use the original 51-cell support for both conditions. The six-panel figure retains every preselected lesion/seed combination, so the remaining inconsistent MN9-only response is visible alongside the cases that become smaller. No new simulation is performed by this checker.

Follow-up package: `scripts/pcdr_followup_sim.py` keeps the original simulation equations and scheduling while accepting a supplied input tape. Original tick positions are mapped by integer factors of two or four at the finer steps; intervening ticks have no input event. `scripts/pcdr_followup.py` checks the old evidence and environment, runs isolated worker subprocesses in ordered stages, and packages rates, population counts, metadata and logs. New output folders are exclusive so another launch cannot overwrite an earlier run. Full spikes stay in the worker folders. The separate notebook uses file-backed process output so a browser disconnect does not break the controller's output pipe. See CCR_FOLLOWUP.md for stage definitions, resource settings, results from local checks and the lack of automatic partial-run resume.

The full downloaded CCR study has now been checked locally. `--snapshot-archive` verifies the original upload ZIP and the local input readers; `--workers` accepts up to eight processes and queues at most twice that many trial reads at a time. Results remain in plan order so each lesion is paired with the correct baseline. A worker error stops the run and records a failed status. No worker writes to the trial directory. The spike-equality column compares the ordered time/neuron entries, not complete Parquet bytes or trial-label columns.

`scripts/pcdr_analyze_raw.py` verifies the completed diagnostic outputs and reconstructs the original condition and seed results. It repeats the original 2,000-resample intervals, then uses shared seed weights to calculate paired A/F differences. Sparse response matrices retain the full neuron universe while avoiding a dense 3,120-by-127,400 allocation. Bootstrap calculations use batches of 100. Added mean-vector comparisons use one fixed support; zero norms remain undefined. The output includes all comparisons, all paired activity rows, and a population-trace figure with every seed at default and the unusual parameter setting. These new contrasts are retrospective and remain conditional on the existing comparison sets.

`scripts/pcdr_raw_diagnostics.py` reads completed trials without invoking the simulator. It validates the saved output hashes, reconstructs counts from spikes, checks actual scheduled and delivered input events, and tests time-grid and refractory consistency. It keeps one paired baseline in memory while writing sparse rate changes, avoiding a dense trials-by-neurons table. `neurons.csv` defines the full index, so sparse omissions mean zero rather than missing data. Its fixed-mode per-seed readout is supplementary and does not replace the original mean-vector endpoint.

`notebooks/CCR_Raw_Diagnostics.ipynb` reuses the repaired CCR Python environment, waits for the diagnostic subprocess, and packages outputs only after a complete audit and checksum verification. The original study remains unchanged. Partial diagnostic folders are preserved and cannot be overwritten. Tests exercise known counts, empty trials and sparse exports, sensory refractory exceptions, timing errors, corrupt tables, large neuron IDs, output conflicts and study locks. The complete downloaded study has now passed these checks locally; see the dated results record.

## Checking the 530-trial download

`scripts/pcdr_check_resolution.py` rebuilds rate vectors from full spike records. It checks the plan, source and output hashes, scheduled-input mapping, delivered-event membership, spike spacing and exact replays before recomputing paired and mean results. Each lesion's own membership and the common 51-cell membership are kept separate because the support size changes A. It records the difference between default mean response vectors at 0.05 and 0.025 ms. Downloaded files remain unchanged. The existing footprint function is reused: this checks reconstruction and use of that definition, not an independent validation of its scientific suitability.

## Saved event and comparison review

`scripts/pcdr_event_review.py` reads completed event and baseline-rate files, verifies their recorded hashes and writes timing and comparison tables. It compares neuron/time pairs on a common clock grid, so row order is irrelevant and large integer neuron IDs remain strings. Ten-millisecond counts describe response development; a declared cumulative-excess crossing is only a descriptive time marker. The comparison section reads baseline rates and fixed memberships, never lesion rates. It retains anatomical features, updates any-spike recruitment, and counts available cells in each sign/recruitment/motor stratum. Stratum capacity can rule out diversity but does not establish joint matching feasibility. The output directory must be new; incomplete local outputs are not silently reused.

## Recorded replay

`scripts/pcdr_observed_sim.py` adds two read-only state monitors to a separate copy of the saved simulator. Explicit scheduling slots distinguish the voltage used for spike detection from the state after synaptic events. It returns v and g in mV and refractory eligibility; g is not an amperage. `scripts/pcdr_observed_replay.py` runs four fixed serial trials only when enough memory is free, compares full events with the downloaded references, saves traces and stops on a mismatch. The frozen plan and detailed process record are OBSERVED_REPLAY_PLAN.json and OBSERVED_REPLAY.md. Small-network tests passed; whole-brain recording remains unrun because the local memory check refused startup.

## Checking recorded replay outputs

`scripts/pcdr_check_observed.py` reads the four completed runs, rechecks event equality and file hashes, and verifies that state arrays use the planned indices, slots and physical sampling times. It checks recorded spike decisions against voltage above -45 mV and refractory eligibility for all selected neurons. It also reports the first exact stored voltage and drive differences within each baseline/lesion pair. This is a descriptive comparison of selected traces, not identification of the cause of the population increase. All four full-network checks passed on 28 September; see the dated verification record.

## Comparing state traces

`scripts/pcdr_trace_analysis.py` verifies the recorded files, aligns finer samples to the coarser physical clock without interpolation, and summarizes every monitored cell in five declared windows. It separates voltage/drive differences from refractory disagreement and saves population counts alongside selected-cell coverage. Positive and negative net g jumps are descriptive slot differences, not separately resolved excitatory/inhibitory currents. The window-coverage check compares the sum of all windows with the original selected-cell spike count. It preserves original traces and writes one new derived evidence directory and figure.

## Recruitment timing

`scripts/pcdr_recruitment_timing.py` verifies the four spike files and builds counts and first times using string neuron IDs. It excludes stimulated inputs, retains the union of active cells and defines the large-only group using all three comparison runs. It saves all early members rather than choosing a causal candidate. The existing signed-graph loader checks index/ID correspondence; zeroed lesion columns remove silenced outgoing edges before descriptive directed counts. Those counts measure anatomical connectivity, not realized input. The protocol explicitly records the outcome-informed 180 ms split and missing annotation handling.

## Reconstructing incoming events

`scripts/pcdr_input_reconstruction.py` multiplies selected postsynaptic weight rows by a sparse spike raster, shifts arrivals by the exact synaptic delay, and masks writes using eligibility reconstructed from postsynaptic spikes. The after-threshold mask matters because newly spiking cells already reject writes to g. It compares the result with after_synapses g minus before_thresholds g, retains unmasked errors as a diagnostic and fails if any recorded flag or declared-tolerance comparison disagrees. This test validates ten non-input cells; it does not reconstruct full voltage or infer causality.

## Inputs to early recruited cells

`scripts/pcdr_early_drive.py` processes the fixed 577-cell cohort in batches of eight. It separates weight signs before reconstructing delayed arrivals and saves raw versus refractory-accepted sums in fixed windows and matched physical pre-first-spike windows. It reuses the validated increment and mask helpers. Dense arrays are limited to a small postsynaptic batch; the full presynaptic raster stays sparse. Group sums across cell-specific windows are descriptive, not a common-time network total or a voltage estimate.

## Presynaptic source partitions

`scripts/pcdr_source_inputs.py` assigns each source neuron to one fixed recruitment group, then counts spikes arriving within each target's pre-first-spike window using binary searches in sorted source spike ticks. Summing per-edge signed weights provides an independent check of the earlier sparse-matrix calculation. Half-open windows include arrivals at the start and exclude arrivals at the first spike. Every target's sums must agree before a completion record is written. Counts represent edge-events: one presynaptic spike can contribute to several targets and must not be described as several independent source spikes.

## Reviewing structural candidates

`scripts/pcdr_candidate_review.py` reads the saved eigenvectors and exact neuron IDs, reorders baseline features by ID, and reconstructs supports from squared complex magnitudes. It checks original membership, recruitment and selection before examining alternative support and spike thresholds for all forty screened modes. Pairwise overlaps use sets of exact IDs. Sparse matrix-vector multiplication checks the four eligible eigenpairs without solving new ones. The script refuses an occupied result location, verifies original feature/model-input hashes and writes a completion record only after all checks pass. It does not choose new lesion targets or infer lesion effects from structural measurements. Tests cover complex power, exact cutoff boundaries, deterministic ties, invalid vectors, reordered or duplicate IDs, floating-point IDs and inconsistent recruitment data.

## Fine-step input recording

`scripts/pcdr_fine_sim.py` maps saved external times to exact fine-grid ticks and records input voltage in consecutive bounded windows. It preserves the before/after synaptic-slot delivery measurement while releasing each window's state monitors. The network and delayed-event queues continue between windows. `pcdr_fine_benchmark.py` checks old/new full-network event agreement on a short prefix; `pcdr_fine_ramp.py` measures runtime and peak resident memory at four fine steps. Neither benchmark reports one-second lesion results. They write protocols before workers run, retain failed-worker logs and refuse occupied output directories.

## Full-duration fine-step package

scripts/pcdr_fine_ccr.py coordinates the fixed study, reuses the established resolution worker's input/output checks with the windowed simulator, measures concurrent throughput, preserves attempts and collects numerical agreement. scripts/pcdr_build_fine_ccr.py validates and packages the required prior evidence and data; scripts/pcdr_fine_run_all.sh loads the separate simulation environment and runs tests before execution. The notebook delegates to this shell so its Python kernel need not match the simulation interpreter. CCR_FINE_RUN.md describes resources, criteria, restart behavior and the differences between a result archive existing and a study actually completing. The tests exercise failures and known-answer summaries as well as successful simulation comparisons.

## Checking the downloaded fine-step results

`scripts/pcdr_fine_differences.py` performs the later descriptive analysis. It checks consumed files against manifests inside the verified result ZIP, constructs sparse bin-by-neuron spike counts, compares same-seed response changes with every distinct-seed distance, and identifies contributors before taking population averages. Sparse tables avoid a dense 127400-neuron allocation for every millisecond of every trial. It also separates new recruitment from repeated spikes in the burst case. Phase windows were chosen after viewing the activity plot and are recorded as such. Tests distinguish equal population totals from equal cell counts and check event boundaries, empty inputs, invalid spike records and seed-pair counting. Outputs include figures, complete cellwise tables locally, a protocol and a completion record with hashes. The compact documentation includes summaries rather than copying all full tables.

`scripts/pcdr_check_fine.py` verifies the fixed plan, retained runtime sources, local model/data and original study, then reads every trial's raw spikes, rates and delivered inputs. It checks IDs, time bounds, time-grid alignment, refractory spacing, event membership, hashes and successful process records. Original source validation is cached by trial so the same evidence is not repeatedly hashed across four steps. It reconstructs sparse rates over the full neuron universe and recomputes paired responses and adjacent-step agreement. The checker shares the footprint and event-validation helpers with existing analysis, but does not call the CCR agreement collector. It preserves a new output folder and records both simulation and analysis environments; it does not rerun simulation or change tolerances. The root downloaded ZIP is required for its archive hash. Tests check that equal A/F values cannot conceal an inverted response, undefined fractions fail, the finer response sets the denominator, and changed or missing results are rejected.

## Recording the burst diagnostic

`pcdr_state_recorder.py` adds read-only monitors at explicit phases and writes each bounded chunk separately. `pcdr_fine_sim.py` accepts this optional recorder; with no recorder its model construction, update and output logic remain unchanged. `pcdr_burst_diagnostic.py` validates the model/data and saved input references, starts from time zero, records a selected interval and compares all resulting spikes and delivered events with the archived prefix. It rejects missing state chunks even if a manifest claims completion. Two separately bounded subprocesses run concurrently; an exclusive controller lock prevents conflicting launches, and failed output is preserved. A result archive is created only after both verified successes. Hard termination can require manual stale-lock review; it is not silently handled by deleting another process's lock.

`pcdr_recurrent_delivery.py` reconstructs weighted arrivals using presynaptic spike ticks plus delay, and applies the observed postsynaptic refractory windows. It sums accepted and blocked excitatory/inhibitory magnitudes separately. The refractory test uses an indexed search in sorted postsynaptic spikes rather than comparing every arrival with every spike. It validates predictions against measured pre-/post-synaptic drive increments in the 20 ms prefixes. The results are conditional on the recorded spike histories; they are not counterfactual effects of changing refractory rules.

`pcdr_build_burst_diagnostic.py` packages the model, data, two replay references, fixed recording plan, tests and Run All notebook. It uses the prepared `results/pcdr/diagnostic_inputs_20261005` directory; the compact evidence copy records its plan and reference hashes, but does not duplicate the datasets. Notebook outputs may change on save; executable run files remain hashed. The notebook runs a detached shell in the allocated job, so a browser disconnection alone does not end computation. Allocation expiry still does. Results and installation logs remain on disk for retrieval through OnDemand Files.

`pcdr_burst_sources.py` groups the reconstructed arrivals by presynaptic source in the two selected pre-burst windows. It checks accepted and attempted totals against the prior reconstruction, ranks sources within the selected targets, and records the leading sources' spike histories across all four steps. It does not infer causal necessity from that ranking. Both source attribution and recurrent-delivery reconstruction now read the immutable initial plan in the evidence directory so adding recording cells for a future diagnostic cannot change the historical analysis population.

## Checking the returned burst recording

`scripts/pcdr_check_diagnostic.py` reads the results ZIP directly, one recorded array file at a time. It does not extract a second copy of the large dataset. It compares the plan and archived simulation sources with the original upload, checks every output hash and recorded time/ID array, and compares spikes and stimulation with the saved reference trajectories. For each recorded cell, threshold crossings outside refractoriness must occur at the saved spike ticks. The ten-millisecond summaries describe voltage, model drive and time spent refractory. Initial sample values and window maxima answer different questions and are kept separate. The output directory must be new so a completed check cannot be silently overwritten. Its three rejection tests use generated temporary archives.

## Incoming events and the first recorded crossing

`pcdr_diagnostic_events.py` reconstructs delayed arrivals from saved spikes and connectivity, applies the existing tested refractory rule, and compares summed increments with the recorded phase difference. It also checks each exact linear state update and spike reset. Only the 13 non-input recorded cells enter the recurrent-only comparison; the 21 externally driven targets require an additional Poisson term. Files are read one chunk at a time. The first tick cannot be propagated from an unsaved previous state. Selected event times preserve ordering that a 50-ms aggregate would lose.

`pcdr_first_spike.py` uses the first recorded voltage/drive and every accepted arrival to reconstruct the first spike of 720575940628455942. This calculation is valid because that cell has no earlier spike or reset in the interval. The analytic response kernel is independently checked by numerical integration. It decomposes the existing trajectory; it does not simulate a network lesion or explain upstream differences before the recording window. Both scripts preserve the original archive and require a new output directory.

## Voltage before a cell has ever fired

For cells with previous spikes, `pcdr_source_resets.py` instead starts each comparison from the most recent reset, rejects refractory arrivals and sums accepted inputs before threshold testing. It checks both runs at the union of their selected-window spike times. Resetting drive to zero makes this decomposition valid despite the initial refractory interval. Every predicted voltage is compared with the saved pre-threshold state. It reads individual compressed state chunks without extracting another dataset. Outputs include inhibitory terms and accepted arrival times; they describe observed inputs rather than a simulated intervention.

`pcdr_upstream_inputs.py` sums the linear voltage response of each saved incoming spike from the known initial state. This calculation applies only before a cell's first spike and excludes directly stimulated targets; prior resets would invalidate this version. It evaluates three retrospectively selected upstream targets at their coarser first-spike times and at the same physical times in the finer replay. It checks the same reconstruction against two recorded cells in each replay. Source contributions are conditional on the saved network spike trains, so removing a term would not be a whole-network lesion simulation. All IDs remain strings, arrivals use integer ticks and only events before the threshold phase contribute. Output includes complete signed source contributions and paired differences, preventing a positive-source ranking from concealing inhibition. The raw archive is unchanged.

## Removing specific connections

`pcdr_edge_intervention.py` validates directed index pairs and sets only their weights to zero in a copy. Missing, repeated, already-zero or invalid edges stop the operation. A temporary Parquet file lets the existing simulator use the modified connectivity without changing its source or the original dataset. Cleanup also runs if simulation fails. This is a connection intervention, not whole-cell silencing. Local tests verify selective loss of transmission and unchanged external input. The four complete-network trials have now finished; see PATHWAY_RESULTS_20261007.md.

`pcdr_pathway_trial.py` uses that helper for the selected whole-network comparison. It checks reference hashes and packages before allocating a new trial directory, records sources and status, and saves returned events before checking equality. It permits only the declared two steps, two conditions and either a 2-ms setup check or 750-ms trial. Short checks produce no scientific endpoints. Full-trial counts use integer ticks so floating-point representation cannot move an event across a window boundary. A prior spike excludes a cell from newly recruited counts. The modified connectivity table is released from memory before simulation; only its temporary file remains until the worker exits the context.

`pcdr_agreement_breakdown.py` separates the already declared agreement requirements using the checked tables. It verifies their hashes, joins each row to its finer-step amplitude, rejects duplicate or missing matches, and requires the recombined decisions to equal the saved decisions. Undefined concentration fails its requirement. This describes which requirements failed; it neither relaxes them nor runs a new simulation.

`pcdr_pathway_run.py` launches the four fixed trials with individual deadlines. One controller lock protects an output folder. Existing trials must pass source, specification and output-hash checks before reuse; incomplete trials stop the run for review. A worker failure is retained while the other already scheduled trials finish. Collection requires all four verified trials and a valid result ZIP. `pcdr_build_pathway.py` packages the required sources, data, reference events, pinned packages and a notebook, checks ZIP CRCs and file hashes, and compiles notebook code cells. The shell uses a second lock around setup and simulation. Neither lock is removed on behalf of another active process. A killed job may require stale-lock review; there is no partial network-state restart.

The notebook starts a separate shell process and polls atomic progress files. It cannot extend an allocation or keep a process alive after the scheduler ends the job. Use the status cell after reconnecting. Setup errors remain in `run_all.log`; worker errors remain in their individual logs. Full-trial results are not inferred from successful setup or short-prefix checks.


`pcdr_review_pathway.py` reads the returned ZIP without extracting or executing its source. It compares the source inventory and bytes with the upload, checks plan/data/reference/output hashes, independently compares actual event tables, and recalculates endpoints through per-cell first-spike times. It checks IDs, grid times, duplicates and refractory spacing, with the original zero-refractory exception for stimulated cells. It also locates the first changed spike and measures per-cell count differences. Corrupted output bytes and omitted sources stop review. Analysis output requires a new path so a saved review is not silently replaced. Its tests include window boundaries, prior recruitment, invalid and empty spike tables.


`pcdr_late_switch.py` uses the existing recorder hook immediately before a simulation chunk starts. It locates the two unique synapses, records their actual scaled weights, and either reassigns them unchanged or zeros them at the selected boundary. It does not reset neuron state or empty delay queues. Tests show that queued events use delivery-time weights, whereas already delivered drive remains and refractory clamping still applies. The simulator itself is unchanged. The pathway worker requires an exact earlier spike prefix for both late conditions and an exact entire reference for the no-change condition. The controller validates the switch record before accepting a completed trial. Full trials switch at 600 ms; two-ms setup checks use 1 ms and cannot establish the late biological result.

The pathway reviewer now also accepts `--late`, using the late package folder and conditions. It independently compares all pre-600-ms events and both complete no-change references, then checks switch timing, exact target indices/root IDs and original scaled weights against connectivity. Merely updating a corrupted switch record hash cannot pass the specification check. The earlier time-zero review remains supported using its retained original upload.

The `--separate` mode reviews all eight separate-connection trials using the original separate upload. G and H each require their own exact target and scaled weight; the reference and joint conditions require both. Summary conditions must occur exactly once at each step, and the result ZIP must contain exactly the expected source, trial, log and environment files. Selected-cell histories must include the source and both targets. Six descriptive comparisons report each intervention against its same-step reference. This mode does not itself compare the repeated joint trajectories against the earlier late-pair archive; that remains a separate cross-experiment check before interpretation. Synthetic archive tests check specification failures even after updating affected hashes and summary records. They establish reviewer behavior, not scientific outcomes.

`pcdr_compare_separate.py` performs that cross-experiment check after verifying both archive hashes against successful independent reviews. It requires exact full spike/input tables and endpoints for the four repeated conditions, calculates supplementary final-20-ms first-spike counts and post-switch source/target histories, and compares the two single-removal event tables. Equal counts do not substitute for exact event equality. It refuses output replacement. Tests reject altered archive bytes, altered repeated endpoints and altered repeated spikes. The supplementary descriptions do not change the original window or convergence criteria.

The separate-connection extension uses the same late-switch class with one selected pair for `late_g` or `late_h`. Reference and joint conditions still select both pairs. `--separate` schedules all four conditions at both steps and permits eight concurrent workers. Completion checks now include the specific expected pair indices and scaled starting weights, not just whether weights became zero. G and H retain the root-ID mapping in the trial source; tests and full-network setup outputs verify that mapping. Existing simulation equations and timing are unchanged.


## Fine-step contrasts and comparison diversity, 8 October

`pcdr_fine_contrasts.py` verifies hashes of the previously checked pair/mean/agreement tables and original downloaded plan, requires complete seed/step/condition coverage, and contrasts each fixed comparison with the selected mode. It keeps mean-vector readouts separate from per-seed readouts, reports all own- and common-support contrasts, and calculates observed-step envelopes and adjacent-step sign changes. It retains the original failed agreement decision. Outputs describe only the saved steps and fixed comparisons.

`pcdr_comparison_capacity.py` uses the original hashed baseline design to calculate the minimum overlap forced by exact strata alone. It does not optimize or accept candidates. Its formulas are tested by exhaustive small-subset enumeration. Six-feature balance can require more overlap than this count-only lower bound.

`pcdr_diverse_comparisons.py` freezes one baseline-only objective before starting an externally bounded worker: minimize overlap with the union of the three existing comparisons, under the original conservative LP mean constraints and exact counts. It enumerates all completions of at most twelve fractional cells and retains every candidate passing the original pooled-SMD rule. Fractional memberships are never accepted lesions. A failed or timed-out worker retains its evidence and does not retry automatically. The source and input hashes are frozen; changing the script requires a new protocol/output directory.

`pcdr_verify_diverse.py` independently recomputes candidate counts, IDs, exclusions, population-variance SMD, old-union overlap, feature variance ratios and empirical-CDF gaps from original inputs. It rejects missing accepted assignments, changed source/output hashes and duplicate memberships. Neither this verification nor successful mean matching turns an optimized family into a random reference ensemble.


## Binary distribution matching, 8 October

`pcdr_distribution_match.py` constructs a fixed baseline-only candidate pool from existing verified memberships plus twenty same-stratum nearest neighbors per target. It records exact pool IDs, all source/input hashes, objective, two overlap cases and worker deadlines before optimization. Binary variables select cells; one continuous variable bounds every empirical-CDF difference over all combined candidate/target breakpoints. Exact strata and the existing sufficient mean bounds remain constraints. A second solve caps overlap with each prior set at thirty cells. Each owned worker has an external deadline; solution vectors and process logs remain evidence. Time-limited incumbents require explicit binary/count/mean/SMD/overlap/CDF validation and are never described as proven optima.

`pcdr_verify_distribution_match.py` independently rebuilds the candidate pool and audits exact IDs, exclusions, counts, original SMD, sufficient mean constraints, overlaps and direct threshold-count CDF differences. It checks process outcomes and solver objective bounds. It separately computes stratum-only lower bounds on achievable CDF gaps in restricted and full eligible pools using sorted threshold counts. These lower bounds ignore joint feature, mean and overlap constraints, so they do not demonstrate achievability. Exhaustive small-subset tests and a direct forced-stratum example check the mathematical bounds.


`pcdr_expand_distribution_pool.py` verifies the original completed study and rebuilds its twenty-neighbor pool before constructing a nested fifty-neighbor pool. It preserves the fifteen reference memberships and invokes the hash-frozen original optimizer under the same worker budgets. The separate protocol records the pool amendment before execution; occupied output directories are refused. The independent verifier supports the declared twenty- and fifty-neighbor designs and reconstructs either without importing the expansion helper. Full vectors remain local evidence; compact snapshots preserve protocols, memberships, solver/process records and independent checks.

`pcdr_family_capacity.py` audits all nineteen saved comparison memberships and records the full threshold grid before enumeration. A subset dynamic program stores each subset's largest CDF count gap and pairwise overlap, then derives maximum capacity at every threshold pair. A separate complete-subgraph search checks all 2,704 maxima. The routine refuses collections above twenty candidates because exhaustive subset cost doubles per added candidate. It retains frontier witnesses and exact environments; the audit is limited to saved sets, not all eligible-cell subsets.

`pcdr_joint_family.py` selects two sets simultaneously using binary memberships, continuous exact intersection variables and a common worst-CDF objective. It retains each set's original sufficient mean and stratum constraints and adds pairwise overlap alongside old-reference caps. Sparse row assembly avoids a large dense joint matrix. One owned worker has internal/external deadlines and preserves solver status even when no candidate is found. `pcdr_verify_joint_family.py` distinguishes a no-incumbent time limit from infeasibility; any saved pair is rechecked using exact IDs, direct CDF counts and pairwise intersections. The separate checker and formulation have known-answer and failure tests. No prior frozen solver is edited.


`pcdr_anchor_family.py` records both eligible existing anchors before serial partner searches. It adds each anchor as a capped reference and invokes the unchanged original single-set worker. The independent member audit validates the anchor and any companion; status interpretation preserves infeasibility versus timeout. Conditional results do not establish a global joint optimum.

`pcdr_anchor_bound.py` removes CDF rows and minimizes overlap with a fixed anchor over fractional memberships, retaining the fifteen older-reference caps, exact strata and sufficient mean bounds. A box-minimized Lagrangian gives a valid lower bound without demanding zero numerical stationarity residual. It reports an explicit floating guard. `pcdr_verify_anchor_bound.py` independently reconstructs the intended rows and evaluates the saved-coefficient bound with rational arithmetic. Saved NPZ matrices/vectors are scientific evidence, not accepted binary memberships. Both diagnostic protocols refuse occupied output directories and preserve worker records.

`pcdr_reference_ablation.py` freezes the complete two-group reference-cap factorial for both anchors and an explicit mutual-only partner amendment before execution. It runs eight fractional bounds and two bounded integer searches through unchanged earlier solvers. `pcdr_verify_reference_ablation.py` independently rebuilds feature/count/reference rows, evaluates saved-coefficient duals with rational arithmetic, checks constraint monotonicity and audits each binary pair. It separates unresolved partner-objective optimality from a pair that reaches its fixed anchor's lower floor. The post-result degree-tail diagnostic is descriptive and does not change membership selection.

`pcdr_pathway_divergence.py` verifies the reviewed archive hash, compares exact neuron/tick events by keyed merge and independent set algebra, and preserves complete changed-event and first-change tables. Fixed descriptive windows and common-neuron summaries do not assign causal routes. Shifted spikes count as unmatched events in both directions. A separate post-result window-count diagnostic distinguishes temporal rearrangement from changed total counts.

`pcdr_pathway_routes.py` checks archived delay/update source, model/data hashes and earlier divergence outputs before mapping G/H edges to earliest outside changes. It calculates scheduled arrivals in integer ticks and reports signed predicted g increments, not voltage jumps. Independent checking joins original IDs and examines all changed incoming presynaptic emissions. No membrane-state or full-route reconstruction is claimed.

`pcdr_step_cancellation.py` processes one default seed at a time across all four steps and five conditions, checks archived rate hashes, and decomposes the paired cross-step L1 into baseline-plus-lesion L1 minus same-sign cancellation. Zero total difference has undefined cancellation fraction. Shared baselines are not counted as independent replicates. Original agreement criteria are untouched.
# Baseline count partition, 9 October 2026

`pcdr_baseline_counts.py` reads all sixty default-baseline trials at the two finest saved steps, verifies archived hashes/specifications, reconstructs counts from spikes and checks saved rates. It partitions full-second count L1 by activity at one or both steps and saves every changed-cell count. `test_pcdr_baseline_counts.py` checks the mathematical partition and invalid inputs, including integer overflow hazards. See BASELINE_COUNTS_20261009.md for scope and interpretation.

## Baseline prefix and endpoint analysis, 9 October 2026

`pcdr_baseline_time.py` authenticates sixty spike files through the prior baseline-count snapshot, counts half-open prefixes using common integer ticks, and saves prefix/interval/suffix L1 plus a conservative bound under arbitrary suffix-spike deletion. Fixed endpoints and limits are recorded before results. Tests include boundary failures and exhaustive small-count bound checking. See BASELINE_TIME_20261009.md.

## Baseline event and count replay, 9 October 2026

`pcdr_baseline_events.py` selects the earliest non-input ordinal spike gap exceeding one coarse tick per seed and reuses `pcdr_local_replay.replay` on saved incoming histories. `pcdr_baseline_count_replay.py` preserves a separately recorded amendment selecting the first fixed 100-ms checkpoint with at least a two-spike gap, largest gap then root-ID tie break. Both verify native prefixes before comparing incoming histories at a fixed fine step, retain no-selection cases/failures, and bound the worker to 180 seconds. Separate dated scripts retain the executed selection/source provenance; do not run them as a new network experiment. BASELINE_REPLAY_20261009.md details interpretation and verification.

## Incoming-history pairing sensitivity, 9 October 2026

`pcdr_history_parts.py` retains the prior 26 selected target/checkpoint cases and four absent seeds. It pairs arrivals within source IDs from the beginning and end, replays the two-by-two paired-time/surplus combinations at fixed fine dt, and requires reconstructed original histories to match prior verified target ticks. Seven selection/partition tests passed. Separate verification checks all input constructions and flags source refractory violations. HISTORY_PARTS_20261009.md explains why mixed histories cannot give a unique timing/count attribution.

## Exact shared-event refractory check, 10 October 2026

`pcdr_baseline_gating.py` reuses tested arrival acceptance on the prior selected native histories, joins source ID and physical tick exactly, and preserves unmatched events. It checks arrival reconstruction against verified arrays; no artificial history or ordinal pairing. Three focused tests and independent interval-membership verification support the computation. BASELINE_GATING_20261010.md explains the low-coverage negative result.

## Actual count-gap crossing states, 10 October 2026

`pcdr_count_crossings.py` selects the first cumulative two-spike gap for prior targets and conditionally reconstructs both native pre-threshold states from actual arrivals and saved resets. Fine-only comparison times retain the coarse tick lag. `pcdr_crossing_sources.py` groups each voltage contribution by source, preserving a failed sum-check attempt separately. Tests and independent matrix-exponential checks are recorded in COUNT_CROSSINGS_20261010.md; these are not free-running network interventions.

## CB4058 actual histories, 10 October 2026

`pcdr_cb4058_history.py` describes all52 target/native states for the source selected in the prior decomposition, retaining absent/contrary cases. It classifies latest actual arrivals relative to observed resets, checks contributions against the independently verified source table, and avoids event pairing. `pcdr_cb4058_plot.py` draws the smallest selected seed in a fixed gap-relative window from actual event tables. CB4058_HISTORY_20261010.md records interpretation and visual review.


## Smaller-step pilot preparation (10 October 2026)

`pcdr_build_smaller_pilot.py` copies archived fine-study simulator bytes and selected original/anchor records into a new self-contained package, checking their hashes and paired inputs. It does not rewrite the old plan. `pcdr_smaller_pilot.py` validates that package, checks the allocation/environment and deadline, reproduces two saved prefixes, measures two new-step prefixes, and gates the twelve scientific trials on remaining resources. Prefix output never substitutes for one-second convergence. Its owned-process wrapper records failures/timeouts and cleans only its own subprocess on interruption. `pcdr_smaller_run_all.sh` bounds installation and controller runtime and prevents duplicate launchers. `test_pcdr_smaller_pilot.py` covers numerical/input checks, reference boundaries, selection integrity, resource gates and process cleanup. Local tests do not establish remote execution; see SMALLER_STEP_PILOT_20261010.md for actual status and provenance.


`pcdr_check_smaller_results.py` independently reads the four-prefix result ZIP, compares returned source bytes to the validated upload, checks output hashes and physical schedules, directly selects old reference prefixes by physical time, compares per-cell counts/timing, and recomputes the capacity refusal. It never executes archived code, refuses overwriting its dated output, and preserves failures. It is specific to this fixed result panel, not a general convergence certifier.
