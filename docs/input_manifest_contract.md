# Input manifest identity contract

This document defines the minimum identity and integrity rules for `data/input_manifest.json`. It is a reproducibility contract, not evidence that an input is authoritative or biologically valid.

## Record identity

Each entry in `inputs` represents one physical input file in the repository checkout used for a run.

- `path` is the canonical identity key. It must be a non-empty, POSIX-style, repository-relative path that resolves inside the repository root.
- Resolved `path` values must be unique. Repeating the same file under two rows inflates `input_count` and can duplicate downstream checksum records without adding an independent input.
- `filename` must equal the basename of `path`.
- `extension` must equal the lowercase suffix of `path`.
- Symlink aliases must not be used to register the same resolved file more than once.

## Integrity facts

For every record:

- `size_bytes` is a non-negative integer matching the file on disk.
- `sha256` is exactly 64 lowercase hexadecimal characters and matches the file bytes.
- `input_count` equals the number of records in `inputs`.
- The manifest timestamp includes an explicit timezone.

Checksums establish byte identity only. They do not establish provenance, correctness, licensing, completeness, or suitability for a scientific claim.

## Provenance separation

Every input retains the full provenance object even when values are unknown. Missing source facts must remain explicit rather than being inferred from filenames. Claim-ready validation should require source-backed values for dataset/release identity, canonical URL or DOI, citation, license or terms, access date, redistribution status, schema, row count, and preprocessing.

## Output propagation

An output manifest derived from an input manifest must preserve, in the same order:

- each canonical input `path`;
- each `sha256`;
- each `size_bytes`;
- the exact input count;
- the repository-relative path of the input manifest used.

A changed input manifest therefore requires regeneration of the output manifest. Hand-editing copied checksum rows is not an acceptable substitute.

## Validation follow-up

The validator should reject duplicate resolved input paths, malformed checksum/size facts, basename or extension drift, and symlink aliases. Each rejection should have a focused regression test before the rule is relied on as a merge gate.

Materialization selection is documented in `docs/materialization-policy.md`. Scripts should pass exact filenames or call `resolve_materialization_inputs()`; bare role or materialization identifiers such as `connectivity_table` or `630` are ambiguous when both 630 and 783 tables are present.
