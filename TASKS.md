# TASKS.md

Prioritized backlog for the connectome perturbation project.

## P0 — Reproducibility spine

- [ ] Run `python tools/build_input_manifest.py` and review `data/input_manifest.json`.
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
- [~] Route baseline and perturbation scripts through `tools/path_resolver.py` instead of hard-coded `Drosophila_brain_model/` paths.
  - `perturbation/baseline.py` resolves the 630 completeness/connectivity files through `data/input_manifest.json` by exact filename.
  - `perturbation/perturb.py` now resolves the same inputs through the manifest and no longer imports removed baseline path constants.
  - `perturbation/analyze.py` now accepts a custom results directory so smoke runs are not silently compared against `results/`.
  - Remaining older tools/scripts still need audit before production use.
- [ ] Decide whether materialization 630 or 783 is the canonical smoke target; document why.

## P1 — Scientific rigor

- [ ] Define perturbation classes before running experiments: neuron silencing, edge removal/reduction, hub removal, pathway interruption, and random matched controls.
- [ ] Define metrics before running experiments: reachability, connected components, centrality changes, shortest-path disruption, motor-output proxy shifts, and null-model deltas.
- [ ] Add permutation/random-control statistics and multiple-comparison correction.
- [x] Add toy connectome fixtures with known expected outcomes.
  - The current fixture artifact is intentionally synthetic and should be promoted into reusable graph-analysis tests before real connectome runs are interpreted.
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