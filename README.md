# Connectome perturbation

Whole-brain *Drosophila* LIF simulation (Brian2) on FlyWire connectivity, with
**output-lesioning** and a motor-population readout.

This repository was reset on 2026-08-30: AI-generated research-management
docs, presentation files, and historical result dumps were removed. The
scientific engine (`model.py`, `perturbation/`, connectome tables) is what
remains.

## Question

**Does the sign of motor ΔHz after a lesion follow the sign of outgoing
synapses, or only the nonlinear dynamics (and the sensory context)?**

Competing accounts, and why the question is still open, are in
[`docs/RESEARCH_QUESTION.md`](docs/RESEARCH_QUESTION.md). That file does not
pick a winner. [`docs/EPISTEMIC_RULES.md`](docs/EPISTEMIC_RULES.md) is the
rule set for not turning a default or a highly-ranked paper into “the truth.”

Infrastructure map: [`docs/INFRASTRUCTURE.md`](docs/INFRASTRUCTURE.md).
Code-backed methods: [`docs/METHODS.md`](docs/METHODS.md).

## Setup

```bash
conda env create -f environment.yml
conda activate brian2
```

`requirements.txt` pins `Cython<3`, which Brian2 2.5.1 needs.

## First experiment (screen, not a claim)

```bash
python perturbation/cell_groups.py
python scripts/run_ei_lesion_screen.py --dry-run
python scripts/run_ei_lesion_screen.py --nt-map classical_fast --n-run 5
python scripts/run_ei_lesion_screen.py --nt-map shiu_2024 --n-run 5
```

`--dry-run` prints group sizes under each transmitter map. A real run writes
parquet spike tables under `results/` (gitignored).

## What the model does, in one paragraph

Neurons come from a completeness table. Synapses come from a connectivity
table. Weight is `Excitatory × Connectivity × 0.275 mV`. Sensory neurons
receive Poisson input. A lesion sets that cell’s **outgoing** weights to zero.
Spikes are recorded; motor neurons (`super_class == motor`) are the readout.
Parameters follow Shiu et al. 2024; this project’s addition is the lesion
engine, annotation join, polarity maps, statistics, and nulls.

## Data

Tracked locally: materializations **630** and **783**, plus
`flywire_annotations.tsv`. They are different releases. Checksums live in
`data/input_manifest.json`. Provenance is partial (no access date). Do not
treat a filename as a DOI.

## Regeneron / STS

Use this repo for code, methods, and numbers. Write the Research Report and
the reference list yourself. Disclose AI assistance. Do not paste model prose
into the report.
