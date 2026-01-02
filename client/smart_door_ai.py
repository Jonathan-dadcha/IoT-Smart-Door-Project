import time
import sys
import cv2
import ssl
import boto3
import paho.mqtt.client as mqtt
from botocore.config import Config

# ייבוא משתנים מקובץ הקונפיגורציה
from config import (
    AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, ENDPOINT, PORT,
    TOPIC, CLIENT_ID, BUCKET_NAME, PATH_TO_CERT, PATH_TO_KEY, PATH_TO_ROOT
)

# ==========================================
# 1. הגדרת חיבור ל-AWS (S3 & Rekognition)
# ==========================================
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

# יצירת הקליינטים עם ההגדרות
s3_client = session.client('s3', config=my_config)
rekognition_client = session.client('rekognition', config=my_config)
print("✅ AWS AI Services Ready.")


# ==========================================
# 2. פונקציית זיהוי מול הענן
# ==========================================
def verify_face_with_bucket(local_image_path):
    visitor_filename = "visitor_temp.jpg"
    
    try:
        # העלאת התמונה מהמצלמה ל-S3
        s3_client.upload_file(local_image_path, BUCKET_NAME, visitor_filename)
        
        # קבלת רשימת התמונות בבאקט
        bucket_objects = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in bucket_objects:
            print("⚠️ Bucket is empty.")
            return False

        print(f"Scanning against {len(bucket_objects['Contents'])-1} authorized users...")

        # לולאה שעוברת על כל התמונות בבאקט (חוץ מהאורח)
        for obj in bucket_objects['Contents']:
            authorized_filename = obj['Key']
            
            if authorized_filename == visitor_filename:
                continue
            
            try:
                # השוואת פנים באמצעות Rekognition
                response = rekognition_client.compare_faces(
                    SourceImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': authorized_filename}},
                    TargetImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': visitor_filename}},
                    SimilarityThreshold=80
                )
                
                if len(response['FaceMatches']) > 0:
                    similarity = response['FaceMatches'][0]['Similarity']
                    print(f" >>> MATCH FOUND! User: {authorized_filename} (Score: {similarity:.1f}%)")
                    return True 
                else:
                    print(f" >>> Checked {authorized_filename}: No match.")

            except Exception as e:
                print(f"Error checking {authorized_filename}: {e}")
                continue

        print("❌ Finished scanning. No authorized user found.")
        return False

    except Exception as e:
        print(f"❌ AWS Error: {e}")
        return False


# ==========================================
# 3. חיבור ל-MQTT (IoT Core)
# ==========================================
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)

# הגדרת תעודות האבטחה
mqtt_client.tls_set(
    ca_certs=PATH_TO_ROOT, 
    certfile=PATH_TO_CERT, 
    keyfile=PATH_TO_KEY, 
    cert_reqs=ssl.CERT_REQUIRED, 
    tls_version=ssl.PROTOCOL_TLSv1_2
)

try:
    print(f"☁️ Connecting to IoT Core...")
    mqtt_client.connect(ENDPOINT, PORT, 60)
    mqtt_client.loop_start()
    print("✅ Connected to MQTT Broker.")
except Exception as e:
    print(f"❌ MQTT Connection Error: {e}")
    sys.exit()


# ==========================================
# 4. לולאת המצלמה והזיהוי
# ==========================================
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(0) # 0 = מצלמת ברירת מחדל

if not cap.isOpened():
    print("❌ Error: Could not open camera.")
    sys.exit()

print("\n🔒 SYSTEM ARMED. 2-Factor Auth Mode (Face + Card).")
print("   Please look at the camera...")

last_check_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    status_text = "SCANNING..."
    color = (255, 0, 0) # כחול

    if len(faces) > 0:
        # בודקים רק פעם ב-5 שניות כדי לא להעמיס
        if time.time() - last_check_time > 5:
            print("\n👀 Face detected. Verifying...")
            
            # שמירת תמונה זמנית
            cv2.imwrite("temp_capture.jpg", frame)
            
            # שליחה לבדיקה בענן
            if verify_face_with_bucket("temp_capture.jpg"):
                print("✅ ACCESS GRANTED (Step 1/2)")
                
                # שליחת הפקודה שדורכת את המערכת
                mqtt_client.publish(TOPIC, "FACE_VERIFIED", qos=1)
                
                status_text = "FACE VERIFIED! USE CARD NOW"
                color = (0, 255, 0) # ירוק
                
                # ציור מסגרת ירוקה והצגת הודעה
                cv2.rectangle(frame, (0,0), (640,480), (0,255,0), 10)
                cv2.putText(frame, status_text, (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
                cv2.imshow('Smart Door AI', frame)
                
                # השהיה קצרה כדי שיראו את האישור
                cv2.waitKey(2000) 
            else:
                print("⛔ ACCESS DENIED (Unknown Face)")
                status_text = "UNKNOWN USER"
                color = (0, 0, 255) # אדום
            
            last_check_time = time.time()

    # ציור ריבועים סביב הפנים
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

    cv2.putText(frame, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow('Smart Door AI', frame)

    # יציאה עם מקש Q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ניקוי משאבים ביציאה
cap.release()
cv2.destroyAllWindows()
mqtt_client.loop_stop()
print("System Shutdown.")