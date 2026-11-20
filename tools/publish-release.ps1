param(
    [Parameter(Mandatory=$true)][string]$Version,
    [ValidateSet("test", "stable", "development")][string]$Channel = "test",
    [Parameter(Mandatory=$true)][string]$PrivateKey,
    [Parameter(Mandatory=$true)][string]$BaseUrl,
    [string[]]$Notes = @()
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$appSource = Join-Path $root "src\app"
$releaseDir = Join-Path $root ("releases\" + $Version)
$channelDir = Join-Path $root $Channel
$channelPackages = Join-Path $channelDir "packages"
$packageName = "FPV-Uhyliant-v$Version-Test-UA-Windows.zip"
$releasePackage = Join-Path $releaseDir $packageName
$channelPackage = Join-Path $channelPackages $packageName
$manifestPath = Join-Path $channelDir "release.json"

if (-not (Test-Path $PrivateKey -PathType Leaf)) { throw "Private key not found: $PrivateKey" }
if (-not (Test-Path (Join-Path $appSource "main.py") -PathType Leaf)) { throw "Missing src\app\main.py" }

New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
New-Item -ItemType Directory -Path $channelPackages -Force | Out-Null
Remove-Item $releasePackage -Force -ErrorAction SilentlyContinue
Remove-Item $channelPackage -Force -ErrorAction SilentlyContinue
Remove-Item $manifestPath -Force -ErrorAction SilentlyContinue

Compress-Archive -Path (Join-Path $appSource "*") -DestinationPath $releasePackage -CompressionLevel Optimal
Copy-Item $releasePackage $channelPackage -Force
$hash = (Get-FileHash $releasePackage -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $packageName" | Set-Content (Join-Path $releaseDir "SHA256SUMS.txt") -Encoding ASCII

$manifest = [ordered]@{
    product = "FPV-Uhyliant"
    channel = $Channel
    version = $Version
    build = 2001
    mandatory = $false
    minimumUpdaterVersion = "2.0.0"
    package = [ordered]@{
        file = $packageName
        url = "$BaseUrl/$Channel/packages/$packageName"
        sha256 = $hash
    }
    releaseNotes = $Notes
}

$manifestJson = $manifest | ConvertTo-Json -Depth 8
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($manifestPath, $manifestJson, $utf8NoBom)

& py -3 (Join-Path $root "src\release-tools\sign_release.py") $manifestPath --key $PrivateKey
if ($LASTEXITCODE -ne 0) { throw "Manifest signing failed. Exit code: $LASTEXITCODE" }

$signed = Get-Content $manifestPath -Raw | ConvertFrom-Json
if ($signed.signature.algorithm -ne "Ed25519") { throw "Missing Ed25519 signature" }
if ($signed.signature.keyId -ne "fpv-uhyliant-production-v1") { throw "Unexpected keyId" }
Copy-Item $manifestPath (Join-Path $releaseDir "release.json") -Force

Write-Host "Release $Version prepared and signed for channel $Channel"
Write-Host "Package: $releasePackage"
Write-Host "Channel package: $channelPackage"
Write-Host "Manifest: $manifestPath"
Write-Host "Package SHA-256: $hash"