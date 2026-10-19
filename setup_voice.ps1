# Connects AIOS to your Echo through Voice Monkey so alerts are spoken aloud.
# Writes voice.env (git-ignored). Safe to run again.
$ErrorActionPreference = 'Stop'
$envFile = Join-Path $PSScriptRoot 'voice.env'
$api = 'https://api-v3.voicemonkey.io'

Write-Host ''
Write-Host '=== AIOS voice alerts (Alexa) ===' -ForegroundColor Cyan
Write-Host 'Before this: sign in at voicemonkey.io, enable the Voice Monkey skill in the'
Write-Host 'Alexa app, and add your Echo as a Speaker device in the Voice Monkey console.'
Write-Host 'Your API token is on the Voice Monkey dashboard (API / Tokens).'
Write-Host ''
$token = (Read-Host 'Paste your Voice Monkey API token').Trim()
if (-not $token) { Write-Host 'No token entered.' -ForegroundColor Red; Read-Host 'Press Enter to close'; exit 1 }

try {
  $devices = (Invoke-RestMethod "$api/devices" -Headers @{ Authorization = "Bearer $token" }).data
} catch {
  Write-Host 'Voice Monkey rejected this token. Copy it again from the dashboard and retry.' -ForegroundColor Red
  Read-Host 'Press Enter to close'; exit 1
}
$speakers = @($devices | Where-Object { $_.capability -eq 'speakers' })
if ($speakers.Count -eq 0) {
  Write-Host 'No Speaker devices yet. In the Voice Monkey console add your Echo as a Speaker, then run this again.' -ForegroundColor Red
  Read-Host 'Press Enter to close'; exit 1
}

if ($speakers.Count -eq 1) {
  $device = $speakers[0]
} else {
  for ($i = 0; $i -lt $speakers.Count; $i++) { Write-Host ("  {0}. {1}" -f ($i + 1), $speakers[$i].name) }
  $pick = [int](Read-Host 'Which speaker should announce alerts? (number)')
  $device = $speakers[$pick - 1]
}
Write-Host "Using speaker: $($device.name)" -ForegroundColor Green

@(
  '# Voice Monkey (Alexa) for AIOS, written by setup_voice.bat. Never commit this file.'
  "VOICEMONKEY_TOKEN=$token"
  "VOICEMONKEY_DEVICE=$($device.id)"
) | Set-Content -Path $envFile -Encoding ascii

$body = @{ token = $token; device = $device.id; speech = 'Hello. Your smart home can talk to you now.' } | ConvertTo-Json
try {
  Invoke-RestMethod -Method Post -ContentType 'application/json' -Uri "$api/announce" -Body $body | Out-Null
  Write-Host 'Your Echo should be speaking now.' -ForegroundColor Green
} catch {
  Write-Host "Saved, but the test announcement failed: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host 'Restart AIOS (restart_aios.bat) to turn voice alerts on.'
Read-Host 'Press Enter to close'
