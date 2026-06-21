# Connectome Perturbation

This repository contains Python/Brian2 simulation code, perturbation and graph-analysis scripts, notebooks, research notes, and several tracked connectome-like data files. Its present status is **provenance and reproducibility triage**: the repository has substantially more material than the old one-line README showed, but it does not yet provide a verified end-to-end path from an authoritative data release to a reproducible result.

Nothing in `results/perturbation_summary.csv` should be treated as validated neuroscience. The file is an existing project artifact whose exact input manifest, run configuration, commit, and validation record are not attached.

## Repository map

- `model.py` and `utils.py`: Brian2 model and result helpers.
- `perturbation/`: baseline, perturbation, statistics, motor, graph, and pathway analysis scripts.
- `analyze_graph_outputs.py`: command-line checks and summaries for graph-analysis outputs.
- `example.ipynb` and `figures.ipynb`: notebooks that reference materialization-630-style input filenames.
- `environment.yml` and `environment_full.yml`: a concise Conda environment and a historical expanded environment export.
- `00_PROJECT_STATE.md` through `12_LITERATURE_AND_SOURCE_NOTES.md`: project-maintained research records. Their claims still require links to source data, run artifacts, and independent validation.
- `docs/progress-log.md`: conservative status log.
- `docs/data-policy.md`: rules for datasets, outputs, privacy, and manifests.
- `docs/environment-plan.md`: evidence-based setup plan and current run blockers.

## Data and provenance status

The repository currently tracks files named for materializations 630 and 783, plus `flywire_annotations.tsv`. Those names and existing project notes suggest a FlyWire-related origin, but filenames are not provenance. The repo still needs authoritative download URLs or DOIs, release/version identifiers, licenses, access dates, checksums, schemas, and a mapping from each experiment to the exact files used.

There is code in `perturbation/perturb.py` that writes a file named `results/perturbation_summary.csv`. However, the tracked summary is not bound to a run manifest, configuration, log, input checksums, or commit. Several scripts also refer to a `Drosophila_brain_model/` directory that is not present in the current layout. These are blockers to claiming reproduction.

## Environment

The concise environment file records Python 3.10, Brian2 2.5.1, NumPy, pandas, joblib, PyArrow, Jupyter, and IPython kernel support.

```bash
conda env create -f environment.yml
conda activate brian2
python tools/validate_research_docs.py
```

The documentation validator does not validate the model or its scientific outputs. Do not start a full simulation until the paths and input manifest described in `docs/environment-plan.md` are resolved.

## Current blockers

1. No authoritative source manifest for the tracked dataset and annotation files.
2. No checksums or schema/version record tying inputs to an experiment.
3. Hard-coded paths do not consistently match the repository layout.
4. No single reproduction command or frozen run configuration for the tracked summary.
5. No validation record connecting `perturbation_summary.csv` to raw outputs.
6. Existing research notes contain project claims that have not been independently verified in this repository review.

## Safe next step

Create a non-sensitive input manifest, reconcile paths without moving or deleting data, and reproduce one tiny documented smoke run before interpreting any output. See `docs/data-policy.md` and `docs/environment-plan.md`.
