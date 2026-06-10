# 07 Issues and Caveats

## High-priority caveats to preserve in any paper or competition writeup

### 1. Low-trial screens can reverse the apparent sign of an effect

The LO/lobula result is the clearest example. At 5 trials, LO silencing appeared to increase total motor output (+21.0 Hz). At 30 trials, the net effect was negative (-34.4 Hz). The correct interpretation is not that the first result was useless; it was an exploratory lead that required validation.

**Rule:** A 5-trial result can motivate a rerun but cannot be a final claim.

### 2. Silencing model is output removal, not full biological ablation

The current perturbation sets outgoing synaptic weights from target neurons to zero. This is clean for causal network testing, but it does not model every biological effect of optogenetic silencing, cell death, developmental compensation, receptor dynamics, or neuromodulation.

**Recommended wording:** “We simulated output silencing by setting all outgoing synaptic weights from the targeted neurons to zero.”

### 3. Annotation releases and counts must be versioned

The local notebook reports 139,244 annotation neurons, while major FlyWire papers/reporting describe the adult brain connectome around 139,255 neurons. This is likely due to release/version/file differences. Do not mix counts without stating file version.

### 4. Trial-level rate code must keep zero-spike trials

Dropping zero-spike trials biases rates upward and can change significance. The current statistics code fixes this by reindexing all trials and filling missing selected-neuron counts with 0.

### 5. Raw p-values are not enough

The project tests multiple groups. Current results should use Benjamini-Hochberg FDR q-values for final claims. Raw p-values can be reported but should not be the only inferential criterion.

### 6. Global graph centrality is not the same as task-specific functional relevance

If AN/ascending neurons are not globally enriched under a degree-matched null, that does not invalidate the perturbation result. It may mean that the relevant property is source-to-motor pathway placement, not whole-brain centrality.

### 7. Motor-neuron “inhibited/disinhibited” thresholds are descriptive

The current motor-impact summaries use thresholds such as ±0.5 Hz for direction counts. This is useful for descriptive figures but is not equivalent to neuron-level statistical testing unless a neuron-level test is explicitly performed.

## Recommended reviewer-proof phrasing

- Use “model-predicted” instead of “proved” for circuit mechanisms.
- Use “output silencing” instead of “ablation” unless the method changes.
- Use “exploratory screen” for 5-trial results.
- Use “validated rerun” only when matched trial counts and accepted statistics are present.
- Use “non-significant trend” for LO/LHCENT/Kenyon/LOP/ME>LO unless later q-values support significance.
