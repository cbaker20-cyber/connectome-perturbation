# ROADMAP.md

Reproducibility-first engineering roadmap. Scientific methods and biological conclusions are out of scope for these items.

Last updated: 2026-07-18

## Completed

| Priority | Item | Status |
|---|---|---|
| P0 | Committed `data/input_manifest.json` with SHA-256 checksums | done (#46) |
| P0 | Route perturbation scripts through `tools/path_resolver.py` | done (#47) |
| P0 | Document materialization 630 vs 783; canonical smoke target | done (#48) |
| P0 | Validate `configs/smoke_run.yaml` in CI | done (#49) |
| P0 | Bind output manifests to run config, environment, commit when outputs declared | done (#50) |
| P0 | Validate research documentation pack in CI | done (this branch) |

| P0 | Authoritative input provenance in registry + CI `--require-provenance` | done (this branch) |

## P0 — Next reproducibility spine

1. **Experiment registry binding** — Connect `03_EXPERIMENT_REGISTRY.csv` entries to `output_manifest.json` and commit hash.
2. **Enforce minimum_claim_standard** — Validate experiment rows against `docs_config.yaml` trial-count and FDR rules.
3. **Notebook path migration** — Route `example.ipynb` and `figures.ipynb` through the resolver or document per-cell materialization.
3. **Results output resolver** — Replace hard-coded `results/` paths in statistics/motor/visualize scripts with a configurable output root.
4. **Toy graph CI sequence** — Add the toy graph artifact → output manifest → validate path to CI alongside the metadata smoke path.

## P1 — Scientific rigor (metadata only)

- Schema checks for connectivity and completeness tables.
- Permutation/null-control statistics (no method changes without explicit review).
- Experiment registry entries bound to commit hash and output manifest.

## P2 — Architecture

- Single CLI entry point for smoke runs.
- Remove remaining `sys.path.insert` calls where practical.
- Separate graph analysis, Brian2 simulation, and manifest code.

## Blockers (do not bypass)

- Experiment registry entries and legacy notebook outputs are not yet bound to output manifests.
- `baseline.py` (5 trials) vs `model.py` (30 trials) trial-count mismatch must be stated per output.
