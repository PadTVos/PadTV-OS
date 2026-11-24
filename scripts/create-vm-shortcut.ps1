$ErrorActionPreference = 'Stop'
$padtvRoot = Split-Path -Parent $PSScriptRoot
$padtvPython = Join-Path $padtvRoot '.venv\Scripts\python.exe'
$padtvPythonWindowed = Join-Path $padtvRoot '.venv\Scripts\pythonw.exe'
$padtvLauncher = Join-Path $PSScriptRoot 'run-vm.py'
$padtvIcon = Join-Path $padtvRoot 'assets\padtv-020.ico'
foreach ($padtvRequired in @($padtvPython, $padtvPythonWindowed, $padtvLauncher, $padtvIcon)) {
    if (-not (Test-Path -LiteralPath $padtvRequired)) { throw "Chybí soubor: $padtvRequired" }
}
& $padtvPython $padtvLauncher --prepare
if ($LASTEXITCODE -ne 0) { throw 'Virtuální stroj se nepodařilo připravit.' }
$padtvShell = New-Object -ComObject WScript.Shell
$padtvDesktop = [Environment]::GetFolderPath('Desktop')
$padtvLink = Join-Path $padtvDesktop 'PadTV 0.6 Native Compatibility - virtuální PC.lnk'
$padtvSuffix = 1
while (Test-Path -LiteralPath $padtvLink) {
    $padtvExisting = $padtvShell.CreateShortcut($padtvLink)
    if ($padtvExisting.TargetPath -eq $padtvPythonWindowed -and $padtvExisting.Arguments -eq ('"' + $padtvLauncher + '"')) { break }
    $padtvSuffix++
    $padtvLink = Join-Path $padtvDesktop "PadTV 0.6 Native Compatibility - virtuální PC ($padtvSuffix).lnk"
}
$padtvShortcut = $padtvShell.CreateShortcut($padtvLink)
$padtvShortcut.TargetPath = $padtvPythonWindowed
$padtvShortcut.Arguments = '"' + $padtvLauncher + '"'
$padtvShortcut.WorkingDirectory = $padtvRoot
$padtvShortcut.IconLocation = "$padtvIcon,0"
$padtvShortcut.Description = 'Celý PadTV 0.6 Native Compatibility / Debian 13 ve virtuálním počítači QEMU'
$padtvShortcut.WindowStyle = 1
$padtvShortcut.Save()
Write-Output "Zástupce vytvořen: $padtvLink"

