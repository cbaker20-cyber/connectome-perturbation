# Data Policy

## Purpose

This policy prevents accidental publication of private material, oversized data, and outputs that lack provenance. It does not certify any tracked file as scientifically valid or legally redistributable.

## Current tracked-data audit

The following large files were already tracked when this policy was written:

| Path | Git object size | Status |
|---|---:|---|
| `Connectivity_783.parquet` | 100,804,642 bytes | Existing input-like artifact; source, license, checksum, and use are not confirmed. |
| `2023_03_23_connectivity_630_final.parquet` | 86,630,944 bytes | Existing input-like artifact referenced by notebooks/scripts; authoritative provenance is missing. |
| `flywire_annotations.tsv` | 32,638,576 bytes | Existing annotation-like artifact; exact release and redistribution terms need confirmation. |
| `Completeness_783.csv` | 3,327,347 bytes | Existing input-like artifact; use is not confirmed. |
| `2023_03_23_completeness_630_final.csv` | 3,057,611 bytes | Existing input-like artifact referenced by notebooks/scripts. |

This audit is descriptive. Do not delete, replace, or republish these files until ownership, source, license, and downstream dependencies are reviewed.

## Never commit

- Secrets, tokens, credentials, `.env` files, or cloud configuration containing real values.
- Private student, participant, health, contact, or account data.
- Raw notes that identify private people or contain confidential correspondence.
- Virtual environments, caches, temporary files, raw simulation dumps, or generated notebook output.
- New large datasets or derived files without explicit human approval and a documented license.
- Files whose redistribution rights are unknown.

The two tracked copies of `source_material/raw_lab_notebook_pasted_text.txt` require a human privacy and copyright review before this repository is promoted or mirrored. This policy makes no assertion about their contents.

## Conditionally acceptable

- Small synthetic fixtures created for tests.
- Source code and documentation without embedded data or secrets.
- Small aggregate outputs only when a manifest ties them to inputs, code, parameters, and validation.
- Dataset manifests containing public metadata, checksums, and source links, but not access tokens or private URLs.

## Neuron and root identifier safety

Neuron/root IDs are opaque identifiers, not numeric measurements. Preserve them as exact decimal strings from ingestion through reports. Do not parse them through floating-point types, normalize away leading zeroes, accept scientific notation, or silently coerce integer-valued fields into strings after parsing.

`tools/validate_neuron_ids.py` checks this representation contract without modifying the source file. Optional original-text provenance must be compared byte-for-byte as strings. A differing valid original value is classified as `suspected_precision_loss`; explicitly unavailable original text is `unverified_precision`; malformed or contradictory provenance is invalid. Reports must remain inside the repository and must not overwrite their input.

A passing identifier report demonstrates only representation integrity for the checked file and column under the declared provenance evidence. It does not establish authoritative dataset provenance, materialization membership, correct biological identity, or any neuroscience conclusion. Real tracked datasets remain unverified until a committed validator version is run against reviewed local inputs and the resulting report is reviewed with the input manifest.

## Required input manifest fields

Before an input is used for a reported run, record:

- local filename and role;
- authoritative dataset name and release/materialization;
- canonical URL or DOI and citation;
- license or redistribution terms;
- access date;
- byte size and SHA-256 checksum;
- table schema and row count;
- any filtering or preprocessing;
- whether the file may be committed or must remain external.

## Required run manifest fields

Every result intended for interpretation needs the exact input checksums, Git commit, environment file, command, configuration, random seed, trial count, output paths, validation checks, and run date. A CSV without that record is an unexplained artifact.

## Repository behavior

`.gitignore` excludes `results/` except for the existing summary CSV, as well as virtual environments and `__pycache__`. That exception does not validate the summary. Future generated results should remain untracked until the data owner approves a specific small artifact and its manifest.
