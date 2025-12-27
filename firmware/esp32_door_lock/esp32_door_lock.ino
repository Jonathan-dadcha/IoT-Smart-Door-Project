#include "WiFi.h"
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "secrets.h" 

WiFiClientSecure net = WiFiClientSecure();
PubSubClient client(net);

#define LED_PIN 2
#define RELAY_PIN 13

unsigned long doorOpenTime = 0;
bool isDoorOpen = false;

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("Message: ");
  Serial.println(message);

  if (message == "OPEN") {
    Serial.println(">>> UNLOCKING DOOR <<<");

    digitalWrite(LED_PIN, HIGH);
    digitalWrite(RELAY_PIN, HIGH);

    isDoorOpen = true;
    doorOpenTime = millis();
  }
}

void connectToAWS() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD); 
  Serial.println("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to Wi-Fi!");

  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  time_t now = time(nullptr);
  while (now < 8 * 3600 * 2) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("\nTime synced!");

  client.setServer(AWS_IOT_ENDPOINT, 8883);
  client.setCallback(callback);

  Serial.println("Connecting to AWS IOT...");
  while (!client.connect(CLIENT_ID)) {
    Serial.print(".");
    delay(100);
  }

  if (client.connected()) {
    client.subscribe(MQTT_TOPIC); 
    Serial.println("AWS IoT Connected!");
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);

  digitalWrite(LED_PIN, LOW);
  digitalWrite(RELAY_PIN, LOW);

  connectToAWS();
}

void loop() {
  if (!client.connected()) {
    connectToAWS();
  }
  client.loop();

  if (isDoorOpen && (millis() - doorOpenTime > 3000)) {
    Serial.println(">>> LOCKING DOOR <<<");

    digitalWrite(LED_PIN, LOW);
    digitalWrite(RELAY_PIN, LOW);

    isDoorOpen = false;
  }
}