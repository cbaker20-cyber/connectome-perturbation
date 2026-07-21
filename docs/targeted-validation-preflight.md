# Targeted validation preflight

This checklist defines the minimum evidence required before interpreting the high-trial sugar/gustatory run tracked in issue #7. It does not establish that the run has occurred or that any biological effect is real.

## Scope

The planned comparison contains four cells under one declared backend and trial count:

- sugar to AN
- sugar to brain_motor_neuron
- gustatory to AN
- gustatory to brain_motor_neuron

The run remains non-interpretable as neuroscience until every gate below is satisfied and the produced artifacts are reviewed.

## Pre-run gates

1. Record the exact Git commit and require a clean, named configuration file rather than undocumented command-line defaults.
2. Record the backend name and version once; abort if the backend changes during the matrix.
3. Record `NRun`, `TRunMs`, random-seed policy, source labels, target labels, and all perturbation parameters.
4. Resolve every input path before execution and compute SHA-256 checksums from the exact bytes used.
5. Record source-ID counts before running. For the current issue contract, sugar must resolve to exactly 21 source IDs; otherwise stop and diagnose.
6. Preserve neuron identifiers as strings. Do not round-trip identifiers through floating-point values.
7. Declare the expected output paths in advance and refuse silent overwrites unless the prior run is explicitly archived.
8. Capture the command, start/end timestamps, host/runtime metadata, and exit status in the run manifest.

## Required artifacts

A complete run must contain all of the following:

- `run_manifest.yml`
- `sweep_summary.csv`
- `sweep_run_info.csv`
- `ranked_targeted_validation.csv`
- `targeted_validation_readable_summary.txt`
- a log file under `logs/`

The manifest should bind the run to:

- the exact Git commit;
- the exact command and configuration;
- backend and dependency versions;
- input filenames, byte sizes, and SHA-256 checksums;
- source and target definitions and counts;
- seed policy and trial parameters;
- every output filename, byte size, and SHA-256 checksum;
- `claim_status: not_interpretable_as_neuroscience` until review is complete.

## Post-run validation

Fail closed if any condition is true:

- the process exits unsuccessfully;
- any required artifact is absent, empty, truncated, or not parseable;
- the backend differs between cells;
- the source count differs from the pre-run declaration;
- output rows do not cover the complete four-cell matrix;
- duplicate or unexpected cells appear;
- run parameters differ across cells except for the declared source/target factors;
- non-finite values occur in reported numeric fields;
- checksums do not match the exact files reviewed;
- the readable summary disagrees with the machine-readable outputs.

A rescue or rerun must receive a new run identifier and manifest. Partial outputs must not be merged into a complete run without an explicit provenance record.

## Interpretation boundary

Even a complete, internally consistent run would provide only repository-local simulation evidence under the declared model, data, backend, and parameters. It would not by itself establish a biological mechanism, causal neural pathway, behavioral effect, generalization across connectome releases, or relevance to regeneration. The planned comparison is useful only as a controlled robustness check against the narrower question in issue #7.

## Review record

Before closing issue #7, attach or link:

1. the exact-head GitHub Actions result for any repository validators;
2. the run manifest and checksummed outputs;
3. a concise discrepancy report for missing, rescued, or excluded trials;
4. a statement separating observed repository-local quantities from biological interpretation;
5. the reviewer decision: accepted for further analysis, rerun required, or blocked.
