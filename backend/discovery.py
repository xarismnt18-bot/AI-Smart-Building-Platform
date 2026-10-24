"""
Broker discovery beacon.

Every few seconds the backend broadcasts a small UDP packet on the LAN:

    THALPOS-BROKER v2 port=1883 ip=192.168.1.23 sig=<64 hex>

The ESP8266 listens for it and connects to that address, so the sensor keeps
working when this PC gets a new IP (another Wi-Fi network, a DHCP change).

`sig` is an HMAC-SHA256 of everything before " sig=", keyed with DISCOVERY_KEY
(shared with the firmware through secrets.h, see tools/discovery_key.py). The
board checks the signature and that `ip` is the packet's sender, so another
device on the network can neither forge a beacon nor replay ours from its own
address. Without a key the backend sends the old unsigned v1 beacon, which
current firmware ignores. Outbound broadcast only: no firewall rule is needed.
"""
import hashlib
import hmac
import logging
import socket
import threading

logger = logging.getLogger(__name__)

BEACON_PREFIX = "THALPOS-BROKER v1"
SIGNED_PREFIX = "THALPOS-BROKER v2"
LEGACY_PREFIX = "AIOS-BROKER v1"  # boards flashed before the rename still listen for this


def beacon_payload(mqtt_port: int) -> bytes:
    """Unsigned v1 beacon, for firmware older than the signed discovery."""
    return f"{BEACON_PREFIX} port={mqtt_port}".encode("ascii")


def signed_payload(mqtt_port: int, ip: str, key: str) -> bytes:
    body = f"{SIGNED_PREFIX} port={mqtt_port} ip={ip}"
    sig = hmac.new(bytes.fromhex(key), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body} sig={sig}".encode("ascii")


def verify(payload: bytes, key: str, sender_ip: str) -> bool:
    """What the firmware does, in Python (used by the tests)."""
    text = payload.decode("ascii", errors="replace")
    body, sep, sig = text.partition(" sig=")
    if not sep or not body.startswith(SIGNED_PREFIX):
        return False
    expected = hmac.new(bytes.fromhex(key), body.encode("ascii"), hashlib.sha256).hexdigest()
    fields = dict(part.split("=", 1) for part in body.split()[2:] if "=" in part)
    return hmac.compare_digest(sig, expected) and fields.get("ip") == sender_ip


def local_ip() -> str | None:
    """The LAN address this PC uses for its default route (no packet is sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        return None if ip.startswith("127.") or ip == "0.0.0.0" else ip
    except OSError:
        return None


class BrokerBeacon:
    def __init__(self, mqtt_port: int, discovery_port: int, interval_sec: float, key: str | None = None):
        self._port = mqtt_port
        self._key = key
        self._target = ("255.255.255.255", discovery_port)
        self._interval = interval_sec
        self._stop = threading.Event()
        self._thread = None

    def payloads(self, ip: str | None) -> list[bytes]:
        if self._key:
            return [signed_payload(self._port, ip, self._key)] if ip else []
        return [beacon_payload(self._port), f"{LEGACY_PREFIX} port={self._port}".encode("ascii")]

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="broker-beacon", daemon=True)
        self._thread.start()
        logger.info("Broker discovery beacon on UDP %s (%s)", self._target[1],
                    "signed" if self._key else "UNSIGNED: run tools/discovery_key.py")

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        sock, bound_ip, warned = None, None, False
        try:
            while not self._stop.is_set():
                try:
                    ip = local_ip()
                    if sock is None or ip != bound_ip:
                        if sock:
                            sock.close()
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                        if ip:   # send from the address we sign, so the board's check matches
                            sock.bind((ip, 0))
                        bound_ip = ip
                    for payload in self.payloads(ip):
                        sock.sendto(payload, self._target)
                    warned = False
                except OSError as e:  # no network yet (e.g. Wi-Fi still connecting)
                    if not warned:
                        logger.warning("Discovery beacon not sent: %s", e)
                        warned = True
                    if sock:
                        sock.close()
                    sock = None
                self._stop.wait(self._interval)
        finally:
            if sock:
                sock.close()
