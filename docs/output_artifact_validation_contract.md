# Output artifact validation contract

This note defines the strict validation boundary for `output_manifest.json` declared outputs. It is intentionally limited to reproducibility/provenance plumbing and does not make biological claims.

## Status

Implemented on the reproducibility branch:

- `tools/write_smoke_artifact.py` creates a deterministic metadata-only artifact at `results/reproducibility_smoke_artifact.json` by default.
- `tools/write_output_manifest.py` can record one or more real output artifacts with `--artifact <repo-relative-path>`.
- Writer-created artifact records are populated from disk with `path`, `sha256`, and `size_bytes`.
- The writer rejects missing artifacts, directories, absolute artifact paths, and parent-directory escapes before writing the manifest.
- `tools/validate_reproducibility.py` validates declared output paths, existence, canonical metadata shape, and on-disk checksum/size matches.
- `tests/test_write_smoke_artifact.py` covers deterministic smoke artifact payload/content and output path boundaries.
- `tests/test_output_manifest_writer.py` covers artifact recording, missing artifacts, and artifact path escapes.
- `tests/test_output_manifest_declared_outputs.py` covers matching declared outputs, path escapes, stale digests, malformed digests, uppercase digests, string sizes, negative sizes, and missing outputs with malformed digests.

## Scope

`tools/write_smoke_artifact.py` creates a stable artifact for reproducibility plumbing only. It does not run Brian2, inspect connectome files, or make biological claims.

`tools/write_output_manifest.py` records output artifacts only when explicitly named with `--artifact`. It does not discover files automatically, because automatic discovery can accidentally bless stale files from previous runs.

`tools/validate_reproducibility.py` validates optional `output_manifest.outputs` records when they exist: paths must remain repo-relative, declared output files must exist, declared `sha256` / `size_bytes` metadata must have canonical shape, and declared metadata values must match disk.

## End-to-end smoke sequence

```bash
python tools/build_input_manifest.py
python tools/write_smoke_artifact.py --output results/reproducibility_smoke_artifact.json
python tools/write_output_manifest.py \
  --config configs/smoke_run.yaml \
  --input-manifest data/input_manifest.json \
  --output output_manifest.json \
  --artifact results/reproducibility_smoke_artifact.json
python tools/validate_reproducibility.py
```

This sequence should prove that the metadata plumbing can create an artifact, declare it, checksum it, and validate it. It still does not prove any neuroscience result.

## Writer contract

Use one `--artifact` flag for each file produced by a smoke or experiment command:

```bash
python tools/write_output_manifest.py \
  --config configs/smoke_run.yaml \
  --input-manifest data/input_manifest.json \
  --output output_manifest.json \
  --artifact results/reproducibility_smoke_artifact.json
```

For every `--artifact` argument:

- The path must be a non-empty repo-relative string and must not escape the repository.
- The path must already exist before the manifest is written.
- The path must be a regular file, not a directory.
- The writer computes `sha256` and `size_bytes` from the file currently on disk.

## Validator contract

For every record in `output_manifest.outputs`:

- `path` must be a non-empty repo-relative string and must not escape the repository.
- If `size_bytes` is present, it must be a non-negative integer.
- If `sha256` is present, it must be a lowercase 64-character hexadecimal SHA-256 digest.
- If the output path exists, `size_bytes` and `sha256`, when present, must match the file on disk.
- If the output path does not exist, validation still reports malformed `size_bytes` or `sha256` values before returning from that record.

## Regression cases covered

Tests alongside `tests/test_write_smoke_artifact.py` cover:

1. The smoke artifact payload is conservative and stable.
2. The written JSON bytes are deterministic.
3. Absolute and escaping output paths fail before writing.

Tests alongside `tests/test_output_manifest_writer.py` cover:

1. A declared artifact is recorded with fresh `sha256` and `size_bytes` metadata from disk.
2. A missing `--artifact` path fails before manifest writing.
3. An escaping `--artifact ../outside.json` path fails before manifest writing.

Tests alongside `tests/test_output_manifest_declared_outputs.py` cover:

1. A declared output with `sha256: "not-a-digest"` fails with `output sha256 must be a 64-character lowercase hex digest: results/summary.json`.
2. Uppercase digest characters fail, keeping manifest hashes canonical and avoiding accidental mixed-format reports.
3. A declared output with `size_bytes: "12"` fails because stringified sizes are not reliable numeric provenance.
4. A declared output with `size_bytes: -1` fails because sizes must be non-negative.
5. A missing declared output path with malformed `sha256` reports both the missing-path error and the malformed-digest error.

## Remaining next step

The next hardening layer is replacing the metadata-only smoke artifact with a tiny deterministic analysis artifact generated from toy fixtures with known expected graph outcomes.