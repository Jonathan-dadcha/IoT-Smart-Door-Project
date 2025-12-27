import cv2
import paho.mqtt.client as mqtt
import time

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/course/project/door"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
try:
    client.connect(BROKER, PORT, 60)
    print(f"Connected to Broker: {BROKER}")
except Exception as e:
    print(f"Failed to connect to MQTT: {e}")
    exit()

cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)

if not cap.isOpened():
    cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)

if not cap.isOpened():
    print("ERROR: Could not open camera. Check Permissions!")
    exit()

print("Camera is ON. Press 'o' to OPEN door, 'q' to QUIT.")

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Can't receive frame. Exiting ...")
        break

    cv2.putText(frame, "Press 'o' to Unlock", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow('Smart Entry System', frame)

    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('o'):
        print("Sending command: OPEN")
        client.publish(TOPIC, "OPEN")
        cv2.putText(frame, "DOOR OPENING...", (100, 200), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        cv2.imshow('Smart Entry System', frame)
        cv2.waitKey(100)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.disconnect()
print("Program finished.")