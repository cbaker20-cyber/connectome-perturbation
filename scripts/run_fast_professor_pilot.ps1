<#
run_fast_professor_pilot.ps1

Emergency small-but-real data run for professor discussion.

This script prioritizes getting usable output quickly:
1. regenerate source contexts with fixed sugar handling;
2. run a fast null-calibrated context exposure audit;
3. run a tiny context-conditioned perturbation sweep.

If you have to stop early, the exposure audit should already exist. The tiny
sweep writes sweep_summary.csv incrementally.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\run_fast_professor_pilot.ps1
#>

$ErrorActionPreference = "Stop"

$OutRoot = "results\fast_professor_pilot"
$LogDir = Join-Path $OutRoot "logs"
New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$PythonExe = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$Start = Get-Date
"Started fast professor pilot: $Start" | Out-File (Join-Path $OutRoot "RUN_STATUS.txt")

function Run-Step {
    param(
        [string]$StepName,
        [string[]]$StepArgs
    )
    $LogPath = Join-Path $LogDir "$StepName.log"
    Write-Host "==== $StepName ===="
    Write-Host "Logging to $LogPath"
    Write-Host "Command: $PythonExe $($StepArgs -join ' ')"

    # Brian2 often writes warnings to stderr. Do not treat warning text as a
    # stopping PowerShell error; rely on the native process exit code instead.
    $OldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $PythonExe @StepArgs 2>&1 | Tee-Object -FilePath $LogPath
    $ExitCode = $LASTEXITCODE
    $ErrorActionPreference = $OldEAP

    if ($ExitCode -ne 0) {
        throw "Step failed: $StepName with exit code $ExitCode"
    }
}

Run-Step -StepName "01_create_source_contexts" -StepArgs @(
    "tools\create_source_contexts.py",
    "--annotations", "flywire_annotations.tsv",
    "--completeness", "Drosophila_brain_model\2023_03_23_completeness_630_final.csv",
    "--sugar-ids", "metadata\sugar_ids_21.txt",
    "--output-dir", "metadata\source_contexts",
    "--matched-k", "21",
    "--seed", "13"
)

Run-Step -StepName "02_fast_context_reachability" -StepArgs @(
    "tools\context_reachability_audit.py",
    "--connectivity", "2023_03_23_connectivity_630_final.parquet",
    "--annotations", "flywire_annotations.tsv",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "matched_size",
    "--group-by", "cell_class",
    "--max-steps", "3",
    "--gamma", "0.80",
    "--n-null", "10",
    "--min-group-size", "20",
    "--output-dir", "$OutRoot\context_reachability_fast"
)

# Tiny Brian2 run: enough for first motor-output examples, not final inference.
Run-Step -StepName "03_tiny_context_perturbation_sweep" -StepArgs @(
    "tools\run_context_perturbation_sweep.py",
    "--annotations", "flywire_annotations.tsv",
    "--completeness", "Drosophila_brain_model\2023_03_23_completeness_630_final.csv",
    "--connectivity", "Drosophila_brain_model\2023_03_23_connectivity_630_final.parquet",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "matched_size",
    "--context-names", "sugar,visual_projection",
    "--group-by", "cell_class",
    "--min-group-size", "50",
    "--max-targets", "8",
    "--n-run", "2",
    "--t-run-ms", "1000",
    "--n-proc", "1",
    "--output-dir", "$OutRoot\tiny_perturbation_sweep"
)

$End = Get-Date
$Elapsed = New-TimeSpan -Start $Start -End $End
"Finished fast professor pilot: $End`nElapsed: $Elapsed" | Out-File (Join-Path $OutRoot "RUN_STATUS.txt") -Append
Write-Host "DONE. Results are in $OutRoot"
