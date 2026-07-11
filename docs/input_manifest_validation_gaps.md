# Input manifest validation gaps

This note records validation rules that are required before the input manifest can be treated as a reliable identity boundary. It does not assert that current datasets satisfy them.

## Current guarantees

`tools/validate_reproducibility.py` currently checks that each input path is repo-relative, remains inside the repository after resolution, exists, and matches the recorded byte size and SHA-256 digest. It also checks manifest counts and the presence of provenance fields.

## Remaining high-priority rules

The validator should reject a record when any of the following is true:

1. `filename` is not exactly `Path(path).name`.
2. `extension` is not exactly `Path(path).suffix`.
3. `sha256` is not a canonical 64-character lowercase hexadecimal digest, even when the file is missing or inaccessible.
4. `size_bytes` is not a non-negative integer.
5. Two records resolve to the same canonical file, including through `.` / `..` normalization or symlink aliases.
6. Two records reuse the same manifest path with conflicting checksum, size, role, materialization, or provenance facts.

These checks prevent misleading manifests in which checksum facts are attached to the wrong filename, duplicate aliases inflate `input_count`, or malformed metadata survives until a later run.

## Minimal regression matrix

Add focused tests that prove rejection of:

- a valid file recorded with a different `filename`;
- `.csv` content recorded with a mismatched `extension` field;
- uppercase, short, or non-hex SHA-256 strings;
- negative, floating-point, boolean, or string `size_bytes` values;
- duplicate literal paths;
- distinct relative paths that resolve to the same canonical file.

Also retain one acceptance test with two distinct, valid repo-relative files so duplicate detection cannot accidentally reject normal multi-input manifests.

## Implementation constraint

Canonical-path duplicate detection must occur after repository-boundary resolution and before checksum comparison. Error messages should identify both record indexes and the original manifest paths. Symlink behavior should be tested only where the test platform supports symlink creation; literal and normalized duplicate-path tests must remain platform-independent.

Until these rules are implemented and pass GitHub Actions, the manifest should be described as checksum-bearing metadata, not as a complete dataset identity contract.
