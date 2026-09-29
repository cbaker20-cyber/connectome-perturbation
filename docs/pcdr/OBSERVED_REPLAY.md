# Recorded replay: process and decisions

Completed locally on 28 September, 23:10–23:21 EDT (29 September 03:10–03:21 UTC). All four recorded trials match the saved spikes and delivered inputs exactly. State-array, clock, index and selected-cell threshold checks also passed. Initial available memory was 7.073 GB; measured worker peak memory ranged from 2.744 to 2.883 GB. See evidence/2026-09-28/observed_replay_check.json. The resource refusal and preparation notes below remain as the historical record.

27 September 2026. Implementation and small-network checks are complete. The four whole-brain trials have not run: the local launcher measured 3.20 GB free and refused to start. No new simulation output or mechanistic result is claimed.

## Why this case

The existing mode-without-MN9 lesion at seed 631405 produces a large response at 0.0125 ms and a much smaller one at 0.00625 ms under weight 1.2/inhibition 0.8. Its delivered inputs match its same-step baseline in both saved trials. The next question is where the recorded voltage, synaptic drive and refractory state differ, not whether another response-size comparison is significant. The plan has exactly four one-second runs: the same lesion and its baseline at each step. Seeds, weights, outgoing-only lesion, equations, refractory settings, delay and scheduled physical inputs remain unchanged.

## Cell selection and its limits

Read the saved lesion/baseline spike differences at each step, ordered by time and then neuron ID. Take the first eight distinct differing cells at each step and union them with MN9. This selects ten cells overall; their exact IDs and the two component lists are in OBSERVED_REPLAY_PLAN.json. Selection uses known spike outcomes, before new state traces. It is retrospective and cannot support a held-out or unbiased cell-selection claim. It samples early event differences and MN9; it does not cover every neuron in the later population increase or establish that those cells cause it. A first event difference can be a shifted spike time.

## What is recorded

Use Brian2 StateMonitor on every simulation tick for v, g and not_refractory at before_thresholds and after_synapses. The first slot follows integration and precedes spike detection. The second follows synaptic updates and precedes resets under the retained schedule. Save the actual scheduling summary with each run so this can be checked rather than inferred from array labels. v and g are saved in millivolts. In these equations g is voltage-valued synaptic drive; it is not a measured current and should not be labeled amperes. The Boolean flag indicates the model's refractory eligibility at the recording slot.

The existing input monitors, simulator body and numerical method are retained in a separate observed copy; the historical simulator is unchanged. Reviewed the source diff: additions are recording-index checks, two state monitors, the scheduling summary and returned trace arrays. The original input helper remains in the copy but the runner constructs the five-step saved tape using the already-tested resolution helper. No alternate integration method, changed precision, newly generated input or state reset was introduced.

Brian2's StateMonitor defaults to the start slot, where reset behavior can hide above-threshold values. The explicit slots avoid conflating that display effect with dynamics. Checked the installed scheduling_summary(net=None) signature and Brian2 2.9.0 documentation: https://brian2.readthedocs.io/en/2.9.0/reference/brian2.monitors.statemonitor.StateMonitor.html . These API facts justify the recording placement; they do not establish the cause of the high-weight response.

## Checks before interpreting a trace

Every run must match the complete ordered saved spike sequence and delivered-event record at its own time step. Scheduled events must also match the original physical tape. The runner verifies source-file hashes, reference manifests, input-file hashes and reference-file hashes; IDs remain strings when converted to FlyWire IDs. A mismatch marks the run failed and stops later trials. State arrays and available events are retained on failure for diagnosis; they are not accepted as comparable traces. Local Python/platform details are recorded separately from the CCR reference environment. Passing the event comparison establishes replay for those outputs, not platform equivalence in general.

Small-network tests compare the unchanged simulator with the observed copy at both steps, with and without a lesion. Every spike and delivered event matched. Tests also check trace shapes and clocks, finite drive, above-threshold voltage and non-refractory flags for recorded spikes, duplicate recording indices, low-memory refusal, changed-source refusal, existing-output preservation, and stopping after worker failure. Twenty-nine focused tests passed; 60 warnings were Brian2/pyparsing deprecation warnings. Full-network recording equivalence remains untested.

## Memory, time and files

The PC has approximately 15.6 GiB visible RAM; the initial check showed about 3 GB available. Prior whole-brain workers peaked around 2.8 GB before these new records. Two slots for ten cells at 160000 ticks need about 54.4 MB for v, g and Boolean arrays alone, plus time arrays, internal monitor buffers, compression work and the existing simulator. This is an array-size calculation, not a measured new peak. Require 6 decimal GB available before startup and before each serial worker to leave headroom. Do not stop unrelated processes to obtain it. The memory check prevents an obviously tight launch but is not a reservation against other applications.

Only one worker runs at once. Each has an external 1200-second deadline; four successful runs therefore have at most 80 minutes of worker allowance, not a measured runtime prediction. The watchdog only terminates its own process tree. Output folders must be new. Completed and failed worker records are retained; automatic partial-run resume is not implemented. A hard process or machine failure can leave a running status, so completion requires four successful worker exits and four matching manifests. This runner is Windows-local; no new CCR allocation or upload artifact was created.

Each worker saves spikes.parquet, delivered_events.parquet, states.npz, schedule.txt and manifest.json. The state index order maps to record_ids in the plan and indices in the saved neuron universe. Units are part of array names. The controller saves plan.json, progress.json and worker stdout/stderr/process records. Sources and reference hashes are frozen in the plan. Do not interpret partial output as a completed four-run comparison.

## Running after memory is available

From C:/Users/Baker/Drosophila_Data, run this single PowerShell line:

```powershell
.venv\Scripts\python.exe scripts/pcdr_observed_replay.py run --plan docs/pcdr/OBSERVED_REPLAY_PLAN.json --original results/pcdr/results_ccr_20260927/raw_download/expanded_sensitivity --reference results/pcdr/results_ccr_20260927/resolution_download --out results/pcdr/observed_replay_20260927
```

The attempt during this review exited before creating the output directory: Need 6 GB available for one worker; currently 3.20 GB. This is a resource refusal, not a failed scientific trial. After successful recording, compare within-step lesion/baseline traces first, then aligned physical times across steps. Examine voltage relative to threshold, recurrent drive changes and refractory eligibility near the first event differences and the later rise. Do not infer causality from a selected cell's timing, call a small-step trace the correct solution, or change the monitored membership after seeing the traces without recording a separate amendment.
