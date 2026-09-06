# Connectome perturbation

Whole-brain *Drosophila* LIF simulation (Brian2) on FlyWire connectivity, with
**output-lesioning** and a motor-population readout.

## What this repo is

This is the scientific engine for a simulation-based test of a narrow question
about signed whole-brain connectivity in the adult fly brain. It is not a
literature survey or a general-purpose graph-analytics repository. The repo
holds:

- a Brian2 leaky integrate-and-fire (LIF) simulator configured on FlyWire
  connectivity (`model.py`);
- an output-lesioning perturbation engine with a motor-population readout
  (`perturbation/`);
- structural predictors and comparison utilities meant to be tested against the
  dynamical lesion results, not promoted to a second "brain" (`connectome_analysis/`);
- reproducibility plumbing: manifest-resolved input paths, output manifests,
  checksums, and provenance records (`tools/`, `data/input_manifest.json`,
  `configs/`);
- the docs that state the question, the competing accounts, and the epistemic
  rules (`docs/`);

The tracked tree contains the current scientific core and reproducibility
support. Files that are not part of the current scientific argument are not
included in the active project tree.

## The data (FlyWire, adult *Drosophila*)

Primary input is the FlyWire FAFB whole-brain connectome. The repo tracks two
releases (materializations) that are **not interchangeable**:

- **Materialization 630** — the active pipeline's input.
  - Completeness table: `2023_03_23_completeness_630_final.csv` — 127,400
    simulated neurons.
  - Connectivity table:
    `2023_03_23_connectivity_630_final.parquet` — 14,687,178 directed edges
    with a neurotransmitter-informed signed weight column
    (`Excitatory x Connectivity`).
  - Provenance: Dorkenwald, S., Matsliah, A., Sterling, A.R. et al. Neuronal
    wiring diagram of an adult brain. *Nature* 634, 124-138 (2024).
    doi:10.1038/s41586-024-07558-y.
- **Materialization 783** — present locally, not the active pipeline's input.
  - `Completeness_783.csv` (138,639 rows) and
    `Connectivity_783.parquet` (15,091,983 rows).
  - Provenance: FlyWire Consortium, FlyWire Whole-brain Connectome Connectivity
    Data, Zenodo (2024), doi:10.5281/zenodo.10676866; see also Dorkenwald et
    al. 2024.

Cell-type annotation comes from the FlyWire annotation table:
`flywire_annotations.tsv`. Provenance: Schlegel, P., Yin, Y., Bates, A.S. et
al. Whole-brain annotation and multi-connectome cell typing of *Drosophila*.
*Nature* 634, 139-152 (2024). doi:10.1038/s41586-024-07686-5. Annotation
tables are distributed via the `flyconnectome/flywire_annotations` repository.

**Important:** `Excitatory x Connectivity` is not a directly measured synapse
sign. It is built from predicted transmitters (Eckstein et al., 2024). Glutamate
in flies can act at inhibitory GluCl channels or at excitatory glutamate
receptors, so collapsing glutamate to one polarity is a modeling choice, not a
settled fact about the fly. The repo keeps this explicit through named NT maps
(see below).

Provenance is partial in this repo: the input manifest records checksums and
citations, but access dates and redistribution status are not all filled in. Do
not treat a filename as a DOI, and do not quote a count from materialization 630
next to a result from 783 without saying so.

## The question

When a set of neurons is **output-lesioned** in a signed whole-brain LIF model of
adult *Drosophila*, is the change in **motor-population firing** predicted by the
**sign and weight of their outgoing synapses** (a static, signed-graph account),
or does the **sign of the effect require the nonlinear, activity-dependent
dynamics** of the network (disinhibition / disfacilitation / silent inhibition)?

Unit of analysis:

```
(input context s, lesion set c, I:E weight ratio r, NT-sign map m)
    ->  ΔHz_motor
```

`ΔHz_motor` is simulated motor-neuron firing under lesion minus the matched
baseline. It is **not** measured behavior.

The competing accounts the project does **not** pick among are:

1. **Shiu et al., 2024, *Nature*** — built the LIF whole-brain model this repo
   uses. They report that connectome weights matter (shuffling them hurts
   predictions) and that the model **failed to predict behavioural results when
   the tested neurons were predicted inhibitory or neuromodulatory**. They assume
   equal |E| and |I| magnitudes, glutamate as inhibitory, and a basal rate of 0
   Hz. Those are stated assumptions, not settled facts.
2. **Eckstein et al., 2024** — provide predicted transmitters. Prediction is not
   the same as a measured synapse sign.
3. **Chen & Xi, 2025 (bioRxiv)** — argue that escape suppresses feeding by
   **upstream disfacilitation of a premotor center**, not by lateral inhibition
   onto the feeding motor neuron MN9, and that the architecture is **distributed
   / redundant**.
4. **Command-neuron vs population** accounts of descending control (e.g. Braun et
   al. 2024 on descending neuron types) — disagree about whether a small labeled
   set should dominate motor ΔHz.

The competing hypotheses kept live in the project are:

| ID | Account | What it predicts for this model |
|---|---|---|
| H1 | Signed-graph | Lesioning cells whose outgoing weights are net inhibitory **raises** motor ΔHz; net excitatory **lowers** it. Rank of \|ΔHz\| tracks signed outgoing strength. |
| H2 | Silent inhibition | If a cell is not recruited by the current sensory drive, lesioning it does nothing, regardless of its transmitter. Sugar vs no-input vs a second context must change the E/I lesion effect. |
| H3 | Distributed redundancy | Large random or class-level inhibitory lesions have small ΔHz because parallel paths remain. Degree-matched nulls of the same size look like the real class. |
| H4 | I:E identification failure | The H1 pattern **flips or vanishes** when the inhibitory:excitatory weight ratio is moved ±50% (the robustness check Shiu already used). |

A result supports an account only if the others are tested in the same run
batch. Confirming H1 at the default ratio and never running H4 is not a result.

## What the simulator does

`model.py` implements a Brian2 LIF network with parameters taken from the Shiu
et al. 2024 framework, not invented here:

- rest/reset −52 mV, threshold −45 mV
- membrane τ 20 ms, synaptic τ 5 ms
- refractory 2.2 ms, delay 1.8 ms
- weight unit 0.275 mV
- `w = (Excitatory × Connectivity) × 0.275 mV`
- sensory drive: `PoissonInput` onto listed sensory IDs (default 150 Hz)
- **lesion:** outgoing synaptic weights of chosen neurons set to 0

There is one `NeuronGroup`. Excitatory vs inhibitory is **only** the sign of
`w`. That sign is inherited from the connectivity table, which itself depends on
a transmitter prediction — see `docs/RESEARCH_QUESTION.md`.

Parameter sources in the code: Kakaria & de Bivort 2017
(doi:10.3389/fnbeh.2017.00008), Jürgensen et al.
(doi:10.1088/2634-4386/ac3ba6), Lazar et al. (doi:10.7554/eLife.62362), Paul
et al. 2015 (doi:10.3389/fncel.2015.00029). The lesion engine, annotation join,
polarity maps, statistics, and nulls are this project's addition.

## How a run works, end to end

1. Inputs are resolved through `tools/path_resolver.py` against
   `data/input_manifest.json` by exact filename/role/materialization. The resolver
   refuses ambiguous matches and paths outside the repo.
2. Sensory neurons receive Poisson input. By default the sugar context drives 21
   right-side sugar-responsive IDs listed in `perturbation/baseline.py`.
3. A lesion sets a chosen set of neurons' **outgoing** weights to zero. Incoming
   synapses are unchanged. This is **output silencing**, not ablation.
4. Spikes are recorded; motor neurons (`super_class == "motor"` in the annotation
   table, restricted to IDs present in the completeness table) are the readout.
5. Per-trial total motor firing rate is computed in Hz. Trials with zero motor
   spikes are **kept as 0 Hz**.
6. Baseline vs lesion is compared with Welch's t-test
   (`equal_var=False`), then Benjamini–Hochberg FDR across the family of tests in
   that batch.

Statistics and controls that matter for the question:

- degree-matched dynamical nulls: `scripts/run_degree_matched_nulls.py`
- distance-matched dynamical nulls: `scripts/run_distance_matched_nulls.py`
- two NT maps in `perturbation/cell_groups.py` (`classical_fast`, `shiu_2024`)
- I:E ratio sweep: change the magnitude of negative weights and rerun (H4)

## Transmitter maps are explicit assumptions

`perturbation/cell_groups.py` assigns excitatory / inhibitory / unmapped under a
**named** map. Both maps must be reported if polarity is part of a claim.

- `classical_fast` — ACh excitatory, GABA inhibitory, glutamate **unmapped**
  (its sign is mixed in Drosophila).
- `shiu_2024` — additionally treats glutamate as inhibitory, matching the Shiu
  et al. 2024 LIF assumptions.

Preference order in the code: `known_nt` wins over `top_nt`; a `known_nt` that
contradicts `top_nt` is labeled `"conflicting"`, not silently overridden.

## First experiment (screen, not a claim)

```bash
python perturbation/cell_groups.py
python scripts/run_ei_lesion_screen.py --dry-run
python scripts/run_ei_lesion_screen.py --nt-map classical_fast --n-run 5
python scripts/run_ei_lesion_screen.py --nt-map shiu_2024 --n-run 5
```

`--dry-run` prints group sizes under each transmitter map. A real run writes
parquet spike tables under `results/` (gitignored).

## What this project will not claim from a simulation

- That a cell class "is" a feeding or grooming neuron in the fly.
- That output-lesioning equals optogenetic silencing, cell death, or a
  developmental mutant.
- That simulated motor Hz equals behavior.
- That the most-cited paper on a topic is the correct one.

## Setup

```bash
conda env create -f environment.yml
conda activate brian2
```

`requirements.txt` pins `Cython<3`, which Brian2 2.5.1 needs.

## Regeneron / STS rules

Use this repo for code, methods, and numbers. Write the Research Report and the
reference list yourself. Disclose AI assistance. Do not paste model prose into
the report. `docs/EPISTEMIC_RULES.md` is the rule set for not turning a default
or a highly-ranked paper into "the truth."

## Files that are part of the argument

- `model.py` — Brian2 LIF simulator
- `perturbation/` — lesion engine, baseline, cell groups, statistics, readout,
  static graph metrics
- `connectome_analysis/` — structural predictors, lesion comparisons, and
  deterministic software checks; these are not Brian2 simulations or biological
  proof
- `scripts/` — run entries for the first experiment, the EI lesion screen, the
  JO and sugar ground-truth sweeps, and the degree/distance-matched nulls
- `tools/` — path resolution, output-manifest writing, reproducibility checks
- `docs/` — research question, methods, infrastructure, epistemic rules
- `data/input_manifest.json` — input filenames, sizes, SHA-256, partial
  provenance

## Files that are not part of the argument

- `archive/` — historical support and exploratory code; not active entry points
- `results/` — simulation outputs; regenerate, do not treat as provenance
  (gitignored)
- `.freebuff/` — local app state (gitignored)
- `GeNNworkspace/` — generated Brian2/GeNN build output (gitignored)
- `*.zip`, `unzipped_files/` — large archives and extracted scratch (gitignored)

## Tests

```bash
.venv/Scripts/python.exe -m pytest -q
```

The test suite includes polarity-map tests, input-manifest validation, path-
resolver boundaries, structural-baseline known-answer tests, surrogate math
tests, and reproducibility-tool tests.
