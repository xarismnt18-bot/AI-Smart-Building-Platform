from fastapi.testclient import TestClient

from backend.api import app

client = TestClient(app)  # no context manager: background threads and MQTT stay off


def test_root_and_config():
    assert client.get("/").json()["message"].startswith("Smart Building")
    t = client.get("/config").json()["thresholds"]
    assert t["HUMIDITY_LOW"] < t["HUMIDITY_HIGH"]


def test_invalid_thresholds_are_rejected():
    r = client.put("/config", json={"TEMP_LOW": 40})
    assert r.status_code == 422


def test_lamp_without_setup():
    assert client.get("/lamp").json()["enabled"] in (True, False)
    if not client.get("/lamp").json()["enabled"]:
        assert client.post("/lamp?on=true").status_code == 503


def test_history_endpoints():
    assert isinstance(client.get("/history/range?hours=1&step=300").json(), list)
    r = client.get("/history.csv?hours=1")
    assert r.status_code == 200 and r.text.startswith("time,room,temperature_c,humidity_pct")
    assert "attachment" in r.headers["content-disposition"]
