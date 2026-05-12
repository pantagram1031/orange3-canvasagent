Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

python -m pip install --upgrade build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Wheel and source distribution written to $Root\dist"
