# Competition Readiness Packet

## Working title

Context-Specific Perturbation Analysis of Sugar-Evoked Motor Output in a FlyWire-Derived Drosophila Connectome Model

## Research question

Does corrected sugar input produce a context-specific AN-linked motor-output effect in a whole-brain Drosophila simulation, and can that effect be separated from broad graph-level AN enrichment claims?

## Short abstract

This project tests whether sensory context changes the predicted effect of ascending-neuron perturbations in a FlyWire-derived Drosophila connectome model. The original hypothesis was broad: AN neurons might generally mediate sugar-evoked motor output. Early graph-level analyses did not support that broad claim. The project therefore shifted to a more careful question: whether AN perturbation has a context-specific effect under corrected sugar input.

A major technical issue was identified during the work. Some 18-digit FlyWire root IDs were parsed through floating point before integer conversion, which silently corrupted source IDs. After switching to direct integer parsing, the corrected sugar source set recovered to 21/21 IDs and aligned with the connectivity table. With corrected contexts, a small targeted Brian2 validation matrix compared sugar, gustatory, mechanosensory, and sensory_ascending inputs against AN and brain_motor_neuron lesion targets. The strongest pilot result was sugar to AN, with mean_abs_motor_delta = 1.4706, l2_motor_delta = 35.0888, top10_motor_shift = 104.0, and 22/85 motor neurons affected.

The result is not treated as a final biological mechanism. AN effects were weak in mechanosensory and sensory_ascending contexts, and the validation used n_run = 3. The current contribution is a corrected, reproducible framework for testing context-specific perturbation effects, plus a clear next step: higher-trial sugar and gustatory reruns under one backend with manifest-tracked inputs and outputs.

## Novelty statement

The project is strongest because it does not force the original hypothesis to be true. It found a real source-ID bug, corrected it, rejected the broadest AN-enrichment framing, and then used the corrected model to define a narrower context-specific validation target. The novelty is not just the pilot sugar-to-AN result. The novelty is the combination of ID-space correction, graph-versus-dynamics comparison, and conservative claim control inside a reproducible connectome perturbation workflow.

## Current evidence

- Corrected direct integer parsing recovered the sugar source set to 21/21 IDs.
- Context sets aligned with the connectivity table after the parsing correction.
- The targeted pilot matrix produced the strongest motor-output shift for sugar to AN.
- AN effects were weak in mechanosensory and sensory_ascending contexts.
- Positive-control brain_motor_neuron lesions produced large shifts in sugar and gustatory contexts, supporting model responsiveness.

## Claim boundary

Supported as a preliminary model result:

The corrected sugar input context produced the strongest AN-linked motor-output shift in the pilot validation matrix.

Not supported yet:

- AN is a proven biological mediator of sugar behavior.
- AN is broadly enriched across all sensory-to-motor paths.
- The structural surrogate alone predicts nonlinear motor output.
- The result is statistically final.

## Methods summary

The project uses FlyWire-derived connectivity, annotation tables, corrected source context files, and a Brian2 whole-brain simulation framework. Source contexts are defined as matched-size input sets. Perturbations are modeled as lesion targets grouped by annotation class. Motor-output effects are measured by comparing motor neuron firing-rate changes between intact and perturbed runs.

The current targeted matrix uses four input contexts: sugar, gustatory, mechanosensory, and sensory_ascending. The primary targets are AN and brain_motor_neuron. Output metrics include mean_abs_motor_delta, l2_motor_delta, top10_motor_shift, affected motor count, strongest inhibition, and strongest disinhibition.

## Limitations

The pilot validation used n_run = 3, so it is not final. The complete pilot table also came from a rescue workflow after Windows blocked Brian2 Cython-generated DLLs, so the next validation should use one backend consistently. The AN target is broad, with more than 2,000 neurons lesioned in the pilot. For a stronger biological story, the next analysis needs to refine AN into a smaller candidate subset.

## Next experiment

Run a higher-trial validation focused on the most informative matrix:

- sugar to AN
- sugar to brain_motor_neuron
- gustatory to AN
- gustatory to brain_motor_neuron

Use one backend, preferably NumPy on the current Windows machine, and write a run manifest before interpretation. The run should produce a ranked summary and preserve null or weakened results rather than only reporting positive outcomes.

## Judge questions and answers

### Why did the project change from a broad AN hypothesis to a context-specific hypothesis?

Because the broad graph-level analyses did not support a general AN-enrichment claim. Keeping that claim would overstate the evidence. The corrected and more defensible question is whether AN has a sugar-specific model effect.

### What was the most important technical correction?

The most important correction was avoiding float conversion for 18-digit FlyWire root IDs. Floating point conversion can change the last digits of large IDs, which changes which neurons are actually selected.

### Why is sugar to AN interesting if it is only preliminary?

It was the strongest row in the pilot validation matrix and affected 22/85 motor neurons. That does not prove a biological mechanism, but it gives a specific target for higher-trial replication.

### What would weaken the current story?

If the higher-trial rerun shows that sugar to AN is unstable, smaller than the positive control, or similar to unrelated contexts, then the sugar-specific interpretation weakens. That would still be useful because it would prevent an unsupported claim.

### What would make the project stronger?

The next step is a clean higher-trial rerun under one backend, followed by AN subset refinement. The project becomes stronger if the sugar-specific effect reproduces and can be narrowed to a smaller, biologically interpretable candidate group.
