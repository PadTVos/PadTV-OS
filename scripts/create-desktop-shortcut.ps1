$ErrorActionPreference = 'Stop'
$padtvRoot = Split-Path -Parent $PSScriptRoot
$padtvPython = Join-Path $padtvRoot '.venv\Scripts\pythonw.exe'
$padtvIcon = Join-Path $padtvRoot 'assets\padtv-020.ico'
$padtvDesktop = [Environment]::GetFolderPath('Desktop')

if (-not (Test-Path -LiteralPath $padtvPython)) {
    throw 'Nejprve připravte náhled podle README.md; chybí .venv\Scripts\pythonw.exe.'
}
if (-not (Test-Path -LiteralPath $padtvIcon)) {
    throw 'Chybí ikona assets\padtv-020.ico.'
}

$padtvShell = New-Object -ComObject WScript.Shell
$padtvLink = Join-Path $padtvDesktop 'PadTV.lnk'
$padtvSuffix = 1
while (Test-Path -LiteralPath $padtvLink) {
    $padtvExisting = $padtvShell.CreateShortcut($padtvLink)
    if ($padtvExisting.TargetPath -eq $padtvPython -and $padtvExisting.WorkingDirectory -eq $padtvRoot) {
        break
    }
    # Keep any unrelated existing shortcut intact.
    $padtvSuffix++
    $padtvLink = Join-Path $padtvDesktop "PadTV ($padtvSuffix).lnk"
}

$padtvShortcut = $padtvShell.CreateShortcut($padtvLink)
$padtvShortcut.TargetPath = $padtvPython
$padtvShortcut.Arguments = '-m padtv --preview --windowed'
$padtvShortcut.WorkingDirectory = $padtvRoot
$padtvShortcut.IconLocation = "$padtvIcon,0"
$padtvShortcut.Description = 'PadTV – náhled televizního rozhraní pro Windows'
$padtvShortcut.WindowStyle = 1
$padtvShortcut.Save()
Write-Output "Vytvořen zástupce: $padtvLink"
