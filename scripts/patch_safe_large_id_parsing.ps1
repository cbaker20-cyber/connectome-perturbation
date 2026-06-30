<#
patch_safe_large_id_parsing.ps1

Emergency local patch for a critical ID parsing bug.

Problem:
  FlyWire root IDs are 18-digit integers, larger than what Python float can
  represent exactly. Code patterns like int(float(tok)) silently corrupt the
  last digits of IDs and make otherwise valid source-context IDs fail to overlap
  connectivity node IDs.

Fix:
  Replace int(float(tok)) / int(float(t)) with direct integer parsing.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\patch_safe_large_id_parsing.ps1
#>

$ErrorActionPreference = "Stop"

$Files = @(
    "tools\create_source_contexts.py",
    "tools\structural_surrogate_benchmark.py",
    "tools\id_space_audit.py",
    "tools\context_reachability_audit.py",
    "tools\run_context_perturbation_sweep.py",
    "perturbation\novel_architecture_analysis.py"
)

foreach ($Path in $Files) {
    if (-Not (Test-Path $Path)) {
        Write-Host "Skipping missing file: $Path"
        continue
    }

    $Text = Get-Content $Path -Raw
    $NewText = $Text.Replace("int(float(tok))", "int(tok)")
    $NewText = $NewText.Replace("int(float(t))", "int(t)")

    if ($NewText -eq $Text) {
        Write-Host "No unsafe large-ID parser pattern found: $Path"
        continue
    }

    Copy-Item $Path "$Path.large_id_parse.bak" -Force
    Set-Content -Path $Path -Value $NewText -NoNewline
    Write-Host "Patched unsafe large-ID parsing: $Path"
}

Write-Host "Done. Regenerate source contexts and rerun ID-space audit."
