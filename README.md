# Smart Door AI

A smart door lock system with cloud-based facial recognition using ESP32, AWS IoT Core, S3, and Rekognition.

## Architecture

```mermaid
flowchart LR
    Camera --> OpenCV["OpenCV\nFace Detection"]
    OpenCV --> S3["AWS S3\nUpload"]
    S3 --> Rekognition["AWS Rekognition\nFace Compare"]
    Rekognition --> MQTT["AWS IoT Core\nMQTT"]
    MQTT --> ESP32["ESP32\nRelay Control"]
    ESP32 --> Door["Door Lock"]
```

**Flow:**
1. Camera captures video feed
2. OpenCV detects faces in real-time
3. Captured face is uploaded to S3
4. AWS Rekognition compares against authorized faces in the bucket
5. If match found (>70% similarity), MQTT "OPEN" command is sent
6. ESP32 receives command and activates relay to unlock door
7. Door auto-locks after 3 seconds

## Hardware Requirements

| Component | Description |
|-----------|-------------|
| ESP32 | Microcontroller with WiFi |
| Relay Module | 5V relay for door lock control |
| Webcam | USB camera for face capture |
| Door Lock | Electric door strike or solenoid |

**Wiring:**
- Relay signal → ESP32 GPIO 13
- LED indicator → ESP32 GPIO 2

## Software Requirements

**Python (Client):**
```
boto3
opencv-python
paho-mqtt
```

**Arduino (ESP32):**
- WiFi
- WiFiClientSecure
- PubSubClient

## Project Structure

```
IoT-Project/
├── client/
│   ├── smart_door_ai.py      # Main AI facial recognition client
│   ├── final_door_cam.py     # AWS IoT SDK version
│   ├── door_windows.py       # Windows/Paho version
│   ├── camera_controller.py  # Manual unlock client
│   ├── unlock.py             # Remote unlock script
│   └── config.py             # Configuration (gitignored)
├── firmware/
│   └── esp32_door_lock/
│       ├── esp32_door_lock.ino
│       └── secrets.h         # WiFi/AWS creds (gitignored)
├── certs/                    # AWS IoT certificates (gitignored)
├── faces/                    # Authorized user faces
└── README.md
```

## Setup

### 1. AWS IoT Core

1. Create a Thing in AWS IoT Core
2. Download the certificates:
   - `*-certificate.pem.crt`
   - `*-private.pem.key`
   - `AmazonRootCA1.pem`
3. Create an S3 bucket for face images
4. Enable AWS Rekognition in your region

### 2. Certificates

Place certificates in `certs/` directory:
```
certs/
├── *-certificate.pem.crt
├── *-private.pem.key
└── AmazonRootCA1.pem
```

### 3. Configuration

Create `client/config.py`:
```python
AWS_ACCESS_KEY = "your-access-key"
AWS_SECRET_KEY = "your-secret-key"
REGION = "us-east-1"
ENDPOINT = "your-iot-endpoint.iot.region.amazonaws.com"
PORT = 8883
TOPIC = "iot/course/project/door"
CLIENT_ID = "SmartDoor_AI"
BUCKET_NAME = "your-s3-bucket"

BASE_DIR = "/path/to/IoT-Project"
CERTS_DIR = BASE_DIR + "/certs"
PATH_TO_CERT = CERTS_DIR + "/your-certificate.pem.crt"
PATH_TO_KEY = CERTS_DIR + "/your-private.pem.key"
PATH_TO_ROOT = CERTS_DIR + "/AmazonRootCA1.pem"
```

### 4. ESP32 Firmware

1. Create `firmware/esp32_door_lock/secrets.h`:
```cpp
#define WIFI_SSID "your-wifi"
#define WIFI_PASSWORD "your-password"
#define AWS_IOT_ENDPOINT "your-iot-endpoint.iot.region.amazonaws.com"
#define CLIENT_ID "ESP32_Door"
#define MQTT_TOPIC "iot/course/project/door"

const char AWS_CERT_CA[] = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----";
const char AWS_CERT_CRT[] = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----";
const char AWS_CERT_PRIVATE[] = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----";
```

2. Flash to ESP32 using Arduino IDE

### 5. Python Environment

```bash
pip install boto3 opencv-python paho-mqtt
```

## Usage

Run the main facial recognition client:
```bash
cd client
python smart_door_ai.py
```

- Camera window opens with "SCANNING..." status
- When a face is detected, it checks against S3 bucket
- **ACCESS GRANTED** (green) = door unlocks
- **UNKNOWN USER** (red) = access denied
- Press `q` to quit

## Adding Authorized Users

Upload face images to your S3 bucket:
```bash
aws s3 cp faces/user.jpg s3://your-bucket-name/
```

Requirements for face images:
- Clear, front-facing photo
- Good lighting
- JPEG format recommended

