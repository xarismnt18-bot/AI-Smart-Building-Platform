// ESP8266 room sensor node for Thalpos -> MQTT.
// Wi-Fi and broker settings live in secrets.h (not committed to git).
//
// v2: knows several Wi-Fi networks (home, phone hotspot, ...) and joins the
// strongest one it can see; firmware updates over Wi-Fi (ArduinoOTA, password
// protected) so the USB cable is only needed once.
// v3: SHT31 temperature/humidity on I2C (found automatically; falls back to the
// DHT11 on D4 when it isn't there), mmWave presence radar on D5, and a 0.96"
// OLED that shows the readings on the device.
//
// Wiring (NodeMCU):  SHT31 + OLED: SDA -> D2, SCL -> D1, VCC -> 3V3, GND -> GND
//                    radar: OT1/OUT -> D5, 3V3 -> 3V3, GND -> GND
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ArduinoOTA.h>
#include <WiFiUdp.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "secrets.h"

#define DHTPIN D4
#define DHTTYPE DHT11
#define PRESENCE_PIN D5        // mmWave radar output: HIGH while someone is in the room
const bool HAS_RADAR = true;   // set false if no radar is wired (the pin would float)

const char* ROOM_NAME = "Bedroom";
const char* FIRMWARE_VERSION = "3.0";
const char* OTA_HOSTNAME = "aios-bedroom";   // reachable as aios-bedroom.local
const unsigned long PUBLISH_INTERVAL_MS = 3000;   // the DHT11 fallback needs >= 1 s between reads
const unsigned long MQTT_RETRY_MS = 3000;

// Broker discovery: the AIOS backend broadcasts "AIOS-BROKER v1 port=1883" on
// this UDP port. The board connects to whoever sent it, so a new IP on the PC
// no longer breaks the sensor. MQTT_SERVER in secrets.h is only the first guess.
const uint16_t DISCOVERY_PORT = 18831;
const char* BEACON_PREFIX = "AIOS-BROKER v1";
WiFiUDP discovery;
IPAddress brokerIp;
uint16_t brokerPort = MQTT_PORT;
bool brokerDiscovered = false;

ESP8266WiFiMulti wifiMulti;
WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);
Adafruit_SSD1306 display(128, 64, &Wire, -1);

uint8_t shtAddress = 0;      // 0x44 or 0x45 when an SHT31 answers, 0 = use the DHT11
bool hasDisplay = false;
float lastTemp = NAN, lastHum = NAN;
bool presence = false;
bool pendingPublish = false;
unsigned long lastDisplay = 0;

String clientId;
unsigned long lastPublish = 0;
unsigned long lastMqttAttempt = 0;

// Every network from secrets.h; WiFiMulti picks the strongest one in range.
void addNetworks() {
  wifiMulti.addAP(WIFI_SSID, WIFI_PASSWORD);
#ifdef WIFI_SSID_2
  wifiMulti.addAP(WIFI_SSID_2, WIFI_PASSWORD_2);
#endif
#ifdef WIFI_SSID_3
  wifiMulti.addAP(WIFI_SSID_3, WIFI_PASSWORD_3);
#endif
#ifdef WIFI_SSID_4
  wifiMulti.addAP(WIFI_SSID_4, WIFI_PASSWORD_4);
#endif
}

bool wasConnected = false;

// Non-blocking: wifiMulti.run() waits at most a few seconds per call, so the
// loop (and OTA) keeps running while no known network is in range.
void connectToWiFi() {
  if (wifiMulti.run(5000) != WL_CONNECTED) {
    if (wasConnected) Serial.println("WiFi lost, looking for a known network...");
    wasConnected = false;
    return;
  }
  if (wasConnected) return;
  wasConnected = true;
  brokerDiscovered = false;  // a new network means the PC may have a new IP
  Serial.print("WiFi connected to ");
  Serial.print(WiFi.SSID());
  Serial.print(", ESP8266 IP: ");
  Serial.println(WiFi.localIP());
}

void setupOta() {
  ArduinoOTA.setHostname(OTA_HOSTNAME);
#ifdef OTA_PASSWORD
  ArduinoOTA.setPassword(OTA_PASSWORD);
#endif
  ArduinoOTA.onStart([]() { Serial.println("OTA update starting"); client.disconnect(); });
  ArduinoOTA.onEnd([]() { Serial.println("OTA update done, rebooting"); });
  ArduinoOTA.onError([](ota_error_t error) { Serial.printf("OTA error %u\n", error); });
  ArduinoOTA.begin();
}

// Non-blocking: one attempt every MQTT_RETRY_MS, so Wi-Fi drops are noticed too.
void ensureMqtt() {
  if (client.connected()) return;
  unsigned long now = millis();
  if (now - lastMqttAttempt < MQTT_RETRY_MS) return;
  lastMqttAttempt = now;

  Serial.print("Connecting to MQTT ");
  if (brokerDiscovered) Serial.print(brokerIp); else Serial.print(MQTT_SERVER);
  Serial.print("...");
  if (client.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
    Serial.println(" connected!");
  } else {
    Serial.print(" failed, rc=");
    Serial.println(client.state());
  }
}

// Reads one pending beacon, if any. Switches broker when the PC's IP changed.
void listenForBroker() {
  int size = discovery.parsePacket();
  if (size <= 0) return;

  char buf[64];
  int len = discovery.read(buf, sizeof(buf) - 1);
  if (len <= 0) return;
  buf[len] = '\0';
  if (strncmp(buf, BEACON_PREFIX, strlen(BEACON_PREFIX)) != 0) return;

  uint16_t port = MQTT_PORT;
  const char* p = strstr(buf, "port=");
  if (p) port = (uint16_t) atoi(p + 5);

  IPAddress from = discovery.remoteIP();
  if (brokerDiscovered && from == brokerIp && port == brokerPort) return;

  brokerIp = from;
  brokerPort = port;
  brokerDiscovered = true;
  Serial.print("Broker found at ");
  Serial.print(brokerIp);
  Serial.print(":");
  Serial.println(brokerPort);

  client.disconnect();
  client.setServer(brokerIp, brokerPort);
  lastMqttAttempt = 0;   // try the new address right away
}

// ---------- SHT31 (plain I2C, no library) ----------
bool i2cPresent(uint8_t addr) {
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

uint8_t crc8(const uint8_t* data, int len) {
  uint8_t crc = 0xFF;
  for (int i = 0; i < len; i++) {
    crc ^= data[i];
    for (int b = 0; b < 8; b++) crc = (crc & 0x80) ? (crc << 1) ^ 0x31 : (crc << 1);
  }
  return crc;
}

// Single-shot, high repeatability measurement (about 15 ms).
bool readSht31(float& temperature, float& humidity) {
  Wire.beginTransmission(shtAddress);
  Wire.write(0x24);
  Wire.write(0x00);
  if (Wire.endTransmission() != 0) return false;
  delay(20);
  if (Wire.requestFrom(shtAddress, (uint8_t) 6) != 6) return false;
  uint8_t d[6];
  for (int i = 0; i < 6; i++) d[i] = Wire.read();
  if (crc8(d, 2) != d[2] || crc8(d + 3, 2) != d[5]) return false;
  temperature = -45.0f + 175.0f * ((d[0] << 8) | d[1]) / 65535.0f;
  humidity = 100.0f * ((d[3] << 8) | d[4]) / 65535.0f;
  return true;
}

bool readClimate(float& temperature, float& humidity) {
  if (shtAddress) return readSht31(temperature, humidity);
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  return !isnan(humidity) && !isnan(temperature);
}

const char* sensorName() { return shtAddress ? "SHT31" : "DHT11"; }

// ---------- OLED ----------
void drawDisplay() {
  if (!hasDisplay) return;
  display.clearDisplay();
  // move the whole picture by a pixel every few minutes so the OLED doesn't burn in
  int dx = (millis() / 180000) % 3, dy = (millis() / 540000) % 2;
  display.setTextColor(SSD1306_WHITE);

  display.setTextSize(1);
  display.setCursor(dx, dy);
  display.print("Thalpos  ");
  display.print(ROOM_NAME);

  display.setTextSize(3);
  display.setCursor(dx, 14 + dy);
  if (isnan(lastTemp)) display.print("--.-");
  else display.print(lastTemp, 1);
  display.setTextSize(1);
  display.print(" C");

  display.setTextSize(2);
  display.setCursor(dx, 40 + dy);
  if (isnan(lastHum)) display.print("--%");
  else { display.print((int) round(lastHum)); display.print("%"); }

  if (HAS_RADAR) {
    display.setTextSize(1);
    display.setCursor(64 + dx, 44 + dy);
    display.print(presence ? "Someone in" : "Empty");
  }

  display.setTextSize(1);
  display.setCursor(dx, 56 + dy);
  if (WiFi.status() != WL_CONNECTED) display.print("No Wi-Fi");
  else if (!client.connected()) display.print("Wi-Fi ok, no broker");
  else { display.print(WiFi.SSID().substring(0, 14)); display.print(" ok"); }
  display.display();
}

// Reads the sensor even while offline, so the OLED keeps showing live values.
bool updateReading() {
  float temperature, humidity;
  if (!readClimate(temperature, humidity)) {
    Serial.print("Failed to read ");
    Serial.println(sensorName());
    return false;
  }
  lastTemp = temperature;
  lastHum = humidity;
  return true;
}

void publishReading() {
  float temperature = lastTemp, humidity = lastHum;

  String payload = "{\"room\":\"";
  payload += ROOM_NAME;
  payload += "\",\"temperature\":";
  payload += String(temperature, 1);
  payload += ",\"humidity\":";
  payload += String(humidity, 1);
  payload += ",\"sensor\":\"";
  payload += sensorName();
  payload += "\"";
  if (HAS_RADAR) {
    payload += ",\"presence\":";
    payload += presence ? "true" : "false";
  }
  payload += ",\"ip\":\"";
  payload += WiFi.localIP().toString();
  payload += "\",\"wifi\":\"";
  payload += WiFi.SSID();
  payload += "\",\"rssi\":";
  payload += String(WiFi.RSSI());
  payload += ",\"fw\":\"";
  payload += FIRMWARE_VERSION;
  payload += "\"}";

  bool ok = client.publish(MQTT_TOPIC, payload.c_str());
  Serial.print(ok ? "Sent: " : "Publish FAILED: ");
  Serial.println(payload);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin();   // NodeMCU: SDA = D2, SCL = D1
  Serial.print("I2C devices:");
  for (uint8_t a = 1; a < 127; a++) if (i2cPresent(a)) Serial.printf(" 0x%02X", a);
  Serial.println();
  if (i2cPresent(0x44)) shtAddress = 0x44;
  else if (i2cPresent(0x45)) shtAddress = 0x45;
  if (!shtAddress) dht.begin();
  Serial.printf("Climate sensor: %s\n", sensorName());

  hasDisplay = display.begin(SSD1306_SWITCHCAPVCC, 0x3C) || display.begin(SSD1306_SWITCHCAPVCC, 0x3D);
  if (hasDisplay) {
    display.ssd1306_command(SSD1306_SETCONTRAST);
    display.ssd1306_command(40);   // dimmer: easier on the eyes at night, slower burn-in
    drawDisplay();
  }
  Serial.println(hasDisplay ? "OLED found" : "No OLED");

  if (HAS_RADAR) pinMode(PRESENCE_PIN, INPUT);

  WiFi.mode(WIFI_STA);
  WiFi.hostname(OTA_HOSTNAME);
  addNetworks();
  connectToWiFi();
  setupOta();

  // Unique per board, so two nodes never kick each other off the broker.
  clientId = "ESP8266_THALPOS_" + String(ESP.getChipId(), HEX);
  client.setServer(MQTT_SERVER, MQTT_PORT);
  discovery.begin(DISCOVERY_PORT);
}

void loop() {
  connectToWiFi();   // returns immediately while connected
  ArduinoOTA.handle();

  if (HAS_RADAR) {
    bool now = digitalRead(PRESENCE_PIN) == HIGH;
    if (now != presence) {
      presence = now;
      Serial.println(presence ? "Presence: someone in the room" : "Presence: room empty");
      lastPublish = millis() - PUBLISH_INTERVAL_MS;   // read and report straight away
    }
  }
  if (millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = millis();
    if (updateReading()) pendingPublish = true;
  }
  if (millis() - lastDisplay >= 1000) {
    lastDisplay = millis();
    drawDisplay();
  }

  if (WiFi.status() != WL_CONNECTED) return;
  listenForBroker();
  ensureMqtt();
  client.loop();

  if (pendingPublish && client.connected()) {
    pendingPublish = false;
    publishReading();
  }
}
