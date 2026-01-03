import boto3
import config
from botocore.exceptions import ClientError
import urllib3

# השתקת אזהרות אבטחה (כי אנחנו מבטלים SSL בכוח)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(f"🔧 Connecting to AWS Region: {config.AWS_REGION}")

# יצירת קליינט עם ביטול SSL (הפתרון לבעיית המקבוק שלך)
rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=config.AWS_ACCESS_KEY,
    aws_secret_access_key=config.AWS_SECRET_KEY,
    region_name=config.AWS_REGION,
    verify=True  # <--- זה התיקון הקריטי!
)

collection_id = config.REKOGNITION_COLLECTION_ID

print(f"🚀 Attempting to create Collection: {collection_id}")

try:
    # מנסה ליצור את האוסף
    response = rekognition.create_collection(CollectionId=collection_id)
    print(f"✅ Collection '{collection_id}' created successfully!")
    print(f"   Collection ARN: {response['CollectionArn']}")
    print(f"   Status Code: {response['StatusCode']}")

except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
        print(f"⚠️ Collection '{collection_id}' already exists. All good.")
    else:
        print(f"❌ Unexpected Error: {e}")

print("\n--- בדיקת חיבור ---")
# בדיקה סופית שאנחנו רואים את האוסף
try:
    cols = rekognition.list_collections()
    print("📋 רשימת האוספים הקיימים בחשבון שלך:")
    print(cols['CollectionIds'])
except Exception as e:
    print(f"❌ Connection failed: {e}")