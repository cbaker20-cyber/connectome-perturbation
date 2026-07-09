# CHANGELOG_AI.md

AI-maintained project changelog. Human review is still required before scientific interpretation.

## 2026-07-09 — Output writer path boundary hardening

- Updated `tools/write_output_manifest.py` so `--config`, `--input-manifest`, and `--output` must be repo-relative paths that stay inside the repository.
- Added regression coverage for absolute output paths and parent-directory output escapes.
- This aligns output-manifest creation with the stricter validator boundary rules, preventing smoke commands from writing outside the repo or recording paths the validator would later reject.

## 2026-07-09 — Output manifest reference validation

- Updated `tools/validate_reproducibility.py` so `output_manifest.json` validates its recorded `input_manifest_path` as a repo-relative path.
- The CLI now passes the validated input-manifest path into output-manifest validation so stale outputs generated from a different manifest can be rejected.
- Added regression tests for absolute output `input_manifest_path` values and mismatched validated input-manifest references.

## 2026-07-09 — Manifest path boundary validation

- Updated `tools/validate_reproducibility.py` so manifest-controlled paths must be repo-relative and cannot be absolute paths or `..` escapes outside the repository.
- Added regression tests for parent-directory input paths and absolute output config paths.
- This keeps smoke/provenance validation from silently reading arbitrary local files when manifests are hand-edited or stale.

## 2026-07-09 — Config checksum validation

- Updated `tools/write_output_manifest.py` to record `config_sha256` for the smoke config referenced by `config_path`.
- Updated `tools/validate_reproducibility.py` to require `config_sha256` and reject output manifests whose recorded config checksum does not match the current config file contents.
- Added regression coverage so a stale `output_manifest.json` cannot silently pass after `configs/smoke_run.yaml` changes.

## 2026-07-09 — Manifest validation hardening

- Updated `tools/validate_reproducibility.py` so `data/input_manifest.json` must include top-level schema fields: `schema_version`, `generated_at_utc`, `input_count`, and `inputs`.
- Added timezone-aware ISO-8601 validation for `input_manifest.generated_at_utc`, matching the existing output-manifest timestamp gate.
- This prevents a stale or hand-edited input manifest without auditable generation time from passing the metadata smoke validator.

## 2026-07-09 — Perturbation manifest resolver wiring

- Updated `perturbation/analyze.py` so `compare_to_baseline` and `load_firing_rates` accept a custom results directory instead of silently reading only `results/`.
- Updated `perturbation/perturb.py` so perturbation smoke sweeps resolve completeness/connectivity inputs through `data/input_manifest.json` using the same manifest IDs as baseline.
- Removed the broken dependency on `PATH_COMP`, `PATH_CON`, and `PATH_RES` exports that no longer exist after baseline manifest migration.
- Added CLI flags for manifest/input IDs/results directory/trial count so a smoke perturbation run can stay tied to manifest-resolved inputs.

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
