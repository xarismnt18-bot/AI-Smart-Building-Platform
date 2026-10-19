"""
Connects AIOS to an IKEA smart plug through the DIRIGERA hub (local API).
Finds the hub on the network, asks you to press its action button, picks the
plug, flashes it once and writes ikea.env (git-ignored). Safe to run again.
Run it through setup_ikea.bat.
"""
import base64
import hashlib
import json
import os
import secrets
import socket
import ssl
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT, "ikea.env")
TLS = ssl.create_default_context()
TLS.check_hostname = False
TLS.verify_mode = ssl.CERT_NONE  # the hub uses a self-signed certificate on the LAN


def call(ip, method, path, token=None, body=None, form=None):
    headers = {}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(f"https://{ip}:8443/v1{path}", data=data, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=10, context=TLS) as response:
        raw = response.read()
    return json.loads(raw) if raw else None


def local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def port_open(ip):
    try:
        with socket.create_connection((ip, 8443), timeout=0.6):
            return ip
    except OSError:
        return None


def challenge(ip, verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    params = urllib.parse.urlencode({
        "audience": "homesmart.local", "response_type": "code",
        "code_challenge": base64.urlsafe_b64encode(digest).rstrip(b"=").decode(),
        "code_challenge_method": "S256",
    })
    return call(ip, "GET", f"/oauth/authorize?{params}")["code"]


def find_hub(verifier):
    prefix = local_ip().rsplit(".", 1)[0]
    print(f"Looking for the IKEA hub on {prefix}.x ...")
    with ThreadPoolExecutor(64) as pool:
        candidates = [ip for ip in pool.map(port_open, (f"{prefix}.{i}" for i in range(1, 255))) if ip]
    for ip in candidates:
        try:
            return ip, challenge(ip, verifier)
        except Exception:
            continue
    return None, None


def done(message, ok=True):
    print(message)
    if ok:
        time.sleep(5)
    else:
        input("Press Enter to close")
    sys.exit(0 if ok else 1)


class Tee:
    """Shows output in the window and keeps a copy in setup_ikea.log."""
    def __init__(self, stream, path):
        self.stream, self.file = stream, open(path, "w", encoding="utf-8")

    def write(self, text):
        self.stream.write(text)
        self.file.write(text)
        self.file.flush()

    def flush(self):
        self.stream.flush()


def main():
    sys.stdout = Tee(sys.stdout, os.path.join(ROOT, "setup_ikea.log"))
    print("\n=== AIOS alert lamp (IKEA DIRIGERA hub) ===")
    print("The plug must already work in the IKEA Home smart app.\n")
    verifier = secrets.token_urlsafe(96)[:128]
    ip, code = find_hub(verifier)
    if not ip:
        ip = input("Hub not found automatically. Type its IP address (IKEA app > Hub settings): ").strip()
        try:
            code = challenge(ip, verifier)
        except Exception as e:
            done(f"Could not talk to a hub at {ip}: {e}", ok=False)
    print(f"Found the hub at {ip}.\n")
    print("Press the ACTION button on the bottom of the hub (one short press).")
    print("Waiting up to 3 minutes ...")
    token, deadline, issued = None, time.time() + 180, time.time()
    while not token and time.time() < deadline:
        try:
            token = call(ip, "POST", "/oauth/token", form={
                "code": code, "name": socket.gethostname(),
                "grant_type": "authorization_code", "code_verifier": verifier,
            })["access_token"]
        except Exception:
            time.sleep(2)
            if time.time() - issued > 50:  # codes expire; ask for a fresh one
                code, issued = challenge(ip, verifier), time.time()
    if not token:
        done("The button was not pressed in time. Run setup_ikea.bat again.", ok=False)
    print("Access granted.\n")

    outlets = [d for d in call(ip, "GET", "/devices", token) if d.get("deviceType") == "outlet"]
    if not outlets:
        done("No smart plugs on this hub. Add the plug in the IKEA Home smart app first.", ok=False)
    for i, d in enumerate(outlets, 1):
        print(f"  {i}. {d['attributes'].get('customName') or d['id']}")
    named = [d for d in outlets if any(w in (d["attributes"].get("customName") or "").lower()
                                       for w in ("lamp", "light", "λάμπα", "φως", "πορτατίφ"))]
    if len(outlets) == 1 or len(named) == 1:
        outlet = (named or outlets)[0]
    else:
        outlet = outlets[int(input("Which plug is the lamp? (number) ")) - 1]
    name = outlet["attributes"].get("customName") or outlet["id"]

    with open(ENV_FILE, "w", encoding="ascii") as f:
        f.write("# IKEA hub for the AIOS alert lamp, written by setup_ikea.bat. Never commit this file.\n")
        f.write(f"IKEA_HUB_IP={ip}\nIKEA_TOKEN={token}\nIKEA_OUTLET_ID={outlet['id']}\n")

    was_on = bool(outlet["attributes"].get("isOn"))
    print(f"Using '{name}'. Flashing it once ...")
    path = f"/devices/{outlet['id']}"
    call(ip, "PATCH", path, token, [{"attributes": {"isOn": not was_on}}])
    time.sleep(2)
    call(ip, "PATCH", path, token, [{"attributes": {"isOn": was_on}}])
    done("Saved. Restarting AIOS turns the alert lamp on.")


if __name__ == "__main__":
    main()
