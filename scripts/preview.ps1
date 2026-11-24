$ErrorActionPreference = 'Stop'
$padtvRoot = Split-Path -Parent $PSScriptRoot
$padtvPython = Join-Path $padtvRoot '.venv\Scripts\python.exe'
Push-Location -LiteralPath $padtvRoot
try {
    if (-not (Test-Path -LiteralPath $padtvPython)) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Nepodařilo se vytvořit Python prostředí.' }
        & $padtvPython -m pip install -r requirements-dev.txt
        if ($LASTEXITCODE -ne 0) { throw 'Nepodařilo se nainstalovat PyQt6.' }
    }
    & $padtvPython -m padtv --preview --windowed
    if ($LASTEXITCODE -ne 0) { throw 'Náhled PadTV skončil chybou.' }
} finally {
    Pop-Location
}
