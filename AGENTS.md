# AGENTS.md

Rules for AI agents and human contributors working on this repository.

## Prime directive

Make the project reproducible before making biological claims. This repository is currently in provenance and reproducibility triage.

## Hard rules

- Do not delete tracked data or results unless a human explicitly approves it in a reviewed PR.
- Do not add secrets, tokens, credentials, private notes, or undisclosed datasets.
- Do not claim neuroscience conclusions from existing outputs until the exact input manifest, command, config, seed, commit, environment, and validation record are attached.
- Prefer small, reviewable PRs.
- Preserve existing exploratory work unless replacing it with a clearly simpler, tested path.
- Record important assumptions, blockers, and decisions in repository files, not only in chat.

## Current engineering priorities

1. Build and validate an input manifest for existing input-like files.
2. Remove hard-coded `Drosophila_brain_model/` assumptions by routing paths through one resolver.
3. Add a fixed-seed, tiny smoke path that writes `output_manifest.json`.
4. Add validation checks for manifests, checksums, paths, and output schema.
5. Only then attempt larger simulations or claims.

## Scientific standards

Every interpretable run should eventually include:

- input manifest with SHA-256 checksums;
- dataset names, materializations, source URLs/DOIs, licenses, and access dates;
- configuration and random seed;
- command used;
- Git commit;
- environment file or lockfile;
- runtime metadata;
- output manifest;
- validation result.

Separate verified facts, assumptions, hypotheses, and future ideas.

## Safe automation behavior

When blocked, document the blocker and pivot to another reproducibility or documentation task. Do not fabricate missing provenance.

## Cursor Cloud specific instructions

The Python dependency environment is provisioned by the startup update script; do not reinstall it.

### Environments and how to run things

- Python dependencies live in a Conda env named `brian2` (Python 3.10) under `~/miniconda3`. Activate it with `source ~/miniconda3/etc/profile.d/conda.sh && conda activate brian2` before running anything.
- Two tiers coexist (see `README.md`): the lightweight reproducibility tooling and tests (`tools/`, `tests/`, `connectome_analysis/`; stdlib + `pytest`), and the heavier Brian2 simulation (`model.py`, `perturbation/`).
- Run tests with `python -m pytest tests/ -q`. The authoritative green subset is listed in `.github/workflows/reproducibility-tools.yml`.
- The metadata-first smoke sequence and the doc validator (`tools/validate_research_docs.py`) commands are documented in `README.md`.

### Non-obvious caveats

- Brian2 2.5.1 imports `pkg_resources`, so `setuptools<81` must be installed (the update script does this); setuptools >= 81 removes `pkg_resources` and breaks the import. `pytest` is also pip-installed because neither it nor `setuptools` are pinned in `environment.yml`.
- There is no C compiler/Cython in the env, so Brian2 prints a warning and falls back to the slower numpy code-generation target. Simulations still run correctly, just slower.
- `test_run.py` and several `perturbation/` scripts reference a `Drosophila_brain_model/` directory that does not exist; the actual connectome inputs are at the repo root (e.g. `2023_03_23_completeness_630_final.csv`, `2023_03_23_connectivity_630_final.parquet`). Point `path_comp`/`path_con` at the repo-root files to run a simulation. A single 200 ms, 1-trial sugar run over the 630 materialization (127,400 neurons, ~14.7M synapses) finishes in a few seconds and writes a spike-table parquet.
- `tests/test_targeted_validation_receipt.py::test_rejects_summary_path_not_declared_as_the_parsed_artifact` currently fails on `main` (an assertion/message mismatch unrelated to the environment); the CI subset itself is green.