# 02 Methods Master

Last updated: 2026-06-10  
Methods version: v0.3-living-record

This is the current accepted methods description. Historical or rejected methods belong in `05_CODE_CHANGELOG.md` and `07_ISSUES_AND_CAVEATS.md`.

## Computational framework

Simulations use a whole-adult-Drosophila leaky integrate-and-fire model based on the Shiu et al. computational brain framework. The modeled network contains 127,400 neurons and approximately 50 million synaptic connections derived from the FlyWire connectome. The model is implemented in Brian2 and stores spike-event outputs as Parquet files with trial number, spike time, FlyWire root ID, and experiment name.

Neuron dynamics follow a leaky integrate-and-fire formulation with resting/reset voltage of -52 mV, threshold of -45 mV, membrane time constant of 20 ms, synaptic decay constant of 5 ms, refractory period of 2.2 ms, synaptic delay of 1.8 ms, and default synaptic scaling of 0.275 mV per signed/weighted synaptic unit. The current project preserves the upstream physical parameters unless a documented methods-version change states otherwise.

## Connectivity and synaptic sign

Connectivity is loaded from the completeness/materialization table and the connectivity Parquet file. The Brian2 network connects presynaptic indices to postsynaptic indices and sets synaptic weights using the signed connectivity column (`Excitatory x Connectivity`) multiplied by the synaptic weight constant. Positive and negative signs are inherited from neurotransmitter-informed upstream preprocessing.

## Sensory stimulation

### Feeding / sugar stimulation

The current feeding condition stimulates 21 right-side sugar-responsive gustatory neurons. External input is delivered with Brian2 `PoissonInput` at 150 Hz, with the upstream default scaling factor. Simulations currently run for 1.0 s per trial in paper-quality analyses. Early setup tests used 500 ms and must be labeled as setup/prototype runs.

### Grooming / Johnston’s Organ stimulation

The planned or documented grooming condition stimulates Johnston’s Organ neurons, including JON-CE, JON-F, and JON-D classes. The user-provided methodology specifies 146 Johnston’s Organ neurons and Poisson input at 150 Hz. Until corresponding result files are registered, grooming should be documented as a parallel protocol or planned comparison, not as a completed feeding result.

## Cell annotation and group selection

Neuron labels are loaded from the FlyWire annotation TSV and joined to modeled neuron root IDs. The local annotation join documented 139,244 annotation neurons, 127,400 simulation neurons, and 106,216 overlapping neurons, giving 83.4% coverage. Group selection is performed by matching annotation fields such as `super_class`, `cell_class`, or `cell_type`, then passing the resulting root IDs into the perturbation engine.

## Perturbation protocol

Targeted silencing is implemented by setting all outgoing synaptic weights from selected neurons to zero. In model terms, this removes the target group’s downstream output while preserving the rest of the network. This should be described as output silencing or axonal-output removal, not as a detailed simulation of all biological consequences of optogenetic silencing, hyperpolarization, neuromodulation, or developmental lesioning.

Each perturbation is compared against a matched baseline condition with identical sensory stimulation and model parameters except for the silenced neuron set.

## Motor-output analysis

Motor output is measured by selecting FlyWire neurons annotated with `super_class == "motor"` and computing total motor population firing rate per trial. For descriptive motor-impact summaries, the project reports:

- total motor firing change in Hz,
- number of motor neurons affected,
- number inhibited (`delta_hz < -0.5`),
- number disinhibited (`delta_hz > 0.5`),
- strongest individual motor-neuron effect.

The ±0.5 Hz threshold is descriptive and should not be confused with statistical significance.

## Statistical testing

The current accepted statistical pipeline compares baseline and perturbation conditions using per-trial total motor firing rates. It keeps trials with zero selected-neuron spikes as 0 Hz rather than dropping them. The current code uses Welch’s two-sample t-test (`equal_var=False`) and applies Benjamini-Hochberg false-discovery-rate correction across all valid p-values. Report both raw p-values and FDR q-values when making inferential claims.

Minimum standard for strong claims:

1. baseline and perturbation trial counts must be matched or explicitly justified;
2. zero-spike trials must be retained;
3. trial count must be stated;
4. raw p and FDR q values must be reported;
5. exploratory screens must be labeled separately from validated reruns.

## Graph/pathway analysis

The graph-analysis track treats the connectome as a directed weighted graph. For task-specific pathway analyses, edges point from presynaptic to postsynaptic neurons. Synaptic weight is used directly for strength metrics and converted to path distance as `distance = 1 / weight` for shortest-path-based source-target betweenness.

The preferred control is a degree-matched bootstrap null model. For a focus group such as AN/ascending neurons, the actual group is compared to random samples drawn from a defined null pool while matching the distribution of total synaptic strength. P-values are empirical bootstrap values with a +1 correction, and Benjamini-Hochberg FDR correction is applied across tested metrics.

## Current reporting hierarchy

1. **Validated perturbation results:** central paper/competition claims.
2. **Exploratory perturbation screens:** hypothesis generation only.
3. **Graph/pathway controls:** mechanistic context and reviewer-proofing.
4. **Non-significant results:** honest negative findings, usually supplementary or used to motivate better questions.
