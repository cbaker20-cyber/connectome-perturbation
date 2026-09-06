# Project history

**Repository snapshot:** 2026-09-05

This is a compact reconstruction of the project from the first reachable commit. It is based on the commit objects, the files introduced by those commits, and the current code. A commit message is evidence that a change was recorded; it is not evidence that the scientific claim in the message was correct.

## Timeline

### 2026-03-31 — model integration and first run

- `c51d8cc` — initial repository.
- `90ecee3` — the upstream Shiu-model workflow was made runnable locally and a sugar-input smoke test was recorded in `test_run.py`.

The project began as a computational reproduction/integration effort: a Brian2 leaky integrate-and-fire model using FlyWire connectivity, not as a new biological model. The initial smoke run established that the model could produce spikes on the local machine. It did not validate a biological conclusion.

### 2026-03-31 — perturbation engine

- `0f15f67` — added `perturbation/baseline.py`, `perturbation/perturb.py`, and `perturbation/analyze.py`.

The central experiment was defined: silence the **outgoing synaptic weights** of a selected neuron set, run the network against a matched baseline, and read out total motor-population firing. This operation is output silencing in the model; it is not cell death, ablation, optogenetics, or measured behavior.

### 2026-04-01 — annotations and named groups

- `afd4a75` — added FlyWire annotations and cell-group selection.
- `a759812`, `222e889`, `7714ee4`, `6487146` — added superclass sweeps, summaries, motor readout analysis, and an early visualization.

This was the transition from arbitrary neuron IDs to named populations selected from annotation fields such as `super_class` and `cell_class`. Annotation membership enabled biologically interpretable *labels for simulation groups*; it did not make the labels experimental measurements.

### 2026-04-01 — first conclusion, reached too early

- `5faa89f` — recorded a 27-class, five-trial screen in which LO appeared to produce a positive net motor effect when silenced.

This was the first major interpretive mistake. The screen was exploratory and underpowered, and the conclusion was formed before the relevant literature and statistical controls had been worked through. The result belongs in the project’s history, but not as evidence that LO suppresses feeding in the fly.

### 2026-04-02 — correction by replication

- `66a2603` — recorded a 30-trial rerun. LO changed from the five-trial positive result to a negative net effect; AN remained a large negative effect.
- `41a87f4` — added the first explicit statistical comparison.

The LO sign reversal is an important methodological lesson: a five-trial screen was not reliable enough to establish the direction of an effect. The early statistical table also used raw p-values and did not yet implement the later project standard of matched trials, zero-spike retention, Benjamini–Hochberg FDR, null comparisons, and assumption sensitivity. The old table must not be used as a current claim table.

### 2026-06-09/10 — graph analysis and data consolidation

- `0427902` — revised the statistics implementation.
- `9938a93`, `e424e0d`, `36f7b7e`, `dfad6bf` — an upload/delete/re-upload/update cycle for early graph analysis.
- `e5b0ede` — imported the active FlyWire materializations, annotation data, model support files, and a large research-document workspace.

The data/model import was substantive. The duplicated document system, copied notes, templates, and management files added clutter rather than a second scientific result. The current active tree retains the data, model, perturbation code, and useful reproducibility components, while older support files are clearly archived or removed.

### 2026-06-19 to 2026-06-25 — planning expansion and abandoned BORA route

- `bb4853a`, `5366942`, `2648f2e` — planning/provenance notes and task-management scaffolding.
- `79f4dff` through `31811f7` — feeding/grooming candidate curation and the BORA/novel-architecture route.
- `65974ce` through `17b0121` — scope plans, literature framing, execution plans, and pasted early lab notes.

The BORA branch tried to infer feeding-versus-grooming routing from structural connectivity and provisional target lists. It did not produce a validated result relevant to the project’s current E/I lesion question. Candidate motor labels were provisional and partly circular, so the BORA implementation, fixtures, target templates, and candidate-curation machinery are deliberately removed rather than presented as negative or positive biological evidence.

The early notes remain useful as a record of how the project developed, especially the five-trial mistake and the later correction. AI-generated or copied narrative is not treated as a source; only facts recoverable from commits, code, data, and cited papers are retained here.

### 2026-06-30 — context sets and ID integrity

- `4c5ce37`, `66eabea`, `2c7394e`, `a95f0dc`, and `9fd07fa` — source-context generation, reachability checks, simulator sanity checks, and context sweep runners.
- `91deab3`, `1d9be87`, `e595d6b`, `6d10c24`, `566ae2b`, and `c384a93` — fixes and audits for explicit source IDs, ID spaces, and large FlyWire ID parsing.
- `b9e287c`, `ef8275b` — targeted context validation tooling.

This work paved the way for the current dual-context design. It is retained where it protects actual inputs, preserves decimal root IDs, or supports reproducible context runs. One-off pilots, adaptive planning, local patch wrappers, and convenience wrappers with no durable scientific role are removed or kept out of the active tree.

### 2026-07-09 to 2026-07-18 — reproducibility and test infrastructure

- `0e87572` — introduced the metadata-first reproducibility spine.
- `41d5744` through `1766867` — added deterministic toy contracts, strict neuron-ID validation, structural known-answer tests, and fail-closed output/provenance checks.
- `5ad0b61` — committed `data/input_manifest.json` with checksums for tracked connectome inputs.

These changes are retained because they make it possible to distinguish a reproducible computational result from an untracked run or an invalid ID/path. Toy fixtures are tests of software behavior, not evidence about fly biology.

The empty Copilot checkpoint commits (`6a7263c`, `d8c291f`) produced no project content and are excluded from the cleaned history. AI-generated management documents and agent-facing task files are also excluded from the public project tree. AI assistance is disclosed in the project’s working records; retained code is judged by its reproducible behavior and scientific relevance, not by who edited it.

### 2026-07-21 to 2026-07-24 — structural controls and second context

- `178e4bc` — added generic matrix helpers for modal controllability, attenuated path flow, and rank correlations.
- `9c96e5c` — added exploratory disinhibition-motif and AN source-target betweenness controls.
- `b4e6ad1` — added the JO 30-trial ground-truth runner and configuration.
- `f5ed148`, `d672e6b`, and `7e135f8` — added structural-versus-dynamical comparison and sugar-versus-JO context comparison code.
- `da3040c` — corrected pipeline issues involving baseline resolution, degree matching, rate deltas, and path resolution.

The generic structural math and the JO/context infrastructure are relevant to the structure-versus-dynamics direction and are retained. Structural fixtures and proxy tables are not biological validation. The AN betweenness and motif analyses remain exploratory controls unless independently recomputed and audited; they are never evidence that AN is a unique dynamical controller.

### 2026-07-31 to 2026-08-02 — mixed workspace and cleanup

- `e36130b`, `d09d844`, `0686359`, `26e7e21`, `fe43d72`, and `1c7d0a0` — mixed WIP/merge/index snapshots and cleanup of backups, agent scaffolding, and duplicate workspace material.

Some commits in this period bundled useful context files with backups, logs, wrappers, and management artifacts. The cleaned tree keeps the useful source-context and validation code rather than treating the mixed snapshot as a scientific milestone.

### 2026-08-08 to 2026-08-17 — ground-truth results and statistical consolidation

- `087840f`, `73dd358`, `98bd149`, `26fda39`, `d22e08c`, `b9f77eb`, and `4e29f44` — JO and sugar result tables, n=20 outputs, null comparisons, context tables, and the configuration used for the ground-truth run.
- `5579708`, `85eb132`, `766b6b5`, `9ec946f`, and `c1db9d0` — documentation/provenance consolidation and null-runner interface fixes.

The results are simulation outputs and should be reported with materialization, trial count, seed, baseline matching, transmitter map, null/permutation details, and FDR status. They are not measurements of feeding, grooming, or behavior. The project keeps sugar and JO because they are relevant contexts, not because every historical table is claim-ready.

### 2026-08-30 — statistical/subgraph correction and scientific reset

- `218d08a` — corrected empirical two-sided p-values and replaced ID-ordered capped-subgraph selection with neighborhood-based sampling; regenerated affected aggregates.
- `73cd2a4` — removed the large research-management bundle, presentation material, provisional labels, historical dumps, and other files that were not part of the scientific core.

The subgraph correction matters because an earlier structural comparison produced a misleading correlation when groups were represented by a broken near-empty/capped graph. The corrected comparison is the relevant record; the earlier apparent correlation is not to be presented as a finding.

### 2026-09-05 — documentation and cleanup

- `8504553` — rewrote the README as a project description with code-backed methods, provenance, literature context, and claim limits.
- This cleanup removes the remaining BORA program and presentation-facing clutter, archives useful historical support scripts rather than deleting them, repairs stale CI paths, and preserves this timeline.

## What survives as the scientific spine

1. Shiu/Brian2 model integration on FlyWire data.
2. Annotation-based neuron-group selection.
3. Output-silencing perturbations with a motor-population readout.
4. The five-trial LO result as a corrected-history lesson, not a discovery.
5. The 30-trial correction and the more careful AN/descending/sugar/JO analyses.
6. Explicit polarity assumptions, matched nulls, FDR, provenance manifests, and ID/path validation.
7. Structural controls and context comparisons retained as computational predictors or future-work infrastructure, not biological proof.

## Rules for using this history in Regeneron documentation

- Cite the paper and the exact repository/configuration used; do not cite a commit message as scientific evidence.
- Distinguish a simulation output, a structural proxy, a software test, and a biological claim.
- State what was wrong in the first conclusion: the screen used too few trials, the early statistics were not FDR-controlled, and the LO direction did not survive replication.
- Do not claim that the project measured behavior or proved a feeding/grooming circuit.
- Disclose AI assistance as required, while keeping the report’s scientific prose and interpretation the student’s own work.
