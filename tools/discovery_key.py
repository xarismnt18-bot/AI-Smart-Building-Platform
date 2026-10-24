"""
Makes sure the board and the backend share a discovery key.

The backend signs its "the broker is here" beacon with this key (HMAC-SHA256)
and the firmware ignores beacons without a valid signature, so another device
on the Wi-Fi cannot point the board at a fake broker.

The key lives in two git-ignored files:
  firmware/esp8266_dht11/secrets.h   #define DISCOVERY_KEY "..."
  mqtt_credentials.env               DISCOVERY_KEY=...
If one of them has it, the other is synced; if neither does, a new random key
is created. Safe to run any number of times. The key is never printed.

    python tools/discovery_key.py
"""
import os
import re
import secrets
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_H = os.path.join(ROOT, "firmware", "esp8266_dht11", "secrets.h")
ENV_FILE = os.path.join(ROOT, "mqtt_credentials.env")

H_PATTERN = re.compile(r'^\s*#define\s+DISCOVERY_KEY\s+"([0-9a-fA-F]{32,128})"', re.M)
ENV_PATTERN = re.compile(r"^\s*DISCOVERY_KEY\s*=\s*([0-9a-fA-F]{32,128})\s*$", re.M)


def _read(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _without(text: str, pattern: str) -> str:
    lines = [line for line in text.splitlines() if not re.match(pattern, line)]
    return "\n".join(lines).rstrip("\n") + "\n" if lines else ""


def ensure(secrets_h: str = SECRETS_H, env_file: str = ENV_FILE) -> str:
    """Returns what was done: 'ok', 'synced' or 'created'. Raises if secrets.h is missing."""
    header = _read(secrets_h)
    if not header:
        raise FileNotFoundError("secrets.h not found: copy secrets.example.h to secrets.h first")
    env = _read(env_file)
    in_h, in_env = H_PATTERN.search(header), ENV_PATTERN.search(env)

    if in_h and in_env and in_h.group(1).lower() == in_env.group(1).lower():
        return "ok"
    # secrets.h wins: it is what the board is (or will be) flashed with.
    key = (in_h or in_env).group(1).lower() if (in_h or in_env) else secrets.token_hex(32)
    action = "synced" if (in_h or in_env) else "created"

    header = _without(header, r"\s*#define\s+DISCOVERY_KEY\b|\s*// Discovery key")
    header += '\n// Discovery key: signs the broker beacon (tools/discovery_key.py)\n'
    header += f'#define DISCOVERY_KEY "{key}"\n'
    _write(secrets_h, header)

    env = _without(env, r"\s*DISCOVERY_KEY\s*=")
    env += f"DISCOVERY_KEY={key}\n"
    _write(env_file, env)
    return action


if __name__ == "__main__":
    try:
        result = ensure()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    print({"ok": "Discovery key already set in secrets.h and mqtt_credentials.env.",
           "synced": "Discovery key synced between secrets.h and mqtt_credentials.env.",
           "created": "New discovery key written to secrets.h and mqtt_credentials.env."}[result])
    if result != "ok":
        print("Restart Thalpos and flash the board (flash_ota.bat) so both use it.")
