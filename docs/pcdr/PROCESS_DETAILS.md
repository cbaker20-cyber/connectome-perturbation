# Process notes and reasons for decisions

Recorded 20 September 2026. This adds explanations to the dated notebook; it does not replace earlier entries. Research review, code and these support notes were assisted by OpenAI Codex. The student should write their own report and disclose assistance.

## What question is being tested?

The user's current wording is:

> Do Pospisil-style 75%-power eigen-sets of Shiu's signed connectivity matrix W, computed de novo on FlyWire v630, predict output-lesion footprints in the sugar-evoked LIF model after controlling for degree, strong-synapse mass, and recruitment?

- Yes, this is still the structural prediction being investigated. W is the actual signed v630 model matrix, not the paper's v783 matrix or the Jacobian of the LIF equations.
- Every firing-rate response begins with lesion Hz minus paired baseline Hz. This is the measured quantity. Choosing an endpoint specifies which parts of that vector are summarized.
- The previously approved primary endpoints are A, mean absolute paired change within the support, and F, its share of the whole-network absolute change. MN9 and motor firing are secondary in that plan.
- The user's latest wording called MN9/motor primary. Asked for clarification on 20 September; the user then delegated the choice after requesting a comparison. Chose the approved localization-primary hierarchy before any mode-lesion results. Running the frozen single-cell trials does not depend on that choice.
- MN9 is a focused simulation readout. Its firing change is not a direct measurement of feeding behavior.
- On-mode/off-mode here means response inside/outside a valid support. It does not mean that an extra off-mode lesion condition was run. Each matched control is evaluated against its own support.
- Single-cell lesions can identify simulated effects of those particular targets. They cannot answer the controlled eigen-set question by themselves.

### Endpoint decision, 20 September

| Option | What it establishes if supported | Why choose or not choose it here |
|---|---|---|
| A and F jointly primary | The selected support has both a stronger within-set response and a more concentrated response than its matched references. | Closest to the stated footprint-localization hypothesis. Chosen. |
| MN9/motor ΔHz primary | The selected lesion changes particular downstream model outputs relative to controls. | Valuable sensorimotor question, but it does not establish localization; an equally large output change can arise from a broad response. Retained as secondary. |

- F alone could be large for a very small total response. A alone could be large during a broad response. Requiring both addresses these different weaknesses, though neither endpoint proves dynamical independence.
- Compute signed mean paired ΔHz first, then its absolute value for A/F. Keep signed MN9 and motor effects visible so increases and decreases are not hidden.
- No observed mode effects informed this choice: the queue had completed only single-cell trials, and mode construction was still waiting for singles.
- This comparison follows the connection-versus-effect distinction in [Pospisil et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446844/) and the model-readout scope in [Shiu et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/). The endpoint hierarchy is this protocol's decision, not a requirement asserted by either paper.

## Why separate a pilot from confirmation?

- A pilot checks whether the inputs, target definition, matching, runtime and analysis work together. It can reveal a useful effect estimate or a failure of the assay.
- Confirmation uses a frozen question, selection rule, endpoints, controls and fresh seeds. This reduces the opportunity to choose a favorable result from many alternatives.
- Confirmation is a study stage, not a special simulator setting. It does not make the model biologically correct.
- The original design requests 199 control sets and 30 fresh seeds. The focal support plus 199 controls plus shared baseline requires 201 × 30 = 6,030 trials. This cost is why it is not the first unattended local batch.
- Five control sets allow a smallest corrected reference p-value of 1/6, even if the focal set exceeds all of them. They cannot support a 0.05 rejection. Thirty or five seeds also do not represent thirty or five animals.
- The new local mode stage is explicitly a reduced pilot: five strict full-match controls and five fresh seeds, 35 trials including baseline. It does not overwrite or satisfy the 199-control confirmation requirement.
- The small pilot keeps degree, strength, model sign, recruitment, baseline rate and strong mass matching. Reducing the number of controls is not permission to loosen their balance.
- If no stable eligible mode or no adequate matched controls exist, report that outcome. Do not substitute a different input context or lower the criterion to produce a favorable result.
- Reference rationale: [Phipson & Smyth](https://pubmed.ncbi.nlm.nih.gov/21044043/) for the Monte Carlo correction; [Pospisil et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446844/) for the connectome/effectome distinction. These papers do not prescribe our exact local budget or matching procedure.

## Why the checks came before interpretation

| Check | Reason | Outcome or current limit |
|---|---|---|
| Exact root ID/index agreement | A correct equation with the wrong neuron order lesions the wrong cells. | All graph indices agreed in the saved audit. Stored IDs are strings. |
| Actual input hashes | Filenames alone do not identify the input version. | Raw and newline-normalized hashes distinguish content changes from CRLF/LF changes. Original files were preserved. |
| Annotation overlap | Dropping unmatched cells would change the simulated network. | Unmatched cells remain; missing annotations are labeled unavailable. |
| Matrix signs versus transmitter labels | A relabeled table is not a changed inhibitory/excitatory network. | Record both maps and actual outgoing-weight signs. Initial E/I targets require agreement. |
| No-input trial | The model assumes zero basal activity. | Zero spikes is an expected model check, not a discovery about fly behavior. |
| Identical-seed replay | Detect uncontrolled randomness or changing code/input state. | Corrected baseline spikes and scheduled inputs repeat exactly. |
| Baseline/lesion input equality | Different stimulation would confound a paired perturbation comparison. | The original input method failed this check; the scheduled-input method passes. |
| Whole declared trial list | A silent trial vanishes if trial count is inferred from spike rows. | Manifests retain trials with zero spikes; rate tables retain all neurons. |
| Outgoing-only lesion | The question concerns removing output influence, not forcing a cell's voltage to zero. | Outgoing weights become zero while incoming connections remain. A lesioned cell may continue firing. |
| Complex eigenvectors and residuals | Taking real parts or accepting a failed solver can change the support. | Keep squared complex magnitudes; test residuals and complete conjugate modes. |
| Repeated eigenvalues | A solver can return different valid bases of the same degenerate subspace. | Unresolved bases are not called uniquely identified circuits. |
| Distinct controls | Replacement can create fewer lesioned cells than requested. | No duplicated neuron inside a set, no unrestricted fallback, exact size and strata. |
| Sign-preserving pruning | An absolute-value filtering calculation must not convert inhibitory edges into excitation. | Apply a mask to original signed weights. Altered networks get their own baselines. |

Detailed commands, measurements and hashes for these checks are in the [19 September record](../../results/pcdr/corrected_20260919/research_record.json), [command list](../../results/pcdr/corrected_20260919/commands.json) and [input audit](../../results/pcdr/corrected_20260919/input_audit.json).

## What changed in the input code, and why?

- Original PoissonInput used N=1. At 150 Hz and dt=0.0001 s its per-step input is Bernoulli with probability 0.015.
- Brian2's generated NumPy code filtered the indices passed to the random generator by `not_refractory`. The voltage equation is conditional on refractory state.
- A lesion can affect a sensory neuron's firing through recurrent feedback. A changed refractory mask can skip a random draw, moving later inputs onto different positions in the random stream.
- Therefore, an identical baseline replay could succeed while a baseline/lesion pair with the same seed received different later inputs. This defect was found by recording actual input voltage jumps, not by assuming seed equality was enough.
- The corrected code generates the complete time-by-input Bernoulli array using a separate seeded generator before network execution. A TimedArray reads the scheduled event for each step. State cannot advance that schedule.
- Retain the same jump amplitude, scheduling slot, zero refractory-period parameter for sugar targets and conditional voltage writes. Recurrent equations and outgoing lesions remain unchanged.
- Scheduled and delivered events are different records. A scheduled event can fail to write voltage because of the neuron's state. Equality is required for the schedules, not for their state-dependent effects.
- Example: input A has scheduled events at ticks 10 and 20 in both runs. A voltage write at tick 20 may be blocked in one run. Input B still receives its own tick-20 draw; it does not inherit A's next random number.
- This changes which trajectory a historical seed denotes. It preserves the stepwise input distribution, not bitwise identity with the old trajectories. New selection baselines were generated instead of combining versions.
- The regression test uses feedback in a small graph: lesions change firing, scheduled inputs stay identical, and delivered events remain a subset of scheduled events.
- Evidence: [generated Brian2 code](../../results/pcdr/corrected_20260919/original_poisson_generated_code.txt), [its manifest](../../results/pcdr/corrected_20260919/original_poisson_code_manifest.json), and [earlier failed pair](../../results/pcdr/corrected_20260919/prior_pair_failure.json). See also [Brian2 PoissonInput](https://brian2.readthedocs.io/en/stable/reference/brian2.input.poissoninput.PoissonInput.html).

## Other code corrections and their consequences

- Complex support: compute abs(v) squared before ranking. For [1, i, 1, i], three entries carry 75% of power. Taking the real part changes the input to [1, 0, 1, 0] and answers a different question.
- Solver seeding: record and actually pass a starting vector. Recording an unused seed provides no reproducibility.
- Mode ordering: count stable complete modes toward the first twenty. Retain raw spectral ranks too. An unstable or incomplete mode must not consume one of the twenty stable-mode positions specified in the plan.
- Rate strata: the initial implementation ranked all neurons, mostly silent ones. Corrected it to rank eligible E and I pools separately. Kept the old selection as a development output.
- Memory measurement: psutil was absent. Used native operating-system peak-memory queries instead of installing another package or inventing a measurement.
- Trial source checks: source archives and hashes identify the implementation behind each run. A changed simulation cannot silently reuse a completed trial with an old signature.
- Collection checks: completion alone is not sufficient. Seeds, lesion IDs, network variants, backend, input protocol and provenance must also match the frozen job manifest.
- Windows timeout handling: a virtual-environment executable can have a child process. Killing only its wrapper can leave computation running. The controller stops the child process tree on timeout and records failure. It does not continue launching jobs after a failed worker.
- None of these corrections was chosen to increase an effect size. The recorded purpose is to make the intended comparison well-defined and reproducible.

## Why were three tests skipped?

- They were `test_validation_tree_symlink_escape_is_rejected_when_supported`, `test_validation_root_symlink_escape_is_rejected_when_supported`, and `test_symlink_escape_is_rejected_when_supported` in `tests/test_validate_neuron_ids.py`.
- Each tries to create a symbolic link so it can test whether path validation rejects an escape from the allowed directory.
- Windows raised an error while creating that link in this environment. The tests explicitly skip in that situation; they did not execute their link-rejection assertion.
- They concern filesystem validation, not eigenvectors, firing, matching, or lesion results. A skip is not a pass.
- Reran the file with `-rs` to obtain the actual reasons, together with the new local-controller tests: 48 passed, 3 skipped. The earlier full suite had 204 passed, 3 skipped.
- The Brian2 warnings in the full suite were deprecated pyparsing calls. They were reported, not repaired by silently changing the environment.

## What is deferred, rather than silently skipped?

| Stage | Why it is pending | What would allow it to proceed |
|---|---|---|
| Remaining individual lesions | These are now queued locally, serially. | Complete all frozen jobs, then collect their paired results. |
| Whole-brain eigen-set lesion | James's individual-cell sequence comes first. | Complete singles and pass stable-mode selection. |
| 199-control confirmation | Its cost is much larger than a local pilot; CCR is unavailable. | Sufficient compute and strict matching, with the full protocol preserved. |
| Cython switch | Compiler/backend agreement has not been established. | The saved benchmark must pass before changing execution. Current runs remain NumPy. |
| Pruning, I:E and global-weight sensitivities | Otherwise several network changes would be mixed into the first result. | Complete the main comparison; use each altered network's own baseline. |
| JO context | It is an extension, not a replacement for unsuccessful sugar selection. | A separately recorded context study. |
| Fixed-membership surrogate analysis | Existing summaries recluster each surrogate, which changes the statistic. | A separately labeled exploratory analysis, without changing the frozen targets. |
| Exact Currier 5% attribution | Accessible evidence verified the broad finding, not this numerical threshold. | Verify the full methods; until then call 5% a protocol choice. |

## How the unattended local work operates

- `pcdr_local_queue.py` reads the already frozen 720-job single-cell manifest. It changes execution order to run each seed across all cells before moving to the next seed. This produces balanced early batches without changing the final sample size or selecting results.
- The 720 jobs are baseline plus 23 cells, each at 30 seeds. The 23 include 20 E/I targets, two outside-group controls, and one silent control. Fresh single-cell seeds are 630201–630230.
- Each job launches a new Python process. Network memory is released when it exits. There are no nested simulation workers. BLAS/OpenMP thread limits are set to one; the controller has reduced scheduling priority.
- Before a job, require 4 GiB available RAM and 10 GiB free disk. Low RAM causes a wait. Low disk or a worker error stops the queue with an explicit status. These are operational limits, not scientific criteria.
- Logs record the command and trial result. Trial manifests retain code, input and output hashes. Controller status records the completed count, current trial, error if any, and deadline.
- The deadline was set at the start of this continuation: Monday 21 September, about 9:43 p.m. Eastern. Restarting the controller preserves that original deadline.
- The controller requests that Windows remain awake during execution, without changing permanent power settings. Manual shutdown/reboot can still interrupt it. A stale lock after a crash requires checking that no old worker is running before resuming.
- `pcdr_local_followthrough.py` waits for completed singles, generates an all-target findings report, then allows up to two hours for mode construction and one hour for strict matching. It shares the overall deadline.
- If those gates pass, it prepares a separate 35-trial mode pilot using seeds 630901–630905. These do not overlap selection or single-cell seeds. It automatically collects and writes its findings too.
- `pcdr_local_findings.py` writes every target into a Markdown table. It does not filter for favorable results. The single-cell report includes the complete 40-test BH family. Mode-pilot results remain labeled exploratory.
- These Python processes make no OpenAI API calls. Model quota is therefore not a dependency of trial execution or report generation. An hourly Codex follow-up is additional supervision, not the engine of progress.
- The scheduled follow-up still requires the desktop app/computer to be available; do not assume it can bypass service limits. [Official scheduled-task documentation](https://learn.chatgpt.com/docs/automations?surface=app) describes returning to a chat and keeping local projects available. The independent-process arrangement is our implementation choice.

## What counts as a finding?

- A reproducible single-cell ΔHz estimate with paired-seed uncertainty and its stated multiple-testing context.
- A stable eligible mode, or a documented failure of the prespecified selection.
- Adequate matched controls, or documented inability to construct them.
- A reduced-pilot effect estimate, explicitly separated from the eventual confirmation.
- A weak, zero or inconclusive effect is a result. The Monday deadline is not a requirement to obtain support for P.

Current status files: [singles](../../results/pcdr/ccr_singles_20260919/local_status.json), [follow-through](../../results/pcdr/local_followthrough_20260920/status.json). Completed-stage reports will be written as `FINDINGS.md` inside each study directory.

## Evening controller repair, 20 September 2026

- A Windows PermissionError prevented atomic replacement of local_status.json after a successful worker. The error handler attempted the same write and failed too, leaving stale running status. A status label alone therefore does not prove controller liveness; supervision also checks process IDs and logs.
- The queue now retries only PermissionError from status replacement, bounded to 30 seconds. The temporary JSON remains complete; os.replace remains the atomic publication step. Persistent denial still stops execution. Tests cover both recovery and bounded failure. The exact interfering reader was not identified, so it is not attributed to any application.
- Resume checks saved manifests before starting jobs. Completed data and frozen scientific code are preserved; restart does not grant another 30-hour window because the original deadline is loaded from status. Old controller code, status and traceback are retained in the study directory.
- The comprehensive Word/PDF record is a timestamped edition. Later notebook entries are not silently added to its frozen source snapshot. The builder handles headings, repeated table headers, equations, citations and figures; Word resolves contents/page fields, and Poppler renders pages for inspection. These publishing changes do not modify scientific results.

## Why local execution ended before the deadline

- The 720 single-cell trials completed; this stage is a thirty-seed study, not a partial batch. Its secondary tests concern the selected individual neurons and are corrected as one 40-test family. They do not test eigencircuit localization.
- The eigen-solver produced 22 stable complete modes from 40 pairs. An independent root-ID join confirmed no baseline spikes inside any of the first 20 75%-power supports. Small recruited power outside those supports is compatible with that result.
- The selection rule requires at least ten support cells with five spikes. A failed prerequisite stops the mode experiment. Controls, mode lesions and confirmation were therefore skipped deliberately, not because of insufficient time. Computing 80 pairs was a conditional remedy for too few complete modes, not a fallback for low recruitment.
- The result narrows this protocol's feasibility in the sugar context. It does not settle P/D/C/R. A future deeper-spectrum or alternative-context experiment must record new rationale and selection rules separately before viewing its lesions.
- Completion verification code is a read-only audit of saved trial manifests, mode memberships and feature counts. It writes an audit record with source hashes; it does not change scientific data or reopen completed stages. FINAL_HANDOFF.md records the early stopping reason and pending work. The monitoring heartbeat is paused after this handoff because no unattended stage remains.

## Authorized exploratory search after the first search stopped

- The 21 September user request authorizes new local work; the first search's failure is still reported. The new amendment doubles the eigensolver budget to 80 pairs and inspects 40 stable complete modes. This search is informed by the earlier recruitment failure and must remain exploratory.
- The separate solver copy preserves the original matrix, complex support calculation, residual and cross-start stability checks. Fixed limits prevent repeated searching until something qualifies. New seeds distinguish numerical starts; selection uses the same frozen baseline and never the single-cell lesion outcomes.
- Cell-class annotations can suggest a context mismatch but cannot substitute for measured neuropil synapse distributions. The available table lacks neuropil fields, so that analysis is explicitly unavailable. Missing annotations are counted rather than removing support cells.
- The autonomous controller stops on unresolved candidate coverage, selection failure, strict matching failure, timeout or error. If all prerequisites pass, only a five-control/five-seed pilot is authorized here. No 199-control confirmation is silently substituted. The current Word/PDF edition predates this new authorization; this entry records its timing, and later exports should incorporate the actual outcome.

## Why the exploratory mode pilot did not run

- The 80-pair search succeeded in finding a recruited support, but mode eligibility and control matching are distinct prerequisites. Strict matching accepted zero of five required sets after 50,000 proposals. The failure guard deliberately blocked preparation and lesions.
- Exact sign/recruitment counts and SMD <= 0.1 across six continuous features were not relaxed. Zero accepted proposals does not prove the feasible set is empty: a finite nearest-neighbor randomized sampler may miss valid combinations. Rejected feature-balance vectors were not recorded, so the present evidence does not establish which constraint was limiting.
- The code's error text says confirmation is blocked because generate() is shared with confirmation preparation. This run was a reduced exploratory pilot; the wording does not make it a confirmation attempt. The generic Brian2 error banner likewise does not identify the scientific cause; the actual exception is insufficient matching.
- No extra eigen search or alternate target was launched after this stop. A future matching-feasibility diagnostic should examine exact stratum capacity and attainable feature balance without adapting lesion outcomes. Any altered sampler requires a new recorded proposal distribution and validation. The completed failed-sampler result remains in the record.

Completed-extension export: 46-page Word/PDF edition preserved separately. Visual QA repaired draft UTF-8 decoding and pagination only. See the dated notebook entry and exports/pcdr_research_record_20260921_completed/export_manifest.json for exact builder, QA and output hashes. No research code or matching rule was changed during export.

### 21 September 2026 matching feasibility audit

- User authorized diagnosing matching and requested defensible documentation. Created scripts/pcdr_matching_audit.py, pcdr_matching_witness.py and pcdr_matching_report.py with Codex assistance. Full purpose, mathematics, commands, limitations and source notes are in MATCHING_AUDIT_20260921.md.
- Wrote protocols before replay and optimization. Reproduced 0 accepted sets in 50,000 proposals. Incoming strength failed every proposal; baseline activity failed none. Two focused tests passed; independent saved-ID validation passed for five optimized feasibility examples, maximum SMD 0.07335.
- Kept the same target, exclusions and thresholds. Five examples establish feasibility, but are not random null draws. No lesion jobs started. Original confirmation and original failure remain preserved. Recommended a separately amended descriptive optimized-comparison pilot; calibrated random-reference inference remains unresolved.
- Source commands and hashes: results/pcdr/matching_audit_20260921/protocol.json, witness/protocol.json and independent_validation.json. Full proposal balances are preserved. Updated the comprehensive record with an audit addendum; earlier editions remain unchanged.

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

### 21 September 2026 optimized pilot completed and audited

- Completed 35/35 trials at 20:07:50 UTC, about 10 minutes 40 seconds after the queue began. Six lesion conditions each have five fresh paired seeds. No extra trials or changed thresholds.
- Ran .venv/Scripts/python.exe scripts/pcdr_verify_optimized.py. Verified all trial outputs against hashes, frozen jobs/provenance, 30 paired input digests, six rate summaries and every row of six 127,400-neuron footprints. All scheduled and delivered input digests matched. No primary/reference p-values or secondary test files exist for this pilot.
- Eigen-set A = 22.576 Hz and F = 0.229408, larger than all five optimized comparisons (A 11.486–16.467 Hz; F 0.1853–0.2162). Off-support response is still 77.06 percent of total absolute mean response. This is descriptive evidence for the predicted ordering in one selected context, not confirmation or independence.
- MN9 mean change = -82.2 Hz; motor total change = +27.6 Hz. Readout membership differs: the mode includes MN9 and 13 motor cells, while comparisons exclude MN9 and include 3–5 motor cells. Preserve this qualification; do not describe secondary contrasts as behavior or a uniquely downstream effect.
- Saved completion_audit.json, per_seed_readouts.csv and FINAL_HANDOFF.md. Added OPTIMIZED_PILOT_RESULTS_20260921.md with every condition and seed, bootstrap intervals, mathematics, code purpose, commands, limitations and pending research. Verification script created with Codex assistance; no simulated outputs modified.
- First verifier pass identified motor membership counts; added those counts to the written interpretation and reran the deterministic verifier so its code hash and report agree. This repeated analysis did not change selection or inferential tests. No new simulation, p-value, sensitivity run or post-outcome mode search was performed.
- Preserved earlier Word/PDF editions and appended a new results chapter using scripts/pcdr_append_pilot_document.py. Prior chapters remain dated history; cover directs readers to Chapter 11. No unfinished confirmation is described as complete. Recommended adviser/design review before additional runs.

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
