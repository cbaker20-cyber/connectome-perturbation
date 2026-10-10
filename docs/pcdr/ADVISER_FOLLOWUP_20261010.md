# Update for James and Dr. Muldoon — 10 October 2026

## Question retained

Do concentrated eigenvector supports of the materialization-630 Shiu matrix predict localized firing-rate responses to output lesions, beyond connectivity, strong connections, and recruitment?

An output lesion removes outgoing connections; the footprint is the neuron-by-neuron firing-rate change from paired baseline. A summarizes absolute mean response inside the support, and F its fraction of the network response. Neither is a behavioral measurement.

## Current execution update

A separate four-trial first wave has now been launched in an 8-core, 92-GB, 72-hour allocation (job26428319). The uploaded package checksum passed and all38 implementation tests passed on CCR in64.57seconds, with52dependency deprecation warnings. This status comes from supplied terminal output. The controller's current reference/capacity phase and full-trial starts or completions have not yet been confirmed from progress.json.

The assigned scientific work is seed631401, baseline and mode output lesion, at0.00005 and0.000025ms, each for one simulated second. The four trials start only after reference and concurrent capacity gates pass. This first wave supplies four of the twelve planned trials; the remaining eight belong to later work. No new convergence result is available. The earlier two-hour pilot and its completed short probes remain separate evidence.

## Work since the recorded 29 September meeting

This is a dated summary of substantive research stages, not a count of assistant sessions. Local work uses saved outputs unless explicitly identified as a replay or simulation. Some branches were chosen after seeing results; they are diagnostic, not fresh confirmation.

| Date / work | Where; change tested | Completed result | What it means / convergence |
|---|---|---|---|
| 29–30 Sep: fine-step preparation | Local; bounded recording/input implementation for finer grids | Event-preservation and analytical checks; reference/prefix validation; frozen scientific plan | Implementation checks, not convergence |
| Completed 5 Oct: fine-step study | CCR;0.0008/0.0004/0.0002/0.0001ms;620 one-second trials | Mean selected A22.443–22.635Hz; F22.977–23.085%; all18 full agreement groups failed | Aggregate stability; detailed footprint convergence unresolved |
| 5–6 Oct: event/state/source diagnostics | Saved-output analysis and diagnostic records; trace selected altered-weight burst | Localized candidate source/reset histories and selected G/H connections | Selected mechanism lead; not initiating-cause proof |
| 6–7 Oct: two-connection removal | CCR;4 trials, both connections removed from time zero | Coarser-window non-input spikes15093→1381; finer1435→1436 | Selected burst suppression; earlier histories also changed |
| 7 Oct: late removal | CCR;4 trials, both connections removed at600ms | Coarser spikes15093→1442; finer1435→1459; earlier spikes reproduced | Addresses earlier-history confounding for the intervention, not numerical convergence |
| 8 Oct: separate G/H removal | CCR;8 trials, neither/both/G/H at two steps | Either single removal suppresses broad coarser recruitment; exact references verified | Each connection matters in this selected case; not sufficient or unique causal pathway |
| 8 Oct: comparison-design work | Local; saved contrasts, distribution matching and overlap feasibility | Fixed-comparator ordering persists; distribution imbalance/forced overlap remain; some searches unresolved | No new comparison simulation or eigencircuit-specific confirmation |
| 8–9 Oct: first downstream events | Local saved arrivals and neuron replays | Compatible direct routes;12 selected prefixes reproduce target spike ticks | Conditional propagation account, not whole-network cause |
| 9 Oct: baseline/endpoint checks | Local;all30 baseline pairs | 96.43% of pooled count disagreement lies in shared active cells; substantial differences before endpoint | Not mainly different recruited cells or only a final-boundary effect |
| 9 Oct: local replay | Local;60 early-timing and52 count-selected native prefixes | All112 reproduce saved target spikes; coarse incoming histories retain coarse counts in26 count-selected cases at fine target step | Incoming histories carry selected count differences; does not identify their network origin |
| 9–10 Oct: failed explanatory branches | Local; constructed event mixtures and exact shared-event refractory check | Mixtures depend on rule in21/26 cases; narrow shared-event check covers1.54% of arrivals | Retained as limitations; no claimed timing/count causal split |
| 10 Oct: actual-state/source analysis | Local;26 selected first two-spike gaps | Other-run targets ready but subthreshold;17 below rest; CB4058 largest inhibitory contribution in16 cases/six targets | Conditional lead with repeated-target/reset-history confounding; no source intervention |
| 10 Oct: smaller-step pilot | CCR;2 reference and2 baseline capacity prefixes,10ms each | Both old references exact; all26 spike counts preserved across new steps; smaller timing differences | Four prefixes complete;0/12 full scientific trials started; no new convergence result |

## Every completed trial in the newest ZIP

All use seed631401. All have26 spikes across18 cells, including only3 non-input spikes;23 external events were scheduled and delivered.

| Run | Step (ms) | Wall time (min) | Result |
|---|---:|---:|---|
| Baseline reference |0.0001|4.00|Exact match to archived first10ms |
| Mode-lesion reference |0.0001|4.03|Exact match to archived first10ms |
| Baseline finer probe |0.00005|7.96|Same per-cell counts; maximum timing change0.0001ms from reference |
| Baseline finest probe |0.000025|15.75|Same per-cell counts; maximum timing change0.00005ms from preceding probe |

The12 planned one-second trials (3seeds × baseline/mode ×2new steps) did not start because they could not fit the bounded work window. Each row is listed in SMALLER_STEP_RESULTS_20261010.md. No new-step lesion footprint is available. These short checks precede the later interval where earlier full runs diverged.

## Separate connection experiment: individual results

One selected altered-weight seed631430; existing MN9 lesion;750ms total. Intervention at600ms; table measures non-input activity in[650,730)ms. Delta is relative to the unchanged switch at the same step.

| Step (ms) | Removal | Spikes | Spike change | Newly recruited cells | Convergence status |
|---|---|---:|---:|---:|---|
|0.0004|None|15093|0|7623|Not established |
|0.0004|Both|1442|-13651|1|Not established |
|0.0004|G only|1388|-13705|1|Not established |
|0.0004|H only|1489|-13604|1|Not established |
|0.0002|None|1435|0|4|Not established |
|0.0002|Both|1459|+24|6|Not established |
|0.0002|G only|1388|-47|6|Not established |
|0.0002|H only|1388|-47|6|Not established |

Equal totals for the finer single removals conceal different spike times. Interventions and cases were selected from earlier outputs. These are not independent replicates of the eigencircuit comparison.

## Next decision

A full-duration, fixed-seed pilot at the two prepared smaller steps is the next direct test of the unresolved numerical question. Current short-prefix screen:26.52/52.51hours per full trial and474.22serial worker-hours for12. These estimates include a2×margin but do not guarantee actual throughput. Validate bounded parallel execution and one full paired seed before expansion. Do not substitute shorter trials, change criteria, or treat the three-seed pilot as the original30-seed confirmation. If disagreement persists, seek advice on an independently validated event reference or a separately specified ensemble-footprint question instead of unlimited halving.

Local checks use separate calculations but are not independent human review. The original research question, criteria and failed findings are retained. Detailed protocols and evidence accompany this summary.
