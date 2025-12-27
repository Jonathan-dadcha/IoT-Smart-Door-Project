import os
import cv2
import time
import numpy as np
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder

# ==========================================
# הגדרות AWS
# ==========================================
ENDPOINT = "a3dznsh4cnffd8-ats.iot.eu-north-1.amazonaws.com"
CLIENT_ID = "MacBook_FaceCam_PlanB"
TOPIC = "iot/course/project/door"
CAMERA_INDEX = 0 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERTS_DIR = os.path.join(BASE_DIR, "certs")
PATH_TO_CERT = os.path.join(CERTS_DIR, "6e1c1cb3b190852a3a40d395285f937daae17874ab4c18d7e6bebabc3f43535c-certificate.pem.crt")
PATH_TO_KEY = os.path.join(CERTS_DIR, "6e1c1cb3b190852a3a40d395285f937daae17874ab4c18d7e6bebabc3f43535c-private.pem.key")
PATH_TO_ROOT = os.path.join(CERTS_DIR, "AmazonRootCA1.pem")

# ==========================================
# חיבור לענן
# ==========================================
print("☁️ Connecting to AWS...")
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=PATH_TO_CERT,
    pri_key_filepath=PATH_TO_KEY,
    client_bootstrap=client_bootstrap,
    ca_filepath=PATH_TO_ROOT,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30
)

connect_future = mqtt_connection.connect()
connect_future.result()
print("✅ AWS Connected!")

# ==========================================
# טעינת המודל של OpenCV (Haar Cascade)
# ==========================================
# המודל הזה מגיע מובנה עם OpenCV, אבל לפעמים צריך למצוא את הנתיב שלו
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

if face_cascade.empty():
    print("❌ Error: Could not load Haar Cascade model.")
    exit()

print("✅ Face Detection Model Loaded.")

# ==========================================
# לולאת המצלמה
# ==========================================
print("\n🔒 SYSTEM LOCKED. Waiting for a face...")
cap = cv2.VideoCapture(CAMERA_INDEX)
last_open_time = 0

while True:
    ret, frame = cap.read()
    if not ret: 
        print("Failed to read camera")
        break

    # המרה לשחור-לבן (נדרש ע"י המודל הזה, ופותר בעיות צבע)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # זיהוי פנים
    # scaleFactor=1.1, minNeighbors=5 הם פרמטרים סטנדרטיים לדיוק
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    status_text = "LOCKED"
    color = (0, 0, 255) # אדום

    if len(faces) > 0:
        # אם זוהו פנים כלשהן
        status_text = "FACE DETECTED - ACCESS GRANTED"
        color = (0, 255, 0) # ירוק
        
        # ציור מלבנים סביב הפנים
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # שליחת פקודה לענן (עם השהיה של 10 שניות בין פתיחות)
        if time.time() - last_open_time > 10:
            print(f"🔓 Face Detected! Sending OPEN command...")
            mqtt_connection.publish(topic=TOPIC, payload="OPEN", qos=mqtt.QoS.AT_LEAST_ONCE)
            last_open_time = time.time()

    cv2.putText(frame, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow('Smart Door Project', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
mqtt_connection.disconnect()
print("System closed.")