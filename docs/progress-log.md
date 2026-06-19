# Fly Connectome Perturbation Progress Log

Last updated: 2026-06-19

## Purpose

This document is an evidence-first status log for the fly connectome perturbation project. It is intentionally conservative: it records only what is visible in the repository or in cited public references, and it marks missing provenance as blockers instead of inventing progress.

## Project goal

The current repository task queue defines the goal as cataloging and stabilizing the fly connectome perturbation project so future research and coding work is reproducible. The project name and tracked output file suggest a Drosophila connectome perturbation analysis, but the exact scientific method is not yet documented in the repository.

## Confirmed repository evidence

- `README.md` exists but currently only contains the title `# connectome-perturbation`.
- `docs/cursor-ready-issues.md` exists and instructs future agents to avoid unsupported neuroscience claims, prefer documentation/reproducibility before features, and document missing datasets or papers as blockers.
- `results/perturbation_summary.csv` exists and contains a small group-level summary table with columns:
  - `group`
  - `n_silenced`
  - `total_delta_hz`
  - `n_neurons_affected`
- The CSV currently lists rows for: `optic`, `central`, `sensory`, `ascending`, `descending`, `visual_projection`, and `motor`.

## Current output file status

`results/perturbation_summary.csv` is evidence that some perturbation-style summary was produced, but it is not enough to validate a scientific result.

Current blockers for interpreting the CSV:

- No confirmed source dataset is named in the repository.
- No script, notebook, command, or pipeline is present showing how the CSV was generated.
- No definition is provided for `total_delta_hz`.
- No explanation is provided for what `n_silenced` means operationally.
- No explanation is provided for how `n_neurons_affected` is computed.
- No explanation is provided for whether groups such as `optic`, `central`, `sensory`, `ascending`, `descending`, `visual_projection`, and `motor` are source-dataset annotations or custom project groupings.
- No units, assumptions, random seeds, thresholds, or validation checks are documented.

Until those are resolved, the CSV should be treated as an unexplained intermediate output, not a validated finding.

## Candidate public datasets and tools

These are candidate references only. The repository does not yet prove that any of them were used.

### FlyWire / FAFB

The FlyWire adult female brain connectome is a likely candidate dataset family for this project because it is a public Drosophila connectome resource. The Nature annotation paper describes the newly completed adult female FAFB connectome as having 139,255 neurons, and states that the full connectome can be represented as a graph with 139,255 nodes and about 15.1 million weighted edges. The NIH/NIMH public summary describes the project as detailing over 50 million connections between more than 130,000 neurons and points users to Codex for data analysis tools.

Relevant public links:

- Nature: Whole-brain annotation and multi-connectome cell typing of Drosophila — https://www.nature.com/articles/s41586-024-07686-5
- NIH/NIMH summary — https://www.nimh.nih.gov/news/science-updates/2024/researchers-fully-map-neural-connections-of-the-fruit-fly-brain
- FlyWire/Codex — https://codex.flywire.ai/
- Zenodo FlyWire connectivity data — https://zenodo.org/records/10676866

### FlyWire connectivity release / Zenodo

The Zenodo FlyWire Whole-brain Connectome Connectivity Data record is a concrete candidate source for reproducible graph work. It is marked as Version 783.0 and says it contains connectivity data for the FlyWire connectome release. It also documents large downloadable tables, including synapse and connectivity-related files, and explains that methods are distributed across the associated FlyWire manuscripts.

Relevant public link:

- https://zenodo.org/records/10676866

### Codex static downloads

Codex states that public users can download FlyWire datasets such as FAFB and BANC, recommends static downloadable files for programmatic analysis rather than scraping or live-querying, and gives an example pattern for working with downloadable CSV resources. This is important for future reproducibility: if this project uses FlyWire/Codex, it should record the exact dataset option, download file names, version, and citation requirements.

Relevant public link:

- https://codex.flywire.ai/faq

### Hemibrain and other connectomes

The repository does not currently identify hemibrain, BANC, MANC, MCNS, or any other connectome as the dataset source. These should remain alternatives to check, not assumed inputs.

## Current methods

No current analysis method can be confirmed from tracked source files. The visible repository evidence does not identify whether perturbation means:

- silencing/removing nodes,
- removing or reweighting edges,
- changing synaptic weights,
- simulating activity,
- running a graph-diffusion model,
- comparing network centrality metrics,
- or applying another method.

No claims about neural function, behavior, disease, or biological causality should be made until methods and source data are documented and cited.

## Completed cataloging steps

- Confirmed that the repository has a minimal README.
- Confirmed that a task queue exists and prioritizes reproducibility and evidence-based documentation.
- Confirmed that a perturbation summary CSV exists.
- Identified missing provenance needed to interpret the CSV.
- Cataloged candidate public source ecosystems: FlyWire/FAFB, FlyWire Codex static downloads, Zenodo FlyWire connectivity release, and other Drosophila connectome families to check.

## Open questions

1. Which dataset generated `results/perturbation_summary.csv`?
2. What exact dataset version was used?
3. Was the input a neuron-level connectivity table, synapse-level table, annotation table, or a derived graph?
4. What perturbation operation was performed?
5. What does `total_delta_hz` mean, and why is it measured in Hz?
6. Are the listed groups imported biological annotations, manually defined groups, or heuristic labels?
7. What scripts or notebooks generated the CSV?
8. What validation or sanity checks were run?
9. Are there any citations or notes connecting this work to a science-fair/research question?
10. Are any private or large derived data files being used outside the repository?

## Source links/files needed next

To move from cataloging to validation, the project needs at least the following:

- Dataset URL or DOI.
- Dataset version identifier.
- Downloaded file names or data manifest.
- Script or notebook that generated `results/perturbation_summary.csv`.
- Dependency file or environment notes.
- Methodology notes describing the perturbation operation.
- Definitions of `n_silenced`, `total_delta_hz`, and `n_neurons_affected`.
- Any project notes, presentation, proposal, or research-question document.
- Any validation output or logs.

## Recommended next actions

1. Add `docs/data-sources.md` with a table for dataset name, URL/DOI, version, files used, access date, and citation.
2. Add `docs/methods.md` defining the perturbation model and every output metric.
3. Add a reproducibility manifest listing every input file needed to regenerate the CSV.
4. If the generating notebook/script exists outside the repo, add it or document why it cannot be committed.
5. Add a minimal validation check that loads `results/perturbation_summary.csv`, verifies required columns, checks numeric fields, and warns that biological interpretation is blocked without methods.
6. Expand the README with the project goal and blocker status.

## Risks

- Reproducibility risk: the output CSV cannot currently be regenerated from the repository.
- Dataset attribution risk: future readers may incorrectly assume FlyWire, hemibrain, or another dataset was used.
- Metric interpretation risk: `total_delta_hz` sounds like a physiological or simulated activity unit, but no model definition exists.
- Scientific validity risk: biological conclusions would be unsupported without source data, methods, and validation.
- Data-management risk: the repository size is large enough that future data additions should be audited carefully before committing.

## Conservative status

The project is currently in documentation/reproducibility triage. There is a visible output table, but there is not enough repository evidence to treat it as a validated neuroscience result.
