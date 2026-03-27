

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_firebase_credentials():
    """
    Retrieves Firebase credentials from environment variables or a local JSON file.
    """
    # Method 1: Single JSON string from .env
    firebase_creds = os.getenv("FIREBASE_CREDENTIALS", "")
    
    if firebase_creds:
        try:
            cred_data = json.loads(firebase_creds)
            if "private_key" in cred_data:
                cred_data["private_key"] = cred_data["private_key"].replace("\\n", "\n")
            print("✅ Using Firebase credentials from FIREBASE_CREDENTIALS env variable")
            return cred_data
        except Exception as e:
            print(f"⚠️ Error with FIREBASE_CREDENTIALS: {e}")
    
    # Method 2: Individual environment variables
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
    if private_key:
        private_key = private_key.replace("\\n", "\n").strip('"')
        
        FIREBASE_CONFIG = {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID", "ai-accident"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
        }
        
        if FIREBASE_CONFIG.get("private_key") and FIREBASE_CONFIG.get("client_email"):
            print("✅ Using Firebase credentials from environment variables")
            return FIREBASE_CONFIG
    
    # Method 3: Local service account JSON file
    json_path = "ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json"
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            print(f"✅ Using Firebase credentials from file: {json_path}")
            return json.load(f)
            
    return None

# --- Initialize Firebase ---
db = None
firebase_initialized = False

try:
    firebase_config = get_firebase_credentials()
    if firebase_config:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_initialized = True
        print("✅ Firebase initialized successfully")
    else:
        print("⚠️ No Firebase credentials found. Using mock database.")
except Exception as e:
    print(f"⚠️ Firebase initialization error: {e}")

# --- Twilio Configuration ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# --- Default Emergency Numbers (Configured for Free Tier) ---
DEFAULT_EMERGENCY_CONTACT = os.getenv("DEFAULT_EMERGENCY_CONTACT", "+918838177899")
DEFAULT_POLICE_NUMBER = os.getenv("DEFAULT_POLICE_NUMBER", "+917338903743")
DEFAULT_AMBULANCE_NUMBER = os.getenv("DEFAULT_AMBULANCE_NUMBER", "+919342170059")
DEFAULT_HOSPITAL_NUMBER = os.getenv("DEFAULT_HOSPITAL_NUMBER", "+918825597447")

# --- External API Services ---
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# --- App Settings ---
APP_NAME = "AI Accident Detection System"
API_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Rate limiting and retry settings
MAX_SMS_RETRIES = 3
CALL_RETRY_DELAY = 5