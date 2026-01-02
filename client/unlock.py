import time
import sys
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder

# ==========================================
# ייבוא הגדרות מתוך config.py
# ==========================================
try:
    # אנחנו מושכים את המשתנים שכבר הגדרת שם
    from config import (
        ENDPOINT, 
        CLIENT_ID, 
        TOPIC, 
        PATH_TO_CERT, 
        PATH_TO_KEY, 
        PATH_TO_ROOT
    )
except ImportError:
    print("❌ Error: Could not import config.py. Make sure it is in the same folder.")
    sys.exit()

# שינוי קטן ל-Client ID כדי שלא יתנגש אם סקריפט המצלמה רץ במקביל
UNLOCKER_CLIENT_ID = CLIENT_ID + "_Manual_Unlocker"

# ==========================================
# חיבור לענן
# ==========================================
print(f"🔑 Initializing Digital Key using settings from config.py...")
print(f"   Target: {ENDPOINT}")
print(f"   Topic:  {TOPIC}")

event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

try:
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=PATH_TO_CERT,
        pri_key_filepath=PATH_TO_KEY,
        client_bootstrap=client_bootstrap,
        ca_filepath=PATH_TO_ROOT,
        client_id=UNLOCKER_CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30
    )

    print(f"☁️ Connecting to AWS IoT Core...")
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("✅ Connected! System Ready.")

    # ==========================================
    # שליחת פקודת פתיחה
    # ==========================================
    print("\nSending OPEN command...")
    
    # שליחת הפקודה "OPEN"
    mqtt_connection.publish(
        topic=TOPIC,
        payload="OPEN",
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    
    print("🚀 Command SENT! Listen for the 'Click' on the door.")
    time.sleep(2) # מחכים קצת לוודא שההודעה יצאה

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    print("Disconnecting...")
    try:
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
    except:
        pass
    print("Done.")