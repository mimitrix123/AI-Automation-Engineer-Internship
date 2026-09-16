// ESP32 smart-home telemetry node.
// Install PubSubClient + WiFiClientSecure and provision a CA certificate before production use.
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

const int PIR_PIN = 27;
const int LIGHT_PIN = 34;
const int SOUND_PIN = 35;
const char* MQTT_TOPIC = "home/living-room/telemetry";

WiFiClientSecure secureClient;
PubSubClient mqtt(secureClient);

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  // Configure Wi-Fi, TLS CA, MQTT credentials, and broker here.
}

void loop() {
  // Replace placeholders with your temperature sensor driver and calibrated ADC conversion.
  int motion = digitalRead(PIR_PIN);
  int light = analogRead(LIGHT_PIN);
  int sound = analogRead(SOUND_PIN);
  char payload[160];
  snprintf(payload, sizeof(payload), "{\"motion\":%d,\"light\":%d,\"sound\":%d}", motion, light, sound);
  if (mqtt.connected()) mqtt.publish(MQTT_TOPIC, payload);
  delay(5000);
}
