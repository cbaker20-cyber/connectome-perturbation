# 08 Data Provenance

Last updated: 2026-06-10

## Local project data files observed

| File | Purpose | Notes |
|---|---|---|
| `2023_03_23_completeness_630_final.csv` | Model neuron/completeness table for FlyWire materialization 630. | Used by baseline/test scripts. |
| `2023_03_23_connectivity_630_final.parquet` | Connectivity table for model runs. | Used by Brian2 model. |
| `Completeness_783.csv` | Later materialization completeness table. | Present locally; not necessarily used by current scripts. |
| `Connectivity_783.parquet` | Later materialization connectivity table. | Present locally; not necessarily used by current scripts. |
| `flywire_annotations.tsv` | FlyWire cell annotations. | Joined to modeled IDs by `cell_groups.py`. |
| `Pasted text.txt` | Raw lab notebook entries. | Copied into `source_material/`. |

## Data versioning requirements

For every analysis, document:

- completeness file path and version/materialization;
- connectivity file path and version/materialization;
- annotation file path, release, and row count;
- exact set of source neurons;
- exact set of perturbation/silenced neurons;
- exact set of target/motor neurons;
- script name and commit hash;
- run date;
- number of trials and trial duration;
- output files.

## Known local counts from notebook

- Modeled neurons: 127,400.
- Local annotation rows: 139,244.
- Annotation/modeled overlap: 106,216 neurons, 83.4% coverage.

## Important warning

Do not assume that the 630 and 783 data files are interchangeable. If switching materialization/version, rerun annotation overlap, group counts, baseline, perturbation outputs, and statistics.
