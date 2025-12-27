import os
import time
import sys
import cv2
import ssl
import paho.mqtt.client as mqtt

# ==========================================
# הגדרות
# ==========================================
ENDPOINT = "a3dznsh4cnffd8-ats.iot.eu-north-1.amazonaws.com"
PORT = 8883
TOPIC = "iot/course/project/door"
CLIENT_ID = "Lenovo_Adar_Paho"
CAMERA_INDEX = 0

# ==========================================
# נתיבים (C:/iot_test)
# ==========================================
BASE_DIR = "C:/iot_test"
CERTS_DIR = BASE_DIR + "/certs"

PATH_TO_CERT = CERTS_DIR + "/6e1c1cb3b190852a3a40d395285f937daae17874ab4c18d7e6bebabc3f43535c-certificate.pem.crt"
PATH_TO_KEY = CERTS_DIR + "/6e1c1cb3b190852a3a40d395285f937daae17874ab4c18d7e6bebabc3f43535c-private.pem.key"
PATH_TO_ROOT = CERTS_DIR + "/AmazonRootCA1.pem"

# בדיקה שהקבצים קיימים ולא ריקים
def check_file(path):
    if not os.path.exists(path):
        print(f"❌ ERROR: File missing: {path}")
        sys.exit()
    if os.path.getsize(path) == 0:
        print(f"❌ ERROR: File is EMPTY (0 bytes): {path}")
        print("Please copy the files again properly.")
        sys.exit()

print("🔍 Checking files...")
check_file(PATH_TO_CERT)
check_file(PATH_TO_KEY)
check_file(PATH_TO_ROOT)
print("✅ Files OK.")

# ==========================================
# פונקציות MQTT
# ==========================================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ CONNECTED to AWS IoT Core!")
    else:
        print(f"❌ Connection failed. Return code: {rc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
client.on_connect = on_connect

# הגדרות אבטחה (SSL/TLS) - פה הקסם קורה
client.tls_set(
    ca_certs=PATH_TO_ROOT,
    certfile=PATH_TO_CERT,
    keyfile=PATH_TO_KEY,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2,
    ciphers=None
)

print(f"☁️ Connecting to {ENDPOINT}...")
try:
    client.connect(ENDPOINT, PORT, 60)
    client.loop_start() # מתחיל תהליך ברקע
    time.sleep(2) # נותן לו רגע להתחבר
except Exception as e:
    print(f"❌ Connection Error: {e}")
    sys.exit()

# ==========================================
# טעינת מודל זיהוי פנים
# ==========================================
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
if face_cascade.empty():
    print("❌ Error loading Haar Cascade.")
    exit()

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

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    status_text = "LOCKED"
    color = (0, 0, 255)

    if len(faces) > 0:
        status_text = "FACE DETECTED"
        color = (0, 255, 0)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # שליחת פקודה
        if time.time() - last_open_time > 10:
            print(f"🔓 OPENING DOOR...")
            info = client.publish(TOPIC, "OPEN", qos=1)
            info.wait_for_publish() # מוודא שההודעה יצאה
            print("🚀 Command Sent!")
            last_open_time = time.time()

    cv2.putText(frame, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow('Smart Door - Paho Version', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
print("Bye.")