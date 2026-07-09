# Output artifact validation contract

This note defines the next strict validation boundary for `output_manifest.json` declared outputs. It is intentionally limited to reproducibility/provenance plumbing and does not make biological claims.

## Scope

`tools/validate_reproducibility.py` currently validates optional `output_manifest.outputs` records when they exist: paths must remain repo-relative, declared output files must exist, and declared `sha256` / `size_bytes` values must match disk.

The next implementation step should harden the *shape* of those declared facts before comparing them to disk.

## Contract

For every record in `output_manifest.outputs`:

- `path` must be a non-empty repo-relative string and must not escape the repository.
- If `size_bytes` is present, it must be a non-negative integer.
- If `sha256` is present, it must be a lowercase 64-character hexadecimal SHA-256 digest.
- If the output path exists, `size_bytes` and `sha256`, when present, must match the file on disk.
- If the output path does not exist, validation should still report malformed `size_bytes` or `sha256` values before returning from that record.

## Regression cases to add

Add tests alongside `tests/test_output_manifest_declared_outputs.py`:

1. A declared output with `sha256: "not-a-digest"` should fail with a clear message such as `output sha256 must be a 64-character lowercase hex digest: results/summary.json`.
2. A declared output with uppercase digest characters should fail. This keeps manifest hashes canonical and avoids accidental mixed-format reports.
3. A declared output with `size_bytes: "12"` should fail because stringified sizes are not reliable numeric provenance.
4. A declared output with `size_bytes: -1` should fail because sizes must be non-negative.
5. A missing declared output path with malformed `sha256` should report both the missing-path error and the malformed-digest error.

## Suggested implementation sketch

Add a helper in `tools/validate_reproducibility.py`:

```python
def is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)
```

Then check declared output metadata shape inside `validate_declared_outputs()` before the file-existence early return.

This should be the next small code patch because it closes a reproducibility loophole without requiring any FlyWire data access, simulation output, or biological interpretation.
