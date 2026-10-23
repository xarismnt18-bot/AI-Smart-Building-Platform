# One-off security setup for Thalpos (run elevated via setup_security.bat).
# - home Wi-Fi profile -> Private, Mosquitto firewall rule -> Private only
# - Mosquitto: password login (anonymous off); random passwords generated here
# - backend + ESP8266 credentials written to git-ignored files
# Passwords are never printed or logged.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Log = Join-Path $Root "setup_security.log"
function Log($m) { $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $m; $line | Out-File $Log -Append -Encoding utf8; Write-Host $line }
"==== setup_security $(Get-Date) ====" | Out-File $Log -Encoding utf8

$MosqDir = "C:\Program Files\mosquitto"
$Conf = Join-Path $MosqDir "mosquitto.conf"
$PwdDir = "C:\ProgramData\mosquitto"
$PwdFile = Join-Path $PwdDir "passwd"
$CredFile = Join-Path $Root "mqtt_credentials.env"
$Secrets = Join-Path $Root "firmware\esp8266_dht11\secrets.h"
$Py = Join-Path $Root "venv\Scripts\python.exe"

function New-Password { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | ForEach-Object { [char]$_ }) }

try {
    # --- 1. network profile + firewall --------------------------------------
    $wifi = Get-NetConnectionProfile | Where-Object { $_.InterfaceAlias -like "Wi-Fi*" } | Select-Object -First 1
    if ($wifi) {
        Set-NetConnectionProfile -InterfaceIndex $wifi.InterfaceIndex -NetworkCategory Private
        Log "Network '$($wifi.Name)' set to Private"
    } else { Log "WARN: no Wi-Fi profile found" }

    $rules = Get-NetFirewallRule | Where-Object { $_.DisplayName -match "mosquitto" }
    foreach ($r in $rules) { Set-NetFirewallRule -Name $r.Name -Profile Private }
    Log "Firewall: $($rules.Count) mosquitto rule(s) limited to Private networks"

    # --- 2. passwords -------------------------------------------------------
    $backendPw = New-Password
    $espPw = New-Password
    New-Item -ItemType Directory -Force -Path $PwdDir | Out-Null
    & "$MosqDir\mosquitto_passwd.exe" -b -c $PwdFile backend $backendPw
    if ($LASTEXITCODE -ne 0) { throw "mosquitto_passwd failed (backend)" }
    & "$MosqDir\mosquitto_passwd.exe" -b $PwdFile esp8266 $espPw
    if ($LASTEXITCODE -ne 0) { throw "mosquitto_passwd failed (esp8266)" }
    # only Administrators/SYSTEM may read the password file
    icacls $PwdFile /inheritance:r /grant:r "SYSTEM:F" "Administrators:F" | Out-Null
    Log "Password file created at $PwdFile (users: backend, esp8266)"
    $svcAccount = (Get-CimInstance Win32_Service -Filter "Name='mosquitto'").StartName
    Log "Mosquitto service runs as: $svcAccount"
    if ($svcAccount -and $svcAccount -notmatch 'LocalSystem') {
        icacls $PwdFile /grant "${svcAccount}:R" | Out-Null
        Log "Granted read access on the password file to $svcAccount"
    }

    # --- 3. dry run: test the new settings on a spare port first ----------
    $testConf = Join-Path $env:TEMP "mosquitto_test.conf"
    $testOut = Join-Path $env:TEMP "mosquitto_test.out"
    Set-Content -Path $testConf -Encoding ascii -Value @(
        "listener 18830 127.0.0.1",
        "allow_anonymous false",
        "password_file $PwdFile"
    )
    $p = Start-Process -FilePath "$MosqDir\mosquitto.exe" -ArgumentList "-c `"$testConf`" -v" `
        -RedirectStandardError $testOut -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 3
    $alive = -not $p.HasExited
    if ($alive) { Stop-Process -Id $p.Id -Force }
    Get-Content $testOut -ErrorAction SilentlyContinue | ForEach-Object { Log "dry-run: $_" }
    Remove-Item $testConf, $testOut -Force -ErrorAction SilentlyContinue
    if (-not $alive) { throw "Mosquitto rejected the new settings in the dry run (see dry-run lines above); real config untouched" }
    Log "Dry run OK - applying to the real broker"

    # --- 3b. apply to mosquitto.conf ----------------------------------------
    $backup = "$Conf.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Copy-Item $Conf $backup
    Log "Backed up mosquitto.conf -> $backup"
    # @() keeps this an array even when only one line remains (otherwise += concatenates strings)
    $lines = @(Get-Content $Conf | Where-Object { $_ -notmatch '^\s*(allow_anonymous|password_file)\b' })
    $lines += @("allow_anonymous false", "password_file $PwdFile")
    Set-Content -Path $Conf -Value $lines -Encoding ascii
    Log "mosquitto.conf: allow_anonymous false + password_file"

    $svc = Get-Service mosquitto
    Restart-Service mosquitto -Force
    try { $svc.WaitForStatus("Running", [TimeSpan]::FromSeconds(30)) } catch {}
    Start-Sleep -Seconds 3
    $listening = [bool](Get-NetTCPConnection -LocalPort 1883 -State Listen -ErrorAction SilentlyContinue)
    if (-not $listening) {
        Log "ERROR: Mosquitto not listening on 1883 with the new config - restoring backup"
        Copy-Item $backup $Conf -Force
        Start-Service mosquitto
        throw "Mosquitto restart failed; original config restored"
    }
    Log "Mosquitto service restarted OK"

    # --- 4. credentials for backend + ESP8266 (git-ignored) -----------------
    Set-Content -Path $CredFile -Encoding ascii -Value @(
        "# Generated by setup_security.bat - git-ignored, do not commit",
        "MQTT_USERNAME=backend",
        "MQTT_PASSWORD=$backendPw"
    )
    Log "Wrote backend credentials to mqtt_credentials.env"

    if (Test-Path $Secrets) {
        $s = @(Get-Content $Secrets | Where-Object { $_ -notmatch '#define\s+MQTT_(USER|PASS)\b' })
        $s += ""
        $s += "// Broker login, generated by setup_security.bat"
        $s += "#define MQTT_USER     ""esp8266"""
        $s += "#define MQTT_PASS     ""$espPw"""
        Set-Content -Path $Secrets -Value $s -Encoding ascii
        Log "Added ESP8266 broker login to firmware secrets.h"
    } else { Log "WARN: secrets.h not found - add MQTT_USER/MQTT_PASS manually" }

    # --- 5. verify: anonymous rejected, backend login accepted --------------
    $test = @"
import paho.mqtt.client as mqtt, sys, time
def attempt(user=None, pw=None):
    res = {}
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if user: c.username_pw_set(user, pw)
    c.on_connect = lambda cl, u, f, rc, p=None: res.setdefault('rc', rc)
    c.connect('127.0.0.1', 1883, 10); c.loop_start()
    for _ in range(30):
        if 'rc' in res: break
        time.sleep(0.1)
    c.loop_stop(); c.disconnect()
    return str(res.get('rc', 'timeout'))
print('anonymous ->', attempt())
print('backend   ->', attempt('backend', sys.argv[1]))
"@
    $tmp = Join-Path $env:TEMP "mqtt_auth_test.py"
    Set-Content -Path $tmp -Value $test -Encoding ascii
    $outFile = Join-Path $env:TEMP "mqtt_auth_test.out"
    cmd /c "`"$Py`" `"$tmp`" $backendPw > `"$outFile`" 2>&1"
    Get-Content $outFile | ForEach-Object { Log "TEST $_" }
    Remove-Item $tmp, $outFile -Force

    Log "DONE"
} catch {
    Log "FAILED: $($_.Exception.Message)"
}
