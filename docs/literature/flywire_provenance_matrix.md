# FlyWire provenance matrix

This is a source-tracking artifact for turning the current metadata-first reproducibility spine into a scientifically auditable FLY connectome project. It intentionally separates verified project metadata from candidate external sources; do not treat any local input file as biologically interpretable until every row below is completed from the exact download/API source used.

## Current repo state

PR #17 adds the manifest/checksum/path/output validation spine and has a passing GitHub Actions workflow for reproducibility tooling. The next scientific blocker is not code plumbing; it is mapping each local file to authoritative provenance.

## Candidate source references to verify

| Source category | Candidate source | What it can support | What still must be captured |
|---|---|---|---|
| Primary connectome paper | Dorkenwald et al., "Neuronal wiring diagram of an adult brain," Nature, published October 2024 | Adult Drosophila brain connectome background; reported whole-brain scale; source citation for project background | DOI, exact citation, data-availability statement, license/terms, whether this paper is the source of the local files |
| FlyWire/Codex data portal | FlyWire Codex downloads/API | Exact neuron, synapse, annotation, and materialization-specific tables | Download URL/API endpoint, materialization ID, access date, schema, row counts, filters, redistribution terms |
| Annotation/cell typing paper | Schlegel et al., "Whole-brain annotation and multi-connectome cell typing of Drosophila," Nature, published October 2024 | Cell-type and annotation provenance if used for biologically meaningful group perturbations | DOI, exact table names, version/materialization, terms, citation |
| Prior benchmark/contrast dataset | Scheffer et al., "A connectome and analysis of the adult Drosophila central brain," eLife, 2020 | Hemibrain comparison/background only, unless repo uses hemibrain identifiers | Whether any local IDs are hemibrain-derived; mapping table provenance |

## Required row schema for `data/input_manifest.json`

For every local input-like file, fill or preserve these fields:

- `path`
- `sha256`
- `size_bytes`
- `guessed_role`
- `authoritative_dataset_name`
- `release_or_materialization`
- `canonical_source_url`
- `doi_or_citation`
- `license_or_terms`
- `access_date`
- `row_count`
- `schema`
- `filters_or_preprocessing`
- `redistribution_status`
- `notes`

## Validation gates before biological claims

A run can be called a reproducible technical smoke only when:

1. `python tools/build_input_manifest.py` records stable paths, sizes, and SHA-256 checksums.
2. `python tools/write_output_manifest.py --config configs/smoke_run.yaml --output output_manifest.json` writes a conservative output manifest.
3. `python tools/validate_reproducibility.py` passes.
4. `output_manifest.json` keeps `claim_status` as `not_interpretable_as_neuroscience` unless provenance and controls are complete.

A run can be called a biologically interpretable experiment only when:

1. Every input file has authoritative source URL, materialization/release, citation/DOI, access date, schema, row count, and license/terms.
2. Perturbation targets are defined before running, with a matching null/control family.
3. The analysis reports graph-level outcomes first and only makes neuron/circuit claims when supported by source-backed annotations.
4. Outputs include the exact input manifest checksums used for that run.

## Immediate next implementation task

Add a `--require-provenance` option to `tools/validate_reproducibility.py` that fails if any input manifest row lacks source URL, release/materialization, citation/DOI, access date, row count, schema, or license/terms. Keep the default validator permissive so PR #17 remains useful before the real source rows are filled.
