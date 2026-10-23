"""
Teaches the ESP8266 the Wi-Fi network this laptop is on right now, then
uploads the firmware over USB. The network name and password are read from
Windows (netsh) and written to secrets.h (git-ignored); the password is never
printed or logged. Run it through add_wifi.bat (asks for admin, which Windows
needs to reveal a saved Wi-Fi password).
"""
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, "firmware", "esp8266_dht11", "secrets.h")
LOG = os.path.join(ROOT, "add_wifi.log")
NS = "{http://www.microsoft.com/networking/WLAN/profile/v1}"


def log(text):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


def netsh(*args):
    out = subprocess.run(["netsh", "wlan", *args], capture_output=True)
    return out.stdout.decode("oem", errors="replace")


def current_ssid():
    for line in netsh("show", "interfaces").splitlines():
        m = re.match(r"\s*SSID\s*:\s*(.+?)\s*$", line)
        if m:
            return m.group(1)
    return None


def saved_password(ssid):
    with tempfile.TemporaryDirectory() as folder:
        netsh("export", "profile", f"name={ssid}", "key=clear", f"folder={folder}")
        for name in os.listdir(folder):
            root = ET.parse(os.path.join(folder, name)).getroot()
            if (root.findtext(f"{NS}SSIDConfig/{NS}SSID/{NS}name") or root.findtext(f"{NS}name")) != ssid:
                continue
            key = root.find(f".//{NS}keyMaterial")
            auth = root.findtext(f".//{NS}authentication") or ""
            if key is not None and key.text:
                return key.text
            if auth.lower() == "open":
                return ""
    return None


def c_string(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    open(LOG, "w", encoding="utf-8").close()
    ssid = current_ssid()
    if not ssid:
        log("The laptop is not connected to Wi-Fi.")
        return 1
    log(f"Laptop Wi-Fi: {ssid}")
    with open(SECRETS, encoding="utf-8") as f:
        text = f.read()
    known = re.findall(r'#define\s+WIFI_SSID(?:_\d)?\s+"((?:[^"\\]|\\.)*)"', text)
    if ssid in [k.replace('\\"', '"').replace("\\\\", "\\") for k in known]:
        log("The ESP already knows this network. Uploading anyway.")
    else:
        password = saved_password(ssid)
        if password is None:
            log("Windows did not reveal the password (run add_wifi.bat and answer Yes to the admin prompt).")
            return 1
        used = set(re.findall(r"#define\s+WIFI_SSID_(\d)\s", text))
        slot = next((n for n in "34" if n not in used), "4")
        if slot in used:  # both extra slots taken: replace slot 4
            text = re.sub(r"#define\s+WIFI_(SSID|PASSWORD)_4\s+.*\n?", "", text)
        text = text.rstrip("\n") + f"\n#define WIFI_SSID_{slot}     {c_string(ssid)}\n#define WIFI_PASSWORD_{slot} {c_string(password)}\n"
        with open(SECRETS, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"Saved as WIFI_SSID_{slot} in secrets.h.")
    log("Uploading over USB (see flash_esp.log) ...")
    code = subprocess.call([sys.executable, os.path.join(ROOT, "tools", "flash.py"), "usb"])
    log("DONE: the ESP now knows this network." if code == 0 else "Upload failed, see flash_esp.log.")
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"CRASHED: {type(e).__name__}: {e}")
        sys.exit(1)
