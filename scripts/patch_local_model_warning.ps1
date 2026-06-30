<#
patch_local_model_warning.ps1

Patch local model.py copies to stop Brian2 namespace-warning spam from the
silence() loop. This does not change the biological perturbation definition:
it still sets outgoing synaptic weights from lesioned Brian-index neurons to 0.

Run from repo root:
    powershell -ExecutionPolicy Bypass -File scripts\patch_local_model_warning.ps1
#>

$ErrorActionPreference = "Stop"

$Targets = @(
    "model.py",
    "Drosophila_brain_model\model.py"
)

foreach ($Path in $Targets) {
    if (-Not (Test-Path $Path)) {
        Write-Host "Skipping missing file: $Path"
        continue
    }

    $Text = Get-Content $Path -Raw
    $Original = @'
    for i in slnc:
        syn.w[' {} == i'.format(i)] = 0*mV
'@
    $Patched = @'
    for brian_idx in slnc:
        # Use Brian2's internal synapse index variable `i` explicitly in the
        # string expression. Avoid a Python local variable named `i`, which
        # causes repeated Brian2 namespace-resolution warnings.
        syn.w['i == {}'.format(brian_idx)] = 0*mV
'@

    if ($Text.Contains($Patched)) {
        Write-Host "Already patched: $Path"
        continue
    }

    if (-Not $Text.Contains($Original)) {
        Write-Host "Pattern not found, leaving unchanged: $Path"
        continue
    }

    Copy-Item $Path "$Path.bak" -Force
    $Text = $Text.Replace($Original, $Patched)
    Set-Content -Path $Path -Value $Text -NoNewline
    Write-Host "Patched: $Path  backup: $Path.bak"
}

Write-Host "Done. Rerun the fast pilot or long sweep. Existing parquet files will be skipped unless force overwrite is enabled."
