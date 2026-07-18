# TASKS.md

Prioritized backlog for the connectome perturbation project.

## P0 — Reproducibility spine

- [x] Run `python tools/build_input_manifest.py` and review `data/input_manifest.json`.
  - Committed manifest records five tracked connectome-like inputs (630/783 completeness and connectivity tables plus `flywire_annotations.tsv`) with SHA-256 checksums, guessed roles/materializations, and explicit `validation_status: checksum_recorded_provenance_missing`.
  - Project registry/ledger CSVs are excluded from the builder so they are not mistaken for simulation inputs.
- [ ] Fill authoritative provenance fields for every input-like file: dataset name, materialization, URL/DOI, citation, license, access date, schema notes, and redistribution status.
- [ ] Run the artifact-producing metadata smoke sequence:
  - `python tools/build_input_manifest.py`
  - `python tools/write_smoke_artifact.py --output results/reproducibility_smoke_artifact.json`
  - `python tools/write_output_manifest.py --config configs/smoke_run.yaml --input-manifest data/input_manifest.json --output output_manifest.json --artifact results/reproducibility_smoke_artifact.json`
  - `python tools/validate_reproducibility.py`
- [ ] Run the toy graph artifact sequence:
  - `python tools/write_toy_graph_artifact.py --output results/toy_graph_artifact.json`
  - `python tools/write_output_manifest.py --config configs/smoke_run.yaml --input-manifest data/input_manifest.json --output output_manifest.json --artifact results/toy_graph_artifact.json`
  - `python tools/validate_reproducibility.py`
- [x] Validate declared output artifact metadata shape before treating output manifests as reproducible evidence.
  - Declared output paths must stay repo-relative.
  - Optional declared output `sha256` values must be canonical lowercase 64-character SHA-256 digests.
  - Optional declared output `size_bytes` values must be non-negative integers.
  - Declared output files, checksums, and sizes are compared against disk when present.
- [x] Let the output-manifest writer record real output artifacts with fresh checksums.
  - `tools/write_output_manifest.py --artifact <repo-relative-file>` records `path`, `sha256`, and `size_bytes` from disk.
  - Missing artifacts, directories, absolute paths, and parent-directory escapes fail before the manifest is written.
  - The writer intentionally requires explicit artifact paths so stale files are not auto-discovered and silently blessed.
- [x] Wire a deterministic smoke command to produce an artifact, write it with `--artifact`, and immediately validate it.
  - `tools/write_smoke_artifact.py` writes `results/reproducibility_smoke_artifact.json` by default.
  - The artifact is deterministic metadata-only JSON with `claim_status: not_interpretable_as_neuroscience`.
  - README and `docs/output_artifact_validation_contract.md` now show the exact create → declare → validate sequence.
- [x] Replace the metadata-only smoke artifact with a tiny deterministic toy-fixture graph analysis artifact with known expected outcomes.
  - `tools/write_toy_graph_artifact.py` writes `results/toy_graph_artifact.json` by default.
  - The artifact contains a four-node directed fixture graph with expected node count, edge count, degree maps, reachability, and weak component count.
  - The artifact is explicitly marked `not_interpretable_as_neuroscience` so it validates analysis plumbing without making biological claims.
- [x] Promote toy graph expected-outcomes logic into reusable graph-analysis fixtures.
  - `connectome_analysis/graph_metrics.py` now owns degree, reachability, weak-component, and expected-metric helpers.
  - `tools/write_toy_graph_artifact.py` uses the shared helper instead of carrying one-off metric code.
  - `tests/test_graph_metrics.py` pins fixture metrics and rejects unknown edge endpoints before real-data integration.
- [~] Add 64-bit-safe neuron/root ID validation without numeric coercion.
  - PR #23 adds strict decimal-string validation, deterministic aggregate reports, repository-boundary/source-overwrite protection, and explicit original-text provenance states.
  - GitHub Actions run `29199342883` passed on exact implementation head `b9091a0910c7cdfea8bbebc8c49a0135b9cea536`; PR review and merge remain outstanding.
  - Real tracked inputs have not been validated, and passing format checks would not establish dataset provenance or biological identity.
- [x] Route baseline and perturbation scripts through `tools/path_resolver.py` instead of hard-coded `Drosophila_brain_model/` paths.
  - `perturbation/baseline.py`, `perturbation/perturb.py`, and `perturbation/analyze.py` resolve 630 completeness/connectivity through `data/input_manifest.json` by exact filename.
  - `perturbation/cell_groups.py`, `perturbation/graph_analysis.py`, and `perturbation/path_analysis.py` now resolve annotations and connectome tables through the shared resolver.
  - `perturbation/statistics.py`, `perturbation/motor_analysis.py`, `perturbation/sweep_cell_class.py`, and `test_run.py` no longer insert `Drosophila_brain_model` on `sys.path`.
  - `tools/path_resolver.py` preserves backwards compatibility via legacy `Drosophila_brain_model/<basename>` fallback when a manifest entry is absent.
  - `tests/test_perturbation_path_migration.py` covers resolver legacy fallback and each migrated script.
- [ ] Decide whether materialization 630 or 783 is the canonical smoke target; document why.

## P1 — Scientific rigor

- [ ] Define perturbation classes before running experiments: neuron silencing, edge removal/reduction, hub removal, pathway interruption, and random matched controls.
- [ ] Define metrics before running experiments: reachability, connected components, centrality changes, shortest-path disruption, motor-output proxy shifts, and null-model deltas.
- [ ] Add permutation/random-control statistics and multiple-comparison correction.
- [x] Add toy connectome fixtures with known expected outcomes.
  - The current fixture artifact is intentionally synthetic and now uses reusable graph-metric helpers before real connectome runs are interpreted.
- [ ] Use reusable graph-metric helpers to test baseline/perturbation metric code on toy fixtures before real connectome inputs.
- [ ] Add schema checks for connectivity and completeness tables.

## P2 — Architecture cleanup

- [ ] Remove direct `sys.path.insert` calls where possible.
- [ ] Move configuration constants out of scripts and into config files.
- [ ] Add a single CLI entry point for smoke runs.
- [ ] Separate graph analysis, Brian2 simulation, and run-manifest code.

## P3 — Documentation and presentation

- [ ] Convert literature notes into a cited background section.
- [ ] Add a figure/table plan with required manifest links for every figure.
- [ ] Add a conservative project status page for mentors/judges.
- [x] Maintain a claim ledger that labels every statement as verified, assumed, hypothesis, future work, or blocked.
  - Added `docs/claim_ledger.md` with promotion rules and report-writing guardrails.

## Current blockers

- Authoritative provenance for tracked data files is missing.
- Existing result CSV is not tied to a command, config, seed, commit, or input checksums.
- The current toy graph artifact validates deterministic graph-analysis plumbing only; it is not evidence for any neuroscience claim.
- Some older scripts still contain historical path assumptions and need audit before use.
- Open PRs already contain overlapping scaffolding; merge order should be reviewed before large refactors.
