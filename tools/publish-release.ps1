param(
  [Parameter(Mandatory=$true)][string]$Version,
  [ValidateSet("test","stable","development")][string]$Channel = "test",
  [Parameter(Mandatory=$true)][string]$PrivateKey,
  [string]$BaseUrl = "https://uhilyant-gg.github.io/fpv-uhyliant-updates",
  [string[]]$Notes = @()
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "src"
$releaseDir = Join-Path $root ("releases\" + $Version)
$packageName = "FPV-Uhyliant-v$Version-win64.zip"
$package = Join-Path $releaseDir $packageName
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
if (Test-Path $package) { Remove-Item $package -Force }
Compress-Archive -Path (Join-Path $source "*") -DestinationPath $package -CompressionLevel Optimal
$hash = (Get-FileHash $package -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $packageName" | Set-Content (Join-Path $releaseDir "SHA256SUMS.txt") -Encoding ascii
$manifest = [ordered]@{
  product = "FPV-Uhyliant"
  channel = $Channel
  version = $Version
  build = [int](($Version -replace '\D','').PadRight(4,'0').Substring(0,4))
  mandatory = $false
  minimumUpdaterVersion = "2.0.0"
  package = [ordered]@{
    file = $packageName
    url = "$BaseUrl/releases/$Version/$packageName"
    sha256 = $hash
  }
  releaseNotes = $Notes
}
$channelDir = Join-Path $root $Channel
New-Item -ItemType Directory -Path $channelDir -Force | Out-Null
$manifestPath = Join-Path $channelDir "release.json"
$manifest | ConvertTo-Json -Depth 8 | Set-Content $manifestPath -Encoding utf8
python (Join-Path $root "src\release-tools\sign_release.py") $manifestPath --key $PrivateKey
Copy-Item $manifestPath (Join-Path $releaseDir "release.json") -Force
Write-Host "Release $Version prepared and signed for channel $Channel"
Write-Host "Package SHA-256: $hash"
Write-Host "Review, then commit and tag manually."
