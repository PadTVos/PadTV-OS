param([string]$Folder = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$releaseFolder = (Resolve-Path -LiteralPath $Folder).Path
$releaseInfo = Get-Content -LiteralPath (Join-Path $releaseFolder 'release-parts.json') -Raw | ConvertFrom-Json
if ($releaseInfo.name -notmatch '^padtv-[0-9.]+-amd64\.iso$' -or $releaseInfo.sha256 -notmatch '^[a-f0-9]{64}$') {
    throw 'Invalid release metadata.'
}
$outputPath = Join-Path $releaseFolder $releaseInfo.name
if (Test-Path -LiteralPath $outputPath) {
    if ((Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant() -eq $releaseInfo.sha256) {
        Write-Output "Verified ISO already exists: $outputPath"
        exit 0
    }
    throw 'A different output file already exists. It was preserved.'
}
if ($releaseInfo.parts.Count -lt 1 -or $releaseInfo.parts.Count -gt 16) { throw 'Invalid part count.' }
foreach ($part in $releaseInfo.parts) {
    if ($part.name -notmatch '^padtv-[0-9.]+-amd64\.iso\.part[0-9]+$' -or $part.sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Invalid part metadata.' }
    $partPath = Join-Path $releaseFolder $part.name
    if ((Get-Item -LiteralPath $partPath).Length -ne $part.bytes -or (Get-FileHash -LiteralPath $partPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $part.sha256) {
        throw "Part is incomplete or changed: $($part.name)"
    }
}
$temporaryPath = Join-Path $releaseFolder ([Guid]::NewGuid().ToString() + '.assembling')
try {
    $outputStream = [System.IO.File]::Open($temporaryPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
    try {
        foreach ($part in $releaseInfo.parts) {
            $inputStream = [System.IO.File]::OpenRead((Join-Path $releaseFolder $part.name))
            try { $inputStream.CopyTo($outputStream) } finally { $inputStream.Dispose() }
        }
    } finally { $outputStream.Dispose() }
    if ((Get-Item -LiteralPath $temporaryPath).Length -ne $releaseInfo.bytes -or (Get-FileHash -LiteralPath $temporaryPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $releaseInfo.sha256) {
        throw 'Final ISO hash mismatch.'
    }
    Move-Item -LiteralPath $temporaryPath -Destination $outputPath
    Write-Output "ISO assembled and SHA-256 verified: $outputPath"
} finally {
    if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath }
}
