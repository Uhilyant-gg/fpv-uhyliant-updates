param(
    [string]$Model = "qwen3.5:9b-q4_K_M",
    [switch]$InstallHarness
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command not found: $Name"
    }
    Write-Host "[OK] $Name -> $($command.Source)"
}

function Require-File {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required canonical file not found: $Path"
    }
    Write-Host "[OK] $Path"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

Write-Host "FPV Uhyliant DeepSeek Harness free-machine bootstrap"
Write-Host "Repository: $repoRoot"
Write-Host "Local model: $Model"

@("node", "npm.cmd", "git", "gh", "ollama") | ForEach-Object { Require-Command $_ }

@(
    "PRODUCT_UX.md",
    "PROJECT_STATE.md",
    "DEVELOPMENT_GUIDE.md",
    "HARDWARE_E2E.md",
    "DELIVERY_ROADMAP.md",
    "AUTONOMOUS_DEVELOPMENT.md"
) | ForEach-Object { Require-File (Join-Path $repoRoot $_) }

$insideWorkTree = (& git rev-parse --is-inside-work-tree 2>$null).Trim()
if ($insideWorkTree -ne "true") {
    throw "The script must run inside a Git worktree."
}

$modelLines = & ollama list 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Unable to query Ollama. Start Ollama and retry."
}
if (-not ($modelLines | Select-String -SimpleMatch $Model -Quiet)) {
    throw "Ollama model '$Model' is not installed. Run: ollama pull $Model"
}
Write-Host "[OK] Ollama model is installed: $Model"

if ($InstallHarness) {
    Write-Host "Installing the current DeepSeek Harness package through npm..."
    & npm.cmd install -g "@deepseek-ai/dsh@latest"
    if ($LASTEXITCODE -ne 0) {
        throw "DeepSeek Harness installation failed."
    }
}

$dsh = Get-Command dsh -ErrorAction SilentlyContinue
if ($dsh) {
    Write-Host "[OK] dsh -> $($dsh.Source)"
} else {
    Write-Warning "dsh is not installed. Re-run with -InstallHarness or use: npm.cmd install -g @deepseek-ai/dsh@latest"
}

Write-Host ""
Write-Host "Bootstrap validation complete."
Write-Host "Configure the local Harness provider:"
Write-Host "  Provider ID: ollama-local"
Write-Host "  Base URL:   http://<scrubbed-url-domain>/v1"
Write-Host "  Protocol:   openai-compatible"
Write-Host "  Credential: leave empty"
Write-Host "  Model:      $Model"
Write-Host ""
Write-Host "Launch from this repository with: dsh web"
Write-Host "Safety: do not expose credentials or treat AI output as hardware evidence."
