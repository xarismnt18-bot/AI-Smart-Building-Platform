# Opens the Thalpos dashboard to your own devices through Tailscale (no router changes).
# Needs Tailscale installed and signed in on this PC and on your phone. Safe to run again.
$ErrorActionPreference = 'Stop'
Write-Host ''
Write-Host '=== Thalpos remote access (Tailscale) ===' -ForegroundColor Cyan

$ts = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
if (-not (Test-Path $ts)) {
  Write-Host 'Tailscale is not installed. Get it from https://tailscale.com/download/windows,' -ForegroundColor Red
  Write-Host 'sign in, then run this again.'
  Read-Host 'Press Enter to close'; exit 1
}

$status = & $ts status --json | ConvertFrom-Json
if ($status.BackendState -ne 'Running') {
  Write-Host 'Tailscale is installed but not signed in. Click the Tailscale icon in the' -ForegroundColor Red
  Write-Host 'taskbar, log in, then run this again.'
  Read-Host 'Press Enter to close'; exit 1
}

Write-Host 'Publishing the dashboard (port 5173) to your tailnet...'
Write-Host '(If Tailscale prints a link to enable HTTPS / Serve, open it, click Enable, and run this again.)'
& $ts serve --bg 5173
if ($LASTEXITCODE -ne 0) {
  Write-Host 'Tailscale Serve did not start. Read the message above.' -ForegroundColor Red
  Read-Host 'Press Enter to close'; exit 1
}

$name = $status.Self.DNSName.TrimEnd('.')
$url = "https://$name/"
Set-Clipboard -Value $url
Write-Host ''
Write-Host "Done. Your dashboard from anywhere: $url" -ForegroundColor Green
Write-Host '(copied to the clipboard) Open it on your phone with Tailscale switched on.'
Write-Host 'Only devices signed in to your Tailscale account can open it.'
Write-Host 'To turn it off: tailscale serve reset'
Read-Host 'Press Enter to close'
