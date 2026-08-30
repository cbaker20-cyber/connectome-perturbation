# Research question (reset, 2026-08-30)

This file states the question the project is now built to answer. It lists
**competing accounts that already exist in the literature**. It does not pick
one of them. A Regeneron report that treats a search-engine summary, a model
default, or a single paper as *the* truth is a weaker report than one that
says which account the experiment can distinguish.

## Question

When a set of neurons is **output-lesioned** in a signed whole-brain leaky
integrate-and-fire model of adult *Drosophila*, is the change in **motor
population firing** predicted by the **sign and weight of their outgoing
synapses** (a static, signed-graph account), or does the **sign of the effect
require the nonlinear, activity-dependent dynamics** of the network
(disinhibition / disfacilitation / silent inhibition)?

Unit of analysis:

```
(input context s, lesion set c, I:E weight ratio r, NT-sign map m)
    →  ΔHz_motor
```

`ΔHz_motor` is simulated motor-neuron firing under lesion minus the matched
baseline. It is **not** measured behavior.

## Why this is still open

These are independent published positions, not a ranked list.

1. **Shiu et al., 2024, *Nature*** built the LIF whole-brain model this repo
   uses. They report that connectome weights matter (shuffling them hurts
   predictions) and that the model **failed to predict behavioural results
   when the tested neurons were predicted inhibitory or neuromodulatory**.
   They also assume equal |E| and |I| magnitudes, glutamate as inhibitory,
   and a basal rate of 0 Hz. Those are stated assumptions, not settled facts.

2. **Eckstein et al., 2024** provide predicted transmitters. Prediction is
   not the same as a measured synapse sign. Glutamate in flies can act at
   inhibitory GluCl channels or at excitatory glutamate receptors. Collapsing
   glutamate to one polarity is a modeling choice.

3. **Chen & Xi, 2025 (bioRxiv)** argue that escape suppresses feeding by
   **upstream disfacilitation of a premotor center**, not by lateral
   inhibition onto the feeding motor neuron MN9, and that the architecture is
   **distributed / redundant**. Under that account, lesioning “the”
   inhibitory class can look weak even if inhibition is doing real work.

4. **Command-neuron vs population** accounts of descending control (e.g.
   Braun et al. 2024 on descending neuron types) disagree about whether a
   small labeled set should dominate motor ΔHz.

None of these papers is “wrong because another paper exists.” They make
different claims at different levels (synapse sign, circuit motif, motor
readout). The experiment is to see which pattern this model actually produces.

## Competing hypotheses (preregistered, all kept live)

| ID | Account | What it predicts for this model |
|---|---|---|
| H1 | Signed-graph | Lesioning cells whose outgoing weights are net inhibitory **raises** motor ΔHz; net excitatory **lowers** it. Rank of \|ΔHz\| tracks signed outgoing strength. |
| H2 | Silent inhibition | If a cell is not recruited by the current sensory drive, lesioning it does nothing, regardless of its transmitter. Sugar vs no-input vs a second context must change the E/I lesion effect. |
| H3 | Distributed redundancy | Large random or class-level inhibitory lesions have small ΔHz because parallel paths remain. Degree-matched nulls of the same size look like the real class. |
| H4 | I:E identification failure | The H1 pattern **flips or vanishes** when the inhibitory:excitatory weight ratio is moved ±50% (the robustness check Shiu already used). |

A result supports an account only if the others are tested in the same run
batch. Confirming H1 at the default ratio and never running H4 is not a
result.

## What this project will not claim from a simulation

- That a cell class “is” a feeding or grooming neuron in the fly.
- That output-lesioning equals optogenetic silencing, cell death, or a
  developmental mutant.
- That simulated motor Hz equals behavior.
- That the most-cited paper on a topic is the correct one.

## First experiment

`scripts/run_ei_lesion_screen.py` lesions polarity groups under two explicit
NT maps (`classical_fast` leaves glutamate unmapped; `shiu_2024` treats
glutamate as inhibitory). Compare ΔHz across maps, contexts, and later I:E
ratios. Report both maps. Do not average them into one “truth.”
