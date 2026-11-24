param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9-]{0,38}$')][string]$Organization,
      [switch]$Publish)
$ErrorActionPreference = 'Stop'
$padtvRoot = Split-Path -Parent $PSScriptRoot
$padtvPlan = Get-Content -LiteralPath (Join-Path $padtvRoot 'github/repositories.json') -Raw | ConvertFrom-Json
foreach ($repo in $padtvPlan.repositories) {
    Write-Output ("PUBLIC {0}/{1}: {2}" -f $Organization, $repo.name, $repo.description)
}
if (-not $Publish) { Write-Output 'Plan only. Use -Publish after reviewing repositories/.'; exit 0 }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI is required; authenticate with gh auth login.' }
& gh auth status
if ($LASTEXITCODE -ne 0) { throw 'GitHub authentication failed.' }
& gh api "orgs/$Organization" --jq '.login'
if ($LASTEXITCODE -ne 0) { throw 'Create the organization in GitHub first.' }
$padtvLogin = & gh api user --jq '.login'
$padtvRole = & gh api "orgs/$Organization/memberships/$padtvLogin" --jq '.role'
if ($LASTEXITCODE -ne 0 -or $padtvRole -ne 'admin') { throw 'Verified organization ownership is required.' }
foreach ($repo in $padtvPlan.repositories) {
    $padtvPath = Join-Path $padtvRoot "repositories/$($repo.name)"
    if (-not (Test-Path -LiteralPath (Join-Path $padtvPath '.padtv-export.json'))) { throw "Missing export: $padtvPath" }
    $padtvExisting = & gh repo view "$Organization/$($repo.name)" --json name 2>$null
    if ($LASTEXITCODE -eq 0) { throw "Repository already exists; preserved: $Organization/$($repo.name)" }
    $padtvExport = Get-Content -LiteralPath (Join-Path $padtvPath '.padtv-export.json') -Raw | ConvertFrom-Json
    foreach ($entry in $padtvExport.files.PSObject.Properties) {
        $padtvFile = Join-Path $padtvPath $entry.Name
        if (-not (Test-Path -LiteralPath $padtvFile -PathType Leaf)) { throw "Missing exported file: $padtvFile" }
        $padtvInfo = Get-Item -LiteralPath $padtvFile
        if ($padtvInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Symlink in export: $padtvFile" }
        if ((Get-FileHash -LiteralPath $padtvFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
            throw "Export changed; review and regenerate it before publishing: $padtvFile"
        }
    }
    foreach ($file in Get-ChildItem -LiteralPath $padtvPath -Recurse -File -Force) {
        $padtvRelative = $file.FullName.Substring($padtvPath.Length + 1).Replace('\','/')
        if ($padtvRelative.StartsWith('.git/') -or $padtvRelative -eq '.padtv-export.json') { continue }
        # Unit tests create bytecode; .gitignore excludes it from publication.
        if ($padtvRelative -match '(^|/)__pycache__/[^/]+\.pyc$') { continue }
        if ($null -eq $padtvExport.files.PSObject.Properties[$padtvRelative]) { throw "Unreviewed extra file: $padtvRelative" }
    }
    # The generated export is reviewed as a whole before creating its first commit.
    & git -C $padtvPath add --all
    if ($LASTEXITCODE -ne 0) { throw 'Git add failed.' }
    & git -C $padtvPath diff --cached --quiet
    if ($LASTEXITCODE -eq 1) {
        & git -C $padtvPath commit -m 'Prepare PadTV 0.3 System Core'
        if ($LASTEXITCODE -ne 0) { throw 'Configure your Git author identity before publishing.' }
    }
}
foreach ($repo in $padtvPlan.repositories) {
    $padtvPath = Join-Path $padtvRoot "repositories/$($repo.name)"
    & gh repo create "$Organization/$($repo.name)" --public --description $repo.description --source $padtvPath --remote origin --push
    if ($LASTEXITCODE -ne 0) { throw "Publishing stopped at $($repo.name); no forced overwrite was attempted." }
}
