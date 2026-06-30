<#
run_long_context_perturbation_sweep.ps1

Long unattended Brian2 perturbation sweep. This is intentionally bigger than the
context reachability audit and may run for many hours depending on hardware.
It is resumable because the Python runner skips existing parquet outputs unless
--force is supplied.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\run_long_context_perturbation_sweep.ps1

Outputs:
    results\long_context_perturbation_sweep\sweep_summary.csv
    results\long_context_perturbation_sweep\sweep_run_info.csv
    results\long_context_perturbation_sweep\*.parquet
#>

$ErrorActionPreference = "Stop"

$OutDir = "results\long_context_perturbation_sweep"
$LogDir = Join-Path $OutDir "logs"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$PythonExe = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$Start = Get-Date
"Started long context perturbation sweep: $Start" | Out-File (Join-Path $OutDir "RUN_STATUS.txt")

function Run-Step {
    param(
        [string]$StepName,
        [string[]]$StepArgs
    )
    $LogPath = Join-Path $LogDir "$StepName.log"
    Write-Host "==== $StepName ===="
    Write-Host "Logging to $LogPath"
    Write-Host "Command: $PythonExe $($StepArgs -join ' ')"
    & $PythonExe @StepArgs 2>&1 | Tee-Object -FilePath $LogPath
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $StepName"
    }
}

# Make sure source contexts exist.
Run-Step -StepName "01_create_source_contexts" -StepArgs @(
    "tools\create_source_contexts.py",
    "--annotations", "flywire_annotations.tsv",
    "--completeness", "Drosophila_brain_model\2023_03_23_completeness_630_final.csv",
    "--sugar-ids", "metadata\sugar_ids_21.txt",
    "--output-dir", "metadata\source_contexts",
    "--matched-k", "21",
    "--seed", "13"
)

# Big but bounded overnight sweep.
# 5 contexts x up to 60 cell classes x 5 trials = a serious first benchmark.
# If it is still running in the morning, leave it; it writes sweep_summary.csv incrementally.
Run-Step -StepName "02_context_perturbation_sweep_matched_cell_class" -StepArgs @(
    "tools\run_context_perturbation_sweep.py",
    "--annotations", "flywire_annotations.tsv",
    "--completeness", "Drosophila_brain_model\2023_03_23_completeness_630_final.csv",
    "--connectivity", "Drosophila_brain_model\2023_03_23_connectivity_630_final.parquet",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "matched_size",
    "--context-names", "sugar,gustatory,mechanosensory,visual_projection,sensory_ascending",
    "--group-by", "cell_class",
    "--min-group-size", "20",
    "--max-targets", "60",
    "--n-run", "5",
    "--t-run-ms", "1000",
    "--n-proc", "1",
    "--output-dir", $OutDir
)

$End = Get-Date
$Elapsed = New-TimeSpan -Start $Start -End $End
"Finished long context perturbation sweep: $End`nElapsed: $Elapsed" | Out-File (Join-Path $OutDir "RUN_STATUS.txt") -Append
Write-Host "DONE. Results are in $OutDir"
