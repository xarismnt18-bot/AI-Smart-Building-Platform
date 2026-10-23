"""
Resets the ESP8266 over USB and records what it prints for a while.

    python tools/serial_log.py [seconds]     # default 40

Writes serial_log.txt next to the project. Run it through serial_log.bat.
Close the Arduino serial monitor first: only one program can open the port.
"""
import glob
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flash  # noqa: E402  (reuses its port finder)

ROOT = flash.ROOT
OUT = os.path.join(ROOT, "serial_log.txt")


def load_pyserial():
    try:
        import serial  # noqa: F401
    except ImportError:
        base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Arduino15", "packages", "esp8266", "hardware", "esp8266")
        for path in sorted(glob.glob(os.path.join(base, "*", "tools", "pyserial")), reverse=True):
            sys.path.insert(0, path)
            break
    import serial
    return serial


def main() -> int:
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 40
    flash.LOG = os.path.join(ROOT, "serial_ports.log")
    open(flash.LOG, "w", encoding="utf-8").close()
    port = flash.find_usb_port()
    with open(OUT, "w", encoding="utf-8") as out:
        if not port:
            out.write("No ESP8266 found on USB.\n")
            print("No ESP8266 found on USB.")
            return 1
        serial = load_pyserial()
        ser = serial.Serial(port, 115200, timeout=0.2)
        ser.dtr = False          # NodeMCU: pulse RTS -> EN low = reset, normal boot
        ser.rts = True
        time.sleep(0.15)
        ser.rts = False
        out.write(f"--- {port}, reset, recording {seconds:.0f} s ---\n")
        end = time.time() + seconds
        while time.time() < end:
            line = ser.readline()
            if line:
                text = line.decode("utf-8", errors="replace").rstrip()
                out.write(text + "\n")
                out.flush()
                print(text)
        ser.close()
        out.write("--- done ---\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        with open(OUT, "a", encoding="utf-8") as f:
            f.write("CRASHED:\n" + traceback.format_exc())
        sys.exit(1)
