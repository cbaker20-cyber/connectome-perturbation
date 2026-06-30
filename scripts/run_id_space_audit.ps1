<#
run_id_space_audit.ps1

Run the ID Space Audit / SourceMap Doctor.
This diagnoses whether annotations, source contexts, completeness, and
connectivity are using FlyWire root IDs or simulator/Brian indices.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\run_id_space_audit.ps1
#>

$ErrorActionPreference = "Stop"

$OutDir = "results\id_space_audit"
$LogDir = Join-Path $OutDir "logs"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$PythonExe = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$Start = Get-Date
"Started ID space audit: $Start" | Out-File (Join-Path $OutDir "RUN_STATUS.txt")
$LogPath = Join-Path $LogDir "id_space_audit.log"

Write-Host "==== ID Space Audit ===="
Write-Host "Logging to $LogPath"
& $PythonExe "tools\id_space_audit.py" `
  --connectivity "2023_03_23_connectivity_630_final.parquet" `
  --annotations "flywire_annotations.tsv" `
  --completeness "Drosophila_brain_model\2023_03_23_completeness_630_final.csv" `
  --contexts "metadata\source_contexts\source_context_manifest.csv" `
  --output-dir $OutDir 2>&1 | Tee-Object -FilePath $LogPath

if ($LASTEXITCODE -ne 0) {
    throw "ID space audit failed with exit code $LASTEXITCODE"
}

$End = Get-Date
$Elapsed = New-TimeSpan -Start $Start -End $End
"Finished ID space audit: $End`nElapsed: $Elapsed" | Out-File (Join-Path $OutDir "RUN_STATUS.txt") -Append
Write-Host "DONE. Results are in $OutDir"
