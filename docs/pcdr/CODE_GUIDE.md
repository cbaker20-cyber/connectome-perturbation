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
