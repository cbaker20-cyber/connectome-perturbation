# CHANGELOG_AI.md

AI-maintained project changelog. Human review is still required before scientific interpretation.

## 2026-07-09 — Deterministic smoke artifact path

- Added `tools/write_smoke_artifact.py` to create `results/reproducibility_smoke_artifact.json`, a deterministic metadata-only artifact for testing output declaration and validation plumbing.
- Added regression coverage in `tests/test_write_smoke_artifact.py` for conservative payload contents, deterministic JSON bytes, absolute output rejection, and parent-directory escape rejection.
- Updated the README smoke command so the reproducibility path now creates an artifact, records it with `tools/write_output_manifest.py --artifact`, and validates it with `tools/validate_reproducibility.py`.
- Updated `docs/output_artifact_validation_contract.md` and `TASKS.md` to mark the create → declare → validate metadata smoke path as implemented and name the next target: a toy-fixture graph artifact with known expected outcomes.

## 2026-07-09 — Output artifact writer support

- Updated `tools/write_output_manifest.py` so smoke/reproduction runs can record real output files with repeated `--artifact <repo-relative-file>` flags.
- Writer-created output records now include `path`, `sha256`, and `size_bytes` computed from the artifact currently on disk.
- The writer now rejects missing artifacts, directories, absolute artifact paths, and parent-directory escapes before writing `output_manifest.json`.
- Added regression coverage for artifact recording, missing artifacts, and artifact path escapes.
- Updated `docs/output_artifact_validation_contract.md` and `TASKS.md` to make the next step explicit: wire a deterministic smoke command to produce, record, and validate an artifact in one reproducible path.

## 2026-07-09 — Declared output metadata shape hardening

- Updated `tools/validate_reproducibility.py` so declared `output_manifest.outputs` metadata must use canonical types before disk comparison.
- Declared output `sha256` values, when present, must now be lowercase 64-character hexadecimal SHA-256 digests.
- Declared output `size_bytes` values, when present, must now be non-negative integers rather than stringified or negative values.
- Added regression coverage for malformed digests, uppercase digests, string sizes, negative sizes, and missing outputs with malformed digests.

## 2026-07-09 — Conservative claim ledger

- Added `docs/claim_ledger.md` to separate verified repository facts from assumptions, hypotheses, future work, and blocked claims.
- Added promotion rules requiring rerunnable commands, manifests/checksums, passing tests, source citations, or committed experiment artifacts before project statements can be treated as verified.
- Added report-writing guardrails so early project summaries do not overclaim biological significance before validated experiments exist.
- Updated `TASKS.md` to mark the claim-ledger documentation task as started/completed for the current reproducibility PR.

## 2026-07-09 — Declared output artifact validation

- Updated `tools/validate_reproducibility.py` so optional `output_manifest.outputs` records are validated when present.
- Declared output artifact paths must now be repo-relative and stay inside the repository.
- If a declared output record includes `sha256` or `size_bytes`, validation now checks those facts against the file on disk.
- Added regression coverage for matching declared outputs, path escapes, and stale output digests.

## 2026-07-09 — Output writer malformed input-manifest hardening

- Updated `tools/write_output_manifest.py` so malformed `input_manifest.inputs` values cannot crash metadata writing.
- The writer now copies checksum records only from safely inspectable object records and leaves full schema rejection to `tools/validate_reproducibility.py`.
- Added regression coverage for non-list `inputs`, non-object input records, and non-integer `input_count` values.

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