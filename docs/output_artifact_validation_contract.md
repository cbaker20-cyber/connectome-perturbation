# Output artifact validation contract

This note defines the strict validation boundary for `output_manifest.json` declared outputs. It is intentionally limited to reproducibility/provenance plumbing and does not make biological claims.

## Status

Implemented on the reproducibility branch:

- `tools/validate_reproducibility.py` validates declared output paths, existence, canonical metadata shape, and on-disk checksum/size matches.
- `tests/test_output_manifest_declared_outputs.py` covers matching declared outputs, path escapes, stale digests, malformed digests, uppercase digests, string sizes, negative sizes, and missing outputs with malformed digests.

## Scope

`tools/validate_reproducibility.py` validates optional `output_manifest.outputs` records when they exist: paths must remain repo-relative, declared output files must exist, declared `sha256` / `size_bytes` metadata must have canonical shape, and declared metadata values must match disk.

## Contract

For every record in `output_manifest.outputs`:

- `path` must be a non-empty repo-relative string and must not escape the repository.
- If `size_bytes` is present, it must be a non-negative integer.
- If `sha256` is present, it must be a lowercase 64-character hexadecimal SHA-256 digest.
- If the output path exists, `size_bytes` and `sha256`, when present, must match the file on disk.
- If the output path does not exist, validation still reports malformed `size_bytes` or `sha256` values before returning from that record.

## Regression cases covered

Tests alongside `tests/test_output_manifest_declared_outputs.py` cover:

1. A declared output with `sha256: "not-a-digest"` fails with `output sha256 must be a 64-character lowercase hex digest: results/summary.json`.
2. Uppercase digest characters fail, keeping manifest hashes canonical and avoiding accidental mixed-format reports.
3. A declared output with `size_bytes: "12"` fails because stringified sizes are not reliable numeric provenance.
4. A declared output with `size_bytes: -1` fails because sizes must be non-negative.
5. A missing declared output path with malformed `sha256` reports both the missing-path error and the malformed-digest error.

## Remaining next step

The next hardening layer is wiring declared-output generation into the actual smoke/execution command, so real pipeline outputs are written, checksummed, recorded in `output_manifest.json`, and immediately validated in one reproducible command.