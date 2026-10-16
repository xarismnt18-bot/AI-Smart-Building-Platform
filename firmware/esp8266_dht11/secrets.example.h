// Copy to secrets.h and fill in. secrets.h is ignored by git.
#pragma once

#define WIFI_SSID     "your-wifi-name"
#define WIFI_PASSWORD "your-wifi-password"

// IP of the PC running Mosquitto (not the ESP8266). Check with `ipconfig`.
#define MQTT_SERVER   "192.168.1.23"
#define MQTT_PORT     1883
#define MQTT_TOPIC    "smartroom/dht11"

// Broker login (setup_security.bat generates these and appends them to secrets.h)
#define MQTT_USER     "esp8266"
#define MQTT_PASS     "change-me"
