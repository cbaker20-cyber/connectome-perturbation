# Every File, Explained

A complete walkthrough of the `connectome-perturbation` repository. This assumes no
background in the project or in computational neuroscience. Each file gets a plain-English
explanation of **what it is** and **what it means in this project**.

> Conventions used throughout:
> - **FlyWire** = the published complete wiring diagram of the fruit-fly brain.
> - **root ID / flywire_id** = the unique integer name of one neuron (e.g. `720575940619341105`).
> - **Brian2** = the Python library that runs the spiking-neuron simulation.
> - **ΔHz (delta_hz)** = change in the motor neurons' total firing rate after a group is silenced.
> - **Silencing / lesion** = turning off a group of neurons (zeroing their outgoing connections).
> - **claim_status** = a field stamped on nearly every artifact. It is almost always
>   `not_interpretable_as_neuroscience`, meaning "this file is plumbing/output, not a
>   biological conclusion."

---

## 0. The one thing to know before anything else: what "atlas" means here

You asked about the "atlas" file. This is important and easy to misread.

There are three atlas-related files:

- `docs/atlas-run-record-v0.md`
- `tools/validate_atlas.py`
- `tests/test_validate_atlas.py`

**"Atlas" in this repo is NOT a brain atlas.** It is not a map of brain regions, not a
FlyWire/neuroscience standard, and not any external "Atlas" project. The very first line of
`docs/atlas-run-record-v0.md` says so:

> Status: **proposed, synthetic-only, not an external Atlas standard** …
> The name does not imply compatibility with any external Atlas project or neuroscience
> data standard.

What it actually is: a **naming scheme for local, synthetic test artifacts**. The project
writes tiny, deterministic "toy" outputs (a fake model run, a fake lesion table, a fake
vulnerability matrix, a fake structural baseline). Each one is a JSON file whose
`schema_version` field begins with `atlas-`:

- `atlas-run-record/v0` — a synthetic model run record
- `atlas-connection-lesion-table/v0` — a synthetic connection-lesion scoring table
- `atlas-vulnerability-signature-matrix/v0` — a synthetic vulnerability matrix
- `atlas-structural-baseline-table/v0` — a synthetic structural (graph) baseline table
- `atlas-node-lesion-table/v0` — referenced as a supported *source* schema for the matrix

So the meaning of the whole "atlas" thread is: **the project built a strict, fail-closed
validator that checks the *shape* of its own synthetic fixtures** (correct field names,
finite numbers, unique string IDs, matching vector lengths, sorted deterministic output),
and it happens to name those schemas `atlas-*`. It is deliberately scoped to validate
"representation and declared limitations only" — never biology. That's why the validator
exists at all: to prove, in an automated way, that a demo file is correctly *labeled* as
"not interpretable as neuroscience."

---

## 1. The top-level numbered documents (00–12)

These are the project's research-management brain. They are maintained as a living,
numbered system and duplicated inside `connectome_research_docs/` (see section 12).

| File | What it is / means |
|---|---|
| `00_PROJECT_STATE.md` | The single "where are we right now" snapshot: current milestone, next steps, open blockers. This is where you look first to know status. (Note: its JO-sweep-complete claim has historically drifted ahead of what's actually on disk — see `06_Audit_History_and_AI_Content_Registry.md`.) |
| `01_LIVING_RESEARCH_LOG.md` | A dated diary of every substantive experiment decision and result. Entries are numbered (001, 002, …). This is the project's memory of *what happened when*. |
| `02_METHODS_MASTER.md` | The authoritative description of the methods: the LIF model parameters, the perturbation protocol, the statistics (Welch t-test + BH-FDR), the null-model contracts. |
| `03_EXPERIMENT_REGISTRY.csv` | A spreadsheet-style index of experiments: ID, date, question, status. One row per experiment. |
| `04_RESULTS_LEDGER.csv` | A spreadsheet-style ledger of results and their claim status (validated / exploratory / negative / etc.). |
| `05_CODE_CHANGELOG.md` | Versioned notes on code changes (M001, M002, …). The code analog of the research log. |
| `06_DECISION_LOG.md` | Log of decisions made and *why* (e.g. "pin Cython<3 to unblock Brian2"). |
| `07_ISSUES_AND_CAVEATS.md` | Known problems, limitations, and caveats. The honest-bad-news file. |
| `08_DATA_PROVENANCE.md` | Where each input dataset came from (FlyWire release, version, DOI) and how it was obtained. |
| `09_REPRODUCIBILITY_CHECKLIST.md` | A checklist for whether a result can be reproduced from a clean checkout. |
| `10_PUBLICATION_NARRATIVE_TRACKER.md` | Tracks the story arc for the eventual paper/poster (what claim goes where). |
| `11_CLAIMS_REGISTER.csv` | Spreadsheet of formal claims and their promotion status (unverified → validated → etc.). |
| `12_LITERATURE_AND_SOURCE_NOTES.md` | Notes on the literature (Dorkenwald 2024, Schlegel 2024, Eckstein 2024, etc.) and sources. |
| `comprehensive_project_history.md` | An AI-reconstructed narrative of the project's history. Treat as a draft narrative, not a source of truth — its hashes were verified real but its prose is AI gloss. |
| `TASKS.md` | A plain to-do list of outstanding tasks. |
| `README.md` | The front-door summary: what the project is, how to install, how to run. |
| `LICENSE` | The open-source license. |

---

## 2. Raw input data (the actual brain data)

| File | What it is / means |
|---|---|
| `2023_03_23_completeness_630_final.csv` | **Completeness table, v630.** One row per neuron in the simulation; tells you which root IDs exist in the 630-materialization connectome. This is the "who is in the network" list. |
| `2023_03_23_connectivity_630_final.parquet` | **Connectivity table, v630.** The actual wiring: every directed synapse edge with a `Connectivity` (synapse-count) weight. This is "who connects to whom, and how strongly." |
| `Completeness_783.csv` | Same idea, but for the newer **v783** materialization (more neurons). Kept as an alternate input; not the primary one. |
| `Connectivity_783.parquet` | Connectivity table for **v783**. |
| `flywire_annotations.tsv` | **Annotation table.** Maps each root ID to its labels: `super_class` (sensory/motor/central/descending…), `cell_class` (AN, LO, Kenyon_Cell…), `cell_type`, `side` (left/right), and neurotransmitter. This is how the code turns raw IDs into named groups like "AN" or "motor." |
| `priority_annotations.tsv` | A smaller, curated annotation subset used early on for priority groups. |
| `sez_neurons.pickle` | A Python pickle of "SEZ" (subesophageal zone — the feeding/grooming center) neuron IDs, used as a targeting list. |
| `Drosophila_brain_model/` | A directory containing an older copy of the model + the two 630 data files. A historical snapshot of the simulation code, not the active one. Contains `model.py` plus two `.bak`/`.backup_before_numpy_backend` backup files. |
| `data/input_manifest.json` | The **input manifest**: a machine-readable record of the 5 raw input files above, with their sizes and SHA-256 checksums. Note its provenance fields are all `null` — the files are checksummed but their citation/metadata is not yet filled in. |
| `target_manifest.csv` | A 9-row list of `cell_type` names (JO-FVA, LC28b, LC26, …) used as *targets* for the adaptive planner (JO-related cell types to probe). |

---

## 3. The simulation model (top-level)

| File | What it is / means |
|---|---|
| `model.py` | **The brain simulation.** Defines `default_params` (the LIF parameters: −52 mV resting, −45 mV threshold, 20 ms tau, 5 ms synaptic decay, 2.2 ms refractory, 1.8 ms delay, 0.275 mV synaptic weight) and `run_exp()`, which loads the connectivity, builds the Brian2 network, drives excitatory inputs, optionally silences a group, and saves spikes to a parquet. This is the single most important code file. |
| `utils.py` | Shared helpers (file resolution, small utilities) used by the model and pipeline. |
| `example.ipynb` / `figures.ipynb` | Notebooks: an example walkthrough, and the figure-generation notebook (the `figures.ipynb` is where the JO neuron curation originally happened). |
| `test_run.py` | A small standalone script that runs a toy/minimal experiment (used as a smoke check). |
| `analyze_graph_outputs.py` | A top-level script that reads graph-analysis outputs and summarizes them. |

---

## 4. `perturbation/` — the analysis engine

This package runs the baseline/perturbed simulations and computes statistics.

| File | What it is / means |
|---|---|
| `baseline.py` | Runs the **baseline** (no silencing) simulation. Defines `NEU_SUGAR` (the sugar/taste sensory drive neurons) and the sensory excitation sets. |
| `perturb.py` | Runs the **perturbation sweep**: for each target group, silence it and record the spike output. Contains `run_perturbation_sweep` and `run_single_perturbation`. |
| `cell_groups.py` | Defines how named groups (AN, descending, LO, Kenyon_Cell, motor) are resolved from the annotation table. |
| `statistics.py` | Computes the headline statistics: per-group ΔHz, Welch t-test p-values, and BH-FDR corrected q-values; writes `statistics.csv`. |
| `analyze.py` | Higher-level analysis that ties simulation outputs to stats and summaries. |
| `motor_analysis.py` | Focused analysis on the **motor** (output) neurons — the project's readout. |
| `graph_analysis.py` | Graph-theory analysis of the connectome (degree, centrality, etc.) on the perturbation groups. |
| `path_analysis.py` | Pathway analysis: does the effect travel along specific paths from sensory → group → motor? |
| `sweep_cell_class.py` | Runs a **cell-class sweep** (many classes silenced one at a time) to screen for interesting targets. |
| `visualize.py` | Plotting helpers for perturbation results. |
| `novel_architecture_analysis.py` | An exploration of "novel architecture" ideas (e.g. the disinhibition motif angle) around the results. |

---

## 5. `connectome_analysis/` — the graph / null-metric modules

These operate on the connectome *as a graph* (no Brian2) or on null-model contracts.

| File | What it is / means |
|---|---|
| `an_betweenness.py` | **AN betweenness control.** Computes source→target betweenness and runs a **degree-matched structural null** for AN (and other groups) — pure graph math, seed=7, 200 permutations. Produced `results/an_betweenness_control.csv`. |
| `bora_routing.py` | **BORA = Behavioral Opponent Routing Analysis** (a novel metric the project preregistered — *not* "Biological Operations Reference Architecture," which is an AI-gloss error). Computes routing scores. |
| `connection_lesion.py` | Connection-level (edge) lesion scoring — measures each *synapse/edge's* contribution, vs `node_lesion.py` which lesions *neurons*. |
| `node_lesion.py` | Node-level (neuron) lesion scoring. |
| `context_comparison.py` | Compares results across sensory contexts (JO vs sugar). |
| `cross_reference_planner.py` | Cross-references the adaptive planner's predictions against ground-truth results. |
| `disinhibition_motifs.py` | Searches for disinhibition motifs (inhibitory→inhibitory→excitatory chains) in the graph. |
| `graph_metrics.py` | Core graph metrics (degree, strength, betweenness) used across the analysis modules. |
| `graph_surrogates.py` | Generates graph surrogates (randomized rewired graphs) for null comparisons. |
| `structural_baseline.py` | Computes a structural baseline (the "what would graph topology alone predict" numbers). |
| `targeted_validation_*.py` (4 files) | A quartet — `csv`, `manifest`, `receipt`, `summary` — implementing **targeted validation**: a specific, pre-registered check with a machine-readable receipt so a human can verify it ran against the intended data. |
| `toy_signal.py` | Generates the deterministic synthetic "toy" signal artifacts (the `atlas-*` fixtures). |
| `validate_surrogates.py` | Validates that surrogate tables are internally consistent. |
| `vulnerability_matrix.py` | Builds the vulnerability-signature matrix (contexts × targets) across contexts. |

---

## 6. `tools/` — provenance, validation, and plumbing

This is the "trust machinery": manifest writers, validators, and auditors.

| File | What it is / means |
|---|---|
| `path_resolver.py` | Resolves input file paths by looking them up in `data/input_manifest.json` (so code never hardcodes a path). |
| `build_input_manifest.py` | Builds/regenerates `data/input_manifest.json` from the raw files on disk (computes sizes + checksums). |
| `validate_neuron_ids.py` | Validates that a list of neuron IDs is well-formed and matches the expected ID space. |
| `validate_atlas.py` | **The "atlas" validator** (see section 0). Enforces the `atlas-*` synthetic schemas. |
| `validate_reproducibility.py` | Checks the reproducibility contract: were inputs checksummed, is provenance present, are trial counts matched? |
| `validate_research_docs.py` | Validates the numbered research documents (00–12) for internal consistency and required fields. |
| `write_output_manifest.py` | Writes an **output manifest** (the record of what a run produced, with hashes). |
| `write_smoke_artifact.py` / `write_toy_graph_artifact.py` | Write small deterministic artifacts used by CI/smoke tests. |
| `adaptive_experiment_planner.py` | The **adaptive planner**: reads current results and proposes the next highest-value experiments. (Its CLI ergonomics were test-written but never fully implemented — see the known broken test.) |
| `context_reachability_audit.py` | Audits how reachable each context's neurons are within the graph (multi-hop reachability with a null model). |
| `create_source_contexts.py` | Builds the "source context" neuron sets (sugar, JO, gustatory, etc.) that define sensory contexts. |
| `id_space_audit.py` | **SourceMap Doctor**: diagnoses whether files use FlyWire root IDs vs simulator indices (a real footgun in this project). |
| `make_motor_candidates.py` | Generates candidate motor-neuron lists for the feeding/grooming readouts. |
| `plot_jo_sweep.py` | Plots the JO sweep results. |
| `rank_motor_outputs.py` | Ranks motor output neurons by their response. |
| `run_context_perturbation_sweep.py` | Runs a perturbation sweep conditioned on a sensory context. |
| `run_targeted_context_validation.py` | Runs the targeted context validation. |
| `simulator_sanity_audit.py` | A sanity audit of the simulator itself (does a tiny run produce sane output?). |
| `structural_surrogate_benchmark.py` | Benchmarks structural surrogates against ground truth. |
| `append_log_entry.py` | Appends a dated entry to the living research log. |

---

## 7. `scripts/` — orchestration and one-offs

Entry points that tie the pieces together (many are `.ps1` PowerShell wrappers because the
work runs on Windows/WSL).

| File | What it is / means |
|---|---|
| `run_jo_sweep.py` | **The main JO sweep.** Runs the JO (Johnston's Organ) baseline + the 5-group silencing sweep; writes `perturbation_summary.csv` + `output_manifest.json`. `--dry-run` validates plumbing without Brian2. |
| `run_sugar_ground_truth_sweep.py` | The matching **sugar**-context sweep (same 5 groups, sugar drive). |
| `run_sugar_stats_and_nulls.py` | Runs statistics + degree-matched nulls for the sugar context. |
| `run_degree_matched_nulls.py` | **Degree-matched dynamical null.** For each group, draws random neuron sets matched in size + weighted-degree, runs full Brian2 silencing, and computes empirical p / z-score vs the observed ΔHz. Resumable. |
| `run_distance_matched_nulls.py` | **Distance-matched dynamical null** — same idea but matched on graph distance from JO, not degree. |
| `aggregate_nulls.py` | Aggregates per-group `*_perms.csv` files into one combined null table. |
| `verify_and_combine_nulls.py` | **The careful version** of aggregating: refuses to combine nulls whose trial count doesn't match the observed sweep, or that are below the 10-permutation floor. Emits `null_comparison_verified.csv`. Exit code 1 if problems. |
| `build_q3_q2.py` | Builds effect-size and null-comparison summary CSVs (an earlier, looser version of the above). |
| `build_context_comparison.py` | Builds `context_comparison_JO_vs_sugar.csv`. |
| `rank_dynamical_vs_structural.py` | Ranks groups by observed ΔHz vs a structural predictor (modal controllability); computes Spearman correlation. |
| `rank_n20.py` | The n=20 version of the rank comparison. |
| `patch_distance.py` | A one-off **patch script** that converted the degree-null script into the distance-null script (kept for history; the patch is already applied). |
| `run_other_groups_betweenness.py` | Runs the betweenness structural null for the *other* groups (descending/LO/Kenyon/motor), extending the AN-only control. |
| `generate_jo_figures.py` | Generates the publication figures (fig1 barplot, fig2 JO-vs-sugar) as PDF + 300-DPI PNG. |
| `make_pptx.py` | Builds the 10-slide `UB_Connectome_Perturbation.pptx` presentation. |
| `cloud_sweep_modal.py` | A **Modal** (cloud compute) runner for the JO sweep — the escape hatch from slow local WSL compute. |
| `update_review.py` | Appends freshly-read CSVs into `HUMAN_REVIEW/02_Current_Verified_Results.md`. |
| `freeze.py` | Copies key result CSVs into `HUMAN_REVIEW/raw_results/` and writes a SHA-256 `FREEZE_MANIFEST.md` (a snapshot so the numbers can't drift silently). |
| `run_fast_professor_pilot.ps1` | Emergency small-but-real run (source contexts → reachability → tiny sweep) for a professor meeting. |
| `run_id_space_audit.ps1` | Wrapper to run the ID-space audit. |
| `run_overnight_context_audit.ps1` | Broad unattended context-reachability audit at increasing depths. |
| `max_overnight_run.ps1` | The big unattended orchestration: wait for the JO sweep to finish, then run plots, planner, full pytest, sugar sweep, nulls, structural benchmark, ID audit — and append a status block to `00_PROJECT_STATE.md`. |
| `run_long_context_perturbation_sweep.ps1` | Long-running context-conditioned perturbation sweep. |
| `run_targeted_context_validation.ps1` | Wrapper for the targeted context validation. |
| `run_micro_motor_pilot_no_sugar.ps1` | A micro pilot run without sugar drive. |
| `run_instant_structural_surrogate.ps1` | Instant structural-surrogate benchmark wrapper. |
| `patch_local_model_warning.ps1` / `patch_safe_large_id_parsing.ps1` | One-off patchers (suppress a local model warning; fix safe large-ID parsing). |
| `Run_Nulls.bat` | **The Windows Scheduled Task batch file.** Runs degree nulls → distance nulls → verify/combine, logging to `results/null_run.log`. This is what's executing your multi-day null run right now. |

---

## 8. `configs/` — experiment configurations

| File | What it is / means |
|---|---|
| `jo_ground_truth_30trial.yaml` | The JO sweep config: 30 trials, 150 Hz Poisson drive, 1000 ms, 146 curated JO sensory root IDs, 5 silencing groups. (The canonical "30-trial" config.) |
| `jo_ground_truth_n20.yaml` | Identical protocol but `run_name: jo_ground_truth_n20` — the config that actually produced the n=20 run (via `--n-trials 20` override). |
| `smoke_run.yaml` | A tiny metadata-only smoke config (≤10 neurons, ≤100 edges, ≤60 s) to prove the plumbing works before any expensive run. |
| `docs_config.yaml` | Configuration for the documentation system itself: status labels, minimum claim standards (matched trial counts, zero-spike retention, FDR correction), and the primary readout (total motor firing rate). |

---

## 9. `environment.yml` / `requirements.txt`

| File | What it is / means |
|---|---|
| `environment.yml` | Conda environment definition (python 3.10, brian2 2.5.1, numpy 1.24, jupyter, pandas, joblib, pyarrow). The preferred environment for Brian2 overnight runs. |
| `requirements.txt` | Pip mirror of the core deps. **Note the `Cython>=0.29,<3.0` pin** — Brian2 2.5.1 imports a Cython function removed in Cython 3.x, so this pin is load-bearing. (A later Modal config uses brian2 2.5.4/2.9 + numpy 1.26 to dodge the numpy 2.x `ndarray.ptp` breakage.) |
| `environment_full.yml` | A fuller environment file (more deps). |

---

## 10. `results/` — the outputs

The most important thing to understand: **many files here are outputs at different
stages/contexts, and some are synthetic fixtures.** The trustworthy ones carry
`claim_status` and are regenerable from `scripts/`. Grouped:

**Headline CSVs (the numbers you care about):**
- `results/statistics.csv`, `results/perturbation_summary.csv`, `results/cell_class_sweep.csv` — the early **sugar-context** super-class/cell-class screen results (5-trial).
- `results/jo_ground_truth/` — the **JO sweep (n=5)** results: `baseline_jo.parquet`, `perturb_{group}.parquet` (AN/descending/LO/Kenyon_Cell/motor), `perturbation_summary.csv`, `statistics.csv`, plus the null files `jo_degree_matched_nulls*.csv`, `planner_vs_groundtruth.csv`, `residual_ranking.csv`, `surrogate_vs_ground_truth.csv`, and `output_manifest.json`.
- `results/jo_ground_truth_n20/` — the **JO sweep (n=20)** results: same shape, plus `null_comparison.csv` and `null_comparison_verified.csv`, and the in-progress `jo_degree_matched_nulls_*_perms.csv` / `jo_distance_matched_nulls_*_perms.csv` files your Scheduled Task is writing right now.
- `results/sugar_ground_truth/` — the **sugar sweep** results (same 5 groups, sugar drive), including `sugar_degree_matched_nulls*.csv`.
- `results/context_comparison_JO_vs_sugar.csv`, `results/effect_sizes_jo_n20.csv`, `results/effect_sizes_sugar.csv`, `results/sugar_vs_jo_context_shift.csv` — cross-context comparisons.
- `results/an_betweenness_control.csv`, `results/other_groups_betweenness_control.csv` — the **structural** degree-matched betweenness nulls (pure graph math, real data).
- `results/graph_analysis/` — graph-metric nulls (betweenness/strength distributions) + figure PNGs/PDFs/SVGs.
- `results/path_analysis/` — pathway-analysis results.

**Synthetic / demo fixtures (do NOT treat as science):**
- `results/example/*.parquet` — tiny example outputs.
- `results/bora_routing_scores.csv`, `results/surrogate_correlations.csv`, `results/sugar_vs_jo_context_shift.csv`, `results/bora_hqAN_provisional*/` — demo/provisional BORA outputs (flagged in the audit registry as fixture-grade).

**Batches (large parameter sweeps, many parquets each):**
- `results/adaptive_jo_batch/` and `results/adaptive_next_batch/` — the adaptive planner's sweep outputs. Naming convention: `ctx_{context}__lesion_cell_type_{type}.parquet` and `ctx_{context}_intact.parquet`, plus `sweep_summary.csv` / `sweep_run_info.csv`.
- `results/adaptive_experiment_planner/` — planner outputs (`adaptive_plan.csv`, `.ps1` commands).
- `results/targeted_context_validation/`, `results/targeted_context_validation_resume_numpy/`, `results/long_context_perturbation_sweep/`, `results/fast_professor_pilot/`, `results/structural_surrogate_benchmark/`, `results/id_space_audit/` — each a scoped sub-experiment with its own `RUN_STATUS.txt`, `logs/`, and CSVs.

**Housekeeping:**
- `results/STATUS_2026-08-08.md`, `results/FREEZE_MANIFEST.md` — status note + the frozen hash manifest from `scripts/freeze.py`.
- `results/UB_Connectome_Perturbation.pptx` (+ a `~$` lock file) — the presentation.
- `results/null_run.log`, `results/jo_degree_matched_nulls_AN_run*.log` — run logs.
- `results/_pre_degree_fix/` — null results from **before** the degree-matching bug was fixed (kept for comparison).
- `results/hq_AN.parquet`, `results/hq_motor_impact.csv`, `results/motor_impact.csv`, `results/motor_impact_figure.png`, `results/disinhibition_motifs.csv`, `results/baseline_sugar.parquet`, `results/test_sugar.parquet` — assorted individual outputs.

---

## 11. `tests/` — the test suite

~40 test files. 323 pass / 4 skip as of the last audit (one file is broken — see below).

Grouped by what they protect:

- **Manifest/plumbing contracts:** `test_build_input_manifest.py`, `test_input_manifest_record_validation.py`, `test_manifest_counts.py`, `test_manifest_path_boundaries.py`, `test_path_resolver_boundaries.py`, `test_output_manifest_*.py` (4 files).
- **Reproducibility tools:** `test_reproducibility_tools.py`.
- **Atlas schemas:** `test_validate_atlas.py` (the atlas validator's tests).
- **Neuron-ID validation:** `test_validate_neuron_ids.py` and its CSV-header/provenance variants (3 files).
- **Lesion/structural contracts:** `test_connection_lesion.py`, `test_node_lesion.py`, `test_structural_baseline.py`, `test_structural_lesion_comparison.py`, `test_validate_structural_baseline.py`.
- **Surrogates/motifs:** `test_math_surrogates.py`, `test_motifs_and_controls.py`, `test_validate_surrogates.py`.
- **Targeted validation:** `test_targeted_validation_*.py` (5 files).
- **Graph/vulnerability/toy:** `test_graph_metrics.py`, `test_vulnerability_matrix.py`, `test_vulnerability_example.py`, `test_toy_signal.py`, `test_write_smoke_artifact.py`, `test_write_toy_graph_artifact.py`.
- **JO sweep + context comparison:** `test_jo_sweep.py`, `test_context_comparison.py`.
- **`tests/fixtures/neuron_id_validation_cases.json`** — the fixture of valid/invalid neuron IDs used by the above.

**Known broken file:** `tests/test_adaptive_planner_cli.py` imports `DEFAULT_CONTEXTS_MANIFEST`,
`looks_like_comma_separated_context_names`, and `resolve_contexts_argument` from
`tools/adaptive_experiment_planner.py`, none of which exist — a test written for a CLI
feature that was never implemented. It causes a collection error; the other 300+ tests pass.

---

## 12. `connectome_research_docs/` — the duplicated documentation system

This directory is a **second, fuller copy** of the numbered doc system. It was reconstructed
(partly with AI) from the raw lab notebook. It contains:

- `README.md` — explains the doc system.
- `00_PROJECT_STATE.md` … `12_LITERATURE_AND_SOURCE_NOTES.md` — the same 00–12 series as the root, but extended.
- **Extra documents beyond 12:** `12_NOVEL_METRIC_PREREGISTRATION.md`, `13_BORA_METRIC_PREREGISTRATION.md`, `13_FINAL_PROJECT_SCOPE.md`, `14_FINAL_PROJECT_SCOPE.md`, `14_SCIENTIFIC_JUSTIFICATION_PORTFOLIO.md`, `15_NEXT_STEPS_EXECUTION_PLAN.md`, `15_SCIENTIFIC_JUSTIFICATION_PORTFOLIO.md`, `16_NEXT_STEPS_EXECUTION_PLAN.md` — preregistrations and scope docs.
- `99_IMPORTANT_LAB_ENTRIES_FROM_BEGINNING.txt` — key early notebook entries.
- `docs_config.yaml` — same as root `docs_config.yaml`.
- `source_material/raw_lab_notebook_pasted_text.txt` — the raw pasted notebook text this was reconstructed from.
- `templates/` — reusable templates (daily entry, experiment record, methods change, preregistration stub, claim record).
- `tools/append_log_entry.py`, `tools/validate_research_docs.py` — copies of the doc tooling.

**Why the duplication matters:** the root docs are the "live" set; `connectome_research_docs/`
is the richer reconstructed archive. Having two overlapping copies is itself a source of
drift risk, and the AI-content registry (`HUMAN_REVIEW/06_...`) flags which parts are
AI-generated vs hand-written.

---

## 13. `docs/` — contracts, history, and reference

| File | What it is / means |
|---|---|
| `00_START_HERE.md` | Onboarding doc. |
| `PROJECT_HISTORY.md` | AI-reconstructed commit-by-commit history (hashes verified real; prose is AI gloss). |
| `RESULTS_SUMMARY.md` | A results summary — **stale** (n=5 only). |
| `atlas-run-record-v0.md` | **The atlas schema proposal** (section 0). |
| `claim_ledger.md` | The claim ledger (promotion rules for claims). |
| `data-policy.md` | How data is handled (redistribution, provenance). |
| `environment-plan.md` | Plan for the Python environment. |
| `progress-log.md` | Progress log. |
| `input_manifest_contract.md`, `input_manifest_validation_gaps.md`, `neuron-id-validation-contract.md`, `output_artifact_validation_contract.md`, `degree-matched-random-control-contract.md`, `node-lesion-scoring-contract.md`, `connection-lesion-scoring-contract.md`, `structural-baseline-contract.md`, `vulnerability-signature-matrix-contract.md`, `targeted-validation-preflight.md`, `targeted-validation-reverification.md`, `reproducibility_validation_plan.md`, `experiment_design_smoke_gate.md`, `toy-lesion-fixture-contract.md`, `toy-fixture-ci-scope.md` | A library of **contracts**: precise written specs for what each validator/scoring module must enforce. These are the "laws" the `tools/` validators implement. |
| `literature/flywire_source_notes.md`, `literature/flywire_provenance_matrix.md` | Source/provenance notes for the FlyWire data. |

---

## 14. `HUMAN_REVIEW/` — the human-facing evidence folder

Built for a human (or judge) to verify everything without reading code.

- `00_READ_ME_FIRST.md` — where to start.
- `01_What_This_Project_Is.md` — plain-language project overview.
- `02_Current_Verified_Results.md` — the verified numbers (auto-updated by `scripts/update_review.py`).
- `03_Key_Files_and_Where_They_Live.md` — a map of key files.
- `04_Git_and_Repo_State.md` — git/repo status.
- `05_Open_Questions_and_Gaps.md` — what's unresolved.
- `06_Audit_History_and_AI_Content_Registry.md` — **the audit history + the AI-content registry**, cataloguing every AI-generated summary/manuscript/citation by date and classifying each as REWRITE / CITE-MANUAL / DISCLOSE / SAFE-FACTUAL.
- `raw_results/` — frozen copies of key CSVs (from `scripts/freeze.py`) so the numbers are pinned.

---

## 15. `analysis_guide/` — your self-teaching kit (built earlier this session)

- `README.md` — index of the kit.
- `DATA_DICTIONARY.md` — every column/symbol in plain English with formulas.
- `TEACH_YOURSELF.md` — the core workbook: explains ΔHz, t-tests, FDR, the null model, z-scores, Spearman, then 8 exercises + answer key (no conclusions drawn).
- `annotated_data.xlsx` — 8-tab annotated spreadsheet including a live fill-in Spearman worksheet.
- `figures/` — 5 annotated figures (ΔHz bars, n5-vs-n20, AN null histogram, rank scatter, live null snapshot).
- `build_guide.py` — regenerates all figures + the workbook.

---

## 16. `metadata/` and `templates/` and `source_material/` and `examples/`

- `metadata/` — curated neuron lists: motor candidates (`all_motor_annotation_candidates.csv`, `feeding_motor_*.csv`, `grooming_motor_*.csv`, `motor_response_candidates_hq_AN.csv`, `motor_target_curation.md`), provisional feeding/grooming IDs, `sugar_ids_21.txt`, and `source_contexts/` (the per-context neuron sets: `sugar_`, `gustatory_`, `mechanosensory_`, `visual_projection_`, `sensory_ascending_`, `all_sensory_`, `no_input_` — each with a `complete` and a `matchedK21_seed13` variant, plus `source_context_manifest.csv`).
- `templates/` — same reusable doc templates as in `connectome_research_docs/templates/`.
- `source_material/raw_lab_notebook_pasted_text.txt` — the raw source notebook text.
- `examples/` — known-answer JSON fixtures: `structural-baseline-known-answer-*.json` and `synthetic_vulnerability/*.json` (the `atlas-*` schema examples the validator checks).

---

## 17. Everything else at the root / hidden

- `.github/workflows/reproducibility-tools.yml` — the CI workflow that runs the reproducibility-tool tests on every push.
- `.gitignore` — standard ignore rules.
- `.pytest_cache/` — pytest's cache (ignore).
- `.freebuff/desktop-v2.db*` — the local Freebuff desktop app's own database (not part of the project).
- `query` — a file of query/notes (non-code scratch).
- `docs_config.yaml` — root copy of the doc-system config.

---

## How to read this project in one pass

1. Start at `README.md` → `00_PROJECT_STATE.md` → `01_LIVING_RESEARCH_LOG.md` for *status*.
2. `02_METHODS_MASTER.md` + `model.py` for *how the simulation works*.
3. `configs/jo_ground_truth_30trial.yaml` + `scripts/run_jo_sweep.py` for *what the experiment is*.
4. `results/jo_ground_truth_n20/statistics.csv` + `null_comparison_verified.csv` for *the numbers*.
5. `HUMAN_REVIEW/` for the *human-verifiable* version of those numbers.
6. `docs/*.md` contracts + `tools/` validators for *why you can trust the plumbing*.
7. `HUMAN_REVIEW/06_Audit_History_and_AI_Content_Registry.md` for *which text was AI-generated and must be treated carefully*.
