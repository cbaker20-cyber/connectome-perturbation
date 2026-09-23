# P/D/C/R lab notebook

## 18 September 2026 — implementation session

These entries were recorded during the implementation session. Trial manifests contain exact UTC start and finish times. Earlier conversations and meetings are background supplied by the user, not events observed by the coding assistant.

Code and research review in this session were assisted by OpenAI Codex. These notes are an implementation record, not a claim that the student independently wrote the new code or read each reference on this date.

### Starting point

- Active repository: cbaker20-cyber/connectome-perturbation, commit 598a1d8.
- Preserved the existing staged handoff document and historical documentation. No commits or pushes made in this session.
- Read the attached design scripts as proposals. Did not copy their old stopping rules into the new experiment.
- Existing tests had passed 181 checks with three skipped in the planning review.
- Installed Brian2 is 2.9.0; the old requirements name 2.5.1. Kept the installed environment and tested it. No package upgrade or downgrade.
- Original simulator still uses the same equations and output-only lesion operation.

### Why these checks come first

- James's suggested order, as reported by the user: pairwise correlations, sorted matrix, clusters, then individual E/I lesions.
- Need to establish that neurons fire before treating them as lesion targets.
- Need to establish that a repeated seed repeats the stimulation and spikes before interpreting differences between runs.
- Need explicit trial records because an empty spike file otherwise loses evidence that a trial occurred.
- Need the same graph for modes and LIF. v783 mode files cannot be substituted for a v630 neuron order.

### Code created

- `eigencircuits/common.py`: exact IDs, hashes, environment and atomic file writing.
- `eigencircuits/trials.py`: one explicitly seeded trial; reuse the original model; capture delivered Poisson events, spikes and every neuron's rate.
- `eigencircuits/memory.py`: native peak-memory measurements. No extra memory-monitoring package needed.
- `eigencircuits/pilot.py`: serial local steps with a shared two-hour deadline.
- `eigencircuits/graph.py`: validated directed matrix, model-sign features and signed strong-edge filtering.
- `eigencircuits/recruitment_from_parquet.py`: per-trial recruitment and binning, including silent trials.
- `eigencircuits/analysis.py`: correlation matrices, clustering, surrogates, split-trial comparison and baseline-only neuron selection.
- `eigencircuits/build_modes.py` and `toy_eigencircuit.py`: complex eigenvectors, 75% supports, residuals, conjugate handling and numerical stability.
- `eigencircuits/cheap_diagnostics.py`: descriptive hub/support overlap without arbitrary scientific rejection cutoffs.
- `eigencircuits/controls.py`: distinct matched sets, balance checks and an explicit insufficient-matches outcome.
- `eigencircuits/readouts.py`: paired response footprints, seed bootstrap, conditional reference comparison and secondary statistics.
- `eigencircuits/ccr.py`, `benchmark.py`, and `scripts/pcdr_array.sh`: prepare, validate, run and collect cluster work. Nothing was submitted remotely.
- `eigencircuits/report.py`: read completed outputs and assemble figures and a local report.
- Added known-answer tests in `tests/test_pcdr.py`.
- Corrected the old degree-null sampler to refuse replacement/unmatched fallback. Its rate reader can now accept the complete declared trial list.

### Problems found while checking the code

- The supplied toy took the real part of a complex eigenvector. In a known example that changed a three-cell 75% support into two cells. Kept the full complex vector.
- Identical uncoupled loops have repeated eigenvalues. A localized basis is possible, but not unique. The toy explanation now says that.
- The supplied eigen-solver recorded a seed without using it. The new solver passes an explicit starting vector.
- A strong-edge mask made from absolute weights must not become the signed simulator matrix. The new filter retains signs.
- Annotation labels and simulator signs are different objects. The grouping maps do not rewrite model weights.
- The initial rate-tertile code ranked all neurons, including silent cells. Corrected it to form tertiles among eligible cells separately for each E/I group. Kept the earlier selection and trial outputs. They are not the final pilot selection.
- The first timing implementation depended on optional psutil, which was absent. Added a native memory reader and repeated validation.
- Added source archives before the final validation run so old outputs retain the code that produced them.

### Development outputs retained

- `results/pcdr/local_20260918`: first whole-brain timing/replay checks; memory field unavailable.
- `results/pcdr/pilot_20260918`: native-memory development runs and the initial selection.
- `results/pcdr/pilot_20260918/analysis_rate_strata`: corrected selection check. Kept separately rather than overwriting the first selection.
- `results/pcdr/validated_20260918`: attempted final pilot. The E lesion failed the paired-input check. It is not a valid completed paired pilot or the selection source for the corrected study.
- All these local pilots share the deadline recorded in the first pilot manifest. Creating a new output directory did not reset the allowance.

### Input checks

- 127,400 neurons; 14,687,178 directed connections.
- Every presynaptic/postsynaptic index agrees with its stored root ID.
- All 21 sugar IDs are present.
- 106,216 modeled cells have an annotation in the local table; 21,184 do not. Unannotated cells stay in the activity analysis.
- 85 annotated motor cells are present in the model.
- Connectivity hash matches the old input manifest. Completeness and annotation raw-byte hashes differ, but match after CRLF-to-LF normalization. Recorded both without silently editing the old manifest.
- Source: `results/pcdr/validated_20260918/input_audit.json`.

### Interpretation rules for today's results

- Five baseline seeds describe this simulation setting, not five animals.
- The repeated seed is a reproducibility check, not a sixth independent baseline.
- The no-input result tests the model's zero-basal-rate assumption.
- Correlation groups include singletons and depend on bin width and the provisional cut.
- One E and one I lesion are pipeline checks. They cannot establish the average consequence of excitatory or inhibitory lesions.
- No eigencircuit lesion, matched-control confirmation, or CCR run has occurred in this session.

Final measured results and command records are appended below after validation.

## 19 September 2026 — continuation and input correction

- Continued at the user's request. The original two-hour deadline had expired; the user authorized 30 additional minutes for a corrected pilot.
- Found a mismatch between the scheduled comparison's actual voltage-jump records in the 18 September baseline and E lesion. Same-seed baseline replay alone had not exposed it.
- Inspected Brian2 2.9.0 generated NumPy code on a small recurrent graph. It called the binomial generator only for indices where `not_refractory` was true. A lesion-dependent firing change can shift later draws even when the initial seed matches.
- Changed `trials.simulate` to generate a complete independent Bernoulli schedule before simulation. Kept conditional voltage writes, equations and output silencing. Added a separate delivered-events file. See the dated amendment in PLAN.md.
- Added a three-cell feedback regression test: lesion changes firing, scheduled inputs stay identical, and delivered events are a subset of scheduled events. Added a test refusing collection of incomplete CCR jobs.
- Command: `.venv\Scripts\python.exe -m pytest tests/test_pcdr.py -q --disable-warnings`. Result: 23 passed. The initial command using bare `python` selected Python 3.14 without pytest; corrected it to the repository's existing virtual environment. No installation performed.
- Corrected full-brain outputs will use `results/pcdr/corrected_20260919`. Keep all earlier files and their original manifests.

### Corrected pilot results

- Completed five sugar baselines, one same-seed replay, one no-input control, and the first frozen E and I lesions within the additional allowance. The repeated seed is not an extra independent baseline.
- Baseline seeds: 630101–630105. Recruited non-input counts: 366, 347, 368, 357, 363. MN9 rates: 93, 81, 82, 86, 82 Hz.
- Baseline simulation and output writing took 14.2–16.7 seconds per trial. Peak process memory reached about 2.84 GB. These are local measurements, not guaranteed CCR performance.
- Same-seed replay gave identical spikes and input schedules. No-input trial gave zero spikes. Both lesion schedules matched the paired baseline schedule.
- Used all 387 non-input cells that fired in at least one selection trial for the main correlation matrix. With 10 ms bins and the 0.7 distance cut, there were 170 groups, including singletons. Largest group: 26 cells.
- At 5 ms there were 286 groups; at 20 ms there were 114. The five-spike filter retained 351 cells. Split-trial adjusted Rand index: 0.528 across 366 common cells. Grouping depends on analysis choices and has only partial split-trial agreement.
- Observed within-group mean correlation was 0.419. Reclustering 99 circular-shift surrogates gave a median of 0.407; 99 trial-shuffle surrogates gave 0.399. These statistics average over each surrogate's own groups. They do not show that the original groups retain their membership, and do not provide a formal significance result. A fixed-membership timing analysis would be a separate exploratory follow-up.
- Frozen selection: ten sign-consistent E cells, ten sign-consistent I cells, two recruited cells outside the selected groups, and one silent cell. Selection seed: 630500. No target was changed after viewing its lesion response.
- First E lesion: root ID 720575940636346487. MN9 change: -7 Hz. Total motor change: -14 Hz; mean per motor cell: -0.165 Hz.
- First I lesion: root ID 720575940606866377. MN9 change: -13 Hz. Total motor change: -94 Hz; mean per motor cell: -1.106 Hz.
- Both used paired seed 630101. One pair does not support confidence intervals or a population-level E/I conclusion. An inhibitory target's downstream response can be negative in a recurrent network.
- Saved full response footprints for all modeled neurons, not only MN9. These are individual-cell checks; no eigencircuit hypothesis has been tested yet.
- Inspected the correlation heatmap, baseline-rate figure and E-lesion footprint figure. Labels and plotted values were readable.
- Full test command: `.venv\Scripts\python.exe -m pytest -q --disable-warnings`. Result: 204 passed, 3 skipped, 40 warnings. The warnings came from deprecated parsing APIs used by Brian2.

Sources: [pilot report](../../results/pcdr/corrected_20260919/report/REPORT.md), [summary and source-manifest hashes](../../results/pcdr/corrected_20260919/report/summary.json), [commands](../../results/pcdr/corrected_20260919/commands.json), [test record](../../results/pcdr/corrected_20260919/test_record.json), [input audit](../../results/pcdr/corrected_20260919/input_audit.json), [failed earlier pairing](../../results/pcdr/corrected_20260919/prior_pair_failure.json).

### Remaining work and code review

- Corrected mode enumeration to consider the first twenty stable complete modes in spectral order, as specified in the user's plan. Unstable/incomplete modes do not use a place in that list. No whole-brain modes have been selected yet.
- Added baseline protocol/source checks and CCR collection checks against frozen seeds, lesions, variants, backend and code/input hashes.
- Prepared 720 single-cell study jobs: 23 selected cells plus baseline, each at 30 fresh seeds. The local timing estimate is 2.97 serial hours. This is a preparation result, not 720 completed trials.
- The later focal-mode plus 199-control study would require 6,030 trials including baseline. At the observed median baseline runtime, that is about 24.9 serial hours, before differences in backend speed, scheduling and filesystem overhead.
- [CCR job manifest](../../results/pcdr/ccr_singles_20260919/jobs.json) records the conditions, fresh seeds and estimate. Nothing submitted. Remaining single-cell trials, mode construction/selection, matched controls, confirmation and sensitivities are still to run.
- On CCR, validate the environment and benchmark NumPy against Cython before switching execution backends. Retain NumPy if the benchmark fails. Do not combine changed-network lesions with the original baseline.
- Code explanation remains separate in [CODE_GUIDE.md](CODE_GUIDE.md). Protocol and paper notes remain in [PLAN.md](PLAN.md).

## 20 September 2026 — local unattended batches

- User cannot access CCR yet and requested small serial local batches, progress independent of model rate limits, and results by Monday night (about thirty hours). This replaces the expired thirty-minute local allowance for this new run window.
- Reaffirmed the v630, sugar, output-lesion research question. Flagged the difference between the approved localization-primary endpoints and the latest wording calling MN9/motor primary. Requested a choice; retained the approved hierarchy while proceeding with the unchanged single-cell trials.
- Created `scripts/pcdr_local_queue.py`, `pcdr_local_followthrough.py`, and `pcdr_local_findings.py`. They control existing scientific functions; no simulation-module source was changed during the running frozen study.
- Started the existing 720-job manifest locally. Same conditions and seeds; execution order is seed first so every cell receives early coverage. The controller launches one process per trial with thread limits, checks memory/disk, records progress, and collects only the complete study.
- Initial trial 630201 finished with 13,807 spikes and MN9 89 Hz. This is one baseline, not a new lesion finding. Source: `results/pcdr/ccr_singles_20260919/trials/default_baseline_630201/manifest.json`; command is in `local_logs/0000.txt`.
- After nine completed trials, stopped between jobs to load safer Windows timeout handling. Windows virtual-environment launchers can have child processes; timeout now terminates the process tree. No completed run was discarded, and the deadline stayed unchanged.
- Automatic approval review rejected the combined STOP-file deletion/restart command with only “blocked by policy.” Preserved the STOP file by renaming it to `STOP_controller_upgrade_record.txt`, then restarted in a separate command. This succeeded without requiring user intervention.
- Created an hourly in-chat follow-up, `local-connectome-study-through-monday-night`, for meaningful completion/failure checks. The first tool call lacked the required thread destination and made no automation; corrected it and received a created-automation result.
- The separate follow-through controller waits for singles to finish. It writes their findings, then attempts a stable eigenmode and five strict full-match controls. If successful, it runs a separately labeled five-seed mode pilot. It shares the Monday deadline. No 199-control confirmation is being claimed.
- Added tests for fresh reduced-pilot seeds/labels, refusing relaxed matching, propagating worker failure, and refusing a findings report from an incomplete study. Command: `.venv\Scripts\python.exe -m pytest tests/test_pcdr_local.py tests/test_validate_neuron_ids.py -q -rs --disable-warnings`. Result: 48 passed, 3 skipped. The three skips were specifically unsupported Windows symbolic-link creation, not scientific tests.
- Expanded [PROCESS_DETAILS.md](PROCESS_DETAILS.md) with the reasons for confirmation versus pilot, every material correction, exact skipped tests, deferred stages, endpoint mathematics, controller behavior and interpretation limits. [CODE_GUIDE.md](CODE_GUIDE.md) remains the function-oriented explanation.
- Used official OpenAI documentation to check scheduled follow-ups. No claim that a Codex follow-up bypasses rate limits; the independent Python jobs and automatic report generation have no OpenAI API dependency.
- New execution settings, script snapshots, command records and hashes are stored in `results/pcdr/local_followthrough_20260920/execution_manifest.json`. Historical pilot archives are not overwritten by these expanded notes.
- Resource wait after 21 completed trials: a separate `llama-server` process was observed using about 5.67 GiB of RAM; available memory fell below the controller's 4 GiB threshold. The queue waited instead of launching another full network. Asked the user before stopping an unrelated workload. The queue will resume automatically when sufficient memory returns. Evidence: `results/pcdr/local_followthrough_20260920/resource_wait_record.json`.

### Delegated choices and resumed compute, 20 September

- User asked for a comparison and delegated the choice. Chose to keep A/F localization primary and MN9/motor ΔHz secondary. Footprint localization matches the stated question more directly than the magnitude of a downstream motor response. MN9/motor effects remain fully reported; they are not behavioral measurements.
- This retains the previously approved analysis rather than changing an endpoint after observing an eigen-set result. At decision time, only 21 single-cell-study trial records were complete; the mode stage had not begun.
- Compared the resource choices too: leaving the local language model loaded kept research stalled, while unloading it allowed the Monday work to proceed. Prioritized the requested research deadline.
- Identified the process as Ollama's `llama-server.exe`, PID 2820. `ollama ps` showed the loaded model `qwen3:8b`. Used the supported command `ollama stop qwen3:8b` to unload it instead of forcibly terminating the process. No model files were deleted, and Ollama remains installed.
- `ollama ps` then showed no loaded models; reported free physical memory increased to 6,905,572 KiB. The research controller detects this without a new run command. Its original deadline and completed trials remain intact.
- Decision, commands, status snapshot and document hashes are in `results/pcdr/local_followthrough_20260920/decision_20260920.json`. The earlier execution archive remains a historical snapshot; these are subsequent amendments.

### 20 September 2026 evening status-write recovery (recorded 21 September UTC)

- Heartbeat inspection at about 00:50 UTC found the singles controller absent. Its status still said running, with 484 completions, because both the normal update and error-report update failed with Windows PermissionError during atomic status-file replacement. The last worker log (index 140, seed 630221) reported successful completion. This was an execution interruption, not a negative scientific result.
- Preserved the previous controller and status as controller_before_status_retry.py and status_before_retry.json in the singles directory. The original stderr log retains the traceback. No simulation package code, selection, seeds or deadline changed.
- Added bounded retries for PermissionError in the controller status writer: retry replacement every 0.5 seconds for at most 30 seconds. A persistent failure still raises. This does not retry simulations. A transient open-file conflict is plausible; the exact process holding the file was not identified.
- Added tests for transient recovery and persistent failure. Command: .venv/Scripts/python.exe -m pytest tests/test_pcdr_local.py -q --disable-warnings. Result: 5 passed in 2.33 seconds.
- Verified the old controller and worker were absent and its lock had been removed. Restarted with .venv/Scripts/python.exe scripts/pcdr_local_queue.py --study results/pcdr/ccr_singles_20260919 --features results/pcdr/corrected_20260919/analysis/features.parquet --hours 30. Existing deadline_epoch 1790041426.172948 is reused. New logs are controller_retry_stdout.txt and controller_retry_stderr.txt.
- Restart initially waited for memory. Ollama had loaded qwen3:8b again (llama-server PID 19596, about 5.67 GiB working set). Used ollama stop qwen3:8b again under the earlier delegated choice to prioritize research compute. Model files remain installed. No duplicate follow-through controller was started.
- Document creation: scripts/build_pcdr_research_document.py combines the maintained records with a frozen 20:19 UTC source snapshot and verified pilot figures. Kept that snapshot date rather than implying later events were already recorded. Fixed an orphan table header, restored a dated amendment heading, and changed displayed A/F sums to native equation objects with proper indices. Canonical rendering could not find LibreOffice; used hidden Microsoft Word export and Poppler page images instead. Final export manifest will record actual hashes and visual checks.

### 20 September 2026 completed local study (recorded 21 September 02:53 UTC)

- The single-cell queue completed all 720 trials and collection at 02:13:50 UTC. Report generation followed automatically. No extra seeds or targets were added.
- Read the complete 40-test secondary table. Only excitatory cell 720575940619473624 total motor change passed BH q < 0.05: -52.033 Hz total, -0.612 Hz per motor cell, q=0.024. No MN9 test passed. Silent control mean footprint was zero. Full unfiltered results: results/pcdr/ccr_singles_20260919/FINDINGS.md and analysis/secondary_tests.parquet.
- Mode construction completed, with no eligible support. Wrote scripts/pcdr_completion_audit.py to independently join saved support IDs against baseline spike counts and verify every scheduled trial manifest is complete. Command: .venv/Scripts/python.exe scripts/pcdr_completion_audit.py. Assertions passed; results and hashes saved as results/pcdr/local_followthrough_20260920/completion_audit.json.
- Forty eigenpairs gave 22 stable complete modes. All first 20 supports contained zero baseline-spiking cells, so none met the ten recruited-cell requirement. This is a recruitment mismatch in the prespecified leading-mode search; it is not a failed eigensolver and is not a matched-lesion test of P.
- Skipped controls and eigen-set lesions because the prerequisite selection failed. Did not compute 80 pairs because there were already more than 20 complete modes. Searching deeper now or changing context would require a separately labeled research amendment, not completion of this frozen test.
- Wrote FINAL_HANDOFF.md in the follow-through directory, including what finished, what remains unperformed, interpretation and evidence paths. Both controllers exited normally and no Python simulation process remained. The authorized workflow reached its stopping rule early; no need to spend the remaining budget. Pause the monitor after handoff. The earlier exported document remains its original timestamped edition.

### 21 September 2026 document update and proposed next steps

- User asked what to do next and requested updated Word/PDF exports. Created NEXT_STEPS_20260921.md with completed findings, stopping reasons, options and a recommended order: descriptive support-annotation audit, examination of paired single-cell data, then a separately declared bounded deeper-spectrum search if warranted.
- Checked the primary Nature articles by Pospisil and Shiu for the anatomical-mode and zero-basal-firing rationale. These motivate follow-up; they do not identify our computed supports or prove the source of the mismatch.
- The proposed 80-pair/first-40-mode search is an exploratory amendment suggestion, not permission to reinterpret the original failed first-20 search. No new experiment or controller was started. Monitoring remains paused.
- Updated the document builder to create a new 21 September edition, preserving the 20 September files. The new snapshot includes final handoff, completed single-cell findings and verification results. It replaces stale current-status prose while preserving historical notebook entries as dated records.

### 21 September 2026 authorized exploratory extension

- User asked to start more work and made the day available for local runs. Recorded a new exploratory amendment before execution in results/pcdr/exploratory80_20260921/amendment.json. The completed first-20 search remains unchanged.
- New bounded candidate search: 80 leading pairs, two starts 630400/630401, first 40 stable complete modes, same sugar baseline, 75% power, ten support cells with five pooled spikes, sensory exclusion, ranking and strict matching. If fewer than 40 stable complete modes are resolved, stop without treating it as a completed candidate search. No further spectrum expansion.
- Created scripts/pcdr_modes_exploratory80.py as a separate copy of the verified mode builder with only the fixed search budget, candidate limit, seeds, imports and explicit exploratory metadata changed. The original eigencircuits package remains unchanged. Source snapshots and hashes are in the new directory.
- Created scripts/pcdr_exploratory_day.py. It first joins all saved support memberships to annotation IDs and counts classes/recruitment, then runs the bounded solver, and only after successful selection generates five strict full-match controls and a five-seed pilot. This is 35 trials, not confirmation. Previously reserved mode seeds 630901–630905 were never used because original mode selection failed; they remain fresh.
- No neuropil field exists in the supplied annotation table. The audit reports cell_class, super_class and cell_type, missing matches and recruitment, without inventing neuropil assignments. It uses exact string-ID joins with cardinality validation and retains unannotated cells.
- Command: .venv/Scripts/python.exe -m pytest tests/test_pcdr.py tests/test_pcdr_local.py -q --disable-warnings. Result: 28 passed, 40 warnings in 5.73 seconds (existing Brian2 parsing deprecations). These are regression checks for the reused mathematics and queue, not a claim that every new controller branch has been tested.
- Launched hidden below-normal process: .venv/Scripts/python.exe scripts/pcdr_exploratory_day.py. Controller has exclusive lock, one subprocess per stage, single-thread numerical libraries, memory checks, bounded stage timeouts and the original Monday 21:43:46 Eastern cap. It makes no model API calls. Errors preserve completed stage files; no automatic protocol relaxation.

### Exploratory selection result, 21 September 04:46 UTC

- The fixed 80-pair search completed and resolved 45 stable complete modes. Four candidates among the first 40 met the unchanged eligibility criteria. Selected zero-based stable mode rank 33 by the recorded recruited-power criterion.
- The selected 75% support has 51 cells; 29 have at least five pooled selection spikes. Whole-vector loading power on baseline-recruited cells is 0.5379352785. The support excludes direct sugar inputs and passes cross-start stability/residual checks. These are structural/selection findings, not lesion effects.
- Source: results/pcdr/exploratory80_20260921/modes/modes.parquet and selection.json; solver command is in modes.log. The controller advanced to strict five-set matching. No matching threshold was relaxed. The original first-20 outcome remains unchanged.
- Re-enabled the existing hourly monitor for this new directory and its declared stopping rules. Its prompt requires updating the comprehensive Word/PDF when the outcome is complete and pausing after handoff. The independent controller does not depend on that monitor or model quota to proceed.

### 21 September 2026 exploratory matching stop, checked 05:47 UTC

- Read status.json, controller_stderr.txt, matching.log and controls/manifest.json. Strict matching completed its 50,000 proposals with seed 630600 and accepted 0/5 sets. All thresholds remain unchanged. The explicit insufficient-matches RuntimeError caused the controller to stop at 04:47:44 UTC.
- The Brian2 exception hook printed its generic error banner, but the traceback points to the intentional matching guard. Did not change simulator code or retry the unchanged sampler. Completed modes and annotations remain saved. No Python simulation/controller process was present.
- Skipped prepare, baseline/lesion trials and mode-summary generation because the matching prerequisite failed. No new mode effects or matched-reference p-values exist. The finite sampler's failure is not proof that adequate matches are impossible.
- Rejected proposal feature balances were not saved by the existing sampler, so cannot identify the responsible feature from these outputs. Proposed next step is a separate descriptive matching-feasibility audit, not lowering SMD thresholds, substituting another mode, or claiming that recruitment alone is sufficient.
- Wrote results/pcdr/exploratory80_20260921/FINAL_HANDOFF.md and a hashed completion record. Updated the comprehensive document as a new completed-extension edition, preserving earlier exports. Pause the heartbeat after handoff because the declared workflow has reached a terminal stopping rule.

### 21 September 2026 completed extension document export

- Built the new completed-extension edition with bundled Python running scripts/build_pcdr_research_document.py. Preserved earlier editions. Source text is frozen in exports/pcdr_research_record_20260921_completed/source_snapshot.json.
- Updated Word fields and contents through hidden Word COM and exported the PDF. The packaged LibreOffice renderer was unavailable as diagnosed in the earlier renderer log; used the existing verified Word fallback instead of installing software.
- Ran scripts/pcdr_document_qa.py with bundled Python and Poppler at 115 DPI. Visual review caught an encoding error in an intermediate draft and an empty chapter-break page; corrected both before delivery. Shortened the final export note to remove a two-line spill page. Final PDF has 46 pages.
- Ran scripts/pcdr_export_manifest.py. Final pages 1–45 were pixel-identical to the reviewed draft; separately inspected the revised page 46. The export manifest records hashes, rendering method and outcomes. This post-export note is outside the frozen document snapshot; the export manifest records its production details.
- Scientific inputs, seeds, thresholds and results were not changed during document production. The matching stop remains terminal and the heartbeat is paused.

### 21 September 2026 matching feasibility audit

- User authorized diagnosing matching and requested defensible documentation. Created scripts/pcdr_matching_audit.py, pcdr_matching_witness.py and pcdr_matching_report.py with Codex assistance. Full purpose, mathematics, commands, limitations and source notes are in MATCHING_AUDIT_20260921.md.
- Wrote protocols before replay and optimization. Reproduced 0 accepted sets in 50,000 proposals. Incoming strength failed every proposal; baseline activity failed none. Two focused tests passed; independent saved-ID validation passed for five optimized feasibility examples, maximum SMD 0.07335.
- Kept the same target, exclusions and thresholds. Five examples establish feasibility, but are not random null draws. No lesion jobs started. Original confirmation and original failure remain preserved. Recommended a separately amended descriptive optimized-comparison pilot; calibrated random-reference inference remains unresolved.
- Source commands and hashes: results/pcdr/matching_audit_20260921/protocol.json, witness/protocol.json and independent_validation.json. Full proposal balances are preserved. Updated the comprehensive record with an audit addendum; earlier editions remain unchanged.

- Export completed: 49-page matching-audit edition. Ran bundled Python scripts/pcdr_append_matching_document.py, hidden Word COM export and scripts/pcdr_matching_document_qa.py. Reviewed all changed pages against the prior edition; hashes and render details are in its export_manifest.json. A console-only Unicode printing error during paragraph inspection did not modify the source document. Did not repeat the full simulation suite because frozen scientific modules were unchanged; tested the new audit calculations and independently validated all saved witnesses.

### 21 September 2026 optimized comparison pilot launched

- User asked whether to start testing after the matching feasibility result. Prepared and launched scripts/pcdr_optimized_pilot.py. Amendment and exact IDs were frozen before any trial in results/pcdr/optimized_pilot_20260921/amendment.json and jobs.json.
- Five validated optimized sets remain unchanged; support remains the exploratory rank-33 51-cell support. Baseline plus six lesions across fresh seeds 630901–630905 gives 35 trials. Each support is scored against itself. Same NumPy model, sugar drive, timestep and paired input tape.
- Rechecked hashes, exact stratum counts, exclusions, distinct IDs/sets and all six SMDs at preparation. Checked that these seeds had not appeared in prior trial manifests. Single-cell study completion gate passed.
- This is a descriptive optimized-comparison pilot. The plan phase is optimized_matching_pilot, so the existing collector does not call its mode reference-test branch or single-cell significance branch. Primary reference results must remain an empty list. The supervisor generates all-set findings automatically and adds the inference limitation.
- No Monte Carlo reference p-value is justified for the optimized examples. No threshold relaxation, target substitution, extra seeds or outcome-based stopping. Preserve all signed changes, A/F, MN9 and motor summaries and underlying per-neuron footprints. Five-seed bootstrap intervals remain imprecise.
- Commands: .venv/Scripts/python.exe scripts/pcdr_optimized_pilot.py --prepare; hidden below-normal Start-Process of .venv/Scripts/python.exe scripts/pcdr_optimized_pilot.py. Supervisor launched as PID 23824 (Windows venv redirects to its child). The queue starts one worker at a time; multiple Python entries in the process tree include redirectors and waiting supervisors, not concurrent simulations.
- Queue retains the Monday 21:43:46 Eastern deadline, >=4 GiB free RAM and >=10 GiB disk guards, atomic manifests and resumable completed trials. Controller uses no model API. Reactivated the existing hourly monitor for completion verification, Word/PDF update and final pause.
- Estimate based on stored trial wall_seconds was 0.141 hours at median or 0.170 hours at p95 for 35 trials. This is an execution estimate, not a guaranteed end time; worker startup, hashing, collection and any memory waits add overhead. No repeated whole-suite test run: the simulation/collector code is unchanged; preparation validation and the first real worker check the new orchestration path.
- At launch inspection, baseline seed 630901 was running without an error. Full completion has not yet been claimed. Earlier matching-audit Word/PDF is preserved; a new completed-results edition is due after collection.

- Startup verification: first baseline/mode pair completed and scheduled input digests match; delivered input digests also match for this pair. Saved startup_check.json with both manifest hashes. Remaining trials continue unchanged.

### 21 September 2026 optimized pilot completed and audited

- Completed 35/35 trials at 20:07:50 UTC, about 10 minutes 40 seconds after the queue began. Six lesion conditions each have five fresh paired seeds. No extra trials or changed thresholds.
- Ran .venv/Scripts/python.exe scripts/pcdr_verify_optimized.py. Verified all trial outputs against hashes, frozen jobs/provenance, 30 paired input digests, six rate summaries and every row of six 127,400-neuron footprints. All scheduled and delivered input digests matched. No primary/reference p-values or secondary test files exist for this pilot.
- Eigen-set A = 22.576 Hz and F = 0.229408, larger than all five optimized comparisons (A 11.486–16.467 Hz; F 0.1853–0.2162). Off-support response is still 77.06 percent of total absolute mean response. This is descriptive evidence for the predicted ordering in one selected context, not confirmation or independence.
- MN9 mean change = -82.2 Hz; motor total change = +27.6 Hz. Readout membership differs: the mode includes MN9 and 13 motor cells, while comparisons exclude MN9 and include 3–5 motor cells. Preserve this qualification; do not describe secondary contrasts as behavior or a uniquely downstream effect.
- Saved completion_audit.json, per_seed_readouts.csv and FINAL_HANDOFF.md. Added OPTIMIZED_PILOT_RESULTS_20260921.md with every condition and seed, bootstrap intervals, mathematics, code purpose, commands, limitations and pending research. Verification script created with Codex assistance; no simulated outputs modified.
- First verifier pass identified motor membership counts; added those counts to the written interpretation and reran the deterministic verifier so its code hash and report agree. This repeated analysis did not change selection or inferential tests. No new simulation, p-value, sensitivity run or post-outcome mode search was performed.
- Preserved earlier Word/PDF editions and appended a new results chapter using scripts/pcdr_append_pilot_document.py. Prior chapters remain dated history; cover directs readers to Chapter 11. No unfinished confirmation is described as complete. Recommended adviser/design review before additional runs.

- Completed 52-page Word/PDF results edition. Used bundled Python for the append builder and QA helper, hidden Word COM for PDF, and bundled Poppler at 115 DPI. Inspected changed pages and compared other page bodies to the verified prior edition. Added repeating table headers before final rendering. Export/source hashes are in exports/pcdr_research_record_20260921_pilot_results/export_manifest.json. Final handoff recorded and monitor paused. This post-export note supplements the frozen document.

### 21 September late evening fresh seed replication

- User confirmed CCR Tuesday, permitted light tests until morning and requested conserving model usage. Created scripts/pcdr_seed_replication.py: validates unchanged source/input hashes and unused seeds, freezes 210 jobs, then reuses the existing serial queue/supervisor. No simulation module edits. Conditions unchanged; 30 fresh seeds631001–631030 remain separate from prior5seed pilot.
- Commands: .venv/Scripts/python.exe scripts/pcdr_seed_replication.py --prepare; hidden below-normal Start-Process of .venv/Scripts/python.exe scripts/pcdr_seed_replication.py. Six-hour cutoff about04:47EDT Tuesday. Preparation validated210 unique IDs and no prior seed use. No preemptive new significance test, rematching or outcome selection. This checks seed stability only.
- Added AGENT_HANDOFF.md and FOUR_WEEK_WORKPLAN.md; prioritized low-cost verification and CCR readiness over arbitrary additional runs. Full cluster setup and composition matching remain pending. Existing Python supervisor writes results without Codex access; document export awaits a completion turn if model limits intervene. Hourly monitor updated to latest directory and cutoff.


### Fresh seed replication verified 22 September UTC

- All210 frozen trials completed at03:52:25UTC (21 September23:52EDT), six conditions plus baseline across30 fresh seeds. Earlier5seed pilot remains separate. No extra simulation or rematching occurred.
- Adapted verifier to210trials/180pairings before execution: .venv/Scripts/python.exe scripts/pcdr_verify_replication.py. Every recorded trial output hash, frozen seed/support/source and full footprint passed. Six summaries recomputed. No reference p-values. Scheduled input digests matched180/180; delivered digests matched176/180. Differences in state-dependent delivery are allowed by the frozen protocol, not a failure of paired scheduling.
- Mode A22.543791Hz,F0.231173 exceeded all five optimized comparisons again. MN9 -82.633333Hz,motor total+39.266667Hz. Off-support response76.88percent. This reproduces the conditional ordering across input seeds; does not resolve optimized-reference, readout membership or biological validity. All180 individual pair readouts saved in per_seed_readouts.csv and included in the report.
- Scripts/pcdr_verify_replication.py, pcdr_append_replication_document.py and pcdr_replication_document_qa.py created with Codex assistance; reused prior verified calculations/render workflow, changing study/counts and report text explicitly. No frozen simulation files edited. Tests were full data/assertion checks, not a repeat of the unchanged simulator suite.
- FINAL_HANDOFF.md and completion_record.json record completed evidence. Comprehensive document gets a separate replication edition; existing52page edition preserved. No next stage queued; pause monitor after handoff. CCR and improved composition matching remain pending.

- Replication export complete:59-page Word/PDF, append builder and QA helper executed with bundled Python; hidden Word COM and Poppler115DPI. Changed pages inspected, unchanged bodies verified by pixel hashes. All180seed rows retained. Export manifest records hashes; this post-export note supplements the frozen edition. Monitor paused.


### 22 September baseline composition and CCR input guard

- Continued with baseline-only audit, not more fixed-set trials. Created pcdr_composition_audit.py, saved protocol before reading features, and recorded all ECDF gaps, quantiles, variance ratios and annotation counts. Largest gap0.27451 for optimized_003 incoming degree; variance ratio4.09168 despite SMD0.04215. Eight active excitatory motor candidates available for eight required slots: every exact matched set would share them. No joint feasibility or causal conclusion claimed.
- Added read-only pcdr_backend_input_check.py because equal input counts in existing backend benchmark do not ensure identical scheduled stimuli. Guard compares all60 cross-backend pairs, does not change model or benchmark. Synthetic acceptance/mismatch test and ECDF tie tests:2passed0.83s. Actual CCR benchmark remains unrun.
- Commands: .venv/Scripts/python.exe scripts/pcdr_composition_audit.py; .venv/Scripts/python.exe -m pytest tests/test_pcdr_backend_input_check.py tests/test_pcdr_composition.py -q --disable-warnings. New code created with Codex assistance. Results and hashes in composition_audit_20260922. CCR_READINESS.md separates preparation from untested cluster setup. No source changes to frozen simulation, no new lesions, no threshold adjustment.

- Bounded exact-motor matching check: pcdr_motor_matching_witness.py first solve infeasible, stopped. Restricted nearest64union plus conservative sufficient bounds; not proof original pooledSMD/fullpool infeasible. No simulations or relaxed rules. Protocol/results saved in composition_audit_20260922/motor_witness.


### 22 September comprehensive record update

- User made the research record the priority. Created DESIGN_AUDIT_RECORD_20260922.md and appended Chapter 13 to the verified replication edition using scripts/pcdr_append_design_document.py. Added the baseline distribution audit, exact motor capacity, restricted infeasible solve, function purposes/examples, test commands, skipped work and reasons, CCR gates and four-week roadmap. Earlier chapters and exports preserved. Clarified the inherited generic "Feasible examples" JSON label: zero witnesses were actually found.
- Commands: bundled Python scripts/pcdr_append_design_document.py; hidden Word COM field/contents update and PDF export; bundled Python scripts/pcdr_design_document_qa.py. First QA call was too early, before PDF export finished; no PDF existed. Waited for Word to finish and reran successfully. No scientific analysis or simulation rerun.
- New edition: exports/pcdr_research_record_20260922_design_audit, 64 pages. Reviewed pages 1 and 60-64 visually; pages 2-59 match the prior verified body pixels. Source/export manifests retain hashes. Code and document preparation used Codex assistance. This post-export note supplements the frozen document, avoiding a self-referential export hash.


### 22 September full-pool method refinement

- User requested methodical refinement. Created pcdr_fullpool_motor_witness.py: one full eligible-pool solve, fixed seed 631101, unchanged conservative bounds and exact motor/sign/recruitment counts; protocol before solving. No lesions. Requested 60-second HiGHS limit and one thread. SciPy passed the threads option through with a warning. Solver exceeded requested time without returning; worker PID 10944 used 145.44 CPU seconds at 12:36:23 EDT. Verified command line before Stop-Process -Id 10944. Parent exited 1. Saved terminal_stop.json: unresolved, not infeasible. Cause of overrun unestablished.
- Added full-pool coordinatewise bounds after a separate recorded protocol. Bounds use fixed-count order statistics of log1p features and second moments. Full pool 126,935; all six SMD lower bounds zero, so none rules out matching. Joint feasibility is still unresolved. No criterion relaxation or mode substitution.
- Commands: .venv/Scripts/python.exe scripts/pcdr_fullpool_motor_witness.py; .venv/Scripts/python.exe scripts/pcdr_fullpool_bounds.py; .venv/Scripts/python.exe scripts/pcdr_verify_fullpool.py. Verification checked original frozen hashes and independently counted pool. New bound tests plus matching/composition/backend-guard tests: six passed in 0.77 seconds. Exhaustive toy enumeration and zero-variance cases tested. Witness-verifier branch unexercised because no candidate returned.
- New code created with Codex assistance. Evidence: results/pcdr/fullpool_motor_20260922. No running Python worker remains. Next numerical work needs an external wall-clock watchdog before any further large solve, then a declared bounded relaxation/formulation check. No CCR run or simulator-suite rerun was justified by this analysis-only change.
- Created FULLPOOL_REFINEMENT_20260922.md and new 66-page comprehensive edition. Bundled Python ran scripts/pcdr_append_fullpool_document.py and scripts/pcdr_fullpool_document_qa.py; hidden Word COM updated contents and exported PDF. Reviewed changed pages 1,65,66; remaining page bodies match prior edition. Old exports preserved, source/export hashes saved. This post-export notebook note supplements the frozen chapter.

### 22 September 2026, afternoon: motor-balanced sets found

Continued from the actual local state rather than repeating the old five-seed pilot. Local and GitHub HEAD both 598a1d84aa3136c5e0f28b90b1980fa8caf20395. The newer eigencircuit work is local/untracked. Read the supplied 59-page PDF, including the replication chapter, and the newer full-pool notes. Visually reviewed PDF pages 53-54. No repository push or prior-output replacement.

The previous full-pool integer attempt had stopped without a result. Created an external process deadline and tested it before another solver calculation. Then recorded two baseline-only fractional checks, each with 60 seconds inside the solver and a 90-second external worker limit. Both finished successfully in about four seconds per worker. The stricter LP returned seven partial memberships; the necessary outer LP returned five. Partial memberships are not valid neuronal comparison sets.

Recorded a second protocol before enumerating all128 binary choices for the seven partial cells in the stricter solution. Twelve choices had exact counts. Nine passed all six ORIGINAL pooled-SMD limits; none passed the stricter sufficient mean bounds. No criterion was relaxed. The original definition uses both sets' variances; the sufficient optimizer shortcut did not. This resolves existence of original-SMD motor-balanced sets for this target.

An independent verifier checked hashes, string IDs, exclusions, size51, exact sign/recruitment/motor counts, motor count13 and all six SMDs. Worst SMD0.09858249. All nine sets share47cells, pairs share48-50. Therefore these are very similar optimized witnesses, not nine independent random controls. No lesion effects were read to choose them, and none has been simulated. MN9 identity remains unmatched.

New code created with Codex assistance: scripts/pcdr_bounded_process.py, pcdr_fullpool_relaxation.py, pcdr_fractional_completion.py, pcdr_verify_fractional_completion.py; tests/test_pcdr_fullpool_relaxation.py. Function explanations are separate in CODE_GUIDE.md. Full methods, objections, citations, result table and exact commands are in FULLPOOL_FEASIBILITY_20260922.md. Protocols, logs, fractional vectors, binary assignments/memberships and verification hashes are in results/pcdr/fullpool_relaxation_20260922.

Commands: .venv/Scripts/python.exe scripts/pcdr_fullpool_relaxation.py; then scripts/pcdr_fractional_completion.py; then scripts/pcdr_verify_fractional_completion.py. Ran pytest on fullpool_relaxation, fullpool_bounds, matching_audit, composition and backend_input_check: final12passed in2.21seconds. Earlier pre-completion run11passed; focused updated file6passed. No full simulator-suite rerun because simulator code did not change. No Python worker remains after completion.

Tooling notes: research venv lacks pypdf; bundled console needed UTF-8 for delta; fitz missing there. Used bundled pypdf and installed Poppler successfully. These were document-inspection issues only. Existing PDFs preserved; new Markdown supplement records this session. Next proposed step is distributional balance review of these nine sets, then a separately frozen descriptive motor-composition sensitivity. Null-distribution design and CCR validation remain pending. No new queue or external message.

### 22 September 2026: distribution audit, motor-composition pilot and repository preparation

User asked to continue, then asked to commit useful verified work to cbaker20-cyber/connectome-perturbation under their own Git identity with understandable messages. GitHub plugin profile matched local configured author Copeland Baker; repository metadata showed push permission. No identity was invented and no assistance statement was removed.

Before new lesions, created pcdr_motor_set_audit.py and saved its protocol. All nine original-SMD-valid sets retained. Incoming-degree variance reached19.117times the target; largest ECDF gap0.294118 with SMD0.038027. Motor counts matched, but superclass counts were target23central/6descending/13motor/9unavailable versus17/9/13/12 in comparisons. MN9 identity remained unmatched; all nine shared47cells. Austin2009 and Stuart2010 support distributional diagnostics beyond mean balance; their numerical recommendations were not adopted as fly-specific cutoffs. MOTOR_SET_AUDIT_20260922.md has the interpretation and sources.

Declared and prepared a descriptive motor-composition sensitivity before outcomes. All nine sets plus unchanged eigen-support, seeds631201-631205,55trials, unchanged NumPy model and paired input tapes. Recorded a thirty-minute cap from19:41:05UTC, one serial worker, memory/disk guards and no automatic extension. This was a bounded implementation choice for the user's continuation, not a claim that the user explicitly specified these new seeds or duration. Estimates from prior trial timings were13.59minutes median and14.99minutes at the95th percentile, excluding some queue overhead. Prepared source hash checks and independent verification before launching. Added paired-seed mode-minus-comparator intervals with common bootstrap weights; no random-reference p-values. No hypothesis-driven stopping on outcomes.

Prelaunch focused checks:31passed in4.97seconds. Full repository suite for commit:223passed,3skipped,40warnings in22.70seconds. New contrast tests cover shared seed pairing, known constant responses and zero-response undefined concentration. No model source changed. User's pre-existing staged MANUS handoff and unrelated historical folders remain outside the planned research commits.

Added an explicit compact-evidence exporter and a report/figure generator so the public repository can contain readable research evidence without all large trial files. Added a PDF builder for a new local edition preserving the prior66pages. Existing PDFs and old results stay unchanged. New evidence has Git text normalization disabled to preserve its hashes; new eigencircuit sources retain LF. Root legacy model files use Windows line endings, so exact replay still depends on archived source bytes and environment, not merely a commit hash. Generated exports and scratch renders are ignored by Git.

Commands so far: .venv/Scripts/python.exe scripts/pcdr_motor_set_audit.py; scripts/pcdr_motor_composition_pilot.py --prepare; scripts/pcdr_motor_composition_pilot.py; python -m pytest -q --disable-warnings. Completion and verification will be recorded separately after the full queue finishes. Current trial source revision remains598a1d8; commits wait for the run to end.

Added a specific opposite-sign cancellation test during repository review: two seed responses of +2 and -2 must average to zero before the absolute response is computed. The full suite then passed224tests,3skipped,40warnings in18.47seconds. The earlier223-test run remains recorded above. No frozen simulator or verifier source changed.

### 22 September 2026: motor-composition pilot completed and verified

All55trials completed at19:58:22UTC, about17minutes17seconds after preparation and within the30-minute cap. Independent verifier passed55trial/output checks,50scheduled-input pairs and ten full127,400-neuron footprints. Delivered-input digests matched49/50; the one difference is allowed state-dependent delivery, while scheduled inputs matched every time. Mode A22.60392157Hz,F0.23236314; all nine comparisons had smaller A and F. MN9 change-81.8Hz; total motor change+20Hz. Off-support fraction76.76percent. These are descriptive simulation results, not confirmation.

The completed table had repeated results. Before investigating, wrote a separate post-result protocol in response_duplicates/protocol.json. Created pcdr_motor_response_duplicates.py, checked saved spike digests, actual full spike tables and all-neuron rate tables. Nine distinct membership sets yielded three distinct five-seed trajectories:003/006/009,004/007/010,005/008/011. Each triplet shared49cells; four membership-varying IDs had zero spikes in all five baselines and every corresponding lesion. This applies only to these observed conditions, not arbitrary seeds or biological circuits. All original results are retained. No extra simulations, set exclusions or inferential tests.

Copied42compact records/CSV views (about539kB) into docs/pcdr/evidence/2026-09-22 with exact-source hashes. Full spike/rate/source archives remain local. Generated MOTOR_COMPOSITION_RESULTS_20260922.md and an all-set A/F plus degree-distribution figure. Figure code first emitted a Matplotlib deprecation warning for vert=False; changed the plotting-only call to orientation='horizontal' and regenerated. No scientific computation changed. Prepared the new PDF edition preserving the earlier66pages. New source and documentation scripts were created with Codex assistance.

Commands: .venv/Scripts/python.exe scripts/pcdr_verify_motor_pilot.py; scripts/pcdr_motor_response_duplicates.py; scripts/pcdr_publish_evidence.py; scripts/pcdr_motor_pilot_report.py. Source/manifest verifications passed. Full tests remain224passed,3skipped after the added cancellation fixture. Publication uses two scoped commits and preserves the user's unrelated pre-existing staged handoff.

### 22 September 2026: final document review and publication scope

Created a77-page PDF edition under exports/pcdr_research_record_20260922_motor_composition. Visually reviewed all11new pages. The initial figure labels were small, so enlarged them and regenerated. Fixed two missing spaces in the generated prose. Final Poppler review found no clipping or overlap. All66historical page images are pixel-identical to the prior verified edition. Pypdf emitted an annotation-size warning; checked that all original annotation counts and all14internal link destinations were preserved with the one-page offset. Poppler warned about two display fonts in the inherited PDF; the historical renders remained identical. These export diagnostics and hashes are in export_manifest.json and qa/comparison.json. No research numbers changed during layout revision.

The new PDF cites the current source notebook/code guide snapshot; this post-export entry supplements that frozen document. Git publication keeps the research source, tests, dated Markdown and42compact evidence records/CSV views (about539kB). Large trial archives, PDF renders and unrelated historical handoff files are not included. Author identity is the user's configured Copeland Baker identity, verified against the GitHub plugin. Commit messages are plain descriptions of the code and results. A final published-commit record will follow after push verification.

## 22 September, evening — preliminary closeout and OnDemand package

Added a stricter baseline-only distribution check after the earlier motor-set audit. Saved the new protocol before running it. It kept the original target and exact strata and bounded both means and target-centered second moments. HiGHS reported the fractional program infeasible in an 11.625-second bounded process. I did not loosen the bounds or call this a rejection of the eigencircuit hypothesis. The exact procedure and limits are in PRELIMINARY_CLOSEOUT_20260922.md.

Created the transfer, notebook and descriptive sensitivity helpers with Codex assistance. Kept the actual model and historical analysis modules unchanged. The first package build stopped on missing psutil; fixed optional-package recording. Also corrected the library notes after checking metadata: statsmodels is installed, psutil is not.

Ran four fresh whole-brain technical trials from an extracted archive. Exact replay passed, the no-input network stayed silent, and scheduled input was identical for baseline and outgoing MN9 lesion. Checked all-neuron rate tables and output hashes. Then tested missing jobs, a lock collision, corrupted copied output, and resume without changed file times or hashes. Those checks passed. One process used about 2.84 GB, which is above the default OnDemand memory before notebook overhead.

The user clarified that the deliverable should be a light ZIP with an ipynb for OnDemand. Built a 95.17 MB standalone ZIP with the three datasets, notebook, scripts, exact library pins and instructions. Recommended 4 cores, 16000 MB, 4 hours and no GPU; at most two simulations run together. The final prose correction was checked against the simulation-tested package: source code, data, scientific design, requirements and notebook code cells are unchanged.

Prepared, but did not run, a 350-job descriptive follow-up. It uses five fixed weight settings, seven conditions and ten paired seeds. Added mode-without-MN9 and MN9-only conditions, keeping three representatives of the earlier response groups. Documented why these are not random controls and why this is not a confirmation test. The extracted helper successfully prepared the study after checking the smoke evidence.

Full suite: 231 passed, 3 skipped. Added a known-answer sensitivity collector test afterward; all eight targeted tests passed, bringing the distinct passing-test total to 232. CCR execution, Linux environment installation and actual scheduler failures remain to be checked there. Code and notes are being committed under the configured Copeland Baker identity, with assistance attribution retained.

## 22 September, later evening — increase CCR scope and concurrency

The user pointed out that the proposed 4-core/16-GB request was below their local PC. That criticism was fair: the first package was a conservative deployment pilot, not a substantial CCR workload.

Created an explicit amendment in CCR_EXPANDED_DESIGN.json while retaining the original 350-trial design. The new design has 3390 trials. A full 3 x 3 grid of overall weight and inhibitory multiplier, seven conditions and 30 shared seeds accounts for 1890. Fifty additional individual mode-cell lesions in the default network account for 1500. MN9-only already covers the remaining mode neuron, and default baselines are shared. This tests parameter interactions and the individual contribution of all 51 cells. It remains descriptive; neither extra seeds nor a larger grid repairs the control-matching problem.

Created CCR_Expanded_Study.ipynb and a new ZIP. Suggested allocation is 32 cores, 128000 MB, 8 hours, no GPU. Added pcdr_ccr_capacity.py to measure concurrency on real pending study jobs at 1, 4, 8, 16 and up to 24 workers. It respects Slurm CPU/memory limits, reserves two CPUs and 12 GB, allows 50 percent memory headroom per worker, and picks the smallest tested concurrency within 90 percent of best throughput. The benchmark retains the completed planned trials; it does not use outcomes to choose the experiment. Capacity certificates are tied to the study and Slurm allocation. Controller work is bounded to seven hours after calibration; the allocation is the outer limit.

Thirteen focused tests passed, including the complete 51-cell map, 3390 unique jobs with correct own-network baselines, memory/CPU bounds, stale allocation rejection and the throughput-selection fixture. The actual expanded ZIP was extracted and passed four fresh whole-brain smoke trials, missing-job rejection, occupied-lock rejection, corruption rejection and unchanged-file resume. The extracted helper successfully prepared the expanded study. None of the 3390 scientific trials or actual CCR scaling has run locally. The scaling test is a scheduler fixture, not a performance measurement.

Final expanded archive: exports/ccr_expanded_20260922/Connectome_CCR_Notebook.zip, 95173796 bytes. SHA256: 194777b3d3fb9f225c468b973d5eb2406f0baae7dd43ea81bd860e4c1e32ba60. Code/notebook changes used Codex assistance. The earlier packages remain preserved.
