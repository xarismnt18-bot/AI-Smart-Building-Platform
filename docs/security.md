# Security

[← Back to the README](../README.md)

- **MQTT login.** `setup_security.bat` (once, asks for admin) creates random passwords for the backend and the board, turns off anonymous access in Mosquitto and writes the logins to git-ignored files (`mqtt_credentials.env`, `firmware/esp8266_dht11/secrets.h`). It also marks the home Wi-Fi as *Private* and limits the Mosquitto firewall rule to private networks, so the broker isn't exposed on public Wi-Fi.
- **The API is local-only.** It has no login, so it listens on `127.0.0.1` and accepts browser calls only from the local dashboard (`CORS_ORIGINS`). Remote access goes through Tailscale, which only your own devices can reach.
- **No secrets in git.** `.env`, `mqtt_credentials.env`, `telegram.env`, `voice.env`, `ikea.env`, `secrets.h`, model files and the runtime files in `data/` (history, settings, preferences) are ignored. `tools/check_secrets.py` runs as a pre-commit hook (`tools/pre-commit`) and blocks commits that stage credentials or keys.
- **Model files.** `.pkl` files can run code when loaded, so they are not versioned: retrain locally instead of loading pickles from elsewhere.
- **Firmware updates over Wi-Fi** need `OTA_PASSWORD` from `secrets.h`.

Known limits:

- **Discovery beacon.** The beacon is signed with a key shared by the backend and the board (`DISCOVERY_KEY`, created by `setup_security.bat` or `tools/discovery_key.py`, kept in `mqtt_credentials.env` and `secrets.h`). The board ignores beacons with a wrong signature or sent from a different address than the one they name, so another device on the Wi-Fi cannot redirect it to a fake broker. To turn discovery off completely, add `#define DISCOVERY_ENABLED 0` to `secrets.h`, reflash, and set a fixed `MQTT_SERVER`.
- **MQTT on the LAN is not encrypted**, because the ESP8266 is too small for comfortable TLS. The password login still stops other devices from reading or injecting data.
