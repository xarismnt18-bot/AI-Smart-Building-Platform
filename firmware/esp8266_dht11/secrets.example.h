// Copy to secrets.h and fill in. secrets.h is ignored by git.
#pragma once

#define WIFI_SSID     "your-wifi-name"
#define WIFI_PASSWORD "your-wifi-password"

// Optional extra networks (e.g. phone hotspot, work). Up to 4 in total; the
// board joins the strongest one in range. Names are case-sensitive.
// #define WIFI_SSID_2     "my-phone-hotspot"
// #define WIFI_PASSWORD_2 "your-hotspot-password"
// #define WIFI_SSID_3     "work-wifi"
// #define WIFI_PASSWORD_3 "your-work-password"

// Password for firmware updates over Wi-Fi (flash_ota.bat). Keep it secret.
#define OTA_PASSWORD  "change-me-to-a-long-random-password"

// IP of the PC running Mosquitto (not the ESP8266). Only a first guess:
// the board also finds the PC automatically from the backend's discovery beacon.
#define MQTT_SERVER   "192.168.1.23"
#define MQTT_PORT     1883
#define MQTT_TOPIC    "smartroom/dht11"

// Broker login (setup_security.bat generates these and appends them to secrets.h)
#define MQTT_USER     "esp8266"
#define MQTT_PASS     "change-me"
