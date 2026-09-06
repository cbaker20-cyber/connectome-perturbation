# Infrastructure that is actually used

This is the active scientific stack for the E/I-lesion and context-comparison
project. If a file is not named here or in `docs/PROJECT_HISTORY.md`, it is not
an active experiment entry point.

## Data (do not mix materializations)

| File | Role |
|---|---|
| `2023_03_23_completeness_630_final.csv` | Simulated neuron list, materialization 630 |
| `2023_03_23_connectivity_630_final.parquet` | Directed edges and signed connectivity weight |
| `Completeness_783.csv` / `Connectivity_783.parquet` | Newer materialization; not interchangeable with 630 |
| `flywire_annotations.tsv` | `super_class`, `cell_class`, `cell_type`, and transmitter annotations |
| `data/input_manifest.json` | Input filenames, sizes, SHA-256, and partial provenance |

FlyWire root IDs are opaque decimal strings. Do not parse them through floating
point.

## Simulator (`model.py`)

Brian2 leaky integrate-and-fire model using the Shiu et al. 2024 framework:

- rest/reset −52 mV, threshold −45 mV;
- membrane τ 20 ms, synaptic τ 5 ms;
- refractory 2.2 ms, delay 1.8 ms;
- weight unit 0.275 mV;
- `w = (Excitatory × Connectivity) × 0.275 mV`;
- Poisson sensory drive, normally 150 Hz;
- output lesion: outgoing weights of selected neurons set to zero.

The model contains one `NeuronGroup`; polarity is inherited from the signed
connectivity input and is therefore dependent on transmitter assumptions.

## Perturbation engine (`perturbation/`)

| File | Role |
|---|---|
| `baseline.py` | Sensory IDs and baseline run parameters |
| `perturb.py` | Output silencing and baseline comparison |
| `cell_groups.py` | Annotation-based groups and named polarity maps |
| `statistics.py` | Per-trial motor Hz, Welch tests, and BH-FDR |
| `analyze.py` / `motor_analysis.py` | Motor readout and summaries |
| `graph_analysis.py` / `path_analysis.py` | Earlier structural controls retained for lineage |
| `sweep_cell_class.py` | Early exploratory class sweep retained for history |

## Run scripts

- `scripts/run_ei_lesion_screen.py` — polarity-map screen;
- `scripts/run_sugar_ground_truth_sweep.py` — sugar context;
- `scripts/run_jo_sweep.py` — JO context;
- `scripts/run_degree_matched_nulls.py` and
  `scripts/run_distance_matched_nulls.py` — dynamical null controls;
- `scripts/run_sugar_stats_and_nulls.py` — historical sugar statistics/null
  wrapper; verify its trial count before using it for new work.

## Input and reproducibility tools

- `tools/path_resolver.py` — exact manifest-based input resolution;
- `tools/create_source_contexts.py` — explicit source-context files;
- `tools/context_reachability_audit.py` and `tools/simulator_sanity_audit.py` —
  input/simulation diagnostics;
- `tools/validate_neuron_ids.py` and `tools/id_space_audit.py` — safe ID handling;
- `tools/build_input_manifest.py`, `tools/validate_reproducibility.py`, and
  `tools/write_output_manifest.py` — provenance and output checks;
- `tools/run_context_perturbation_sweep.py` and
  `tools/run_targeted_context_validation.py` — context-run infrastructure.

These tools are retained because they either enabled later experiments or
protect against known failure modes. Their generated outputs are not biological
claims.

## Structural comparison code

`connectome_analysis/graph_surrogates.py`, `validate_surrogates.py`,
`context_comparison.py`, `graph_metrics.py`, `node_lesion.py`,
`connection_lesion.py`, `structural_baseline.py`, `toy_signal.py`, and
`vulnerability_matrix.py` implement structural predictors, toy known-answer
contracts, or comparisons against simulated ΔHz. They do not constitute a
second biological brain model. Keep `claim_status` and the provenance fields
when using them.

## Archives

`archive/early_support/` contains the original smoke-test notebook, helper
utilities, IDs, and context-support files. `archive/structural_exploratory/`
contains intermediate structural/null scripts. These files are kept so the
project lineage is not erased, but they are not current entry points.

## Removed from the active repository

The cleaned tree removes abandoned structural-routing code, provisional target
curation, duplicate workspaces, and stale generated result dumps. The abandoned
route is documented only as a methodological dead end in
`docs/PROJECT_HISTORY.md`; none of its outputs is evidence.
