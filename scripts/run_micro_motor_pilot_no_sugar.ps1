<#
run_micro_motor_pilot_no_sugar.ps1

Ultra-fast motor-output pilot that avoids the unresolved explicit sugar-ID
coverage problem. It uses annotation-derived contexts that are present in the
current simulator completeness table.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\run_micro_motor_pilot_no_sugar.ps1

Outputs:
    results\micro_motor_pilot_no_sugar\sweep_summary.csv
#>

$ErrorActionPreference = "Stop"

$OutDir = "results\micro_motor_pilot_no_sugar"
$LogDir = Join-Path $OutDir "logs"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$PythonExe = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$Start = Get-Date
"Started micro motor pilot no-sugar: $Start" | Out-File (Join-Path $OutDir "RUN_STATUS.txt")

function Run-Step {
    param(
        [string]$StepName,
        [string[]]$StepArgs
    )
    $LogPath = Join-Path $LogDir "$StepName.log"
    Write-Host "==== $StepName ===="
    Write-Host "Logging to $LogPath"
    Write-Host "Command: $PythonExe $($StepArgs -join ' ')"
    $OldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $PythonExe @StepArgs 2>&1 | Tee-Object -FilePath $LogPath
    $ExitCode = $LASTEXITCODE
    $ErrorActionPreference = $OldEAP
    if ($ExitCode -ne 0) {
        throw "Step failed: $StepName with exit code $ExitCode"
    }
}

# Recreate contexts. Sugar may remain under-covered in the current completeness
# table, but this micro run intentionally uses only annotation-derived contexts.
Run-Step -StepName "01_create_source_contexts" -StepArgs @(
    "tools\create_source_contexts.py",
    "--annotations", "flywire_annotations.tsv",
    "--completeness", "Drosophila_brain_model\2023_03_23_completeness_630_final.csv",
    "--sugar-ids", "metadata\sugar_ids_21.txt",
    "--output-dir", "metadata\source_contexts",
    "--matched-k", "21",
    "--seed", "13"
)

# Smallest real motor-output run: 2 contexts x 3 targets x 1 trial.
# This is not final inference; it exists to produce a professor-discussion CSV.
Run-Step -StepName "02_micro_perturbation_sweep" -StepArgs @(
    "tools\run_context_perturbation_sweep.py",
    "--annotations", "flywire_annotations.tsv",
    "--completeness", "Drosophila_brain_model\2023_03_23_completeness_630_final.csv",
    "--connectivity", "Drosophila_brain_model\2023_03_23_connectivity_630_final.parquet",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "matched_size",
    "--context-names", "gustatory,visual_projection",
    "--group-by", "cell_class",
    "--min-group-size", "100",
    "--max-targets", "3",
    "--n-run", "1",
    "--t-run-ms", "1000",
    "--n-proc", "1",
    "--output-dir", $OutDir
)

$End = Get-Date
$Elapsed = New-TimeSpan -Start $Start -End $End
"Finished micro motor pilot no-sugar: $End`nElapsed: $Elapsed" | Out-File (Join-Path $OutDir "RUN_STATUS.txt") -Append
Write-Host "DONE. Results are in $OutDir"
