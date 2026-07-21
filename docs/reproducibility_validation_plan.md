# Reproducibility validation plan

This note records the next test targets for PR #17. It is intentionally metadata-first: these checks do not claim that any connectome result is biologically valid.

## Priority tests

1. `tools/build_input_manifest.py`
   - Create a temporary CSV such as `connectivity_630.csv`.
   - Assert the manifest record includes the relative path, file size, SHA-256, guessed role `connectivity_table`, guessed materialization `630`, and empty source-backed provenance fields.
   - Assert files under `results/`, `.git/`, `.venv/`, and `__pycache__/` are not included.

2. `tools/path_resolver.py`
   - Resolve by exact path and filename from a tiny temporary `data/input_manifest.json`.
   - Assert ambiguous identifiers such as a shared role or materialization raise `ValueError` instead of silently selecting one file.
   - Assert missing identifiers raise `FileNotFoundError`.

3. `tools/validate_reproducibility.py`
   - Assert checksum or size drift in an input file produces a validation error.
   - Assert `input_count` mismatches are caught.
   - Assert missing required output-manifest fields are caught.
   - Assert smoke output manifests must keep `claim_status` as `not_interpretable_as_neuroscience`.

4. `tools/write_output_manifest.py`
   - Build an output manifest from a tiny input manifest.
   - Assert the config path, input manifest path, command, status, commit field, input checksums, and conservative claim status are present.

## Suggested local command

```bash
python tools/build_input_manifest.py
python tools/write_output_manifest.py --config configs/smoke_run.yaml --output output_manifest.json
python tools/validate_reproducibility.py
python -m pytest tests/test_reproducibility_tools.py -q
```

## Acceptance criteria

- PR #17 has at least one test file covering the metadata tools.
- Validation fails loudly on stale checksums, ambiguous path resolution, and non-conservative smoke claim status.
- No test requires large FlyWire data or network access.
