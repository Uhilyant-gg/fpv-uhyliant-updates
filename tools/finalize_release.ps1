param(
  [Parameter(Mandatory=$true)][ValidateSet("test","stable","development")][string]$Channel,
  [Parameter(Mandatory=$true)][string]$Version,
  [Parameter(Mandatory=$true)][int]$Build,
  [Parameter(Mandatory=$true)][string]$Package,
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [Parameter(Mandatory=$true)][string]$PrivateKey,
  [Parameter(Mandatory=$true)][string]$KeyId,
  [string[]]$Notes = @()
)
$ErrorActionPreference = "Stop"
python tools\build_release.py --channel $Channel --version $Version --build $Build --package $Package --base-url $BaseUrl --notes $Notes
$unsigned = "$Channel\release.unsigned.json"
Copy-Item $unsigned "$Channel\release.json" -Force
python tools\sign_release.py "$Channel\release.json" --key $PrivateKey --key-id $KeyId
python tools\verify_repository.py --channel $Channel
Write-Host "Signed $Channel/release.json is ready for commit/push."
