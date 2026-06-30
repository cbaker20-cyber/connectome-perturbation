<#
run_targeted_context_validation.ps1

Run the first explicit Brian2 validation of structural-surrogate hits.
This is not a broad sweep. It tests AN against a motor-proximal positive control
in a few corrected source contexts.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\run_targeted_context_validation.ps1

Outputs:
    results\targeted_context_validation\sweep_summary.csv
#>

$ErrorActionPreference = "Stop"

$OutDir = "results\targeted_context_validation"
$LogDir = Join-Path $OutDir "logs"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$PythonExe = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$Start = Get-Date
"Started targeted context validation: $Start" | Out-File (Join-Path $OutDir "RUN_STATUS.txt")
$LogPath = Join-Path $LogDir "targeted_context_validation.log"

Write-Host "==== Targeted Context Validation ===="
Write-Host "Logging to $LogPath"

# Important: do not pipe native stderr as a stopping error; Brian2 may still emit warnings.
$OldEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $PythonExe "tools\run_targeted_context_validation.py" `
  --annotations "flywire_annotations.tsv" `
  --completeness "Drosophila_brain_model\2023_03_23_completeness_630_final.csv" `
  --connectivity "Drosophila_brain_model\2023_03_23_connectivity_630_final.parquet" `
  --contexts "metadata\source_contexts\source_context_manifest.csv" `
  --context-mode "matched_size" `
  --context-names "sensory_ascending,mechanosensory,gustatory,sugar" `
  --group-by "cell_class" `
  --target-names "AN,brain_motor_neuron" `
  --n-run 3 `
  --t-run-ms 1000 `
  --n-proc 1 `
  --output-dir $OutDir 2>&1 | Tee-Object -FilePath $LogPath
$ExitCode = $LASTEXITCODE
$ErrorActionPreference = $OldEAP

if ($ExitCode -ne 0) {
    throw "Targeted context validation failed with exit code $ExitCode"
}

$End = Get-Date
$Elapsed = New-TimeSpan -Start $Start -End $End
"Finished targeted context validation: $End`nElapsed: $Elapsed" | Out-File (Join-Path $OutDir "RUN_STATUS.txt") -Append
Write-Host "DONE. Results are in $OutDir"
