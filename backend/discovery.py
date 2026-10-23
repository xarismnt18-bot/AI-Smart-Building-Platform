"""
Broker discovery beacon.

Every few seconds the backend broadcasts a small UDP packet on the LAN:

    THALPOS-BROKER v1 port=1883

The ESP8266 listens for it and connects to the sender's IP address, so the
sensor keeps working when this PC gets a new IP (another Wi-Fi network, a
DHCP change). Outbound broadcast only: no firewall rule is needed on the PC.
"""
import logging
import socket
import threading

logger = logging.getLogger(__name__)

BEACON_PREFIX = "THALPOS-BROKER v1"
LEGACY_PREFIX = "AIOS-BROKER v1"  # boards flashed before the rename still listen for this


def beacon_payload(mqtt_port: int) -> bytes:
    return f"{BEACON_PREFIX} port={mqtt_port}".encode("ascii")


class BrokerBeacon:
    def __init__(self, mqtt_port: int, discovery_port: int, interval_sec: float):
        self._payloads = [beacon_payload(mqtt_port), f"{LEGACY_PREFIX} port={mqtt_port}".encode("ascii")]
        self._target = ("255.255.255.255", discovery_port)
        self._interval = interval_sec
        self._stop = threading.Event()
        self._thread = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="broker-beacon", daemon=True)
        self._thread.start()
        logger.info("Broker discovery beacon on UDP %s", self._target[1])

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        warned = False
        try:
            while not self._stop.is_set():
                try:
                    for payload in self._payloads:
                        sock.sendto(payload, self._target)
                    warned = False
                except OSError as e:  # no network yet (e.g. Wi-Fi still connecting)
                    if not warned:
                        logger.warning("Discovery beacon not sent: %s", e)
                        warned = True
                self._stop.wait(self._interval)
        finally:
            sock.close()
