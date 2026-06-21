# Environment Plan

## Evidence in the repository

This is a Python project. `environment.yml` specifies Python 3.10 and Brian2 2.5.1 with NumPy 1.24, pandas, joblib, PyArrow, Jupyter, and ipykernel. `environment_full.yml` is an older expanded Windows-oriented export with more transitive pins; it should be treated as a historical snapshot unless a reproduction attempt proves it is required.

The main visible entry points are:

- `model.py`: model construction and experiment execution helpers;
- `perturbation/baseline.py`: baseline simulation wrapper;
- `perturbation/perturb.py`: perturbation sweep and summary writer;
- `perturbation/statistics.py`, `motor_analysis.py`, `graph_analysis.py`, and `path_analysis.py`: downstream analyses;
- `analyze_graph_outputs.py`: CLI-oriented output checks;
- `example.ipynb` and `figures.ipynb`: notebook workflows.

## Proposed setup

```bash
conda env create -f environment.yml
conda activate brian2
python -c "import brian2, numpy, pandas, pyarrow; print('imports ok')"
python tools/validate_research_docs.py
```

These commands only establish an environment and validate documentation structure. They do not reproduce or validate a simulation.

## Blockers before a model run

1. `perturbation/baseline.py`, `perturbation/perturb.py`, and other scripts refer to paths under `Drosophila_brain_model/`, while the corresponding filenames are at the repository root.
2. The exact input version for each proposed run is not selected: materialization-style 630 and 783 files coexist.
3. No authoritative source manifest, checksums, or schema validation is committed.
4. No frozen run configuration ties parameters, random seeds, trial counts, neuron groups, and outputs together.
5. The tracked `perturbation_summary.csv` has no attached command or execution log.
6. Full simulations may be expensive; resource expectations and a tiny smoke configuration are not documented.

Do not fix these blockers by guessing which dataset or path is canonical.

## Reproducibility sequence

1. Record SHA-256 checksums and authoritative metadata for each existing input without modifying it.
2. Choose exactly one dataset/materialization for a smoke run and document why.
3. Reconcile path configuration in a dedicated code PR; avoid copying another 80–100 MB dataset into a second directory.
4. Add a tiny, clearly labeled smoke configuration with fixed seed and minimal runtime.
5. Capture the command, commit, environment, parameters, and output manifest.
6. Validate schemas and numerical invariants before any biological interpretation.
7. Run larger experiments only after the smoke path is reproducible.

## Evidence needed for completion

Environment setup is complete only when a clean checkout can create the environment, pass import checks, locate approved inputs from a manifest, run the documented smoke command, and produce schema-valid outputs. No such end-to-end verification was performed in this documentation-only task.
