# FlyWire and Drosophila connectome source notes

This file is a starting point for source-backed provenance. It is not a complete literature review and does not certify that the tracked local files came from these sources.

## Source-backed background facts

- The FlyWire adult fly brain connectome was published as a Nature collection on October 2, 2024.
- Contemporary reporting of the Nature collection describes the adult Drosophila brain dataset as 139,255 neurons and approximately 50-54.5 million synaptic connections.
- The repository's local files named with materialization-style identifiers (`630`, `783`) must not be treated as authoritative until each file is tied to exact download/API provenance, schema, license or terms of use, and access date.

## Candidate primary and secondary source log

| Source | Use in this repo | Notes |
| --- | --- | --- |
| Nature FlyWire collection, `https://www.nature.com/collections/hgcfafejia` | Primary publication family to cite for the 2024 adult fly brain connectome. | Must identify the specific paper(s) used for any claim before writing research text. |
| FlyWire Codex / Codex downloads and APIs | Candidate source for local connectome tables. | Must verify exact dataset, materialization, query/API endpoint, export date, and redistribution rules. |
| Reuters coverage, `https://www.reuters.com/science/scientists-map-fruit-fly-brain-neurobiological-milestone-2024-10-02/` | Secondary sanity check for public-facing counts and project description. | Do not use as the primary scientific citation if the Nature papers are available. |
| Le Monde coverage, `https://www.lemonde.fr/sciences/article/2024/10/03/le-reseau-de-neurones-du-cerveau-d-une-mouche-entierement-cartographie_6342949_1650684.html` | Secondary sanity check for the 139,255 neuron / 54.5 million synapse count and October 2 Nature collection date. | Secondary source only. |
| FT coverage, `https://www.ft.com/content/4e041fd1-7633-44ab-9afd-72cbdfe4e295` | Secondary sanity check for public narrative. | Secondary source only; may be paywalled. |

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

## Local data questions that block scientific claims

These must be answered before any graph metric, Brian2 simulation, perturbation, or neuroscience narrative is treated as interpretable:

1. Which exact source produced each local file in `data/input_manifest.json`?
2. Are identifiers root IDs, supervoxel IDs, cell body IDs, or another ID type?
3. Are IDs preserved as strings throughout the pipeline, avoiding float/scientific-notation corruption?
4. Which materialization or snapshot does each file belong to?
5. Are synapse counts represented as T-bars, postsynaptic partner counts, weighted edges, or pre-aggregated graph weights?
6. Are rows filtered by brain region, neurotransmitter, cell type, confidence, or synapse threshold?
7. Is redistribution of the checked-in local files permitted, or should the repo keep only manifests and download instructions?
8. What row counts and column schemas should validators expect for each canonical input table?

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
