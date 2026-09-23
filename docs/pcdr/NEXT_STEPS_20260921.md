# Completed results and next research steps

Latest:30freshseed replication completed and verified. See SEED_REPLICATION_RESULTS_20260922.md. Original ordering reproduced conditionally on fixed optimized sets; no random-reference confirmation. Next: CCR validation and composition/distributional design audit. No extra jobs queued.

Latest completed stage: all 35 optimized-pilot trials verified. Eigen-set A and F exceeded all five optimized comparisons, but this is descriptive evidence only; 77.06 percent of its response lies off support. MN9/motor membership differs between lesion sets. See OPTIMIZED_PILOT_RESULTS_20260921.md for all results and limitations. No more runs are queued; next step is adviser/design review of reference sampling before confirmation. Earlier notes below are historical.

Latest update after the matching audit on 21 September: five distinct optimized sets meet every unchanged matching requirement (maximum SMD 0.07335). The replay shows incoming strength failed all 50,000 original proposals. See [the full matching audit](MATCHING_AUDIT_20260921.md). The earlier recommendation to diagnose matching is now complete. Next recommendation is a separately amended descriptive optimized-comparison pilot; these examples are not a calibrated random reference distribution. No new simulation has started. The historical account below remains preserved.

Updated 21 September 2026 after the exploratory extension stopped. The original study and the later amendment are separate analyses. The records below retain both outcomes.

## What finished

- All 720 individual-cell trials completed: baseline and 23 lesions, with 30 fresh paired seeds per condition. Targets comprised ten excitatory cells, ten inhibitory cells, two outside-group comparisons and one silent control.
- One secondary test passed BH q < 0.05 across the declared 40-test family: excitatory target 720575940619473624 reduced total motor firing by 52.033 Hz, or 0.612 Hz per motor neuron (q = 0.024). Its MN9 estimate was -0.133 Hz. No MN9 test passed correction. These are selected-cell simulation effects, not feeding measurements or a general E/I comparison.
- The silent control gave zero mean footprint and zero MN9/motor changes; its F is undefined. Other nonsignificant tests do not establish exactly zero effects.
- The original 40-pair search produced 22 stable complete modes. All first 20 75%-power supports contained zero baseline-spiking cells, so the original recruitment selection failed. The independent root-ID join reproduced the counts. Maximum residual among those 20 was 3.726e-15.
- The separately authorized 80-pair search produced 45 stable complete modes. Four candidates among the first 40 were eligible. The recorded ranking rule selected rank 33 (zero based), with 51 support cells, 29 meeting the five-spike criterion and whole-vector recruited power 0.5379352785.
- Strict matching then accepted zero of five required control sets after 50,000 proposals. The controller stopped before any eigen-set lesion. The primary localization hypothesis remains untested.

## What I recommend next

The immediate next step is a descriptive matching-feasibility audit for the fixed 51-cell target. Examine exact model-sign/recruitment pool sizes, feature ranges and attainable joint balance. Rejected-set balance vectors were not saved, so the present records do not show which constraint prevented acceptance. Zero accepted samples does not prove that valid controls do not exist.

Keep the target and SMD <= 0.1 balance requirement unchanged during that audit. If a different sampling algorithm is justified, record its proposal distribution, budget, seeds and acceptance checks as a separate exploratory amendment before lesions. Do not silently substitute another mode, relax balance or keep expanding the eigen-search. No such new experiment was launched during this handoff.

Also inspect all 30 paired-seed changes and the full footprint for the one motor-associated cell. Analysis selected because that cell stood out is exploratory. A fresh-seed replication needs a separately declared test; the discovery p-value cannot serve as replication evidence.

## How the annotation audit informs interpretation

The saved-support audit joined annotations by exact root ID and retained missing labels. The table includes cell classes for the original 22 modes, not measured neuropil synapse distributions. An annotation-row match does not guarantee that its cell_class field is populated: Annotated counts matched rows, while unavailable in the class column includes missing class labels within matched rows.

Pospisil and colleagues report anatomically localized modes, including a leading visual circuit. This motivates examining our support annotations, but does not establish that our v630 supports share their identities. Their dataset and matrix preparation differ. [Pospisil et al., 2024](https://www.nature.com/articles/s41586-024-07982-0).

Shiu and colleagues assume zero basal firing. A structural mode can therefore be present without its support cells being recruited by a given input. This makes context mismatch plausible, not proven; it does not establish recruitment as the explanation for lesion effects. [Shiu et al., 2024](https://www.nature.com/articles/s41586-024-07763-9).

## What remains unperformed

- The five-control, five-seed mode pilot: blocked by matching, with no trials created.
- The 199-control, 30-seed confirmation: not run.
- Alternative sensory contexts, active-subnetwork modes, altered-network sensitivities and CCR backend benchmarking: not run.
- A mathematical feasibility proof or validated alternative control sampler: not performed.

The handoff, annotation table and complete single-cell results follow. Their data, commands and manifests are saved in results/pcdr/ccr_singles_20260919, results/pcdr/local_followthrough_20260920 and results/pcdr/exploratory80_20260921. Preserve all three records when discussing what the study establishes.
