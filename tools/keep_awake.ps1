# Lets Thalpos keep running with the lid closed: only when plugged in, the laptop
# never sleeps or hibernates, closing the lid does nothing and the screen turns
# off after 2 minutes. Battery settings are not touched. Writes keep_awake.log.
$log = Join-Path (Split-Path -Parent $PSScriptRoot) 'keep_awake.log'
"==== $(Get-Date) ====" | Out-File $log
$steps = @(
  @('/setacvalueindex', 'SCHEME_CURRENT', 'SUB_BUTTONS', 'LIDACTION', '0'),  # lid closed: do nothing
  @('/change', 'standby-timeout-ac', '0'),                                   # never sleep
  @('/change', 'hibernate-timeout-ac', '0'),                                 # never hibernate
  @('/change', 'monitor-timeout-ac', '2'),                                   # screen off after 2 min
  @('/setactive', 'SCHEME_CURRENT')
)
foreach ($s in $steps) {
  & powercfg @s 2>&1 | Out-File $log -Append
  "powercfg $($s -join ' ') -> exit $LASTEXITCODE" | Out-File $log -Append
}
'--- lid action (AC) ---' | Out-File $log -Append
& powercfg /query SCHEME_CURRENT SUB_BUTTONS LIDACTION 2>&1 | Select-String 'AC Power Setting' | Out-File $log -Append
'--- sleep (AC) ---' | Out-File $log -Append
& powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 2>&1 | Select-String 'AC Power Setting' | Out-File $log -Append
Write-Host 'Done. Plugged in, the laptop now stays awake with the lid closed.' -ForegroundColor Green
Start-Sleep -Seconds 3
