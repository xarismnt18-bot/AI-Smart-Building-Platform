import pytest

from ai.mqtt_client import InvalidPacket, SharedMQTTClient, parse_payload


def test_old_firmware_payload_still_works():
    r = parse_payload('{"room":"Bedroom","temperature":24.2,"humidity":55}')
    assert r == {"room": "Bedroom", "temperature": 24.2, "humidity": 55.0}


def test_v3_fields_are_kept():
    r = parse_payload('{"room":"Bedroom","temperature":23.46,"humidity":51.2,"sensor":"SHT31",'
                      '"presence":true,"ip":"192.168.1.20","wifi":"Home","rssi":-61,"fw":"3.0"}')
    assert r["presence"] is True and r["sensor"] == "SHT31" and r["rssi"] == -61 and r["temperature"] == 23.5


def test_bad_optional_fields_are_ignored():
    r = parse_payload('{"temperature":20,"humidity":50,"presence":"yes","rssi":"strong"}')
    assert "presence" not in r and "rssi" not in r


def test_latest_reports_presence_and_sensor():
    c = SharedMQTTClient(stale_after_sec=60)
    assert c.latest["presence"] is None
    c.ingest('{"temperature":20,"humidity":50,"sensor":"SHT31","presence":false,"fw":"3.0"}')
    latest = c.latest
    assert latest["presence"] is False and latest["sensor"] == "SHT31" and latest["device"] == {"fw": "3.0"}


def test_invalid_still_rejected():
    with pytest.raises(InvalidPacket):
        parse_payload('{"temperature":200,"humidity":50}')
