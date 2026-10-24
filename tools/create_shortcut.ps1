# Puts a "Thalpos" icon on the desktop that starts broker, backend and dashboard
# (Run_Thalpos.bat) and opens the dashboard. Removes the older dashboard links.
$root = Split-Path -Parent $PSScriptRoot
$desktops = @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:USERPROFILE 'Desktop')) | Select-Object -Unique

foreach ($d in $desktops) {
  foreach ($old in 'AIOS Dashboard.url', 'Thalpos.url') {
    $p = Join-Path $d $old
    if (Test-Path $p) { Remove-Item $p -Force }
  }
}

$link = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Thalpos.lnk'
$shell = New-Object -ComObject WScript.Shell
$s = $shell.CreateShortcut($link)
$s.TargetPath = Join-Path $root 'Run_Thalpos.bat'
$s.WorkingDirectory = $root
$s.IconLocation = (Join-Path $root 'tools\thalpos.ico') + ',0'
$s.Description = 'Start Thalpos: broker, backend and dashboard'
$s.Save()
Write-Host "Desktop icon ready: $link"
