import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

load_dotenv()

creds_json = os.getenv('FIREBASE_CREDENTIALS')

# If FIREBASE_CREDENTIALS env var is not set, try loading a local JSON file
if creds_json is None:
    # Allow specifying a path via FIREBASE_CREDENTIALS_FILE, or try the default file
    creds_file = os.getenv('FIREBASE_CREDENTIALS_FILE', 'ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json')
    if os.path.exists(creds_file):
        with open(creds_file, 'r', encoding='utf-8') as f:
            firebase_creds = json.load(f)
    else:
        raise ValueError("ERROR: FIREBASE_CREDENTIALS not found in .env and default JSON file missing!")
else:
    firebase_creds = json.loads(creds_json)

cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred)
db = firestore.client()