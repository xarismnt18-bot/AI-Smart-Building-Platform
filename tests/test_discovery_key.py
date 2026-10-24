import re

from tools.discovery_key import ensure


def keys(h, env):
    a = re.search(r'#define DISCOVERY_KEY "(\w+)"', h.read_text())
    b = re.search(r"DISCOVERY_KEY=(\w+)", env.read_text())
    return a and a.group(1), b and b.group(1)


def test_creates_one_key_in_both_files(tmp_path):
    h, env = tmp_path / "secrets.h", tmp_path / "creds.env"
    h.write_text('#define WIFI_SSID "x"\n')
    env.write_text("MQTT_USERNAME=backend\n")
    assert ensure(str(h), str(env)) == "created"
    a, b = keys(h, env)
    assert a == b and len(a) == 64
    assert "MQTT_USERNAME=backend" in env.read_text() and "WIFI_SSID" in h.read_text()
    assert ensure(str(h), str(env)) == "ok"


def test_syncs_from_secrets_h(tmp_path):
    h, env = tmp_path / "secrets.h", tmp_path / "creds.env"
    h.write_text('#define DISCOVERY_KEY "' + "1f" * 32 + '"\n')
    env.write_text("DISCOVERY_KEY=" + "aa" * 32 + "\n")
    assert ensure(str(h), str(env)) == "synced"
    assert keys(h, env) == ("1f" * 32, "1f" * 32)
