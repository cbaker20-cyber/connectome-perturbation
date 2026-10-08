# Separate G/H removal: results reviewed 8 October

Either single removal interrupts the broad late recruitment in the selected 0.0004-ms case. Joint removal is not required among these tested interventions. This resolves the separate-connection comparison; it does not resolve numerical convergence or establish an eigencircuit-specific effect.

## Design and primary results

Eight trials retained seed 631430, weight scale 1.2, inhibitory scale 0.8, the existing MN9 outgoing lesion, archived stimulation, and 750-ms duration. At each of two steps, unchanged switch, joint removal, G-only removal and H-only removal were applied at 600 ms. G is target 720575940629667639; H is 720575940623862015. Both connections originate at 720575940628695043. Their original scaled weights are 94.38 and 78.21 mV. The intervention changes connection weights; it does not directly silence a neuron.

The declared window remains [650,730) ms. Input cells are excluded. Newly recruited cells have no earlier spike before 650 ms and at least one spike in the window. Counts below were independently recalculated from raw spikes using integer clock ticks and each cell's first spike.

| Step (ms) | Connection removal at 600 ms | Non-input spikes | Newly recruited cells |
|---|---|---:|---:|
| 0.0004 | None | 15,093 | 7,623 |
| 0.0004 | Both | 1,442 | 1 |
| 0.0004 | G only | 1,388 | 1 |
| 0.0004 | H only | 1,489 | 1 |
| 0.0002 | None | 1,435 | 4 |
| 0.0002 | Both | 1,459 | 6 |
| 0.0002 | G only | 1,388 | 6 |
| 0.0002 | H only | 1,388 | 6 |

At 0.0004 ms, G-only removal reduces the window spike count by 13,705 (90.80%); H-only removal reduces it by 13,604 (90.13%). Joint removal gives the previously observed 90.45% reduction. The remaining background activity and one new cell mean this is suppression of broad recruitment, not elimination of all activity.

At 0.0002 ms, each single removal reduces spikes by 47 (3.28%), while joint removal increases spikes by 24 (1.67%). All three interventions increase the small new-cell count from four to six. The finer reference has no corresponding broad burst. Single effects therefore cannot be added to predict the joint result. There is one selected seed, with no sampling inference or p-value.

## Independent verification

The returned ZIP is 1,820,538 bytes and contains 97 files with no duplicate names or CRC errors. SHA-256: `b042e45569de75f90486cef1fe5cacc1917ceb79014c8a9bb8cb9688eb151dca`. Source inventory and every archived source byte match the preserved original upload, SHA-256 `d7f578079ab04e1155148a61646933585f755d5af83383ef4bea1695a5ca6197`. No archived code was executed for review.

All eight manifests, full output inventories/hashes, exact trial identities, original model/data/reference hashes, recorded simulation package versions, successful process exits and 750-ms progress records pass. Stderr is empty for every worker. Python was 3.11.5. The installed-library record matches all listed pinned libraries after case normalization; it omits setuptools, so that record alone does not independently establish the installed setuptools version. The recorded trial package map agrees with the frozen plan.

Every pre-600-ms spike prefix matches the archived original reference exactly. Both unchanged-switch trajectories reproduce the complete 750-ms original. Every scheduled and delivered input table matches the original input tape and delivered reference. Switch indices map to the intended exact string IDs; original scaled weights agree with the connectivity; time and post-switch weights match each condition. Source and both target histories are required and recalculated. Spike checks cover valid IDs, time bounds/order/grid, duplicate events and non-input refractory spacing.

The repeated joint-removal and unchanged-switch trials also match the previous late-pair experiment exactly at both steps: all spike events, scheduled/delivered inputs and saved endpoints. This is reproduction of the same case, not an independent seed replication.

Workers finished by 8 October 05:22:25.989 UTC (1:22:25.989 a.m. Eastern). Coarser trials took 88.5–95.3 minutes each; finer trials took 157.1–164.7 minutes. Recorded peak memory was about 3.00–3.36 GB per worker. The ZIP was visible on CCR at 1:22:27 a.m.; the user downloaded it after automated browser download attempts did not produce a local file. No second run or allocation was launched during review.

## Additional descriptions, chosen after primary review

The first changed event in G-only removal is the missing G spike at 616.7112 ms (coarser) or 603.6980 ms (finer). For H-only removal it is the missing H spike at 618.6280 or 605.6464 ms. In each single removal, the selected target has no post-switch spike; the other target continues to fire. The source's first post-switch spike remains at its reference time. Later histories differ, consistent with propagation through recurrent activity without identifying every route or the initiating numerical difference.

The two finer single removals have equal primary totals and equal total run spike counts, but their spike trains are not identical. They differ in 2,400 neuron/tick events present in only one run; only two neurons differ in total spike count, with an absolute count difference of two. Thus equal totals hide timing differences. At the coarser step, the singles differ in 3,470 such events and 280 per-neuron total counts. These are descriptive comparisons, not convergence tests.

The additional [730,750)-ms check gives:

| Step (ms) | Removal | Non-input spikes | Newly recruited in this later window |
|---|---|---:|---:|
| 0.0004 | None | 15,250 | 1,850 |
| 0.0004 | Both | 256 | 0 |
| 0.0004 | G only | 223 | 0 |
| 0.0004 | H only | 419 | 2 |
| 0.0002 | None | 322 | 2 |
| 0.0002 | Both | 319 | 0 |
| 0.0002 | G only | 356 | 0 |
| 0.0002 | H only | 356 | 0 |

No comparable burst is displaced into the final 20 recorded milliseconds. Activity after 750 ms is unknown. Later-window recruitment means the first spike occurs in that later window, with no spike before 730 ms. These supplementary checks do not replace the original endpoint or introduce an acceptance threshold.

## Decision and remaining research question

The selected case now supports a narrow causal statement: after identical earlier spike histories, removing either of the two source-to-target connections at 600 ms interrupts the observed broad coarser-step recruitment. Neither connection alone is shown sufficient to generate the burst. The result does not show that these are the only effective interventions or establish a biological mechanism. Connections, timing and case were selected after viewing the trajectories.

Do not launch another burst intervention or a broad seed sweep by default. The immediate individual-versus-joint question is answered, and further tracing would chiefly refine a selected, step-sensitive example. A rescue, dose or timing sweep would answer a new question and needs an explicit design; none is prepared or launched here.

The original question remains whether concentrated eigenvector support predicts localized outgoing-lesion responses beyond degree/strength, strong connections and recruitment. These eight trials do not compare eigenvector supports or repair the optimized comparison sets. All 18 full fine-step convergence-group criteria still fail; stable selected-group averages are not trajectory convergence. The next useful research decision is which claim can be supported despite those numerical and comparison limitations, before spending CCR time on another experiment. Review the saved fine-step paired contrasts and comparison diversity against that claim; do not change the declared convergence decision or treat the finest step as exact. This is proposed local synthesis, not completed new evidence or a confirmed eigencircuit result.

## Reproduction and assistance

Run from the repository with `.venv/Scripts/python.exe`:

```text
scripts/pcdr_review_pathway.py --separate --archive CCR_separate_pathway_results.zip --package results/pcdr/separate_package_validation_20261008/original_upload.zip --out <new-review.json>
scripts/pcdr_compare_separate.py --out <new-comparison.json>
-m pytest tests/test_pcdr_review_pathway.py -q
```

Both analysis commands refuse to overwrite their output. The comparison script requires archives to match successful review hashes before comparing tables. Twenty-five focused tests pass, including changed prior archive bytes, changed repeated endpoints and changed repeated spikes. Both older complete reviews still reproduce their saved evidence exactly. These tests verify analysis implementation, not biological validity. Codex assisted code, review and documentation; this page is not an independently student-written submission.

Evidence: [independent eight-trial review](evidence/2026-10-08/separate_review.json), [cross-experiment comparison and supplementary counts](evidence/2026-10-08/separate_comparison.json), [reviewer preparation record](evidence/2026-10-08/separate_reviewer_preparation.json). The preparation record's unavailable status describes the earlier access check and is superseded by this completed review.
