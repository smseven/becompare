$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force build | Out-Null
nasm -f win64 src\bc.asm -o build\bc.obj
if ($LASTEXITCODE) { exit $LASTEXITCODE }
gcc build\bc.obj -o bc.exe
if ($LASTEXITCODE) { exit $LASTEXITCODE }
Write-Host 'built bc.exe'
