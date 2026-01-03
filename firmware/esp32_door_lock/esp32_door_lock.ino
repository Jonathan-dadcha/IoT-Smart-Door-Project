#include "WiFi.h"
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <SPI.h>          
#include <MFRC522.h>      
#include "secrets.h"      

#define SS_PIN  5  
#define RST_PIN 22 
MFRC522 mfrc522(SS_PIN, RST_PIN); 

#define LED_PIN 2
#define RELAY_PIN 13

WiFiClientSecure net = WiFiClientSecure();
PubSubClient client(net);

unsigned long doorOpenTime = 0;
bool isDoorOpen = false;

bool waitingForCard = false;       
unsigned long faceAuthTime = 0;    

void unlockDoor(String reason) {
  Serial.print(">>> UNLOCKING DOOR: ");
  Serial.println(reason);

  digitalWrite(LED_PIN, HIGH);
  digitalWrite(RELAY_PIN, HIGH); 

  isDoorOpen = true;
  doorOpenTime = millis();
  
  waitingForCard = false;
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("MQTT Message: ");
  Serial.println(message);

  if (message == "FACE_VERIFIED") {
    Serial.println("Face Verified! Waiting for Card (10 seconds window)...");
    waitingForCard = true;
    faceAuthTime = millis();
    
    digitalWrite(LED_PIN, HIGH); delay(200); digitalWrite(LED_PIN, LOW);
  }
  else if (message == "EMERGENCY_OPEN") {
    unlockDoor("Emergency Remote Open");
  }
}

void connectToAWS() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD); 
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
  
  client.setServer(AWS_IOT_ENDPOINT, 8883);
  client.setCallback(callback);

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

  SPI.begin();        
  mfrc522.PCD_Init(); 
  Serial.println("System Ready: 2-Factor Authentication Mode");

  connectToAWS();
}

void loop() {
  if (!client.connected()) connectToAWS();
  client.loop();

  if (waitingForCard) {
    if (millis() - faceAuthTime > 10000) {
      waitingForCard = false;
      Serial.println("Timeout! Face authentication expired.");
      for(int i=0; i<5; i++) { digitalWrite(LED_PIN, HIGH); delay(50); digitalWrite(LED_PIN, LOW); delay(50); }
    }
  }

  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    
    String content = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
      content.concat(String(mfrc522.uid.uidByte[i], HEX));
    }
    content.toUpperCase();
    String cleanUID = content.substring(1);
    
    Serial.print("Scanned Card UID: ");
    Serial.println(cleanUID);

    bool isKnownCard = (cleanUID == "63 B4 B0 1B" || cleanUID == "61 3A 4E 5D");

    if (isKnownCard) {
      if (waitingForCard) {
        unlockDoor("2FA Success (Face + Card)");
      } else {
        Serial.println("ACCESS DENIED: Face verification required first!");
        for(int i=0; i<3; i++){ digitalWrite(LED_PIN, HIGH); delay(100); digitalWrite(LED_PIN, LOW); delay(100); }
      }
    } else {
      Serial.println("ACCESS DENIED: Unknown Card");
    }
    
    delay(1000); 
  }

  if (isDoorOpen && (millis() - doorOpenTime > 3000)) {
    Serial.println(">>> LOCKING DOOR <<<");
    digitalWrite(LED_PIN, LOW);
    digitalWrite(RELAY_PIN, LOW);
    isDoorOpen = false;
  }
}