# TASKS.md

Prioritized backlog for the connectome perturbation project.

## P0 — Reproducibility spine

- [ ] Run `python tools/build_input_manifest.py` and review `data/input_manifest.json`.
- [ ] Fill authoritative provenance fields for every input-like file: dataset name, materialization, URL/DOI, citation, license, access date, schema notes, and redistribution status.
- [ ] Run `python tools/write_output_manifest.py --config configs/smoke_run.yaml --output output_manifest.json`.
- [ ] Run `python tools/validate_reproducibility.py`.
- [x] Validate declared output artifact metadata shape before treating output manifests as reproducible evidence.
  - Declared output paths must stay repo-relative.
  - Optional declared output `sha256` values must be canonical lowercase 64-character SHA-256 digests.
  - Optional declared output `size_bytes` values must be non-negative integers.
  - Declared output files, checksums, and sizes are compared against disk when present.
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
- [ ] Add schema checks for connectivity and completeness tables.
- [ ] Add toy connectome fixtures with known expected outcomes.

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
- Some older scripts still contain historical path assumptions and need audit before use.
- Open PRs already contain overlapping scaffolding; merge order should be reviewed before large refactors.