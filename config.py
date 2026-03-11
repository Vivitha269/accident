import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

# Firebase Configuration - Try multiple methods
def get_firebase_credentials():
    """
    Try to get Firebase credentials from multiple sources:
    1. FIREBASE_CREDENTIALS (single JSON string in .env)
    2. Individual environment variables
    3. Service account JSON file
    """
    
    # Method 1: Try FIREBASE_CREDENTIALS (single JSON string)
    firebase_creds = os.getenv("FIREBASE_CREDENTIALS", "")
    
    if firebase_creds:
        try:
            # Parse the JSON string
            cred_data = json.loads(firebase_creds)
            # Fix the private key - replace \n with actual newlines
            if "private_key" in cred_data:
                cred_data["private_key"] = cred_data["private_key"].replace("\\n", "\n")
            print("✅ Using Firebase credentials from FIREBASE_CREDENTIALS env variable")
            return cred_data
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parsing FIREBASE_CREDENTIALS JSON: {e}")
        except Exception as e:
            print(f"⚠️ Error with FIREBASE_CREDENTIALS: {e}")
    
    # Method 2: Try environment variables (individual fields)
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
    
    if private_key:
        # Clean up the private key - replace escaped newlines
        private_key = private_key.replace("\\n", "\n")
        # Handle quotes if present
        private_key = private_key.strip('"')
        
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
        
        # Validate that we have the required fields
        if FIREBASE_CONFIG.get("private_key") and FIREBASE_CONFIG.get("client_email"):
            print("✅ Using Firebase credentials from environment variables")
            return FIREBASE_CONFIG
    
    # Method 3: Try to load from JSON file
    json_file_paths = [
        "ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json",
        os.path.join(os.path.dirname(__file__), "ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json")
    ]
    
    for json_path in json_file_paths:
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    cred_data = json.load(f)
                print(f"✅ Using Firebase credentials from file: {json_path}")
                return cred_data
            except Exception as e:
                print(f"⚠️ Error loading Firebase JSON from {json_path}: {e}")
                continue
    
    # Method 4: Check for GOOGLE_APPLICATION_CREDENTIALS
    google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if google_creds_path and os.path.exists(google_creds_path):
        try:
            with open(google_creds_path, 'r') as f:
                cred_data = json.load(f)
            print(f"✅ Using Firebase credentials from GOOGLE_APPLICATION_CREDENTIALS: {google_creds_path}")
            return cred_data
        except Exception as e:
            print(f"⚠️ Error loading Firebase from GOOGLE_APPLICATION_CREDENTIALS: {e}")
    
    return None


# Initialize Firebase
db = None
firebase_initialized = False

try:
    firebase_config = get_firebase_credentials()
    
    if firebase_config:
        # Validate required fields
        required_fields = ["private_key", "client_email", "project_id"]
        missing_fields = [field for field in required_fields if not firebase_config.get(field)]
        
        if missing_fields:
            print(f"⚠️ Firebase config missing required fields: {missing_fields}")
            raise ValueError(f"Missing Firebase config fields: {missing_fields}")
        
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_initialized = True
        print("✅ Firebase initialized successfully")
    else:
        print("⚠️ No Firebase credentials found. Using mock database.")
        print("   To fix: Set FIREBASE_CREDENTIALS in .env")
        print("   Or set FIREBASE_PRIVATE_KEY and FIREBASE_CLIENT_EMAIL in .env")
        print("   Or place your service account JSON file in the project root")
        
except Exception as e:
    print(f"⚠️ Firebase initialization error: {e}")
    print("   The app will continue without Firebase database.")
    print("   Emergency alerts will still work via Twilio.")
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

