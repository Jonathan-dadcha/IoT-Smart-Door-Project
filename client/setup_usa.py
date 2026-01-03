import boto3
import config
import urllib3
from botocore.exceptions import ClientError

# עקיפת SSL למקבוק
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(f"🔧 Setting up infrastructure in Region: {config.AWS_REGION}")

# יצירת סשן מאומת
session = boto3.Session(
    aws_access_key_id=config.AWS_ACCESS_KEY,
    aws_secret_access_key=config.AWS_SECRET_KEY,
    region_name=config.AWS_REGION
)

# לקוחות עם ביטול SSL
s3 = session.client('s3', verify=False)
rekognition = session.client('rekognition', verify=False)

# 1. יצירת באקט (S3)
bucket_name = config.S3_BUCKET_NAME
print(f"🚀 Creating Bucket: {bucket_name}...")
try:
    s3.create_bucket(Bucket=bucket_name)
    print(f"✅ Bucket '{bucket_name}' created!")
except ClientError as e:
    if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
        print(f"⚠️ Bucket already exists. Good.")
    else:
        print(f"❌ S3 Error: {e}")

# 2. יצירת אוסף (Rekognition)
collection_id = config.REKOGNITION_COLLECTION_ID
print(f"🚀 Creating Collection: {collection_id}...")
try:
    rekognition.create_collection(CollectionId=collection_id)
    print(f"✅ Collection '{collection_id}' created!")
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
        print(f"⚠️ Collection already exists. Good.")
    else:
        print(f"❌ Rekognition Error: {e}")

print("\n🎉 Setup Complete! You can runs smart_door_ai.py now.")