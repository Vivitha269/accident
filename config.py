import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

load_dotenv()

creds_json = os.getenv('FIREBASE_CREDENTIALS')

if creds_json is None:
    raise ValueError("ERROR: FIREBASE_CREDENTIALS not found in .env file!")

firebase_creds = json.loads(creds_json)
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred)
db = firestore.client()