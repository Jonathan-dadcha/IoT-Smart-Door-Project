import time
import sys
import cv2
import ssl
import boto3
import paho.mqtt.client as mqtt
from botocore.config import Config

from config import (
    AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, ENDPOINT, PORT,
    TOPIC, CLIENT_ID, BUCKET_NAME, PATH_TO_CERT, PATH_TO_KEY, PATH_TO_ROOT
)

my_config = Config(
    region_name=REGION,
    connect_timeout=10,
    read_timeout=10,
    retries={'max_attempts': 3}
)

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

# שימוש בקונפיגורציה החדשה
s3_client = session.client('s3', config=my_config)
rekognition_client = session.client('rekognition', config=my_config)
print("AWS AI Services Ready.")

print("Connecting to AWS...")
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)
s3_client = session.client('s3')
rekognition_client = session.client('rekognition')
print("AWS AI Services Ready.")

def verify_face_with_bucket(local_image_path):
    visitor_filename = "visitor_temp.jpg"
    
    try:
        s3_client.upload_file(local_image_path, BUCKET_NAME, visitor_filename)
        bucket_objects = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in bucket_objects:
            print("Bucket is empty.")
            return False

        print(f"Scanning against {len(bucket_objects['Contents'])-1} users in cloud...")

        for obj in bucket_objects['Contents']:
            authorized_filename = obj['Key']
            
            if authorized_filename == visitor_filename:
                continue
            
            try:
                response = rekognition_client.compare_faces(
                    SourceImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': authorized_filename}},
                    TargetImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': visitor_filename}},
                    SimilarityThreshold=70
                )
                
                if len(response['FaceMatches']) > 0:
                    similarity = response['FaceMatches'][0]['Similarity']
                    print(f" >>> Checked {authorized_filename}: MATCH! Score: {similarity:.1f}%")
                    return True 
                else:
                    print(f" >>> Checked {authorized_filename}: No match (Score too low)")

            except Exception as e:
                print(f"Error checking {authorized_filename}: {e}")
                continue

        print("Finished scanning all users. No match found.")
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
mqtt_client.tls_set(ca_certs=PATH_TO_ROOT, certfile=PATH_TO_CERT, keyfile=PATH_TO_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)

try:
    mqtt_client.connect(ENDPOINT, PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"MQTT Error: {e}")
    sys.exit()

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(0)

print("SYSTEM ARMED. Multi-User Mode.")
last_check_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    status_text = "SCANNING..."
    color = (255, 0, 0) 

    if len(faces) > 0:
        if time.time() - last_check_time > 5:
            print("Face detected. Checking permissions...")
            cv2.imwrite("temp_capture.jpg", frame)
            
            if verify_face_with_bucket("temp_capture.jpg"):
                print("ACCESS GRANTED")
                mqtt_client.publish(TOPIC, "OPEN", qos=1)
                
                status_text = "ACCESS GRANTED"
                color = (0, 255, 0) 
                
                cv2.rectangle(frame, (0,0), (640,480), (0,255,0), 10)
                cv2.imshow('Smart Door AI', frame)
                cv2.waitKey(3000) 
            else:
                print("ACCESS DENIED")
                status_text = "UNKNOWN USER"
                color = (0, 0, 255) 
            
            last_check_time = time.time()

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

    cv2.putText(frame, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow('Smart Door AI', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
mqtt_client.loop_stop()