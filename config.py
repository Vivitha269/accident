import firebase_admin
from firebase_admin import credentials, firestore, messaging
import os
import json
from dotenv import load_dotenv

load_dotenv()
# Load Firebase credentials from env var (JSON string)
firebase_creds = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred)
db = firestore.client()