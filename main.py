#!/usr/bin/env python3
"""Accident Detection API - FastAPI application"""

import os
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import math

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import firebase_admin
from firebase_admin import credentials, firestore
import requests
from twilio.rest import Client

# ==================== CONFIGURATION ====================
PORT = int(os.environ.get("PORT", 8000))

# Initialize Firebase
try:
    cred = credentials.Certificate("ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    db = None

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# Google Maps API
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "AIzaSyBV4-ApL_6i-KpJ0s2r2yL8K1zK1zK1zK1z")

# Distance threshold in meters for alert triggering
DISTANCE_THRESHOLD_METERS = 5000  # 5km radius

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FASTAPI APP ====================
app = FastAPI(title="Accident Detection API", description="API for accident detection and emergency alert system")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PYDANTIC MODELS ====================
class AccidentReport(BaseModel):
    """Pydantic model for accident reporting with validation."""
    userId: str
    name: str = "Accident User"  # Default name if not provided
    latitude: float
    longitude: float

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class TriggerAlertsRequest(BaseModel):
    """Request model for triggering alerts."""
    accidentId: str


class UserLocation(BaseModel):
    """Model for user location data."""
    userId: str
    latitude: float
    longitude: float


class UserProfile(BaseModel):
    """Model for user profile."""
    userId: str
    name: str
    phone: str
    emergencyContact: str


# ==================== HELPER FUNCTIONS ====================
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula (in meters)."""
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def get_address_from_coords(lat: float, lon: float) -> str:
    """Get address from coordinates using Google Maps Geocoding API."""
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "latlng": f"{lat},{lon}",
            "key": GOOGLE_MAPS_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("results"):
            return data["results"][0].get("formatted_address", "Unknown location")
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
    
    return "Unknown location"


def send_sms(to: str, message: str) -> bool:
    """Send SMS using Twilio."""
    try:
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            logger.warning("Twilio credentials not configured")
            return False
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to
        )
        logger.info(f"SMS sent to {to}")
        return True
    except Exception as e:
        logger.error(f"SMS error: {e}")
        return False


# ==================== API ENDPOINTS ====================
@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Accident Detection API is running", "status": "active"}


@app.post("/accident")
def accident_report(report: AccidentReport):
    """
    Reports an accident, saves it to Firestore, and immediately returns an ID.
    The Android app will then call /trigger_alerts after a delay.
    """
    try:
        acc_ref = db.collection("accidents").add({
            "userId": report.userId,
            "name": report.name,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "status": "reported",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        accident_id = acc_ref[1].id
        logger.info(f"New accident reported. ID: {accident_id}")
        return {
            "accidentId": accident_id,
            "status": "User notified. 30s buffer started."
        }
    except Exception as e:
        logger.error(f"Could not create accident record: {e}")
        raise HTTPException(status_code=500, detail="Failed to create accident record in database.")


@app.post("/trigger_alerts")
def trigger_alerts(request: TriggerAlertsRequest):
    """
    Trigger alerts for nearby users after accident is reported.
    
    FIXED: This endpoint now actually sends SMS to:
    1. Victim's emergency contacts (family)
    2. Nearby users (within 5km)
    3. Nearest police station
    4. Nearest hospital
    """
    try:
        # Get accident details
        accident_doc = db.collection("accidents").document(request.accidentId).get()
        
        if not accident_doc.exists:
            raise HTTPException(status_code=404, detail="Accident not found")
        
        accident_data = accident_doc.to_dict()
        accident_lat = accident_data.get("latitude")
        accident_lon = accident_data.get("longitude")
        victim_name = accident_data.get("name", "Accident Victim")
        victim_userId = accident_data.get("userId")
        
        if not accident_lat or not accident_lon:
            raise HTTPException(status_code=400, detail="Invalid accident coordinates")
        
        # Get location address
        address = get_address_from_coords(accident_lat, accident_lon)
        location_url = f"https://www.google.com/maps?q={accident_lat},{accident_lon}"
        
        logger.info(f"Triggering alerts for accident {request.accident_id} at {address}")
        
        # Get all user locations
        users_ref = db.collection("users").stream()
        nearby_users = []
        alert_messages_sent = 0
        
        for user_doc in users_ref:
            user_data = user_doc.to_dict()
            user_lat = user_data.get("latitude")
            user_lon = user_data.get("longitude")
            
            if user_lat and user_lon:
                distance = calculate_distance(
                    accident_lat, accident_lon, user_lat, user_lon
                )
                
                if distance <= DISTANCE_THRESHOLD_METERS:
                    nearby_users.append({
                        "userId": user_doc.id,
                        "name": user_data.get("name"),
                        "distance": round(distance, 2)
                    })
        
        logger.info(f"Found {len(nearby_users)} nearby users")
        
        # ========================================================================
        # FIX: Actually send SMS to nearby users and emergency contacts
        # ========================================================================
        
        # Import Twilio functions from twilio_config
        try:
            from twilio_config import (
                send_sms_to_family, 
                send_sms_with_route, 
                send_sms_to_police, 
                send_sms_to_hospital,
                normalize_phone_number
            )
        except ImportError as e:
            logger.error(f"Failed to import Twilio functions: {e}")
            return {"status": "error", "message": "SMS functions not available"}
        
        # 1. Send SMS to VICTIM'S EMERGENCY CONTACTS (Family)
        if victim_userId:
            try:
                victim_user_doc = db.collection("users").document(victim_userId).get()
                if victim_user_doc.exists:
                    victim_user_data = victim_user_doc.to_dict()
                    contacts_raw = victim_user_data.get("emergencyContacts", [])
                    
                    # Parse and get family contacts
                    contacts = []
                    if isinstance(contacts_raw, list):
                        for item in contacts_raw:
                            if isinstance(item, dict):
                                contacts.append(item)
                            elif isinstance(item, str):
                                if item.startswith('+'):
                                    contacts.append({"phone": item, "name": "Emergency Contact"})
                    elif isinstance(contacts_raw, dict):
                        contacts.append(contacts_raw)
                    
                    logger.info(f"Found {len(contacts)} emergency contacts for victim")
                    
                    # Send SMS to each family contact
                    for contact_map in contacts:
                        phone_number = (contact_map.get("phone") or 
                                      contact_map.get("phoneNumber") or 
                                      contact_map.get("mobile") or
                                      contact_map.get("telephone"))
                        
                        if phone_number:
                            try:
                                normalized = normalize_phone_number(phone_number)
                                if normalized:
                                    # Build emergency SMS message
                                    sms_text = f"🚨 EMERGENCY! {victim_name} has been in an accident!\n"
                                    sms_text += f"📍 Location: {address}\n"
                                    sms_text += f"🗺️ Maps: {location_url}\n"
                                    sms_text += f"\nAmbulance is being dispatched. Please rush to the location if possible!"
                                    
                                    send_sms(normalized, sms_text)
                                    alert_messages_sent += 1
                                    logger.info(f"Family SMS sent to {normalized}")
                            except Exception as e:
                                logger.error(f"Failed to send family SMS to {phone_number}: {e}")
                                
            except Exception as e:
                logger.error(f"Error getting victim user data: {e}")
        
        # 2. Send SMS to NEARBY USERS (people within 5km who might help)
        for nearby_user in nearby_users:
            try:
                user_id = nearby_user.get("userId")
                user_doc = db.collection("users").document(user_id).get()
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    user_phone = user_data.get("phone")
                    user_name = user_data.get("name", "User")
                    
                    if user_phone:
                        normalized = normalize_phone_number(user_phone)
                        if normalized:
                            # Send alert to nearby user
                            sms_text = f"⚠️ ACCIDENT ALERT! There is an accident nearby.\n"
                            sms_text += f"📍 Location: {address}\n"
                            sms_text += f"🗺️ Maps: {location_url}\n"
                            sms_text += f"\nVictim: {victim_name}\n"
                            sms_text += f"Please check if you can help!"
                            
                            send_sms(normalized, sms_text)
                            alert_messages_sent += 1
                            logger.info(f"Nearby user alert sent to {normalized}")
                        
            except Exception as e:
                logger.error(f"Failed to alert nearby user: {e}")
        
        # 3. Send SMS to POLICE (find nearest police station)
        try:
            from services.places import find_nearest_police
            police = find_nearest_police(accident_lat, accident_lon)
            if police:
                police_phone = police.get('phone')
                if police_phone:
                    normalized = normalize_phone_number(police_phone)
                    if normalized:
                        sms_text = f"🚔 POLICE ALERT! Accident Emergency!\n\n"
                        sms_text += f"👤 Victim: {victim_name}\n"
                        sms_text += f"📍 Location: {address}\n"
                        sms_text += f"📌 Coordinates: {accident_lat}, {accident_lon}\n"
                        sms_text += f"🗺️ Maps: {location_url}\n"
                        sms_text += f"\n⚠️ IMMEDIATE RESPONSE REQUIRED!"
                        
                        send_sms(normalized, sms_text)
                        alert_messages_sent += 1
                        logger.info(f"Police SMS sent to {normalized}")
        except Exception as e:
            logger.error(f"Failed to send police SMS: {e}")
        
        # 4. Send SMS to HOSPITAL (find nearest hospital)
        try:
            from services.places import find_top_3_hospitals
            hospitals = find_top_3_hospitals(accident_lat, accident_lon)
            if hospitals:
                hospital = hospitals[0]
                hospital_phone = hospital.get('phone')
                if hospital_phone:
                    normalized = normalize_phone_number(hospital_phone)
                    if normalized:
                        sms_text = f"🏥 HOSPITAL ALERT! Accident Emergency!\n\n"
                        sms_text += f"👤 Patient: {victim_name}\n"
                        sms_text += f"📍 Accident Location: {address}\n"
                        sms_text += f"🗺️ Maps: {location_url}\n"
                        sms_text += f"\n⚠️ PREPARED FOR EMERGENCY ADMISSION!"
                        
                        send_sms(normalized, sms_text)
                        alert_messages_sent += 1
                        logger.info(f"Hospital SMS sent to {normalized}")
        except Exception as e:
            logger.error(f"Failed to send hospital SMS: {e}")
        
        # Update accident status
        db.collection("accidents").document(request.accidentId).update({
            "status": "alerts_triggered",
            "alerts_sent": alert_messages_sent,
            "alerts_triggered_at": firestore.SERVER_TIMESTAMP
        })
        
        logger.info(f"Alerts complete. Total SMS sent: {alert_messages_sent}")
        
        return {
            "status": "success",
            "accidentId": request.accidentId,
            "nearby_users_notified": len(nearby_users),
            "total_alerts_sent": alert_messages_sent,
            "address": address
        }
        
    except Exception as e:
        logger.error(f"Error in trigger_alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger alerts: {str(e)}")


# ============================================================================
# Additional API Endpoints (kept from original)
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "accident-detection-api"
    }


# ============================================================================
# Emergency Contacts Endpoints
# ============================================================================

class EmergencyContact(BaseModel):
    """Model for emergency contact."""
    name: str
    phone: str
    relationship: Optional[str] = None


@app.post("/api/contacts/{userId}")
def add_emergency_contact(userId: str, contact: EmergencyContact):
    """Add an emergency contact for a user."""
    try:
        user_doc = db.collection("users").document(userId)
        
        if not user_doc.get().exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get existing contacts
        user_data = user_doc.get().to_dict()
        contacts = user_data.get("emergencyContacts", [])
        
        # Add new contact
        contacts.append({
            "name": contact.name,
            "phone": contact.phone,
            "relationship": contact.relationship or ""
        })
        
        user_doc.update({"emergencyContacts": contacts})
        
        return {
            "status": "success",
            "message": "Emergency contact added",
            "contactCount": len(contacts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding contact: {e}")
        raise HTTPException(status_code=500, detail="Failed to add contact")


@app.get("/api/contacts/{userId}")
def get_emergency_contacts(userId: str):
    """Get all emergency contacts for a user."""
    try:
        user_doc = db.collection("users").document(userId).get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        contacts = user_data.get("emergencyContacts", [])
        
        return {
            "status": "success",
            "userId": userId,
            "contacts": contacts,
            "count": len(contacts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get contacts")


# ============================================================================
# User Management Endpoints
# ============================================================================

class UserRegister(BaseModel):
    """Model for user registration."""
    userId: str
    name: str
    email: str
    phone: str
    password: str


class UserLogin(BaseModel):
    """Model for user login."""
    email: str
    password: str


@app.post("/api/users/register")
def register_user(user: UserRegister):
    """Register a new user."""
    try:
        existing = db.collection("users").document(user.userId).get()
        if existing.exists:
            raise HTTPException(status_code=400, detail="User ID already exists")
        
        users_by_email = db.collection("users").where("email", "==", user.email).get()
        if users_by_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db.collection("users").document(user.userId).set({
            "userId": user.userId,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "password": user.password,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "emergencyContacts": []
        })
        
        return {
            "status": "success",
            "message": "User registered successfully",
            "userId": user.userId
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")


@app.post("/api/users/login")
def login_user(credentials: UserLogin):
    """Login user and return user ID."""
    try:
        users = db.collection("users").where("email", "==", credentials.email).get()
        
        if not users:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user_doc = users[0]
        user_data = user_doc.to_dict()
        
        if user_data.get("password") != credentials.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return {
            "status": "success",
            "message": "Login successful",
            "userId": user_data.get("userId"),
            "name": user_data.get("name")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.get("/api/users/{userId}")
def get_user_profile(userId: str):
    """Get user profile."""
    try:
        user_doc = db.collection("users").document(userId).get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        user_data.pop("password", None)
        user_data["userId"] = userId
        
        return {"status": "success", "user": user_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")


# ============================================================================
# Accident Reports Endpoints
# ============================================================================

class AccidentEvent(BaseModel):
    """Model for accident event with sensor data."""
    userId: str
    name: str
    lat: float
    lon: float
    timestamp: str
    speed: Optional[float] = None
    acceleration: Optional[Dict] = None
    disturbance: Optional[str] = None


@app.post("/api/accidents")
def create_accident(accident: AccidentEvent):
    """Store accident event with GPS location, timestamp, and sensor values."""
    try:
        acc_ref = db.collection("accidents").add({
            "userId": accident.userId,
            "name": accident.name,
            "latitude": accident.lat,
            "longitude": accident.lon,
            "timestamp": accident.timestamp,
            "serverTimestamp": firestore.SERVER_TIMESTAMP,
            "status": "reported",
            "sensorData": {
                "speed": accident.speed,
                "acceleration": accident.acceleration,
                "disturbance": accident.disturbance
            }
        })
        
        accident_id = acc_ref[1].id
        
        return {
            "status": "success",
            "message": "Accident recorded successfully",
            "accidentId": accident_id
        }
    except Exception as e:
        logger.error(f"Error creating accident: {e}")
        raise HTTPException(status_code=500, detail="Failed to create accident record")


@app.get("/api/accidents/{userId}")
def get_accident_history(userId: str, limit: int = 10):
    """Retrieve accident history for a user."""
    try:
        accidents = db.collection("accidents") \
            .where("userId", "==", userId) \
            .order_by("timestamp", direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .get()
        
        accident_list = []
        for acc in accidents:
            data = acc.to_dict()
            accident_list.append({
                "accidentId": acc.id,
                "name": data.get("name"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "timestamp": data.get("timestamp"),
                "status": data.get("status"),
                "sensorData": data.get("sensorData")
            })
        
        return {
            "status": "success",
            "userId": userId,
            "accidents": accident_list,
            "count": len(accident_list)
        }
    except Exception as e:
        logger.error(f"Error getting accident history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get accident history")


# ============================================================================
# SMS Diagnostic Endpoints
# ============================================================================

@app.get("/diagnose_sms")
def diagnose_sms():
    """Diagnostic endpoint to check SMS configuration and test Twilio."""
    diagnostics = {
        "status": "checking",
        "environment_variables": {},
        "twilio_config": {}
    }
    
    env_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER']
    for var in env_vars:
        value = os.getenv(var)
        diagnostics["environment_variables"][var] = {
            "set": value is not None,
            "length": len(value) if value else 0
        }
    
    all_vars_set = all(os.getenv(v) for v in env_vars)
    diagnostics["twilio_config"]["all_variables_set"] = all_vars_set
    
    if all_vars_set:
        diagnostics["status"] = "ready"
        diagnostics["message"] = "All Twilio variables are configured."
    else:
        diagnostics["status"] = "error"
        diagnostics["message"] = "Missing Twilio environment variables!"
    
    return diagnostics


@app.get("/test_sms/{phone_number}")
def test_sms(phone_number: str):
    """Test endpoint to send a sample SMS."""
    try:
        from twilio_config import normalize_phone_number, send_sms
        
        normalized = normalize_phone_number(phone_number)
        if not normalized:
            raise HTTPException(status_code=400, detail=f"Invalid phone number: {phone_number}")
        
        test_message = "🔧 Test SMS from AI Accident Detection System. If you received this, SMS is working!"
        
        result = send_sms(normalized, test_message)
        if result:
            return {
                "status": "success",
                "message": f"Test SMS sent successfully to {normalized}"
            }
        else:
            return {
                "status": "failed",
                "message": "SMS sending failed. Check server logs."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"SMS Error: {str(e)}"
        }

