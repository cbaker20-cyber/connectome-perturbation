# Explaining the study

A short meeting guide, current through 29 September 2026. Read the [overview](RESEARCH_OVERVIEW.md) for the full sequence.

## What can I present today?

The defensible result is a reproducible simulated response for one exploratory structural candidate. In a separate 30-seed replication, its 51 cells had A = 22.544 Hz and contained 23.12% of the absolute mean response. This exceeded the five fixed comparisons, but about 77% remained outside, and the comparisons do not isolate eigenmode membership from other properties. The study has identified a candidate worth investigating, not established an independent circuit or confirmed the main hypothesis. [Replication numbers](SEED_REPLICATION_RESULTS_20260922.md), [comparison limitations](MOTOR_SET_AUDIT_20260922.md).

## What is the question?

Can a small neuron set identified from a connectome eigenvector predict where a simulated brain responds to an outgoing-connection lesion, beyond connectivity and baseline activity? P/D/C/R organize overlapping explanations: eigenmode information, degree/strength, strong connections and recruitment. We have not isolated an eigenmode-specific effect. [Original question](PLAN.md#question).

## Why these papers?

[Pospisil et al.](https://doi.org/10.1038/s41586-024-07982-0) motivate structural-mode selection for dynamical study. [Shiu et al.](https://doi.org/10.1038/s41586-024-07763-9) provide the spiking model. Our lesions are not stimulation along an eigenvector or an experimentally measured effectome. Simulated MN9 firing is not observed feeding. [Paper discussion](CCR_RESULTS_20260927.md#paper-review-and-implications-for-this-procedure).

## What happens in a trial?

Twenty-one sugar-input neurons receive stimulation. Baseline and lesion share scheduled physical input events. A lesion removes outgoing weights; selected cells can still receive input and spike. Delivered events are also checked because delivery can depend on refractory state. An early mismatch showed why a shared seed alone was insufficient. [Methods](PLAN.md), [correction history](LAB_NOTEBOOK.md).

## What are A and F?

Average each neuron's signed lesion-minus-baseline rate changes across paired seeds, then take absolute values. A is the average absolute change inside the selected set, in Hz. F is the fraction of the whole-network absolute change inside it. F is undefined if the total is zero. F near 0.23 means roughly 77% remains outside: relatively greater concentration does not mean independence. [Readout code](../../eigencircuits/readouts.py), [pilot interpretation](OPTIMIZED_PILOT_RESULTS_20260921.md).

## Did the original test succeed?

The original first-20-mode screen found no eligible support under sugar stimulation. A separately declared deeper exploratory search found four eligible candidates among the first 40 stable complete modes and selected rank 33, with 51 cells. The four were not matches to correlation clusters. The subsequent comparisons concern the exploratory candidate. [History](LAB_NOTEBOOK.md), [experiment sequence](RESEARCH_OVERVIEW.md#3-experiment-sequence-and-why-each-stage-exists).

## How well have the four candidates been examined?

Today's review reproduced the original supports and recruitment values for all 40 screened modes. The four eligible supports have 819, 51, 813 and 724 cells; respectively 17, 29, 27 and 15 meet the original five-pooled-spike rule. The selected 51-cell support has 28 cells active in all five selection trials. The other three candidate lesions have not been tested in this comparison series, so we cannot rank their dynamical effects.

Rank 33 stays selected at 75% and 90% support across pooled-spike thresholds 1, 5 and 10. At 50% no mode qualifies: rank 33's smaller 15-cell support has only nine qualifying cells, below the rule's ten. Selection is therefore not independent of the support convention. All four saved eigenpairs pass the matrix-residual check; this verifies the structural calculation, not biological identity. [Complete candidate review and tables](RESEARCH_OVERVIEW.md#8-candidate-review-for-the-meeting-29-september).

## What is the strongest finding?

The selected mode has greater A/F than the fixed comparisons at default. Its mean results reproduce across fresh input seeds and remain close across tested clock steps. This supports a reproducible response for that candidate in this model, not independence or superiority beyond every alternative explanation. [Seed replication](SEED_REPLICATION_RESULTS_20260922.md), [time-step results](CCR_RESULTS_20260927.md#completed-530-trial-time-step-comparison).

## Why aren't the controls enough?

They were optimized, overlap substantially and retain distribution differences despite similar means. Nine memberships produced only three distinct observed response patterns. Matching motor counts does not match motor identities or MN9 membership. Some strata force shared cells into every eligible set. More seeds cannot fix this. [Distribution audit](MOTOR_SET_AUDIT_20260922.md), [composition results](MOTOR_COMPOSITION_RESULTS_20260922.md), [later review](CCR_RESULTS_20260927.md#local-event-and-comparator-review). [Austin](https://doi.org/10.1002/sim.3697) motivates distribution checks; it supplies no fly-specific cutoff.

## Why check time steps after exact replay passed?

Replay asks whether the same setup reproduces events. Time-step testing asks whether numerical resolution changes the result. The high-weight lesion gives 629557 spikes at 0.0125 ms and 17959 at 0.00625 ms. Both replay exactly with recording enabled, yet convergence remains unresolved. File checks cannot choose the correct trajectory. [Recorded replay](OBSERVED_REPLAY.md).

## What did recording show?

The ten recorded cells produce 23 fewer spikes where the whole network produces 611598 more. They miss the population responsible for the increase. Full spike records identify 11530 cells active only in the large-response run, with 577 recruited before 180 ms. Those groups use known outcomes; they describe the response rather than independently predict it. [Trace analysis](CCR_RESULTS_20260927.md#local-state-trace-analysis), [recruitment](CCR_RESULTS_20260927.md#recruitment-outside-the-recorded-cells).

## How reliable is reconstructed input?

It reproduces 4.8 million recorded cell/tick increments within the declared tolerance and matches refractory flags exactly. A second counting method reproduces 2308 target/run comparisons. These validate the tested calculation, not full voltage or causality. About 90% of positive arrivals in selected pre-spike windows come from the early-recruited group, but the earliest cells need another explanation. [Validation](CCR_RESULTS_20260927.md#incoming-event-reconstruction-test-29-september), [source analysis](CCR_RESULTS_20260927.md#source-partition-check-and-broader-tests-29-september).

## What limitations should I state directly?

The 75% support rule, clustering cut, matching tolerances and timing windows are operational choices, not universal biological constants. Some were fixed before results; others explicitly use known outcomes. Seeds are not animals, and neurons/time bins are not independent replicates. More compute does not repair imperfect comparisons. Passing software tests does not confirm a biological hypothesis. [Decision rationale](RESEARCH_OVERVIEW.md#4-decision-rationale-and-what-is-not-established).

## What next?

Validate the earliest targets' state reconstruction and inspect their sources before choosing an intervention. Separately, define a defensible comparison design or narrow the claim. Another broad simulation run is not yet justified. The current conclusion is candidate-specific reproducibility with unresolved comparison and high-weight numerical limitations. [Current stopping point](RESEARCH_OVERVIEW.md#6-verification-and-stopping-point).
