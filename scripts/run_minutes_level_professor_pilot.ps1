param(
    [int]$NRun = 2,
    [double]$TRunMs = 500,
    [int]$NProc = 4,
    [string]$OutputRoot = "results/minutes_level_professor_pilot"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$PythonExe = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $OutputRoot "run_$Stamp"
$LogDir = Join-Path $OutDir "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null

$ContextNames = "sugar"
$TargetNames = "AN,brain_motor_neuron"
$GroupBy = "cell_class"

$CommandText = "$PythonExe tools\run_targeted_context_validation.py --annotations flywire_annotations.tsv --completeness Drosophila_brain_model\2023_03_23_completeness_630_final.csv --connectivity Drosophila_brain_model\2023_03_23_connectivity_630_final.parquet --contexts metadata\source_contexts\source_context_manifest.csv --context-mode matched_size --context-names $ContextNames --group-by $GroupBy --target-names $TargetNames --n-run $NRun --t-run-ms $TRunMs --n-proc $NProc --output-dir $OutDir"

& $PythonExe tools\make_run_manifest.py `
    --output-dir $OutDir `
    --command $CommandText `
    --annotations flywire_annotations.tsv `
    --completeness Drosophila_brain_model\2023_03_23_completeness_630_final.csv `
    --connectivity Drosophila_brain_model\2023_03_23_connectivity_630_final.parquet `
    --contexts metadata\source_contexts\source_context_manifest.csv `
    --context-names $ContextNames `
    --target-names $TargetNames `
    --group-by $GroupBy `
    --n-run $NRun `
    --t-run-ms $TRunMs `
    --backend numpy

Write-Host "Running minutes-level professor pilot..."
Write-Host "This is not validation. It is a fast tangible pilot for debugging, discussion, and meeting preparation."
Write-Host $CommandText

& $PythonExe tools\run_targeted_context_validation.py `
    --annotations flywire_annotations.tsv `
    --completeness Drosophila_brain_model\2023_03_23_completeness_630_final.csv `
    --connectivity Drosophila_brain_model\2023_03_23_connectivity_630_final.parquet `
    --contexts metadata\source_contexts\source_context_manifest.csv `
    --context-mode matched_size `
    --context-names $ContextNames `
    --group-by $GroupBy `
    --target-names $TargetNames `
    --n-run $NRun `
    --t-run-ms $TRunMs `
    --n-proc $NProc `
    --output-dir $OutDir 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "minutes_level_professor_pilot.log")

& $PythonExe tools\rank_targeted_validation.py `
    --summary (Join-Path $OutDir "sweep_summary.csv") `
    --output-dir $OutDir

Write-Host ""
Write-Host "Done. Professor-pilot outputs:"
Write-Host "  $OutDir\run_manifest.yml"
Write-Host "  $OutDir\sweep_summary.csv"
Write-Host "  $OutDir\ranked_targeted_validation.csv"
Write-Host "  $OutDir\targeted_validation_readable_summary.txt"
Write-Host ""
Write-Host "Interpretation boundary: use this as a tangible pilot only, not as final evidence."
