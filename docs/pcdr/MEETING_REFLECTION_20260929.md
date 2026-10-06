# Reflection after the meeting with James and Dr. Muldoon

Meeting notes, 29 September 2026.

## What they recommended

James and Dr. Muldoon recommended a substantially smaller simulation time step, giving 0.0001 ms as an example, because of integration accuracy in the LIF model. They otherwise thought the work sounded good. The recommendation was to continue testing; the hypothesis remains unconfirmed.

The practical lesson is that the completed finer-step comparisons have not settled numerical accuracy. Default averages remained close over the steps tested, but some altered-weight trajectories changed substantially. A finer-resolution follow-up should precede stronger interpretation of those trajectories. Existing results remain evidence at their recorded settings; they should not be overwritten or described as having passed a new convergence test.

## Technical assessment

There is no objection to reducing the time step as a controlled numerical experiment. Preserve the model, weights, neuron and lesion IDs, duration, paired inputs and endpoints so the comparison still addresses timing resolution. A smaller step is not an adverse change to validity when recorded as a separate follow-up. Selecting whichever step gives a preferred response, changing membership along with the step, or treating multiple steps as independent replicates would be inappropriate.

One clarification matters: model.py constructs the neurons with method='linear'. Brian2 2.9.0 identifies this as an alias of exact integration for linear equations. That applies to subthreshold evolution, not exact continuous-time detection of every threshold crossing or network event. The simulation clock still governs threshold checks, resets, refractory recovery and synaptic delivery. The meeting recommendation is therefore reasonable as a network timing/convergence check, without claiming that this implementation uses forward Euler or that every LIF model requires this particular step. [Brian2 integration methods](https://brian2.readthedocs.io/en/2.9.0/user/numerical_integration.html), [clocks and scheduling](https://brian2.readthedocs.io/en/2.9.0/user/running.html#scheduling).

The suggested unit was milliseconds: 0.0001 ms = 0.1 microseconds = 1e-7 seconds. It is not 0.0001 seconds, which equals our original 0.1 ms. A one-second trial at the recommended example has 10000000 ticks: 1000 times the original tick count and 62.5 times the count at 0.00625 ms. These are exact step-count ratios, not measured runtime predictions. Float64 roundoff and repeated event handling also mean that smaller steps alone do not prove monotonic improvement in every measured output.

## Implementation and resource issues found before running

The completed resolution runner accepts only 0.1, 0.05, 0.025, 0.0125 and 0.00625 ms. Merely entering 0.0001 into the old notebook will not execute this experiment. It needs a new, tested extension and a separate frozen plan. The old package and completed source snapshots should stay intact.

The saved-input implementation expands a binary tape to one row per tick and retains two full input-voltage monitors. At 0.0001 ms, the 21-input int8 tape alone is 210000000 bytes. The two 21-cell float64 voltage arrays alone total 3360000000 bytes (3.36 GB decimal), excluding recorded times, allocation overhead, copies, differences, weights and spikes. Ten additional state-recorded cells with two float64 variables plus a Boolean flag in two scheduling slots would add approximately 3.4 GB of raw values, excluding timestamps. These are size calculations from the current code, not a measured peak memory allocation.

At this resolution, production recording should retain full spikes and sparse external-event/delivery evidence rather than full voltage at every tick for all monitored cells. Any recorder or backend change must first preserve events at previously verified settings and agree with the existing before/after delivery method on small test networks. Subsampling the delivery monitor without another validated event record could miss input delivery and is not an acceptable shortcut. Short benchmarks can estimate resources but cannot substitute for one-second scientific trials, because previous large responses developed later in a trial.

## Proposed next work, not yet executed

First, validate step-to-time conversions, delay and refractory boundaries, paired physical input preservation, silent-input behavior and known-answer single-neuron responses at the new steps. Use explicit units and integer-tick checks. Retain the threshold inequality and Brian2 scheduling order. Measure runtime and memory for the intended backend; if a faster compiled backend is introduced, validate it separately rather than silently combining that change with the time-step experiment.

Then run a recorded convergence sequence that includes 0.0001 ms and neighboring steps, for example 0.0008, 0.0004, 0.0002 and 0.0001 ms. This sequence halves the step and exactly divides the original 0.1 ms external grid, the 1.8 ms delay and 2.2 ms refractory duration. It is a proposed sequence, not an adviser-specified requirement or an already frozen job list. Preserve original physical input times; this tests numerical resolution conditional on the same input realization. A finer or continuous-time input-generation study would be a separate change.

Include both questions: the default-setting selected mode and its three existing CCR comparators, and the previously identified altered-weight cases. Retain mode-without-MN9 seed 631405 and MN9-only seed 631430 with matched baselines, rather than only an easy trajectory. A fixed initial seed panel can establish feasibility and expose failures, but must not be reported as replacing the complete thirty-seed default comparison. Determine the full job count after resource measurement; do not extrapolate the old eight-hour package blindly.

Evaluate A and F using the original averaging order, complete mean-response vectors, baseline and lesion spike counts, population time courses, recruitment and MN9 separately. Define practical agreement tolerances before viewing new outcomes, with both absolute and relative criteria where a denominator can approach zero. Agreement of A/F alone will not establish trajectory convergence. Report discrepancies at every tested step. If 0.0002 and 0.0001 disagree materially, the study remains unresolved at that level; 0.0001 is not a reference solution merely because it is the smallest requested value.

Finally, revisit the comparison design. Smaller time steps can address a numerical concern; they do not resolve motor-identity differences, distributional imbalance or forced overlap between comparison sets. Keep the current candidate fixed for numerical comparisons. Additional modes or revised reference sets require their own recorded selection and evaluation rules.

## Current status

Later on 29 September, implementation and short local measurements were completed; see [fine-step tests](FINE_TIMESTEP_TESTS_20260929.md). The paragraph below records the state at the time this reflection was first written.

Completed in this follow-up: reflection, documentation review, code inspection and arithmetic resource estimates. No new simulation, benchmark, timestep support, acceptance tolerance or CCR upload package has been implemented in this meeting-reflection step. Next implementation priority is a validated recording/input path suitable for very fine steps, followed by measured CCR sizing and a frozen convergence plan. The existing PDF exports describe the pre-meeting records and do not yet include this reflection.
