<#
.SYNOPSIS
  One-click GATP demo launcher (Windows -> WSL). Cleans old processes, starts
  fixtures + runner + API + web UI, waits until they are healthy, opens the browser.

.EXAMPLE
  .\scripts\demo-up.ps1            # real Gemini model
  .\scripts\demo-up.ps1 -Fake      # offline fake provider (labelled as fake in the UI)
  .\scripts\demo-up.ps1 -Site v2   # serve the modified site (Phase 2 rescan)
#>
param(
    [switch]$Fake,
    [ValidateSet('v1', 'v2')][string]$Site = 'v1',
    [string]$Repo = '~/GATP',     # the WSL clone that runs the stack
    [int]$TimeoutSec = 150
)
$ErrorActionPreference = 'Stop'

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { throw 'wsl.exe not found' }

# Run the supervisor straight from this repo's copy (no manual sync to WSL).
# `tr -d '\r'` makes it immune to Windows CRLF line endings.
$sh = (Resolve-Path (Join-Path $PSScriptRoot 'demo-up.sh')).Path -replace '\\', '/'
$wslSh = (wsl.exe wslpath -u "$sh").Trim()
if (-not $wslSh) { throw "could not translate $sh to a WSL path" }

$provider = if ($Fake) { 'fake' } else { 'gemini' }
$inner = "export GATP_REPO=$Repo GATP_LLM_PRIMARY=$provider GATP_SITE=$Site; " +
         "exec bash <(tr -d '\r' < '$wslSh')"

# 1. Fresh supervisor window: it stays open (shows logs/status) and owns the processes.
#    Closing it, or Ctrl+C in it, stops the whole stack.
Write-Host "Starting GATP in WSL (model: $provider, site: $Site)..." -ForegroundColor Cyan
$proc = Start-Process -FilePath wsl.exe -ArgumentList @('-e', 'bash', '-lc', "`"$inner`"") -PassThru

# 2. Wait for the UI *through the API proxy*, so "up" means the whole stack works.
$deadline = (Get-Date).AddSeconds($TimeoutSec)
$ok = $false
while ((Get-Date) -lt $deadline) {
    if ($proc.HasExited) { throw 'WSL supervisor exited early; read the message in its window (or data/logs/*.log in WSL).' }
    try {
        $ui  = Invoke-WebRequest 'http://localhost:5173/' -UseBasicParsing -TimeoutSec 3
        $api = Invoke-WebRequest 'http://localhost:5173/api/runner/health' -UseBasicParsing -TimeoutSec 3
        if ($ui.StatusCode -eq 200 -and $api.StatusCode -eq 200) { $ok = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
}
if (-not $ok) { throw "GATP did not become healthy within $TimeoutSec s. See the WSL window for the failing service." }

Write-Host 'GATP is up. Opening http://localhost:5173' -ForegroundColor Green
Start-Process 'http://localhost:5173'
Write-Host 'Leave the WSL window open during the demo. Ctrl+C there (or close it) stops everything.'
