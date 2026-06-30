<#
run_overnight_context_audit.ps1

Broad overnight run for the context-conditional connectome benchmark.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\run_overnight_context_audit.ps1

This is designed to run unattended. It generates source contexts, runs a fast
sanity audit, then runs several context reachability audits at increasing depth.
It does not run expensive Brian2 perturbation sweeps.
#>

$ErrorActionPreference = "Stop"

$OutRoot = "results\overnight_context_audit"
$LogDir = Join-Path $OutRoot "logs"
New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Python = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $Python)) {
    $Python = "python"
}

function Run-Step {
    param(
        [string]$Name,
        [string[]]$Args
    )
    $LogPath = Join-Path $LogDir "$Name.log"
    Write-Host "==== $Name ===="
    Write-Host "Logging to $LogPath"
    & $Python @Args 2>&1 | Tee-Object -FilePath $LogPath
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name"
    }
}

$Start = Get-Date
"Started overnight context audit: $Start" | Out-File (Join-Path $OutRoot "RUN_STATUS.txt")

Run-Step "01_simulator_sanity_audit" @("tools\simulator_sanity_audit.py")

Run-Step "02_create_source_contexts" @(
    "tools\create_source_contexts.py",
    "--annotations", "flywire_annotations.tsv",
    "--completeness", "Drosophila_brain_model\2023_03_23_completeness_630_final.csv",
    "--sugar-ids", "metadata\sugar_ids_21.txt",
    "--output-dir", "metadata\source_contexts",
    "--matched-k", "21",
    "--seed", "13"
)

# Broad but still reasonable first pass: matched-size contexts, cell_class level.
Run-Step "03_matched_cell_class_deep" @(
    "tools\context_reachability_audit.py",
    "--connectivity", "2023_03_23_connectivity_630_final.parquet",
    "--annotations", "flywire_annotations.tsv",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "matched_size",
    "--group-by", "cell_class",
    "--max-steps", "6",
    "--gamma", "0.80",
    "--n-null", "100",
    "--min-group-size", "10",
    "--output-dir", "$OutRoot\matched_cell_class"
)

# Coarser super_class analysis should be robust and easier to interpret.
Run-Step "04_matched_super_class_deep" @(
    "tools\context_reachability_audit.py",
    "--connectivity", "2023_03_23_connectivity_630_final.parquet",
    "--annotations", "flywire_annotations.tsv",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "matched_size",
    "--group-by", "super_class",
    "--max-steps", "6",
    "--gamma", "0.80",
    "--n-null", "100",
    "--min-group-size", "10",
    "--output-dir", "$OutRoot\matched_super_class"
)

# Fine cell_type pass. This may take longer; still useful if it finishes.
Run-Step "05_matched_cell_type_deep" @(
    "tools\context_reachability_audit.py",
    "--connectivity", "2023_03_23_connectivity_630_final.parquet",
    "--annotations", "flywire_annotations.tsv",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "matched_size",
    "--group-by", "cell_type",
    "--max-steps", "6",
    "--gamma", "0.80",
    "--n-null", "100",
    "--min-group-size", "20",
    "--output-dir", "$OutRoot\matched_cell_type"
)

# Complete contexts can be heavier. This is last so earlier data survive if time runs out.
Run-Step "06_complete_cell_class_deep" @(
    "tools\context_reachability_audit.py",
    "--connectivity", "2023_03_23_connectivity_630_final.parquet",
    "--annotations", "flywire_annotations.tsv",
    "--contexts", "metadata\source_contexts\source_context_manifest.csv",
    "--context-mode", "complete",
    "--group-by", "cell_class",
    "--max-steps", "6",
    "--gamma", "0.80",
    "--n-null", "100",
    "--min-group-size", "10",
    "--output-dir", "$OutRoot\complete_cell_class"
)

$End = Get-Date
$Elapsed = New-TimeSpan -Start $Start -End $End
"Finished overnight context audit: $End`nElapsed: $Elapsed" | Out-File (Join-Path $OutRoot "RUN_STATUS.txt") -Append
Write-Host "DONE. Results are in $OutRoot"
