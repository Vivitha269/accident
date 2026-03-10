import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

# Firebase Configuration
FIREBASE_CONFIG = {
    "type": os.getenv("FIREBASE_TYPE", "service_account"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID", "ai-accident"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
}

# Initialize Firebase
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CONFIG)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase initialized successfully")
except Exception as e:
    print(f"⚠️ Firebase initialization error: {e}")
    db = None

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Default Emergency Numbers (hardcoded as requested)
DEFAULT_EMERGENCY_CONTACT = os.getenv("DEFAULT_EMERGENCY_CONTACT", "+1234567890")
DEFAULT_POLICE_NUMBER = os.getenv("DEFAULT_POLICE_NUMBER", "+1000000000")
DEFAULT_AMBULANCE_NUMBER = os.getenv("DEFAULT_AMBULANCE_NUMBER", "+1000000001")
DEFAULT_HOSPITAL_NUMBER = os.getenv("DEFAULT_HOSPITAL_NUMBER", "+1000000002")

# App Configuration
APP_NAME = "AI Accident Detection System"
API_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Geocoding Configuration
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# Routing Configuration
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"

# Overpass API for places
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Rate limiting
MAX_SMS_RETRIES = 3
CALL_RETRY_DELAY = 5  # seconds

