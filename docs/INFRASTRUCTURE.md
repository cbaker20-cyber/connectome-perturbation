# Infrastructure that is actually used

This is the scientific stack after the 2026-08-30 reset. If a file is not
named here, it is not part of the argument.

## Data (do not mix materializations)

| File | Role |
|---|---|
| `2023_03_23_completeness_630_final.csv` | Simulated neuron list, materialization 630 (~127,400 IDs) |
| `2023_03_23_connectivity_630_final.parquet` | Directed edges + `Excitatory x Connectivity` signed weight |
| `Completeness_783.csv` / `Connectivity_783.parquet` | Newer materialization. Present; **not interchangeable** with 630 |
| `flywire_annotations.tsv` | `super_class`, `cell_class`, `cell_type`, `top_nt`, `known_nt` |
| `data/input_manifest.json` | Filenames, sizes, SHA-256, partial provenance |

Root IDs are opaque decimal strings. Do not parse them as floats.

## Simulator (`model.py`)

Brian2 leaky integrate-and-fire, parameters taken from the Shiu et al. 2024
framework (not invented here):

- rest/reset −52 mV, threshold −45 mV
- membrane τ 20 ms, synaptic τ 5 ms
- refractory 2.2 ms, delay 1.8 ms
- weight unit 0.275 mV
- `w = (Excitatory × Connectivity) × 0.275 mV`
- sensory drive: `PoissonInput` onto listed sensory IDs (default 150 Hz)
- **lesion:** outgoing synaptic weights of chosen neurons set to 0

There is one `NeuronGroup`. Excitatory vs inhibitory is **only** the sign of
`w`. That sign is inherited from the connectivity table, which itself depends
on a transmitter prediction — see `docs/RESEARCH_QUESTION.md`.

## Perturbation engine (`perturbation/`)

| File | Role |
|---|---|
| `baseline.py` | Sugar sensory IDs + default run params |
| `perturb.py` | Silence a list of IDs, compare to baseline |
| `cell_groups.py` | Join annotations; **polarity groups under named NT maps** |
| `statistics.py` | Per-trial motor Hz, retain zeros, Welch t, BH-FDR |
| `analyze.py` / `motor_analysis.py` | Motor readout helpers |
| `graph_analysis.py` / `path_analysis.py` | Static graph metrics (no Brian2) |

## Graph / structure (`connectome_analysis/`)

Node and connection lesions on a **toy deterministic propagator** (not Brian2)
plus betweenness, surrogates, disinhibition motifs. Use these as *structural
predictors* to compare against dynamical ΔHz, not as a second “brain.”

## Controls that matter for the question

- Degree-matched dynamical nulls: `scripts/run_degree_matched_nulls.py`
- Distance-matched dynamical nulls: `scripts/run_distance_matched_nulls.py`
- Two NT maps in `perturbation/cell_groups.py` (`classical_fast`, `shiu_2024`)
- I:E ratio sweep: change the magnitude of negative weights and rerun (H4)

## What was removed

AI research-management docs (including `MASTER_GUIDE.md`), presentation
files, historical result dumps (`results_8_22-pre_n30/`), atlas/receipt
plumbing, and provisional feeding/grooming labels derived from unvalidated
hq_AN screens. Those files are not evidence.
