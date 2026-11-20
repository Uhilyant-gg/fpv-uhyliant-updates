param(
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [Parameter(Mandatory=$true)][string]$PrivateKey,
  [string]$KeyId = "fpv-uhyliant-test-2026"
)
$ErrorActionPreference = "Stop"
python tools\build_release.py --channel test --version 1.5.1 --build 1510 --package test\packages\fpv-uhyliant-1.5.1-win64.zip --base-url $BaseUrl --notes "Signed repository release"
python tools\sign_release.py test\release.unsigned.json --key $PrivateKey --key-id $KeyId
Copy-Item test\release.unsigned.json test\release.json -Force
python tools\verify_repository.py --channel test
Write-Host "Repository files are ready. Commit and push, then enable GitHub Pages for the publishing source."
