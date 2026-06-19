# Fly Connectome Perturbation Progress Log

## Status

This document is an evidence-based catalog of the repository state and research context. It is intentionally conservative: it records only files, outputs, and goals that were visible in the repository or supported by external references.

## Confirmed project goal

The repo-local task queue states that the current goal is to catalog and stabilize the fly connectome perturbation project so future coding and research work is reproducible. It also requires that no neuroscience claims be made without citations and that missing datasets or papers be documented as blockers rather than guessed.

Working interpretation: this project appears to be intended as a graph/network perturbation analysis project for a Drosophila connectome dataset, likely comparing the modeled effect of silencing/removing neuron groups or regions. That interpretation is based on the repository name and the tracked summary output file listed below, not on a complete methods document.

## Confirmed repository files and outputs

Confirmed files inspected:

- `README.md` — currently contains only the project title.
- `.gitignore` — ignores `venv/`, `results/`, and `__pycache__/`, while explicitly allowing `results/perturbation_summary.csv`.
- `docs/cursor-ready-issues.md` — task queue for repo inventory, README improvement, data policy, environment planning, and validation.
- `results/perturbation_summary.csv` — tracked output summary with columns `group`, `n_silenced`, `total_delta_hz`, and `n_neurons_affected`.

Confirmed output rows in `results/perturbation_summary.csv`:

| group | n_silenced | total_delta_hz | n_neurons_affected |
|---|---:|---:|---:|
| optic | 59373 | -518.6 | 272 |
| central | 28690 | -7702.0 | 374 |
| sensory | 8129 | -10666.4 | 372 |
| ascending | 1587 | -1319.0000000000002 | 358 |

Important caveat: no source dataset, script, notebook, model equations, or units documentation has been confirmed yet. Therefore the meaning of `total_delta_hz`, the method used to compute it, and the biological meaning of each group label are currently undocumented.

## Current methods: confirmed vs. missing

Confirmed:

- A perturbation summary CSV exists.
- A task queue exists and prioritizes documentation, reproducibility, data handling, and validation before new features.
- `.gitignore` is partly configured to keep generated `results/` out of version control except for the summary CSV.

Missing or not yet confirmed:

- Source connectome dataset link or citation.
- Data schema for the raw connectome table or graph.
- Script/notebook that generated `results/perturbation_summary.csv`.
- Definition of perturbation operation: silencing, node deletion, edge deletion, neurotransmitter-specific inhibition/excitation, randomization, or other.
- Definition and units of `delta_hz`.
- Dependency file such as `requirements.txt`, `pyproject.toml`, `environment.yml`, or notebook metadata.
- Reproduction command.
- Validation tests.
- Whether large data files are intentionally tracked in the repository.

## External research context

The FlyWire Consortium published a complete adult Drosophila brain wiring diagram in Nature in 2024. Reporting on that publication describes more than 139,000 neurons and more than 50 million connections/synapses in the adult fruit fly brain. This makes FlyWire a plausible source family for a whole-brain perturbation project, but the repository does not yet identify FlyWire, hemibrain, BANC, neuPrint, Codex, or any other dataset as its actual source.

The earlier Janelia/Google hemibrain connectome, described in eLife in 2020, is another plausible source family for adult Drosophila connectome work. Hemibrain is not a complete whole-brain dataset, so results from hemibrain-style data should not be described as whole-brain without checking the actual source.

FlyWire Codex is a likely interface to investigate if the project uses FlyWire-derived data, but this repository must document the exact dataset/version/export method before results can be interpreted.

## Open questions

1. What is the exact dataset and version?
2. Was the analysis run on FlyWire, hemibrain/neuPrint, BANC, a synthetic graph, or a manually prepared CSV?
3. What are the raw node and edge files?
4. What does each group label mean: `optic`, `central`, `sensory`, and `ascending`?
5. How were group memberships assigned?
6. What does `n_silenced` count: neurons, synapses, edges, weighted edges, or something else?
7. What does `total_delta_hz` mean and how is it calculated?
8. Why are affected-neuron counts much smaller than silenced counts in the summary?
9. Are neurotransmitter signs, synapse weights, or directionality included?
10. Are the results deterministic? If not, what random seed was used?
11. What validation would show that the perturbation calculation is numerically correct?
12. Are any large/private/generated data files currently tracked?

## Blockers

The main blocker is lack of provenance. A reproducible project needs, at minimum:

- Exact source dataset link.
- Dataset citation.
- Download/export instructions.
- Raw input file schema.
- Analysis script or notebook.
- Reproduction command.
- Explanation of model assumptions.
- Validation plan.

Without those, the existing summary CSV should be treated as an unexplained output rather than a result.

## Next actions

1. Add a repository inventory method that can list high-level tracked files and sizes.
2. Improve README with a conservative project summary and a clear “data source missing” section.
3. Create `docs/data-policy.md` explaining which files may be committed and which should remain external.
4. Create `docs/environment-plan.md` after identifying the actual language/runtime and dependencies.
5. Locate or reconstruct the script that generated `results/perturbation_summary.csv`.
6. Add a minimal validation test once a script or pure function exists.
7. Add citations beside any biological or neuroscience interpretation.

## Risks

- Unsupported biological claims: the repository currently has output but no documented source or method.
- Reproducibility failure: no confirmed dependency file or run command.
- Data-size risk: repository metadata indicates a large repository, but a full tracked-file audit has not yet been completed.
- Dataset/version drift: connectome resources have multiple releases and derived tables; results must identify exact versions.
- Model-validity risk: structural connectivity alone does not automatically imply activity, behavior, or causal neural function.

## Reference candidates to evaluate

These references are candidates for the README/background section once the project’s actual dataset is identified:

- FlyWire Consortium / Dorkenwald et al., “Neuronal wiring diagram of an adult brain,” Nature, 2024.
- Scheffer et al., “A connectome and analysis of the adult Drosophila central brain,” eLife, 2020.
- FlyWire Codex / Codex Connectome Data Explorer.
- neuPrint / Janelia FlyEM resources, if the project uses hemibrain-derived data.

## Log entry

- Created this progress log as Task 1 scaffolding.
- No code behavior changed.
- No research result was interpreted as biologically meaningful because dataset provenance and methods are missing.
