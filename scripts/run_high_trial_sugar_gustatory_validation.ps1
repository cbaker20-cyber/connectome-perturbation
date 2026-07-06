param(
    [int]$NRun = 30,
    [double]$TRunMs = 1000,
    [string]$ContextNames = "sugar,gustatory",
    [string]$TargetNames = "AN,brain_motor_neuron",
    [string]$GroupBy = "cell_class",
    [string]$OutputRoot = "results/high_trial_targeted_validation"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$PythonExe = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $OutputRoot "run_$Stamp"
$LogDir = Join-Path $OutDir "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null

$CommandText = "$PythonExe tools\run_targeted_context_validation.py --annotations flywire_annotations.tsv --completeness Drosophila_brain_model\2023_03_23_completeness_630_final.csv --connectivity Drosophila_brain_model\2023_03_23_connectivity_630_final.parquet --contexts metadata\source_contexts\source_context_manifest.csv --context-mode matched_size --context-names $ContextNames --group-by $GroupBy --target-names $TargetNames --n-run $NRun --t-run-ms $TRunMs --n-proc 1 --output-dir $OutDir"

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

Write-Host "Running high-trial targeted validation..."
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
    --n-proc 1 `
    --output-dir $OutDir 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "high_trial_validation.log")

& $PythonExe tools\summarize_targeted_validation.py `
    --summary (Join-Path $OutDir "sweep_summary.csv") `
    --output-dir $OutDir

Write-Host "Done. Outputs:"
Write-Host "  $OutDir\run_manifest.yml"
Write-Host "  $OutDir\sweep_summary.csv"
Write-Host "  $OutDir\ranked_targeted_validation.csv"
Write-Host "  $OutDir\targeted_validation_readable_summary.txt"
