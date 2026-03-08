"""
Firebase Configuration Module
Initializes Firebase Admin SDK for Firestore access.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Global Firestore client
_db = None


def get_firebase_db():
    """
    Get or initialize Firebase Firestore client.
    Handles already-initialized Firebase to prevent errors.
    """
    global _db
    
    if _db is not None:
        return _db
    
    # Check if Firebase is already initialized
    if firebase_admin._apps:
        # Use default app if already initialized
        _db = firestore.client()
        return _db
    
    creds_json = os.getenv('FIREBASE_CREDENTIALS')
    
    # If FIREBASE_CREDENTIALS env var is not set, try loading a local JSON file
    if creds_json is None:
        # Allow specifying a path via FIREBASE_CREDENTIALS_FILE, or try the default file
        creds_file = os.getenv('FIREBASE_CREDENTIALS_FILE', 'ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json')
        
        # Try multiple possible paths
        possible_paths = [
            creds_file,
            os.path.join(os.path.dirname(__file__), creds_file),
            os.path.join(os.getcwd(), creds_file),
        ]
        
        firebase_creds = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    firebase_creds = json.load(f)
                break
        
        if firebase_creds is None:
            raise ValueError(f"ERROR: FIREBASE_CREDENTIALS not found and JSON file '{creds_file}' not found in any location!")
    else:
        firebase_creds = json.loads(creds_json)
    
    # Initialize Firebase with credentials
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
    _db = firestore.client()
    
    return _db


# Initialize db on module import
try:
    db = get_firebase_db()
    print("Firebase initialized successfully!")
except Exception as e:
    print(f"Firebase initialization warning: {e}")
    db = None

