# FlyWire and Drosophila connectome source notes

This file is a starting point for source-backed provenance. It is not a complete literature review and does not certify that the tracked local files came from these sources.

## High-confidence background facts to verify against primary papers

- The FlyWire adult fly brain connectome was published in a Nature collection in October 2024.
- Contemporary coverage reports approximately 139,255 neurons and roughly 50 to 54.5 million synaptic connections for the adult fly brain connectome.
- The repository's local files named with materialization-style identifiers (`630`, `783`) must not be treated as authoritative until they are tied to exact download/API provenance, schema, license, and access date.

## Provenance fields still needed for each tracked file

For each local input-like file, fill:

- authoritative dataset name;
- release or materialization;
- canonical download URL or DOI;
- citation;
- license or terms of use;
- access date;
- row count and schema;
- filtering/preprocessing notes;
- redistribution status.

## Candidate source categories to investigate

1. FlyWire Codex / Codex downloads and APIs.
2. FlyWire Consortium Nature 2024 collection.
3. FAFB/FlyWire data access documentation.
4. Hemibrain comparison papers and annotations if used for cell typing.
5. Virtual Fly Brain/FlyBase identifiers if used for anatomical names.

## Method notes for project design

The first scientifically defensible project should avoid claiming behavior from the existing Brian2 outputs. A safer sequence is:

1. Validate data provenance and schema.
2. Build a graph-only perturbation smoke test on a toy fixture.
3. Predefine perturbations and null controls.
4. Run matched random controls.
5. Report only graph-level hypotheses unless a biological validation source supports interpretation.

## Immediate literature tasks

- Find the exact DOI and citation format for the FlyWire Nature connectome paper/collection.
- Identify whether local files map to Codex/materialization 630 or 783 downloads.
- Determine whether redistribution of local parquet/CSV/TSV files is allowed.
- Record the access date and source URL for every local input file in `data/input_manifest.json`.
