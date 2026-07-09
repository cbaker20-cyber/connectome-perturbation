# CHANGELOG_AI.md

AI-maintained project changelog. Human review is still required before scientific interpretation.

## 2026-07-09 — Baseline manifest resolver wiring

- Updated `perturbation/baseline.py` so the baseline sugar experiment resolves the 630 completeness/connectivity files through `data/input_manifest.json` by exact filename instead of directly hard-coding `Drosophila_brain_model/...` input paths.
- Added CLI flags for `--manifest`, `--completeness-id`, `--connectivity-id`, `--results-dir`, and `--force` so future smoke/validation runs can be tied to manifest records.
- Updated `TASKS.md` to mark path-resolver migration as partially complete; remaining perturbation scripts still need migration.

## 2026-07-09 — Reproducibility spine branch

- Added `AGENTS.md` with repository rules for AI/human contributors.
- Added `TASKS.md` with a prioritized backlog focused on provenance, manifests, path resolution, smoke execution, and validation.
- Added tooling plan files in this branch to support input and output manifests without deleting or rewriting existing data/results.
- Confirmed current status from existing docs: the project is not yet ready for biological claims because tracked inputs and outputs lack complete provenance and run manifests.

## Standing note

A change appearing here means it was proposed or created by an AI-assisted workflow. It does not mean the change has been scientifically validated.
