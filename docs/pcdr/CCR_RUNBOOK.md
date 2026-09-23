# Transfer and technical checks at CCR

22 September 2026. Prepared with Codex assistance. No CCR connection or submission has occurred. This package contains a four-job technical smoke test, not the proposed confirmatory experiment.

The new matching check found the specified distribution guard infeasible even with fractional memberships. The older motor-matched pilot therefore stays descriptive. Do not dispatch the old 199-control confirmation plan with optimized controls or relabel them as a random reference sample.

## Package contents and environment

`scripts/pcdr_ccr_transfer.py build --out PATH` copies exact source bytes, the three v630 input files, pinned package targets and this runbook into `connectome-ccr.tar.gz`. A SHA256 manifest covers each payload file. The outer `archive.json` records the archive hash; retain it separately when transferring. Raw historical simulation output and credentials are excluded.

The local Python is 3.11.9. `requirements-ccr.txt` records the numerical packages actually used locally, including Brian2 2.9.0. The old root requirements file describes a different environment. Linux installation and node-specific behavior are still untested. If a pinned version cannot be installed, record a new environment amendment and rebuild the package; do not edit an existing trial manifest to evade checks. Use a compute allocation for simulations and follow CCR guidance for environment installation.

CCR's current documentation describes architecture-dependent modules, multiple clusters and allocation-specific partitions. Obtain the actual account using ColdFront or `slimits`; inspect available modules for the intended node architecture. No account, partition, Python module or concurrency has been assumed here. References: [CCR jobs](https://docs.ccr.buffalo.edu/en/latest/hpc/jobs/), [CCR modules](https://docs.ccr.buffalo.edu/en/latest/software/modules/), [CCR login](https://docs.ccr.buffalo.edu/en/latest/hpc/login/).

## On the destination

Check the archive hash against the separately retained `archive.json`, then extract into a new directory. Load the chosen module, create the environment, install `requirements-ccr.txt`, and set `CCR_PYTHON` to that environment's absolute Python path. From the extracted `connectome` directory:

```bash
"$CCR_PYTHON" scripts/pcdr_ccr_transfer.py verify
"$CCR_PYTHON" scripts/pcdr_ccr_transfer.py initialize
"$CCR_PYTHON" scripts/pcdr_ccr_transfer.py prepare --study results/smoke
```

`initialize` makes a local Git snapshot solely because the existing provenance code needs a Git HEAD. Its author is explicitly “Research transfer snapshot”; this is not the GitHub project's history. The transfer manifest retains the original project commit and exact file hashes. Initialization refuses to replace an existing repository. Preparation freezes the destination environment and the four jobs: baseline, identical-seed replay, no-input trial, and outgoing-only MN9 lesion. Seed 631301 is a technical check, not an added hypothesis-test replicate.

Set actual allocation values and provisional smoke resources after checking node limits. One CPU per task and serial array concurrency are sufficient for the NumPy smoke. The following is a template, not an executed command; MEMORY and WALLTIME must be chosen for the smoke allocation and revised from measured results:

```bash
sbatch --clusters="$CCR_CLUSTER" --account="$CCR_ACCOUNT" \
  --partition="$CCR_PARTITION" --nodes=1 --ntasks=1 --cpus-per-task=1 \
  --mem="$MEMORY" --time="$WALLTIME" --array=0-3%1 \
  --output='smoke-%A_%a.out' scripts/pcdr_ccr_smoke.sh results/smoke
```

Add your actual QoS or architecture constraint if the allocation requires it. The environment variable `CCR_PYTHON` must be exported to the job. Load any required runtime modules before calling Python; the template cannot guess them. No automatic submission command exists in the Python helper.

After all four jobs finish, run collection in the same environment:

```bash
"$CCR_PYTHON" scripts/pcdr_ccr_transfer.py collect --study results/smoke
```

Collection checks every output checksum, complete neuron coverage, spike/rate consistency, scheduled input identity, exact replay and undriven silence. It records wall time, peak process RSS and output size. For scheduler accounting, retain `sacct` job state, elapsed time, MaxRSS, exit code and requested resources. The Python measurements do not replace scheduler measurements.

## Failure, resume and next gate

Each worker owns an exclusive lock. A normal exception releases its lock; a killed process may leave one. Confirm the scheduler job is terminal and no process is active before manually removing a stale lock. A matching completed trial is reused only after output checksums pass. A changed configuration or damaged completed output is rejected. Preserve damaged output and rerun in a new study directory instead of silently overwriting evidence.

Test one intentionally omitted array index: collection must fail without a certificate. Submit that missing index, collect again, and check that finished trials were preserved. Test a duplicate active index and verify lock rejection. Actual Slurm cancellation/requeue tests remain to be done on CCR; local process tests are not scheduler validation.

Do not treat a successful technical certificate as permission for a large scientific array. The comparison design still needs defensible balance and response-relevant diversity. Any new design must be frozen before its outcomes are inspected. Keep NumPy unless the separate backend benchmark and cross-backend input check both pass.
