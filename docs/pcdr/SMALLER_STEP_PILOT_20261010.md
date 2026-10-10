# Authorized smaller-step pilot — 10 October 2026

User authorized preparing and running the proposed pilot, with a two-hour work window ending16:30UTC October10. The earlier no-launch restriction is superseded for this pilot. This record precedes new simulation outcomes. Current status: preparation; no CCR launch yet.

Keep original three seeds631401–631403, baseline and mode, new steps0.00005/0.000025ms and one-second scientific duration: twelve possible new scientific trials. Existing0.0001ms outputs are anchors. Keep signed-mean averaging and original convergence criteria. The first three seeds are previously inspected and are not independent confirmation. All18 old agreement groups remain failed.

## Capacity and reproduction gate

Before attempting scientific trials, reproduce the first10ms of the archived0.0001ms baseline and mode for seed631401, comparing all ordered spikes and delivered input events exactly. Then run baseline seed631401 through10ms at each new step, in order0.00005 then0.000025ms. These fixed prefixes measure runtime and observed memory under the actual environment; they are not shorter scientific trials and cannot support convergence of the one-second responses. No seed or window is selected from new outcomes.

One worker at a time; require a real Slurm compute allocation, at least3CPU cores and32,000MB allocated memory, plus sufficient personal disk quota. Keep8GB for other processes. Preserve same NumPy backend, input schedules and model code. Record environment and exact hashes. Bound each subprocess by the earlier of45minutes, the block deadline minus collection reserve, or allocation expiry minus reserve. Reserve5minutes for collection. Do not run simulation on login nodes. A stopped prefix is incomplete and remains preserved.

Only consider one-second work if both references and probes complete, measured peak memory with50%headroom fits available memory, and a conservative runtime screen fits the remaining window. Use twice the observed full-prefix runtime scaled100× as a scheduling screen for each new step; include all12serial trials in the remaining-budget comparison. This is a conservative planning rule, not a guarantee or a scientific threshold. All-or-none gate prevents spending the remaining window on predictably unfinished full trials. If it cannot fit, report capacity and retain the twelve-trial design as unexecuted. Do not expand resources/concurrency, truncate scientific duration or relax criteria to manufacture completion.

The short prefix does not measure later recurrent activity or full one-second tape/recorder memory. Require at least16GB per scientific worker in addition to the8GB reserve; measured peak alone cannot establish production memory. No automatic allocation extension, backend change, new seed or larger panel.

## Integrity and completion

New package and output directories refuse overwriting. Existing archived packages, data and failed attempts remain untouched. Validate selected source/reference output hashes, all physical input IDs/times and identical baseline/mode input schedules. New output states distinguish prepared, probe-complete, budget-insufficient, failed, interrupted and scientific-complete. A ZIP or launcher PID is not completion. Reproduction is a prerequisite, not convergence.

No independent human review is implied. Implementation and technical documentation use Codex assistance. Any capacity results must report actual node/allocation/environment and runtime, not just extrapolation. The user will receive exact launched-versus-prepared status and the unresolved next decision.

## Validation and access status

Local tests:24 passed in22.41seconds,52 dependency warnings. They cover new-step physical input mapping, exact delay/refractory tick representation, invalid inputs, analytical linear states, tiny-network agreement with the earlier unwindowed recorder, prefix boundaries, deadline/resource gates and corrupted package inputs. First test attempt had22passes/two failures: a toy fixture with connection weight50 did not produce the asserted downstream spike within3ms. Preserved source, XML and candidate package; changed only the toy fixture to200 to exercise the intended downstream-spike comparison. No scientific source/data was changed. Final extracted-package tests and independent release verification remain pending at this entry.

CCR OnDemand initially timed out and the old terminal did not respond. User was asked to restore usual access while local preparation continued. No remote simulation has been observed or claimed launched.

## Launch when access is available

Use only the final validated `exports/CCR_Smaller_Pilot.zip`, extracting into the new `connectome_smaller_pilot` folder. Do not overlay an earlier study or run the old fine-study notebook. The new shell launcher requires a current CCR compute allocation,32GB and at least3cores; it runs a single worker. The account/partition must be confirmed in the actual allocation, not assumed from an expired browser terminal. The launcher loads the previously used Python3.11.5 modules and installs the archived pinned requirements in an isolated environment. The outer process deadline bounds installation as well as simulation.

Run `bash -lc 'bash run_all.sh'` from the new folder inside that allocation. Inspect `smaller_results/progress.json` and retained worker logs. Results are written to `CCR_smaller_pilot_results.zip` even after a handled failure; its existence does not establish scientific completion. Only `scientific_completed:12` with checked outputs indicates twelve complete new trials. `budget_insufficient` means the four reproduction/capacity prefixes completed but the12scientific trials were not started. Independent local verification is still required after retrieval.


Package validation found a second preparation issue before launch: the new support verifier compared list order, although the frozen mode list is in eigenvector rank order and archived lesions are sorted by ID. Their51-cell memberships agree. Corrected only the new verifier to require identical membership and reject duplicates; retained both frozen orderings and the failed package. Added failure cases for wrong membership and missing jobs. A separate command invocation initially targeted the repository rather than the extracted package and failed on the absent package manifest; its record is retained. Neither failure is an archived simulation defect or a scientific outcome.


## Final local release check

Final extracted package:25tests passed in22.29seconds,52dependency warnings. The package verifier passes; separate ZIP/hash/pandas checks verify all96 hashed members, six anchor outputs, input IDs/times/pairing and the12-job panel with unchanged criteria. The shell launcher passes Bash syntax checking. These checks do not substitute for Linux execution or full-network reference reproduction. [Release evidence](evidence/2026-10-10/smaller_pilot/release.json) records source hashes and all preserved preparation failures.

Current upload: `exports/CCR_Smaller_Pilot.zip`,92,670,858bytes, SHA256 `e7d5e046ee366ea0dfb2ce1cd609827b6588ed8b5a5be7d39cd14f2785a1c8f9`. Earlier upload artifacts remain historical evidence; only this new pilot upload is current for the authorized task. The packaged guide records preparation-stage status; this dated local section records the later final validation.

At15:12UTC CCR became reachable but required password/OTP sign-in. Asked user to complete it in Brave. No allocation, upload or simulation launch has been observed. Deadline remains16:30UTC; no extension or claim of new scientific results.


Pre-launch interruption review added owned-worker cleanup on controller interruption as well as timeout. The previous bounded helper handled timeouts but could leave a separately grouped worker alive if its controller was interrupted. The new runner retains the process record and terminates only its owned child/process group before propagating the interruption. Real timeout/failure and simulated interruption tests pass. This changes orchestration only; archived simulator bytes remain unchanged. The final upload hash below supersedes the earlier preparation candidate after its own extracted tests.

Final current upload after interruption cleanup:27extracted tests passed in22.44seconds,52dependency warnings. SHA256 `33c0db11ab9315de5d343a9a73b90986c256cb7e2451a615093c69c057e24476`, 92672641bytes. Independently compared every archive member to the preceding verified release: only orchestration, its tests, the guide and manifest changed; frozen simulator, inputs, anchors and plan are byte-identical. Replaced only the current new pilot upload after validation and preserved the prior candidate. No remote launch.


## Remote execution update — 10 October, after local release

User-supplied terminal output confirms installation/dependency checks and 27 tests passed with 52 deprecation warnings in31.25s. Subsequent process output shows controller638663 and worker674985 running reference_mode at0.0001ms oncpn-d02-23. A displayed Ctrl-C did not eliminate those processes according to that later listing. Do not duplicate/relaunch. No progress JSON or remote result archive has yet been retrieved; reference agreement, actual Slurm allocation/resources and scientific completion remain unverified. Deadline16:30UTC remains unchanged. This execution update supersedes the earlier no-remote-launch statements, which are retained as preparation history.
