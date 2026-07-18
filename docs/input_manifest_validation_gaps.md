# Input manifest validation gaps

This note records validation rules for the input manifest identity contract. Rules marked **implemented** are enforced by `tools/validate_reproducibility.py` and covered by focused tests in CI.

## Implemented guarantees

`tools/validate_reproducibility.py` currently checks that each input path is repo-relative, remains inside the repository after resolution, exists, and matches the recorded byte size and SHA-256 digest. It also checks manifest counts, the presence of provenance fields, basename/extension alignment, canonical lowercase SHA-256 digests, non-negative integer sizes, duplicate literal paths, and duplicate resolved paths (including `.` / `..` normalization).

Focused regression tests live in:

- `tests/test_input_manifest_record_validation.py`
- `tests/test_build_input_manifest.py`
- `tests/test_manifest_path_boundaries.py`

## Remaining follow-ups

1. **Symlink alias detection (platform-dependent):** reject two manifest rows that resolve to the same file through symlinks. Add tests only where the CI platform supports symlink creation.
2. **Conflicting facts on duplicate paths:** if the same manifest path appears twice with mismatched checksum, size, role, materialization, or provenance, reject before merge. Today duplicate paths are rejected outright; a merge-time overlay tool may need stricter conflict reporting.
3. **Claim-ready provenance:** `python tools/validate_reproducibility.py --require-provenance` should gate biological interpretation once source-backed fields are filled in `data/input_manifest.json`.

## Regression matrix (implemented)

The following rejection cases are covered:

- a valid file recorded with a different `filename`;
- `.csv` content recorded with a mismatched `extension` field;
- uppercase, short, or non-hex SHA-256 strings;
- negative, floating-point, boolean, or string `size_bytes` values;
- duplicate literal paths;
- distinct relative paths that resolve to the same canonical file;
- acceptance with two distinct, valid repo-relative files.

## Implementation constraint

Canonical-path duplicate detection occurs after repository-boundary resolution and before checksum comparison. Error messages identify both record indexes and the original manifest paths.

The committed `data/input_manifest.json` is validated in CI with `python tools/validate_reproducibility.py --skip-output-manifest`. Until authoritative provenance is filled, the manifest should be described as checksum-bearing metadata, not as a complete dataset identity contract for biological claims.
