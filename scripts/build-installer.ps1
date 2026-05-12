Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

python -m pip install --upgrade build pyinstaller
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m build --wheel
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m PyInstaller installer/CanvasAgentSetup.spec --noconfirm
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Installer written to $Root\dist\CanvasAgentSetup.exe"
