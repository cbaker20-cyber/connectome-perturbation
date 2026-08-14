# Connectome Perturbation

This repository contains Python/Brian2 simulation code, perturbation and graph-analysis scripts, notebooks, research notes, and several tracked connectome-like data files. Its present status is **provenance and reproducibility triage**: the repository has substantially more material than the old one-line README showed, but it does not yet provide a verified end-to-end path from an authoritative data release to a reproducible result.

> **New readers:** see **`MASTER_GUIDE.md`** for the single consolidated reference — model and parameters, methods, all verified results (n=5 and n=20), the null models and controls, provenance status, the AI-content registry, and an interview answer bank.

Nothing in `results/perturbation_summary.csv` should be treated as validated neuroscience. The file is an existing project artifact whose exact input manifest, run configuration, commit, and validation record are not attached.

## Repository map

- `model.py` and `utils.py`: Brian2 model and result helpers.
- `perturbation/`: baseline, perturbation, statistics, motor, graph, and pathway analysis scripts.
- `analyze_graph_outputs.py`: command-line checks and summaries for graph-analysis outputs.
- `example.ipynb` and `figures.ipynb`: notebooks that reference materialization-630-style input filenames.
- `environment.yml` and `environment_full.yml`: a concise Conda environment and a historical expanded environment export.
- `00_PROJECT_STATE.md` through `16_NEXT_STEPS_EXECUTION_PLAN.md`: project-maintained research records. Their claims still require links to source data, run artifacts, and independent validation.
- `docs/data-policy.md`: rules for datasets, outputs, privacy, and manifests.
- `docs/claim_ledger.md` and the `docs/*-contract.md` specs: the reproducibility/validation contracts.
- `docs/environment-plan.md`: evidence-based setup plan and current run blockers.
- `TASKS.md`: active project backlog for reproducibility and analysis work.

## Data and provenance status

The repository currently tracks files named for materializations 630 and 783, plus `flywire_annotations.tsv`. Those names and existing project notes suggest a FlyWire-related origin, but filenames are not provenance. The repo still needs authoritative download URLs or DOIs, release/version identifiers, licenses, access dates, checksums, schemas, and a mapping from each experiment to the exact files used.

There is code in `perturbation/perturb.py` that writes a file named `results/perturbation_summary.csv`. However, the tracked summary is not bound to a run manifest, configuration, log, input checksums, or commit. Several scripts also refer to a `` directory that is not present in the current layout. These are blockers to claiming reproduction.

## Environment

The concise environment file records Python 3.10, Brian2 2.5.1, NumPy, pandas, joblib, PyArrow, Jupyter, and IPython kernel support.

```bash
conda env create -f environment.yml
conda activate brian2
python -c "import brian2, numpy, pandas, pyarrow; print('imports ok')"
python tools/validate_research_docs.py
```

The documentation validator does not validate the model or its scientific outputs. Do not start a full simulation until the paths and input manifest described in `docs/environment-plan.md` are resolved.

## Metadata-first smoke command

This command builds a local input manifest, writes a deterministic metadata-only smoke artifact, records that artifact in the output manifest, and validates metadata plumbing. It does **not** validate a neuroscience result.

```bash
python tools/build_input_manifest.py
python tools/write_smoke_artifact.py --output results/reproducibility_smoke_artifact.json
python tools/write_output_manifest.py \
  --config configs/smoke_run.yaml \
  --input-manifest data/input_manifest.json \
  --output output_manifest.json \
  --artifact results/reproducibility_smoke_artifact.json
python tools/validate_reproducibility.py
```

Expected artifacts:

- `data/input_manifest.json`: local filenames, sizes, SHA-256 checksums, guessed roles/materializations, and empty provenance fields.
- `results/reproducibility_smoke_artifact.json`: deterministic metadata-only artifact used to exercise output declaration and checksum validation.
- `output_manifest.json`: command/config/commit/environment/input-checksum/output-artifact metadata with `claim_status` set to `not_interpretable_as_neuroscience`.

Do not use any of these files as evidence for a biological conclusion until authoritative provenance and an actual validated run are attached.

## Neuron ID representation validator

`tools/validate_neuron_ids.py` checks identifier representation without converting IDs to integers or floating-point values. Inputs and reports must resolve inside the repository, and the report may not overwrite the source input. A successful result establishes only compliance with this syntax and declared original-text provenance contract; it does not establish dataset provenance, neuron identity, materialization membership, biological validity, perturbation effects, or any neuroscience conclusion.

For CSV input, provide the identifier column and, when available, explicit original-text provenance columns:

```bash
python tools/validate_neuron_ids.py data/example_ids.csv \
  --column neuron_id \
  --original-text-column neuron_id_original_text \
  --availability-column original_text_available \
  --report results/example_ids.validation.json
```

CSV availability values must be `true` or `false` (case-insensitive). For JSON input, the top level must be either a list of objects or an object containing a `records` list; availability values must be JSON booleans:

```bash
python tools/validate_neuron_ids.py data/example_ids.json \
  --column neuron_id \
  --original-text-column neuron_id_original_text \
  --availability-column original_text_available
```

The command prints deterministic JSON when `--report` is omitted. It exits with status `0` only when every record is classified `valid_exact_string`; all missing, malformed, unverifiable, or suspected precision-loss records produce an invalid aggregate result and exit status `1`. The report includes sorted status counts, validator and schema versions, the selected column names, and `claim_status: not_interpretable_as_neuroscience`.

## Current blockers

1. No authoritative source manifest for the tracked dataset and annotation files.
2. No completed schema/version record tying inputs to an experiment.
3. Hard-coded paths do not consistently match the repository layout.
4. No single reproduction command or frozen run configuration for the tracked summary.
5. No validation record connecting `perturbation_summary.csv` to raw outputs.
6. Existing research notes contain project claims that have not been independently verified in this repository review.

## Safe next step

Create a non-sensitive input manifest, reconcile paths without moving or deleting data, and reproduce one tiny documented smoke run before interpreting any output. See `docs/data-policy.md`, `docs/environment-plan.md`, and `TASKS.md`.
