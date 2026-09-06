# Project history

**Repository snapshot:** 2026-09-05

This is a reconstruction of the project from its first commit through the
current cleaned tree. It is based on the recorded changes, source code, tests,
input manifests, and retained analysis artifacts. A commit message records what
was attempted; it does not, by itself, establish that a scientific claim was
correct.

The timeline uses dates and commit subjects rather than commit hashes. The
history was subsequently rewritten to remove discarded artifacts, so old hashes
are intentionally not treated as stable identifiers. Run `git log --date=short`
for the current identifiers.

## Timeline

### 2026-03-31 — model integration and first run

- **Initial commit** — created the repository.
- **“initial setup: shiu model running, baseline sugar neuron test works”** —
  made the upstream Shiu-model workflow runnable locally and recorded a sugar
  input smoke test.

The project began as a computational integration and reproduction effort: a
Brian2 leaky integrate-and-fire model using FlyWire connectivity, not as a new
biophysical model. The first smoke test established that the model could run
and produce spikes on the local machine. It did not validate a biological
conclusion.

### 2026-03-31 — perturbation engine

- **“perturbation engine working: sweep pipeline, baseline comparison, results
  summary”** — added the first baseline, lesion, analysis, and sweep workflow.

The central operation was defined: select a neuron set, set its **outgoing
synaptic weights** to zero, run the network against a matched baseline, and
read out total motor-population firing. This is output silencing in the model;
it is not cell death, anatomical ablation, optogenetics, or measured behavior.

### 2026-04-01 — annotations and named groups

- **“add cell type annotations and first real perturbation:
  descending->motor circuit confirmed”** — joined FlyWire annotations to the
  simulated neuron IDs and enabled named populations.
- **“first full super-class perturbation sweep complete”** — ran the first
  broad superclass screen.
- **“add perturbation summary results”** and **“motor neuron impact analysis
  across all perturbation groups”** — added summaries and motor readout
  analysis.
- **“add motor impact visualization”** — produced the first inspection figure.

This changed the work from arbitrary ID experiments to groups selected through
annotation fields such as `super_class` and `cell_class`. The annotations give
biological labels to simulation groups; they do not turn a simulation label into
an experimental measurement.

### 2026-04-01 — first conclusion, reached too early

- **“cell class sweep complete - LO disinhibition finding”** — recorded a
  27-class, five-trial screen in which LO appeared to produce a positive net
  motor effect when silenced.

This was the first major interpretive mistake. The screen was exploratory and
underpowered, and the conclusion was formed before the relevant literature and
statistical controls had been worked through. The result is retained here as
project history, not as evidence that LO suppresses feeding in the fly.

### 2026-04-02 — replication corrected the LO interpretation

- **“30-trial high quality rerun: LO result corrected, AN confirmed,
  disinhibition persists”** — reran the interesting groups with more trials.
- **“add statistical testing: sensory, central, descending, ascending, AN all
  significant”** — added the first explicit condition-versus-baseline tests.

The LO direction changed between the five-trial screen and the 30-trial rerun,
while AN remained a large effect. The lesson is methodological: a small screen
was not reliable enough to establish the direction of an effect.

The early statistical table also used raw p-values and did not yet implement the
later project standard of matched trials, zero-spike retention, Benjamini–Hochberg
FDR, null comparisons, and assumption sensitivity. The old table must not be
used as a current claim table. “Five significant findings is sufficient” is not
a valid conclusion without defining the tested family, correction, effect size,
and robustness checks.

### 2026-06-09 to 2026-06-10 — repository consolidation and graph code

- **“Update statistics.py”**, file-upload revisions, and graph-analysis updates
  consolidated the early code and data in the repository.
- **“Update local scripts and initialize research docs system”** added a large
  documentation workspace and local-management material.

The data and model consolidation was substantive. The duplicated management
workspace and copied narrative were not a second scientific result. The cleaned
repository retains the model, inputs, perturbation engine, and useful graph and
reproducibility code while removing duplicated management material.

### 2026-06-21 to 2026-06-30 — context expansion and ID safeguards

- **“Document connectome provenance blockers”** made input provenance a first-
  class issue.
- **“Add source context generation tool”**, **“Add context reachability audit
  tool”**, and **“Add simulator sanity audit helper”** established explicit
  sensory contexts and diagnostics.
- **“Add context perturbation sweep runner”** and **“Preserve explicit sugar
  source IDs from completeness table”** connected contexts to perturbation
  runs.
- **“Add ID space audit tool”** and **“Fix safe parsing of large FlyWire IDs in
  source contexts”** addressed the danger of treating opaque FlyWire root IDs as
  ordinary floating-point numbers.
- **“Add targeted context validation runner”** added targeted checks for context
  reachability and run validity.

This work paved the way for the current dual-context design. It is retained
because it protects actual inputs and makes a run reproducible. The explicit
source lists, materialization distinctions, and ID handling are infrastructure,
not biological conclusions.

### 2026-07-11 to 2026-07-18 — reproducibility and test infrastructure

- **“Add metadata-first reproducibility spine”** introduced manifest-first input
  and output handling.
- A sequence of deterministic toy contracts added strict neuron-ID validation,
  known-answer structural tests, vulnerability/lesion fixtures, and fail-closed
  output checks.
- **“Add committed input manifest with checksums for tracked connectome files”**
  recorded file identity and partial provenance.
- Targeted-validation commits added byte-level artifact checks, declared-output
  contracts, and receipt validation.

These changes are retained because they distinguish a reproducible computational
result from an untracked run or an invalid ID/path. Toy fixtures test software
behavior; they are not evidence about fly biology.

Some substantive commits in this period and later periods were created with
editor assistance. The cleanup preserves authorship metadata for retained work;
empty checkpoints and management-only artifacts are removed because they add no
scientific or reproducibility value. Retained code is included because its role
can be inspected and tested, not because of the editing tool used.

### 2026-07-21 to 2026-07-24 — structural controls and second context

- **“Add graph math surrogates for modal controllability, path attenuation, and
  graph-analysis”** added generic structural comparison mathematics.
- **“Add JO 30-trial ground-truth sweep config and runner”** added the second
  sensory context and its ground-truth run entry point.
- **“Add surrogate vs ground-truth Spearman/Pearson correlation harness”** and
  **“Add Sugar vs JO motor context-shift DVI module”** connected structural
  predictors and context comparisons to dynamical outputs.
- **“feat(analysis): complete structural comparison surrogate correlation and
  dual-context DVI comparison”** completed the comparison layer.
- **“fix(pipeline): resolve Bugbot findings for baseline resolution, degree
  binning, rate deltas, and path resolver”** corrected important pipeline
  details.

The generic structural mathematics, JO/sugar runners, null controls, and
pipeline fixes are retained because they support the structure-versus-dynamics
question. Structural proxy outputs are not automatically biological validation.
The current documentation keeps the distinction between a graph metric, a
simulation output, a software test, and a biological claim.

### 2026-07-31 to 2026-08-02 — mixed workspace and cleanup

- **“WIP: stage all working changes before branch cleanup”**, merge commits, and
  cleanup commits bundled useful context work with backups, generated outputs,
  local wrappers, and management files.
- **“chore: finish post-merge cleanup of remote branches scaffolding”** and
  **“chore: remove residual scaffolding”** removed some of that material.

These commits are not all independent scientific milestones. The cleaned history
keeps the source-context, model, perturbation, structural-control, and validation
work that later experiments depended on, rather than deleting every intermediate
script merely because it was written before the final pipeline.

### 2026-08-08 to 2026-08-17 — ground-truth results and statistical consolidation

- **“results: multi-group degree-matched nulls…”**, **“results: JO n=20 sweep,
  Kenyon null, sugar stats+degree nulls”**, and successive dual-context result
  commits recorded the JO and sugar runs and their null comparisons.
- **“chore: commit config that produced n=20 ground truth”** preserved a run
  configuration.
- Documentation and interface commits consolidated provenance and supported
  positional group arguments in null runners.

These outputs are simulation results, not measurements of feeding, grooming, or
behavior. A result is only claim-ready when its materialization, trial count,
seed, baseline matching, transmitter map, null/permutation details, and FDR
status are reported. The retained project treats sugar and JO as relevant
contexts, while avoiding the claim that every historical table is final
evidence.

### 2026-08-30 — statistical and subgraph correction; project reset

- **“fix: correct two-sided empirical p-values and capped-subgraph sampling;
  regenerate null aggregates…”** corrected empirical testing and replaced
  ID-ordered capped-subgraph selection with neighborhood-based sampling.
- **“Reset repo to scientific core…”** removed the large research-management
  bundle, provisional target material, old result dumps, and delivery artifacts
  that were not part of the scientific core.

The subgraph correction matters because an earlier structural comparison used a
broken capped representation for several groups. The apparent structural
correlation from that setup is not a valid finding; the corrected comparison is
the relevant record.

### 2026-09-05 — documentation and conservative cleanup

- **“Document project scope, methods, provenance, and claim limits”** rewrote the
  README around the actual model, inputs, question, assumptions, and limits.
- **“Prune abandoned analyses and preserve project history”** moved useful early
  support and exploratory structural scripts into clearly marked archives while
  removing dead-end code and generated delivery material.
- **“Finalize cleaned project history and infrastructure”** aligned the active
  infrastructure documentation and CI paths.
- **“Remove editor-agent ignore clutter”** simplified ignore rules.

The final active tree is intentionally smaller, but scripts that enabled the
model integration, annotation join, context construction, nulls, structural
comparison, or reproducibility safeguards were retained either in the active
pipeline or in an archive with an explicit non-active status.

## Scientific spine that survives

1. Shiu/Brian2 whole-brain LIF model integration on FlyWire data.
2. Annotation-based neuron-group selection.
3. Output-silencing perturbations with a motor-population readout.
4. The five-trial LO result as a corrected-history lesson, not a discovery.
5. The 30-trial replication and the more careful AN, descending, sugar, and JO
   analyses.
6. Explicit transmitter-polarity assumptions, matched nulls, FDR, provenance
   manifests, and ID/path validation.
7. Structural controls and context comparisons retained as testable computational
   predictors and future-work infrastructure, not biological proof.

## Rules for using this history in Regeneron documentation

- Cite the paper and exact repository/configuration used; do not cite a commit
  message as scientific evidence.
- Distinguish a simulation output, a structural proxy, a software test, and a
  biological claim.
- State what was wrong in the first conclusion: too few trials, no FDR control,
  and an LO direction that did not survive replication.
- Do not claim that output-lesioning measured behavior or proved a feeding or
  grooming circuit.
- Disclose computational assistance if required by the competition or school,
  while keeping the report's scientific prose and interpretation your own.
