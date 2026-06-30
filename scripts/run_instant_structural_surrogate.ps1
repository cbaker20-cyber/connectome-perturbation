<#
run_instant_structural_surrogate.ps1

Fast non-Brian2 structural surrogate benchmark.
This gives immediate professor-facing data while slow spiking sweeps are still
being debugged or running.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\run_instant_structural_surrogate.ps1
#>

$ErrorActionPreference = "Stop"

$OutDir = "results\structural_surrogate_benchmark"
$LogDir = Join-Path $OutDir "logs"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$PythonExe = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$Start = Get-Date
"Started instant structural surrogate benchmark: $Start" | Out-File (Join-Path $OutDir "RUN_STATUS.txt")

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
        throw "Step failed: $StepName with exit code $LASTEXITCODE"
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

Run-Step -StepName "02_structural_surrogate_benchmark" -StepArgs @(
    "tools\structural_surrogate_benchmark.py",
    "--connectivity", "2023_03_23_connectivity_630_final.parquet",
    "--annotations", "flywire_annotations.tsv",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "matched_size",
    "--context-names", "gustatory,mechanosensory,visual_projection,sensory_ascending,all_sensory",
    "--group-by", "cell_class",
    "--max-steps-source", "3",
    "--max-steps-motor", "3",
    "--gamma", "0.80",
    "--min-group-size", "20",
    "--output-dir", $OutDir
)

$End = Get-Date
$Elapsed = New-TimeSpan -Start $Start -End $End
"Finished instant structural surrogate benchmark: $End`nElapsed: $Elapsed" | Out-File (Join-Path $OutDir "RUN_STATUS.txt") -Append
Write-Host "DONE. Results are in $OutDir"
