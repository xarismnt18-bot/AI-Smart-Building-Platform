from backend.discovery import BrokerBeacon, signed_payload, verify

KEY = "ab" * 32


def test_signed_beacon_verifies_from_its_own_address():
    payload = signed_payload(1883, "192.168.1.23", KEY)
    assert payload.startswith(b"THALPOS-BROKER v2 port=1883 ip=192.168.1.23 sig=")
    assert verify(payload, KEY, "192.168.1.23")


def test_replay_from_another_address_is_rejected():
    payload = signed_payload(1883, "192.168.1.23", KEY)
    assert not verify(payload, KEY, "192.168.1.66")


def test_forged_or_wrong_key_is_rejected():
    forged = b"THALPOS-BROKER v2 port=1883 ip=192.168.1.66 sig=" + b"0" * 64
    assert not verify(forged, KEY, "192.168.1.66")
    assert not verify(signed_payload(1883, "192.168.1.66", "cd" * 32), KEY, "192.168.1.66")


def test_tampered_port_is_rejected():
    payload = signed_payload(1883, "192.168.1.23", KEY).replace(b"port=1883", b"port=1884")
    assert not verify(payload, KEY, "192.168.1.23")


def test_with_a_key_only_signed_beacons_are_sent():
    beacon = BrokerBeacon(1883, 18831, 3, key=KEY)
    assert [p[:17] for p in beacon.payloads("10.0.0.5")] == [b"THALPOS-BROKER v2"]
    assert beacon.payloads(None) == []          # no LAN address: nothing to sign


def test_without_a_key_the_old_beacons_are_sent():
    assert BrokerBeacon(1883, 18831, 3).payloads("10.0.0.5")[0] == b"THALPOS-BROKER v1 port=1883"
