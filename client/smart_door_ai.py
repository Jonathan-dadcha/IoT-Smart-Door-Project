import time
import json
import boto3
import cv2
import os
import urllib3 
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import config

# השתקת אזהרות SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- AWS Configuration ---
AWS_IOT_ENDPOINT = config.AWS_IOT_ENDPOINT
CLIENT_ID = config.CLIENT_ID
TOPIC_COMMAND = config.TOPIC
BUCKET_NAME = config.BUCKET_NAME
COLLECTION_ID = config.REKOGNITION_COLLECTION_ID

# --- Initialize AWS Clients (US Region) ---
print(f"🔑 Connecting to AI Services in {config.AWS_REGION}...")
session = boto3.Session(
    aws_access_key_id=config.AWS_ACCESS_KEY,
    aws_secret_access_key=config.AWS_SECRET_KEY,
    region_name=config.AWS_REGION
)

# לקוחות עם עקיפת SSL
s3_client = session.client('s3', verify=False)
rekognition_client = session.client('rekognition', verify=False)
print("✅ Connected to Rekognition & S3.")

# --- Initialize MQTT Client (EU Endpoint) ---
print(f"☁️ Connecting to IoT Broker in EU...")
mqtt_client = AWSIoTMQTTClient(CLIENT_ID)
mqtt_client.configureEndpoint(AWS_IOT_ENDPOINT, 8883)
mqtt_client.configureCredentials(config.AWS_ROOT_CA, config.PRIVATE_KEY, config.CERTIFICATE)
mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
mqtt_client.configureOfflinePublishQueueing(-1)
mqtt_client.configureDrainingFrequency(2)
mqtt_client.configureConnectDisconnectTimeout(10)
mqtt_client.configureMQTTOperationTimeout(5)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def connect_mqtt():
    try:
        mqtt_client.connect()
        print("✅ Connected to MQTT Broker!")
    except Exception as e:
        print(f"❌ MQTT Connection Error: {e}")

def scan_and_verify():
    cap = cv2.VideoCapture(0) 
    time.sleep(1)
    
    print("👀 Scanning for faces...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        if len(faces) > 0:
            print("👤 Face detected locally! Sending to US Server...")
            
            image_path = os.path.join(config.CAPTURED_FACES_DIR, "live_scan.jpg")
            cv2.imwrite(image_path, frame)
            
            try:
                # 1. העלאה ל-S3
                s3_filename = "live_scan.jpg"
                s3_client.upload_file(image_path, BUCKET_NAME, s3_filename)
                
                # 2. בדיקה מול Rekognition
                response = rekognition_client.search_faces_by_image(
                    CollectionId=COLLECTION_ID,
                    Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': s3_filename}},
                    FaceMatchThreshold=85,
                    MaxFaces=1
                )
                
                face_matches = response['FaceMatches']
                if face_matches:
                    print(f"✅ ACCESS GRANTED! Confidence: {face_matches[0]['Similarity']:.2f}%")
                    
                    mqtt_client.publish(TOPIC_COMMAND, "FACE_VERIFIED", 1)
                    print("🔓 sent FACE_VERIFIED to ESP32.")
                    
                    time.sleep(10) 
                else:
                    print("⛔ ACCESS DENIED (Unknown Face)")
                    time.sleep(2) 

            except Exception as e:
                print(f"AWS Error: {e}")
                time.sleep(2)

        cv2.imshow('Security Camera', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    connect_mqtt()
    scan_and_verify()