import time
import os
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder

# ==========================================
# הגדרות
# ==========================================
ENDPOINT = "a3dznsh4cnffd8-ats.iot.eu-north-1.amazonaws.com"
CLIENT_ID = "MacBook_Remote_Key" 
TOPIC = "iot/course/project/door"

# נתיבים לתעודות (משתמשים בנתיבים הקיימים שלך)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERTS_DIR = os.path.join(BASE_DIR, "certs")
PATH_TO_CERT = os.path.join(CERTS_DIR, "6e1c1cb3b190852a3a40d395285f937daae17874ab4c18d7e6bebabc3f43535c-certificate.pem.crt")
PATH_TO_KEY = os.path.join(CERTS_DIR, "6e1c1cb3b190852a3a40d395285f937daae17874ab4c18d7e6bebabc3f43535c-private.pem.key")
PATH_TO_ROOT = os.path.join(CERTS_DIR, "AmazonRootCA1.pem")

# ==========================================
# חיבור לענן
# ==========================================
print("🔑 Initializing Digital Key...")
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

print(f"Connecting to AWS IoT Core...")
connect_future = mqtt_connection.connect()
connect_future.result()
print("✅ Connected! System Ready.")

# ==========================================
# שליחת פקודת פתיחה
# ==========================================
try:
    print("\nSending OPEN command...")
    
    # שליחת הפקודה "OPEN" נקייה
    mqtt_connection.publish(
        topic=TOPIC,
        payload="OPEN",
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    
    print("🚀 Command SENT! Listen for the 'Click'.")
    time.sleep(2) # מחכים קצת לוודא שההודעה יצאה

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Done.")