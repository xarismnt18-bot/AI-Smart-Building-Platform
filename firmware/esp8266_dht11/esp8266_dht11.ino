// ESP8266 + DHT11 -> MQTT sensor node for Smart Building AI OS.
// Wi-Fi and broker settings live in secrets.h (not committed to git).
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <PubSubClient.h>
#include <DHT.h>
#include "secrets.h"

#define DHTPIN D4
#define DHTTYPE DHT11

const char* ROOM_NAME = "Bedroom";
const unsigned long PUBLISH_INTERVAL_MS = 3000;   // DHT11 needs >= 1 s between reads
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

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

String clientId;
unsigned long lastPublish = 0;
unsigned long lastMqttAttempt = 0;

void connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Connecting to WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi connected, ESP8266 IP: ");
  Serial.println(WiFi.localIP());
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

void publishReading() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read DHT11");
    return;
  }

  String payload = "{\"room\":\"";
  payload += ROOM_NAME;
  payload += "\",\"temperature\":";
  payload += String(temperature, 1);
  payload += ",\"humidity\":";
  payload += String(humidity, 1);
  payload += "}";

  bool ok = client.publish(MQTT_TOPIC, payload.c_str());
  Serial.print(ok ? "Sent: " : "Publish FAILED: ");
  Serial.println(payload);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  dht.begin();
  connectToWiFi();

  // Unique per board, so two nodes never kick each other off the broker.
  clientId = "ESP8266_DHT11_" + String(ESP.getChipId(), HEX);
  client.setServer(MQTT_SERVER, MQTT_PORT);
  discovery.begin(DISCOVERY_PORT);
}

void loop() {
  connectToWiFi();   // returns immediately while connected
  listenForBroker();
  ensureMqtt();
  client.loop();

  if (client.connected() && millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = millis();
    publishReading();
  }
}
