# 01 Living Research Log

This file is the chronological scientific notebook. It is reconstructed from the attached journal entries and should continue from here. Each entry should include what changed, why it changed, exactly what was run, what happened, and how the interpretation changed.

---

## Entry 001 — Setup and first simulation

**Date:** 2026-03-20  
**Status:** completed  
**Type:** infrastructure / first model run

### Goal

Get the Shiu et al. whole-Drosophila-brain leaky integrate-and-fire model running locally and confirm that sensory input produces propagated spiking activity.

### Work performed

- Set up WSL2/Ubuntu on a Windows PC.
- Installed Python, GCC, Git, Brian2, and dependencies.
- Cloned the upstream model repository and created a local project repository.
- Ran a 500 ms test simulation with 10 sugar-responsive sensory neurons activated.
- Corrected a neuron ID mismatch by using the IDs from the example notebook rather than guessed IDs.

### Outcome

- Spikes recorded: 2,422.
- Unique neurons that fired: 261.
- Runtime: about 33 seconds.
- Result: model produced a real propagated signal through the connectome.

### Scientific consequence

This established that the local environment could reproduce a biologically grounded whole-brain signal propagation run.

### Caveats / notes

- WSL default memory caused instability; `.wslconfig` was increased to 12 GB.
- Brian2 C++ code generation required GCC.
- Poisson input introduces trial-to-trial stochasticity, so multi-trial averaging is required.

---

## Entry 002 — Perturbation engine

**Date:** 2026-03-26  
**Status:** completed  
**Type:** code infrastructure / perturbation framework

### Goal

Build a systematic lesion/silencing framework around the Shiu model so arbitrary neuron groups could be silenced and compared against baseline stimulation.

### Work performed

- Built `baseline.py` to run sugar activation with no silencing.
- Built `analyze.py` to load Parquet outputs and compute firing rates.
- Built `perturb.py` to sweep over defined groups, call the model, and compare against baseline.
- Tested three random 10-neuron groups.

### Outcome

- Baseline had 403 active neurons in the early run.
- Random perturbations affected about 240–280 downstream neurons.
- The pipeline worked end-to-end.

### Scientific consequence

This converted the project from “run the model” into “test causal perturbation hypotheses.”

### Caveats / notes

- The upstream `silence()` method zeros outgoing synaptic weights from target neurons.
- Parallel `n_proc=-1` caused memory problems in WSL; sequential `n_proc=1` became the stable default.
- Early runs used 5 trials for speed and must be treated as exploratory.

---

## Entry 003 — FlyWire annotation join and first biological perturbation

**Date:** 2026-03-30  
**Status:** completed  
**Type:** data integration / first biologically meaningful experiment

### Goal

Connect simulation neuron IDs to FlyWire cell annotations so perturbation targets correspond to real biological classes instead of random IDs.

### Work performed

- Downloaded FlyWire annotation TSV.
- Joined annotation root IDs with the modeled neuron list.
- Built `cell_groups.py`, which retrieves neuron IDs by `cell_class`, `super_class`, or `cell_type`.
- Silenced all descending neurons and measured the effect on motor neurons.

### Outcome

- Annotation neurons: 139,244 in the local annotation file.
- Simulation neurons: 127,400.
- Overlap: 106,216 neurons, 83.4% coverage.
- Descending perturbation: most motor neurons dropped firing; 3 motor neurons increased firing.

### Scientific consequence

The first meaningful biological finding was disinhibition: some motor neurons appear actively suppressed under baseline feeding/sugar stimulation and are released when descending outputs are removed.

### Caveats / notes

- The first descending result should be preserved but tied to exact trial count/output file.
- “Disinhibition” should be described as a model-inferred circuit mechanism, not direct experimental proof.

---

## Entry 004 — Super-class perturbation sweep

**Date:** 2026-03-30  
**Status:** exploratory screen  
**Type:** perturbation screen

### Goal

Sweep major FlyWire super-classes and quantify how silencing each group changes total motor neuron firing.

### Work performed

Silenced seven super-classes: optic, central, sensory, ascending, descending, visual_projection, and motor.

### Outcome

| Group | Motor delta Hz | Motor neurons affected / direction |
|---|---:|---|
| sensory | -1,119.6 | 23 affected |
| central | -1,117.4 | 23 affected |
| descending | -200.4 | 19 inhibited, 5 disinhibited |
| ascending | -124.4 | 21 inhibited, 1 disinhibited |
| optic | -88.2 | 19 inhibited, 3 disinhibited |
| motor feedback | -49.8 | 16 inhibited, 6 disinhibited |
| visual_projection | -27.0 | 12 inhibited, 7 disinhibited |

### Scientific consequence

The sweep suggested that sensory and central neurons produce the largest absolute motor effects, while descending neurons have a strong effect relative to group size. It also suggested that disinhibition is not isolated to one group.

### Caveats / notes

This was a 5-trial screen and should be used for hypothesis generation, not final significance claims.

---

## Entry 005 — Cell-class sweep

**Date:** 2026-03-31 to 2026-04-01  
**Status:** exploratory screen  
**Type:** overnight cell-class sweep

### Goal

Move from broad super-classes to cell-class-level perturbations and identify candidate classes for validation reruns.

### Work performed

- Ran 27 cell classes with at least 20 neurons each.
- Saved results progressively to avoid losing overnight work.

### Exploratory notable results

| Cell class | Exploratory motor delta Hz | Interpretation at the time |
|---|---:|---|
| LO | +21.0 | looked like strong disinhibition |
| AN | -142.6 | looked like pure excitatory drive |
| LOP>LO.ME | -70.2 | efficient small group |
| ME>LO | -79.2 | large visual group |
| LHCENT | -1.0 | tiny group with mixed direction |
| Kenyon_Cell | -9.4 | mushroom-body-related trend |

### Scientific consequence

This identified LO, AN, LOP>LO.ME, LHCENT, ME>LO, and Kenyon_Cell as candidate groups for 30-trial validation.

### Caveats / notes

The LO interpretation was later revised. The screen was useful because it identified candidates, but it was not reliable enough for final signs/effect directions.

---

## Entry 006 — 30-trial validation rerun

**Date:** 2026-04-02  
**Status:** validation / revised findings  
**Type:** high-quality rerun

### Goal

Rerun the six most interesting cell classes at 30 trials to test whether the 5-trial screening patterns were stable.

### Outcome

| Cell class | Motor delta Hz | Inhibited | Disinhibited | Mean | Std | Status |
|---|---:|---:|---:|---:|---:|---|
| LO | -34.4 | 10 | 6 | -1.49 | 3.22 | revised from 5-trial screen |
| AN | -129.4 | 20 | 1 | -5.62 | 3.87 | robust |
| LOP>LO.ME | -20.6 | 10 | 5 | -0.89 | 2.16 | trend |
| LHCENT | -29.2 | 11 | 5 | -1.27 | 2.38 | interesting small group |
| ME>LO | -14.8 | 11 | 5 | -0.62 | 1.65 | trend |
| Kenyon_Cell | -33.4 | 14 | 3 | -1.45 | 2.07 | trend |

### Scientific consequence

LO changed from an apparent net disinhibition effect at 5 trials to a net inhibitory effect at 30 trials. This became a central rigor lesson: low-trial stochastic screens can identify candidate groups but can misstate effect direction.

### Current interpretation

AN/antennal neurons are currently the strongest cell-class-level feeding motor drive candidate. LO still shows some disinhibited motor neurons, but net LO silencing reduces motor output at 30 trials.

---

## Entry 007 — Statistical validation

**Date:** 2026-04-02  
**Status:** validation / statistical refinement  
**Type:** inferential statistics

### Goal

Compare total motor firing per trial between baseline and perturbation conditions, avoiding underpowered/mismatched comparisons.

### Work performed

- Used per-trial total motor firing rates.
- Matched baseline and perturbation trial counts after an underpowered baseline issue was discovered.
- Used two-sample testing; current code implements Welch’s t-test.
- Added multiple-comparison correction in the current statistics pipeline.

### Logged results from notebook

| Condition | Delta Hz | p value | Status in notebook |
|---|---:|---:|---|
| sensory | -1120.6 | ~0.0000 | significant |
| central | -1122.0 | ~0.0000 | significant |
| descending | -205.0 | ~0.0000 | significant |
| AN | -134.0 | ~0.0000 | significant |
| ascending | -129.0 | 0.0021 | significant |
| LO | -39.0 | 0.1270 | ns |
| LHCENT | -33.8 | 0.1579 | ns |
| Kenyon_Cell | -38.0 | 0.1047 | ns |
| LOP>LO.ME | -25.2 | 0.2860 | ns |
| ME>LO | -19.4 | 0.4033 | ns |

### Scientific consequence

The project now has a stronger result set centered on robust feeding motor-output reductions from sensory, central, descending, AN, and ascending perturbations. Non-significant classes should be framed as trends or supplementary, not central claims.

### Caveats / notes

- The exact current `statistics.csv` should be archived alongside this entry.
- Report FDR-corrected q-values when using the current code pipeline.
- Never mix raw p-value claims and FDR-corrected claims without labeling them.

---

## Entry 008 — Graph/null-model rigor track

**Date:** 2026-06-10  
**Status:** active analysis track  
**Type:** graph validation / null-model design

### Goal

Avoid overclaiming graph-theoretic enrichment by comparing observed groups against degree-matched null samples and by distinguishing whole-brain centrality from task-specific pathway centrality.

### Work performed / implemented

- Added or reviewed a path-analysis framework using directed weighted edges.
- Converts synaptic weight to path distance as `1 / weight`.
- Computes source-target betweenness from sugar sensory sources to motor targets.
- Runs degree-matched bootstrap null tests and applies Benjamini-Hochberg FDR correction.
- Added audit logic for zero-valued graph metrics and null values so zeros are not silently dropped.

### Scientific consequence

This protects the project from a common mistake: claiming that a functionally important group must also be globally central. A group can be behaviorally important because it lies on the relevant source-to-target pathway, even if it is not globally enriched under a degree-matched null.

### Caveats / notes

- Negative graph-centrality results should be treated as useful controls, not failures.
- Keep graph claims separate from perturbation claims unless explicitly integrated.

---

## Template for next entry

Copy `templates/daily_lab_entry_template.md` below this line for future work.
