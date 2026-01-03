<p align="center">
  <h1 align="center">Smart Door AI</h1>
  <p align="center">
    <strong>Enterprise IoT Access Control with AI-Powered Facial Recognition & 2-Factor Authentication</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/C++-ESP32-00599C?style=for-the-badge&logo=cplusplus&logoColor=white" alt="C++">
    <img src="https://img.shields.io/badge/AWS-Rekognition-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" alt="AWS">
    <img src="https://img.shields.io/badge/AWS-IoT_Core-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" alt="IoT Core">
    <img src="https://img.shields.io/badge/Security-mTLS-00C853?style=for-the-badge&logo=letsencrypt&logoColor=white" alt="mTLS">
  </p>
</p>

---

## Executive Summary

Traditional access control systems rely on single-factor authentication (keys, cards, or codes) which are vulnerable to theft, cloning, and unauthorized sharing. **Smart Door AI** solves this with a cloud-native, AI-powered **2-Factor Authentication (2FA)** system that combines:

1. **Biometric Verification** - AWS Rekognition-powered facial recognition
2. **Physical Token** - RFID card/fob validation on the edge device

The door **only unlocks** when both factors are validated within a 10-second security window, providing enterprise-grade access control for residential and commercial applications.

---

## Hybrid Cloud Architecture

This project implements a **multi-region AWS architecture** to optimize performance and reliability:

| Layer | Region | Services | Purpose |
|-------|--------|----------|---------|
| **AI/ML** | `us-east-1` (N. Virginia) | S3, Rekognition | Stable ML inference, mature service availability |
| **IoT** | `eu-north-1` (Stockholm) | IoT Core, MQTT | Device connectivity, low-latency edge communication |

This separation resolves DNS propagation issues and leverages the strengths of each region.

```mermaid
flowchart TB
    subgraph ClientLayer [Client Layer - MacBook]
        Camera[Webcam Capture]
        OpenCV[OpenCV Face Detection]
        Python[Python Client]
    end

    subgraph AWS_US [AWS us-east-1 - AI/ML Layer]
        S3[(S3 Bucket)]
        Rekognition[AWS Rekognition]
    end

    subgraph AWS_EU [AWS eu-north-1 - IoT Layer]
        IoTCore[IoT Core MQTT Broker]
    end

    subgraph EdgeDevice [ESP32 Edge Device]
        ESP32[ESP32 Controller]
        RFID[RFID-RC522 Reader]
        Relay[5V Relay Module]
    end

    Door[Electric Door Lock]

    Camera --> OpenCV
    OpenCV -->|Face Detected| Python
    Python -->|Upload Image| S3
    S3 --> Rekognition
    Rekognition -->|Match Result| Python
    Python -->|FACE_VERIFIED via mTLS| IoTCore
    IoTCore -->|MQTT over TLS| ESP32
    ESP32 -->|10s Access Window| RFID
    RFID -->|Card Valid| ESP32
    ESP32 --> Relay
    Relay --> Door
```

---

## 2-Factor Authentication Flow

The security model enforces strict sequential authentication:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           2FA AUTHENTICATION FLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FACTOR 1: FACE RECOGNITION                                                │
│   ┌─────────┐    ┌─────────┐    ┌─────────────┐    ┌──────────────────┐    │
│   │ Camera  │───▶│ OpenCV  │───▶│ S3 Upload   │───▶│ Rekognition 85%+ │    │
│   └─────────┘    └─────────┘    └─────────────┘    └────────┬─────────┘    │
│                                                              │              │
│                                                              ▼              │
│   ┌──────────────────────────────────────────────────────────────────┐     │
│   │              MQTT: "FACE_VERIFIED" → ESP32                       │     │
│   └──────────────────────────────────────────────────────────────────┘     │
│                                                              │              │
│                                                              ▼              │
│   FACTOR 2: RFID TOKEN (10-SECOND WINDOW)                                   │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐    │
│   │ Card Tap    │───▶│ UID Check   │───▶│ 2FA Success → Relay ON      │    │
│   └─────────────┘    └─────────────┘    └─────────────────────────────┘    │
│                                                                             │
│   ⚠️  Card tap WITHOUT prior face verification = ACCESS DENIED             │
│   ⏱️  Card tap AFTER 10 seconds = TIMEOUT, face scan required again        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Hardware Stack

| Component | Model | Purpose | GPIO/Connection |
|-----------|-------|---------|-----------------|
| Microcontroller | ESP32 DevKit | WiFi + processing | - |
| RFID Reader | MFRC522 (RC522) | Card/fob authentication | SPI (SS=5, RST=22) |
| Relay Module | 5V Single-Channel | Door lock control | GPIO 13 |
| Status LED | Built-in | Visual feedback | GPIO 2 |
| Door Lock | 12V Solenoid | Physical locking | Via Relay NO/COM |
| Camera | MacBook Built-in | Face capture | USB/AVFoundation |

### Wiring Diagram

```
ESP32 GPIO Layout:
┌────────────────────────────────────────┐
│  ESP32                                 │
│                                        │
│  GPIO 5  ────────── SS   (RFID)        │
│  GPIO 22 ────────── RST  (RFID)        │
│  GPIO 18 ────────── SCK  (RFID)        │
│  GPIO 23 ────────── MOSI (RFID)        │
│  GPIO 19 ────────── MISO (RFID)        │
│  3.3V    ────────── VCC  (RFID)        │
│  GND     ────────── GND  (RFID)        │
│                                        │
│  GPIO 13 ────────── IN   (Relay)       │
│  GPIO 2  ────────── LED  (Status)      │
│  5V      ────────── VCC  (Relay)       │
│  GND     ────────── GND  (Relay)       │
└────────────────────────────────────────┘
```

---

## Software Stack

### Python Client (macOS)

| Library | Version | Purpose |
|---------|---------|---------|
| `boto3` | Latest | AWS SDK (S3, Rekognition) |
| `opencv-python` | 4.x | Face detection & camera capture |
| `AWSIoTPythonSDK` | 1.5+ | MQTT client with mTLS |
| `urllib3` | Latest | HTTP handling (SSL warnings suppressed) |

### ESP32 Firmware (Arduino)

| Library | Purpose |
|---------|---------|
| `WiFi.h` | Network connectivity |
| `WiFiClientSecure` | TLS/SSL for MQTT |
| `PubSubClient` | MQTT protocol |
| `MFRC522` | RFID reader driver |
| `SPI` | Serial peripheral interface |

---

## Installation & Setup

### 1. AWS Configuration

#### Create Resources in `us-east-1`:
```bash
# Create S3 bucket for face images
aws s3 mb s3://your-smart-door-bucket --region us-east-1

# Create Rekognition collection
aws rekognition create-collection \
    --collection-id authorized_faces \
    --region us-east-1
```

#### Create IoT Thing in `eu-north-1`:
1. Navigate to AWS IoT Core → Manage → Things
2. Create a new Thing: `ESP32_Door_Controller`
3. Download certificates:
   - `certificate.pem.crt`
   - `private.pem.key`
   - `AmazonRootCA1.pem`

### 2. Certificate Placement

```
IoT-Project/
└── certs/
    ├── certificate.pem.crt    # Device certificate
    ├── private.pem.key        # Private key
    └── AmazonRootCA1.pem      # Root CA
```

### 3. Python Client Setup

```bash
# Install dependencies
pip install boto3 opencv-python AWSIoTPythonSDK

# Configure client/config.py
```

Create `client/config.py`:
```python
import os

# AWS Credentials
AWS_ACCESS_KEY = "your-access-key"
AWS_SECRET_KEY = "your-secret-key"

# Multi-Region Configuration
AWS_REGION = "us-east-1"              # AI/ML services
AWS_IOT_ENDPOINT = "xxxxx-ats.iot.eu-north-1.amazonaws.com"  # IoT endpoint

# S3 & Rekognition
S3_BUCKET_NAME = "your-smart-door-bucket"
REKOGNITION_COLLECTION_ID = "authorized_faces"

# MQTT Settings
CLIENT_ID = "SmartDoor_MacBook_Scanner"
PORT = 8883
TOPIC = "iot/course/project/door"

# Certificate Paths
CERTS_DIR = "/path/to/IoT-Project/certs"
AWS_ROOT_CA = os.path.join(CERTS_DIR, "AmazonRootCA1.pem")
CERTIFICATE = os.path.join(CERTS_DIR, "certificate.pem.crt")
PRIVATE_KEY = os.path.join(CERTS_DIR, "private.pem.key")
```

### 4. ESP32 Firmware Setup

Install Arduino Libraries:
- `PubSubClient` by Nick O'Leary
- `MFRC522` by GithubCommunity

Create `firmware/esp32_door_lock/secrets.h`:
```cpp
#ifndef SECRETS_H
#define SECRETS_H

const char* WIFI_SSID = "your-wifi-ssid";
const char* WIFI_PASSWORD = "your-wifi-password";
const char* AWS_IOT_ENDPOINT = "xxxxx-ats.iot.eu-north-1.amazonaws.com";
const char* MQTT_TOPIC = "iot/course/project/door";
const char* CLIENT_ID = "ESP32_Door_Controller";

// Paste your certificates here
static const char AWS_CERT_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
)EOF";

static const char AWS_CERT_CRT[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
)EOF";

static const char AWS_CERT_PRIVATE[] PROGMEM = R"EOF(
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
)EOF";

#endif
```

### 5. Enroll Authorized Faces

```bash
# Upload face images to Rekognition collection
cd client
python upload_all_faces.py
```

Place authorized user photos in the `faces/` directory before running.

---

## Usage

### Start the Security System

```bash
cd client
python smart_door_ai.py
```

### User Journey

1. **Approach Camera** - Stand in front of the security camera
2. **Face Scan** - OpenCV detects face, uploads to AWS
3. **Cloud Verification** - Rekognition matches against authorized collection (85%+ threshold)
4. **Access Window Opens** - ESP32 receives `FACE_VERIFIED`, LED blinks, 10-second timer starts
5. **Tap RFID Card** - Present authorized card to reader
6. **Door Unlocks** - 2FA success, relay activates for 3 seconds
7. **Auto-Lock** - Door secures automatically

### MQTT Commands

| Command | Action |
|---------|--------|
| `FACE_VERIFIED` | Opens 10-second RFID window |
| `EMERGENCY_OPEN` | Bypasses 2FA (admin only) |

---

## Security Features

| Feature | Implementation |
|---------|----------------|
| **Mutual TLS (mTLS)** | X.509 certificates for MQTT authentication |
| **Face Match Threshold** | 85% minimum confidence required |
| **Time-Bound Access** | 10-second window prevents replay attacks |
| **Dual-Factor Enforcement** | Card alone is rejected without prior face auth |
| **Known Card Whitelist** | Only pre-registered UIDs accepted |
| **SSL/TLS Everywhere** | Encrypted communication on all channels |

---

## Troubleshooting

### macOS SSL Certificate Warnings

The Python client suppresses urllib3 SSL warnings for compatibility:

```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

For boto3 clients, SSL verification is disabled due to macOS certificate store issues:
```python
s3_client = session.client('s3', verify=False)
rekognition_client = session.client('rekognition', verify=False)
```

**Production Recommendation:** Configure proper CA certificates or use `certifi` package.

### DNS Resolution Issues

If IoT Core connection fails, verify DNS resolution:
```bash
nslookup xxxxx-ats.iot.eu-north-1.amazonaws.com
```

Consider using `8.8.8.8` as DNS server if corporate firewall interferes.

### RFID Reader Not Responding

1. Verify SPI wiring (SS=GPIO5, RST=GPIO22)
2. Check 3.3V power supply (not 5V!)
3. Confirm `MFRC522` library is installed

### Common Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| `MQTT Connection Error` | Certificate mismatch | Regenerate certs in IoT Core |
| `Face not found` | Poor lighting/angle | Ensure clear frontal view |
| `ACCESS DENIED: Face verification required` | Card tapped without face scan | Complete face auth first |
| `Timeout! Face authentication expired` | 10-second window passed | Scan face again |

---

## Project Structure

```
IoT-Project/
├── client/
│   ├── smart_door_ai.py        # Main 2FA client (face + MQTT)
│   ├── config.py               # AWS configuration
│   ├── upload_all_faces.py     # Face enrollment utility
│   ├── unlock.py               # Manual MQTT unlock tool
│   └── captured_faces/         # Temporary scan storage
├── firmware/
│   └── esp32_door_lock/
│       ├── esp32_door_lock.ino # 2FA firmware (RFID + MQTT)
│       └── secrets.h           # WiFi/AWS credentials
├── certs/                      # AWS IoT certificates
├── faces/                      # Authorized user photos
└── README.md
```

---

## License

This project is developed for educational and portfolio purposes.

---

<p align="center">
  <strong>Built with AWS IoT Core, Rekognition, and ESP32</strong><br>
  Secure. Intelligent. Connected.
</p>
