"""
Compiles the ESP8266 firmware and uploads it, over USB or over Wi-Fi (OTA).

    python tools/flash.py usb          # finds the board's COM port by itself
    python tools/flash.py ota [host]   # default host: thalpos-bedroom.local
    python tools/flash.py compile      # only checks that the sketch builds

Uses the arduino-cli bundled with Arduino IDE. Writes flash_esp.log next to
the project. Run it through flash_esp.bat / flash_ota.bat.
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKETCH = os.path.join(ROOT, "firmware", "esp8266_dht11")
BUILD = os.path.join(ROOT, "firmware", "build")
LOG = os.path.join(ROOT, "flash_esp.log")
FQBN = "esp8266:esp8266:nodemcuv2"
CLI = r"C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"
OTA_HOST_PORT = "48266"  # the board connects back here; allow_ota.bat opens it in the firewall
# Arduino libraries the sketch needs (installed once, then skipped).
LIBRARIES = ["PubSubClient", "DHT sensor library", "Adafruit Unified Sensor", "Adafruit GFX Library", "Adafruit SSD1306"]
USB_SERIAL_VIDS = {"0x1A86", "0x10C4", "0x0403"}  # CH340, CP210x, FTDI


def log(text: str) -> None:
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    enc = sys.stdout.encoding or "utf-8"
    print(text.encode(enc, errors="replace").decode(enc))


def run(args: list[str], secret: str | None = None) -> int:
    """Exit code of the command; also non-zero when esptool reports a fatal error
    (arduino-cli sometimes exits 0 anyway)."""
    log("> " + " ".join("***" if secret and a == secret else a for a in args))
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if secret:
        out = out.replace(secret, "***")
    if out:
        log(out[-4000:])
    code = proc.returncode or (1 if "fatal esptool.py error" in out.lower() else 0)
    log(f"exit code: {code}")
    return code


def install_libraries() -> None:
    out = subprocess.run([CLI, "lib", "list", "--format", "json"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    missing = [lib for lib in LIBRARIES if f'"{lib}"' not in out]
    if missing:
        run([CLI, "lib", "install", *missing])


def compile_sketch() -> bool:
    install_libraries()
    return run([CLI, "compile", "--fqbn", FQBN, "--output-dir", BUILD, SKETCH]) == 0


def find_usb_port() -> str | None:
    out = subprocess.run([CLI, "board", "list", "--format", "json"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    try:
        data = json.loads(out or "[]")
    except ValueError:
        return None
    ports = data.get("detected_ports", []) if isinstance(data, dict) else data
    candidates = []
    for entry in ports:
        port = entry.get("port", {})
        if port.get("protocol") != "serial":
            continue
        vid = (port.get("properties") or {}).get("vid", "").upper().replace("0X", "0x")
        candidates.append((vid in USB_SERIAL_VIDS, port.get("address")))
    candidates.sort(reverse=True)
    for label, address in candidates:
        log(f"serial port: {address} ({'USB-serial chip' if label else 'other'})")
    usb = [address for is_usb, address in candidates if is_usb]
    return usb[0] if usb else None  # Bluetooth/modem COM ports are never the board


def ota_password() -> str | None:
    with open(os.path.join(SKETCH, "secrets.h"), encoding="utf-8") as f:
        match = re.search(r'#define\s+OTA_PASSWORD\s+"([^"]+)"', f.read())
    return match.group(1) if match else None


def espota() -> str | None:
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Arduino15", "packages", "esp8266", "hardware", "esp8266")
    found = sorted(glob.glob(os.path.join(base, "*", "tools", "espota.py")))
    return found[-1] if found else None


def main() -> int:
    open(LOG, "w", encoding="utf-8").close()
    mode = sys.argv[1] if len(sys.argv) > 1 else "usb"
    if not os.path.exists(CLI):
        log(f"arduino-cli not found at {CLI}")
        return 1
    try:  # the board must know the key the backend signs its beacon with
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from discovery_key import ensure
        if ensure() != "ok":
            log("Discovery key written to secrets.h and mqtt_credentials.env: restart Thalpos so the backend uses it.")
    except FileNotFoundError as e:
        log(str(e))
        return 1
    if not compile_sketch():
        log("COMPILE FAILED: nothing was uploaded.")
        return 1

    if mode == "compile":
        log("COMPILE OK (nothing uploaded)")
        return 0
    if mode == "usb":
        port = find_usb_port()
        if not port:
            log("No ESP8266 found on USB. Plug it in with a data cable (not a charge-only one) and close the Arduino serial monitor.")
            return 1
        code = run([CLI, "upload", "-p", port, "--fqbn", FQBN, "--input-dir", BUILD, SKETCH])
    else:
        host = sys.argv[2] if len(sys.argv) > 2 else "thalpos-bedroom.local"
        password, tool = ota_password(), espota()
        if not password or not tool:
            log("OTA needs OTA_PASSWORD in secrets.h and the ESP8266 core's espota.py.")
            return 1
        binary = os.path.join(BUILD, "esp8266_dht11.ino.bin")
        code = run([sys.executable, tool, "-i", host, "-p", "8266", "-P", OTA_HOST_PORT, "-a", password, "-f", binary], secret=password)
    log("UPLOAD OK" if code == 0 else "UPLOAD FAILED")
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        log("CRASHED:\n" + traceback.format_exc())
        sys.exit(1)
