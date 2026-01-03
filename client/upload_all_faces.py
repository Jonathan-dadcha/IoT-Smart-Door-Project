import boto3
import os
import urllib3
import config

# ==========================================
# הגדרות ועקיפת SSL
# ==========================================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(f"🔧 Connecting to AI Region: {config.AWS_REGION}")

session = boto3.Session(
    aws_access_key_id=config.AWS_ACCESS_KEY,
    aws_secret_access_key=config.AWS_SECRET_KEY,
    region_name=config.AWS_REGION
)

s3 = session.client('s3', verify=False)
rekognition = session.client('rekognition', verify=False)

def upload_folder():
    # === התיקון כאן: הולכים תיקייה אחת אחורה מ-client ל-IoT-Project ===
    project_root = os.path.dirname(config.BASE_DIR) 
    faces_dir = os.path.join(project_root, "faces")
    
    print(f"📂 Looking for images in: {faces_dir}")

    if not os.path.exists(faces_dir):
        print(f"❌ Error: Folder not found! Checked path: {faces_dir}")
        return

    # סינון קבצי תמונה בלבד (כולל jpeg/jpg/png)
    files = [f for f in os.listdir(faces_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not files:
        print("⚠️ No image files found in the folder.")
        return

    print(f"🚀 Found {len(files)} images. Starting upload...\n")

    for file_name in files:
        full_path = os.path.join(faces_dir, file_name)
        # השם במערכת יהיה שם הקובץ בלי הסיומת (adar / jonathan)
        external_id = os.path.splitext(file_name)[0]
        
        print(f"🔄 Processing: {file_name} -> User: {external_id}")

        try:
            # 1. העלאה ל-S3
            s3.upload_file(full_path, config.BUCKET_NAME, file_name)
            
            # 2. אינדוקס ב-Rekognition
            response = rekognition.index_faces(
                CollectionId=config.REKOGNITION_COLLECTION_ID,
                Image={'S3Object': {'Bucket': config.BUCKET_NAME, 'Name': file_name}},
                ExternalImageId=external_id,
                MaxFaces=1,
                QualityFilter="AUTO",
                DetectionAttributes=['ALL']
            )

            if len(response['FaceRecords']) > 0:
                print(f"   ✅ SUCCESS! Added user '{external_id}'.")
            else:
                print(f"   ⚠️ Warning: No face detected in {file_name}.")

        except Exception as e:
            print(f"   ❌ Error processing {file_name}: {e}")

    print("\n🎉 All done! Now run smart_door_ai.py")

if __name__ == "__main__":
    upload_folder()