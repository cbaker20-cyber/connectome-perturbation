# Smaller-step saved-output comparison, 19 October 2026

Ten of twelve full pilot trials were located in Downloads under temporary filenames. Five distinct archives report completed baseline/mode pairs; duplicate recovery downloads were deduplicated by SHA256. Three archive hashes match prior live CCR observations. The two newly located archives have no separately recorded remote archive hash; their package records match the frozen upload and all scientific output hashes match their manifests.

The original question remains whether concentrated eigenvector supports predict localized firing-rate responses to output lesions beyond connectivity, strong connections and recruitment. These comparisons address numerical reliability of the response measurements, not the full biological or predictive question.

| Seed | Timestep comparison (ms) | A difference (Hz) | F difference | Response difference | Population difference (worst condition) | All individual criteria |
|---|---|---:|---:|---:|---:|---|
|631401|0.0001 → 0.00005|1.765|0.00401|14.84%|19.34%|FAIL|
|631401|0.00005 → 0.000025|0.980|0.00273|12.49%|11.64%|FAIL|
|631402|0.0001 → 0.00005|0.000|0.00000|0.00%|0.00%|PASS|
|631402|0.00005 → 0.000025|0.118|0.00334|7.55%|12.00%|FAIL|
|631403|0.0001 → 0.00005|0.824|0.00095|18.70%|22.91%|FAIL|
|631403|0.00005 → 0.000025|—|—|—|—|Finest pair not in downloads|

A is the mean absolute lesion-minus-baseline firing-rate change inside the fixed51-cell support. F is the fraction of the network's absolute response inside that support. Response difference compares every cell's signed lesion-minus-baseline response; population difference compares total spike counts in10ms bins separately for baseline and lesion. Smaller values mean closer agreement. Response and population differences must each be at most5%; F difference at most0.01; A difference at most max(1Hz,5% of finer A). All must pass together.

Seed631401 improves on the next halving but remains outside response and population tolerances. Seed631402 has identical rate responses and population bins for one halving, then differs at the next; identical readouts do not imply identical spike times. There is no consistent monotonic trend across seeds and no convergence finding. One of three available first-halving comparisons and zero of two second-halving comparisons pass. The>=95% individual-pair group requirement is therefore already unmet in these available subsets; no pooled mean criterion was computed here. This three-seed pilot also cannot meet the original30-seed study requirement.

## Checks completed

ZIP CRC and duplicate-member checks; frozen package manifest/plan/execution record equality to exports/CCR_Four_Trial.zip; exact trial specifications and package-version records; all four scientific output hashes; neuron ID strings and unique rate IDs; spike bounds/order/grid and duplicate events; rates reconstructed from spikes; population bins reconstructed from spikes; source manifest/input digest identity; and delivered physical input schedules compared directly with frozen source inputs. Existing0.0001ms anchor output hashes were checked before comparisons. No simulation rerun, source change or tolerance adjustment occurred.

Three local comparison tests passed, covering hand-calculated differences, sparse zero-filled IDs, identical nonzero responses, temporal failure and undefined zero-response concentration. This is saved-output verification, not independent validation of the simulation equations. Reference-prefix output reproduction, worker exit records and refractory intervals were not rechecked in this pass; prior remote controller checks are separate evidence. The last two pilot trials' current cluster status was not checked during this local analysis.

Machine-readable results: results/pcdr/pairs_verified_20261019/verification.json and comparisons.csv. Raw archive copies in that directory preserve downloaded bytes; original temporary downloads remain untouched. The full original eighteen agreement groups remain failed; these new comparisons do not replace that result.
