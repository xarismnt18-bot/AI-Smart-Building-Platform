# Connects Thalpos to a Telegram bot so alerts reach your phone.
# Writes telegram.env (git-ignored). Safe to run again to change bot or chat.
$ErrorActionPreference = 'Stop'
$envFile = Join-Path (Split-Path -Parent $PSScriptRoot) 'telegram.env'

Write-Host ''
Write-Host '=== Thalpos Telegram alerts ===' -ForegroundColor Cyan
Write-Host '1. In Telegram, open @BotFather and send /newbot'
Write-Host '2. Pick a name and a username ending in "bot"'
Write-Host '3. BotFather replies with a token like 123456789:AAH...'
Write-Host ''
$token = (Read-Host 'Paste the bot token here').Trim()
if ($token -notmatch '^\d{6,}:[A-Za-z0-9_-]{30,}$') {
  Write-Host 'That does not look like a bot token. Run this again and paste the whole token.' -ForegroundColor Red
  Read-Host 'Press Enter to close'; exit 1
}

try {
  $me = Invoke-RestMethod "https://api.telegram.org/bot$token/getMe"
} catch {
  Write-Host 'Telegram rejected this token. Copy it again from BotFather and retry.' -ForegroundColor Red
  Read-Host 'Press Enter to close'; exit 1
}
$botName = $me.result.username
Write-Host ''
Write-Host "Bot found: @$botName" -ForegroundColor Green
Write-Host "4. Open https://t.me/$botName on your phone and press Start (or send any message)."
Start-Process "https://t.me/$botName"
Read-Host 'Press Enter here after you have sent it'

$chatId = $null
for ($i = 0; $i -lt 10 -and -not $chatId; $i++) {
  $updates = Invoke-RestMethod "https://api.telegram.org/bot$token/getUpdates"
  $last = $updates.result | Where-Object { $_.message } | Select-Object -Last 1
  if ($last) { $chatId = $last.message.chat.id } else { Start-Sleep -Seconds 2 }
}
if (-not $chatId) {
  Write-Host 'No message reached the bot yet. Send it a message and run this again.' -ForegroundColor Red
  Read-Host 'Press Enter to close'; exit 1
}

@(
  '# Telegram alerts for Thalpos (written by setup_telegram.bat). Never commit this file.'
  "TELEGRAM_BOT_TOKEN=$token"
  "TELEGRAM_CHAT_ID=$chatId"
) | Set-Content -Path $envFile -Encoding ascii

$body = @{ chat_id = "$chatId"; text = 'Thalpos is connected. You will get alerts here.' } | ConvertTo-Json
Invoke-RestMethod -Method Post -ContentType 'application/json; charset=utf-8' `
  -Uri "https://api.telegram.org/bot$token/sendMessage" -Body ([Text.Encoding]::UTF8.GetBytes($body)) | Out-Null

Write-Host ''
Write-Host 'Done. Check your phone for the test message.' -ForegroundColor Green
Write-Host 'Restart Thalpos (Run_Thalpos.bat, or sign out and in) to turn alerts on.'
Read-Host 'Press Enter to close'
