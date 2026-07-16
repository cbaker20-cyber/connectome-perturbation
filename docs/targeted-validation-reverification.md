# Independent targeted-validation receipt reverification

## Purpose

A stored targeted-validation receipt is only a compact record of checks that were reported as completed. Validating the receipt's JSON schema does not independently prove that the referenced manifest and artifact bytes still exist, still match their recorded digests, or still satisfy the underlying validation gates.

This document defines the minimum fail-closed behavior for an independent re-verifier. It is a reproducibility control, not an experiment and not evidence for any neuroscience claim.

## Required inputs

The re-verifier must receive explicit paths to:

1. the stored receipt JSON;
2. the staged run manifest;
3. the staged run root containing all manifest-declared inputs and outputs.

It must not discover a manifest or run directory by searching for a matching `run_id`.

## Required checks

The re-verifier must fail unless all of the following hold:

1. The receipt parses as UTF-8 JSON and passes the current receipt contract.
2. The manifest parses and passes the current manifest contract.
3. `run_id`, `git_commit`, manifest schema version, and run parameters agree between receipt and manifest.
4. Every manifest-declared artifact path is relative, normalized POSIX, non-escaping, and resolves beneath the supplied staged run root.
5. Every declared input and output exists as a regular file.
6. Every file's byte size and SHA-256 digest match the manifest declarations.
7. The receipt's `summary_path`, `summary_size_bytes`, and `summary_sha256` match both the manifest declaration and the actual summary artifact bytes.
8. The summary CSV is reparsed from the verified bytes using the strict CSV contract.
9. The four-cell semantic checks are rerun from the reparsed rows.
10. The re-verifier recomputes the list of gates it actually executed and requires exact equality with the receipt's `validated_gates` list.

The implementation must stop at the first failed gate with a non-zero exit status and a specific error message. It must not emit a replacement passing receipt after a failed verification.

## Suggested machine-readable result

A successful verification may emit a separate canonical JSON record containing:

- verifier schema version;
- receipt SHA-256;
- manifest SHA-256;
- verified run ID and commit;
- rechecked artifact count;
- exact gate list;
- verification timestamp supplied by the caller or execution environment;
- the same scientific limitations carried by the receipt.

The result must be stored separately from the original receipt so the original evidence record is not overwritten.

## Minimum rejection tests

Tests should use synthetic staged files and prove rejection when:

- the receipt is changed without changing the staged artifacts;
- the manifest is changed after receipt creation;
- any declared input or output byte changes;
- the summary is replaced by a same-size file with a different digest;
- receipt and manifest parameters disagree;
- a manifest path is absolute, traverses with `..`, or uses ambiguous separators;
- a required file is a directory, symlink, or missing file rather than a regular file;
- CSV bytes still hash correctly but violate the strict CSV contract;
- the four required cells are incomplete, duplicated, or semantically invalid;
- the receipt claims a gate the re-verifier did not execute.

## Evidence boundary

Passing independent re-verification would show only that the stored receipt, manifest, and currently staged bytes remain mutually consistent under the repository's implemented contracts. It would not establish parser independence, correctness of upstream FlyWire annotations, simulation validity, biological validity, causality, behavioral relevance, generalization, or regeneration.