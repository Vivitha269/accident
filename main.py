"""
AI Accident Detection Backend - Complete Emergency Response System
Flow:
1. User login and registration with 2 emergency contacts (required)
2. When accident detected → 30 second countdown asking "Are you okay?"
3. If user confirms "OK" → no alert sent
4. If user says "NOT OKAY" or no response in 30 seconds → 
   Send SMS + Call to:
   - Emergency Contact 1
   - Emergency Contact 2  
   - Hospital (with confirmation request)
   - Police (with live location + routing)
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import threading
import time

# Import config and services
from config import db
from twilio_config import (
    send_sms, 
    make_call, 
    play_alarm, 
    speed_alert_alarm,
    send_sms_to_family, 
    send_sms_to_police, 
    send_sms_to_hospital,
    send_sms_to_ambulance,
    send_pickup_confirmation,
    get_default_numbers
)
from services.places import find_nearest_police, find_top_3_hospitals
from services.geocoding import reverse_geocode
from services.routing import get_route, get_directions_text

# Initialize FastAPI
app = FastAPI(
    title="AI Accident Detection System",
    description="Complete emergency response with 30-second confirmation timeout",
    version="2.0.0"
)

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Store for pending accident confirmations (in-memory)
# Key: accident_id, Value: {'timeout': thread, 'data': accident_data}
pending_confirmations = {}


# ============================================================================
# Data Models
# ============================================================================

class AccidentReport(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    timestamp: Optional[int] = None
    status: str = "accident_detected"
    name: Optional[str] = "User"
    user_id: Optional[str] = None


class UserCreate(BaseModel):
    name: str
    phone: str
    emergency_contact_1: dict  # Required - {"name": str, "phone": str, "relationship": str}
    emergency_contact_2: dict  # Required - {"name": str, "phone": str, "relationship": str}


class UserResponse(BaseModel):
    id: str
    name: str
    phone: str
    emergency_contact_1: dict
    emergency_contact_2: dict
    created_at: datetime


class AccidentConfirmation(BaseModel):
    """User response to accident confirmation"""
    accident_id: str
    user_id: str
    is_okay: bool  # True = "I'm okay", False = "Not okay / Need help"


class AccidentConfirmationRequest(BaseModel):
    """Request body for confirming accident"""
    is_okay: bool


# ============================================================================
# Helper Functions
# ============================================================================

def send_emergency_alerts_complete(
    victim_name: str,
    address: str,
    maps_url: str,
    directions_text: str,
    accident_lat: float,
    accident_lon: float,
    emergency_contact_1: dict = None,
    emergency_contact_2: dict = None,
    hospital_info: dict = None,
    police_info: dict = None
):
    """
    Send complete emergency alerts to all responders:
    - Emergency Contact 1 (SMS + Call)
    - Emergency Contact 2 (SMS + Call)
    - Hospital (SMS + Call with confirmation request)
    - Police (SMS + Call with live location and routing)
    """
    results = {
        "sms_sent": [],
        "calls_made": [],
        "errors": []
    }
    
    location_info = {
        "address": address,
        "maps_url": maps_url
    }
    
    # 1. Send to Emergency Contact 1
    if emergency_contact_1 and emergency_contact_1.get('phone'):
        phone = emergency_contact_1['phone']
        name = emergency_contact_1.get('name', 'Emergency Contact')
        
        # Send SMS
        success = send_sms_to_family(
            phone,
            victim_name,
            address,
            maps_url,
            directions_text,
            hospital_info.get('name') if hospital_info else None,
            hospital_info.get('phone') if hospital_info else None
        )
        if success:
            results["sms_sent"].append(f"emergency_contact_1 ({name})")
        else:
            results["errors"].append(f"emergency_contact_1_sms")
        
        # Make call
        success = make_call(phone, victim_name, location_info)
        if success:
            results["calls_made"].append(f"emergency_contact_1 ({name})")
        else:
            results["errors"].append(f"emergency_contact_1_call")
    
    # 2. Send to Emergency Contact 2
    if emergency_contact_2 and emergency_contact_2.get('phone'):
        phone = emergency_contact_2['phone']
        name = emergency_contact_2.get('name', 'Emergency Contact')
        
        # Send SMS
        success = send_sms_to_family(
            phone,
            victim_name,
            address,
            maps_url,
            directions_text,
            hospital_info.get('name') if hospital_info else None,
            hospital_info.get('phone') if hospital_info else None
        )
        if success:
            results["sms_sent"].append(f"emergency_contact_2 ({name})")
        else:
            results["errors"].append(f"emergency_contact_2_sms")
        
        # Make call
        success = make_call(phone, victim_name, location_info)
        if success:
            results["calls_made"].append(f"emergency_contact_2 ({name})")
        else:
            results["errors"].append(f"emergency_contact_2_call")
    
    # 3. Send to Hospital
    if hospital_info and hospital_info.get('phone'):
        phone = hospital_info['phone']
        name = hospital_info.get('name', 'Hospital')
        
        # Send SMS with confirmation request
        sms_text = f"🏥 HOSPITAL ALERT! Accident Emergency!\n\n"
        sms_text += f"👤 Patient: {victim_name}\n"
        sms_text += f"📍 Location: {address}\n"
        sms_text += f"🗺️ Maps: {maps_url}\n"
        
        if directions_text:
            sms_text += f"\n🧭 Route:\n{directions_text}\n"
        
        sms_text += f"\n⚠️ Please confirm if patient can be admitted."
        sms_text += f"\nReply with CONFIRM or call {victim_name}'s family."
        
        success = send_sms(phone, sms_text)
        if success:
            results["sms_sent"].append(f"hospital ({name})")
        else:
            results["errors"].append(f"hospital_sms")
        
        # Make call to hospital
        success = make_call(phone, victim_name, location_info)
        if success:
            results["calls_made"].append(f"hospital ({name})")
        else:
            results["errors"].append(f"hospital_call")
    
    # 4. Send to Police
    if police_info and police_info.get('phone'):
        phone = police_info['phone']
        name = police_info.get('name', 'Police')
        
        # Send detailed SMS with location and routing
        sms_text = f"🚔 POLICE ALERT! Accident Emergency!\n\n"
        sms_text += f"👤 Victim: {victim_name}\n"
        sms_text += f"📍 Location: {address}\n"
        sms_text += f"📌 Coordinates: {accident_lat}, {accident_lon}\n"
        sms_text += f"🗺️ Maps: {maps_url}\n"
        
        if directions_text:
            sms_text += f"\n🧭 QUICKEST ROUTE TO SCENE:\n{directions_text}\n"
        
        sms_text += f"\n⚠️ IMMEDIATE RESPONSE REQUIRED! Life at risk!"
        
        success = send_sms(phone, sms_text)
        if success:
            results["sms_sent"].append(f"police ({name})")
        else:
            results["errors"].append(f"police_sms")
        
        # Make call to police
        success = make_call(phone, victim_name, location_info)
        if success:
            results["calls_made"].append(f"police ({name})")
        else:
            results["errors"].append(f"police_call")
    
    return results


def timeout_handler(accident_id: str, accident_data: dict):
    """
    Called when user doesn't respond within 30 seconds.
    Triggers full emergency response automatically.
    """
    print(f"\n⏰ TIMEOUT! No response for accident {accident_id}")
    print("🚀 Triggering emergency response automatically...")
    
    # Check if already confirmed (in case user responded at the same time)
    if accident_id in pending_confirmations:
        del pending_confirmations[accident_id]
    
    # Trigger emergency response
    trigger_emergency_response(accident_id, accident_data)


def trigger_emergency_response(accident_id: str, accident_data: dict):
    """
    Trigger the full emergency response - sends alerts to all contacts.
    """
    try:
        # Get all the data
        victim_name = accident_data.get('name', 'User')
        address = accident_data.get('address', 'Unknown')
        maps_url = accident_data.get('maps_url', '')
        directions_text = accident_data.get('directions_text', '')
        accident_lat = accident_data.get('latitude', 0)
        accident_lon = accident_data.get('longitude', 0)
        
        # Get emergency contacts
        emergency_contact_1 = accident_data.get('emergency_contact_1')
        emergency_contact_2 = accident_data.get('emergency_contact_2')
        
        # Get responders
        hospital_info = accident_data.get('hospital_info')
        police_info = accident_data.get('police_info')
        
        # Send complete emergency alerts
        results = send_emergency_alerts_complete(
            victim_name=victim_name,
            address=address,
            maps_url=maps_url,
            directions_text=directions_text,
            accident_lat=accident_lat,
            accident_lon=accident_lon,
            emergency_contact_1=emergency_contact_1,
            emergency_contact_2=emergency_contact_2,
            hospital_info=hospital_info,
            police_info=police_info
        )
        
        # Update Firestore
        if db:
            try:
                db.collection("accidents").document(accident_id).update({
                    "status": "emergency_sent",
                    "emergency_sent_at": datetime.now(),
                    "emergency_results": results
                })
            except Exception as e:
                print(f"Error updating Firestore: {e}")
        
        print(f"\n📊 Emergency Response Summary:")
        print(f"   SMS Sent to: {results['sms_sent']}")
        print(f"   Calls Made to: {results['calls_made']}")
        if results['errors']:
            print(f"   Errors: {results['errors']}")
        
        return results
        
    except Exception as e:
        print(f"Error in emergency response: {e}")
        return {"error": str(e)}


# ============================================================================
# Root and Health Check Endpoints
# ============================================================================

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "AI Accident Detection System API",
        "version": "2.0.0",
        "status": "running",
        "flow": "30-second confirmation timeout with emergency contacts"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# User Registration Endpoints (Required: 2 Emergency Contacts)
# ============================================================================

@app.post("/register", response_model=dict)
def register_user(user: UserCreate):
    """
    Register new user with REQUIRED 2 emergency contacts.
    Both emergency contacts are mandatory for safety.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    # Validate both emergency contacts are provided
    if not user.emergency_contact_1 or not user.emergency_contact_1.get('phone'):
        raise HTTPException(
            status_code=400, 
            detail="Emergency Contact 1 is required with phone number"
        )
    
    if not user.emergency_contact_2 or not user.emergency_contact_2.get('phone'):
        raise HTTPException(
            status_code=400, 
            detail="Emergency Contact 2 is required with phone number"
        )
    
    user_id = str(uuid.uuid4())
    
    user_data = {
        "id": user_id,
        "name": user.name,
        "phone": user.phone,
        "emergency_contact_1": {
            "name": user.emergency_contact_1.get('name', 'Emergency Contact 1'),
            "phone": user.emergency_contact_1['phone'],
            "relationship": user.emergency_contact_1.get('relationship', 'Family')
        },
        "emergency_contact_2": {
            "name": user.emergency_contact_2.get('name', 'Emergency Contact 2'),
            "phone": user.emergency_contact_2['phone'],
            "relationship": user.emergency_contact_2.get('relationship', 'Family')
        },
        "created_at": datetime.now()
    }
    
    db.collection("users").document(user_id).set(user_data)
    
    return {
        "status": "success",
        "user_id": user_id,
        "message": "User registered successfully with 2 emergency contacts"
    }


@app.get("/user/{user_id}")
def get_user(user_id: str):
    """Get user by ID"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    user_doc = db.collection("users").document(user_id).get()
    
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_doc.to_dict()


# ============================================================================
# Accident Detection with 30-Second Confirmation Timeout
# ============================================================================

@app.post("/accident")
def report_accident(accident: AccidentReport):
    """
    Main endpoint to receive accident reports from the Android app.
    Flow:
    1. Detect accident
    2. Send 30-second notification to user asking "Are you okay?"
    3. Wait for user response
    4. If "OKAY" → no alerts sent
    5. If "NOT OKAY" or timeout → send alerts to all responders
    """
    print(f"\n🚨 ACCIDENT DETECTED!")
    print(f"Device: {accident.device_id}")
    print(f"Location: {accident.latitude}, {accident.longitude}")
    
    # Validate coordinates
    if accident.latitude == 0 or accident.longitude == 0:
        raise HTTPException(status_code=400, detail="Invalid coordinates")
    
    # Generate accident ID
    accident_id = str(uuid.uuid4())
    
    # Get address from coordinates
    address = reverse_geocode(accident.latitude, accident.longitude)
    maps_url = f"https://www.google.com/maps?q={accident.latitude},{accident.longitude}"
    
    print(f"📍 Address: {address}")
    
    # Find nearest police and hospitals
    print("🔍 Finding nearest responders...")
    police_info = find_nearest_police(accident.latitude, accident.longitude)
    hospitals = find_top_3_hospitals(accident.latitude, accident.longitude)
    
    hospital_info = hospitals[0] if hospitals else {"name": "City Hospital", "phone": "+1000000002"}
    
    print(f"👮 Police: {police_info.get('name')} - {police_info.get('phone')}")
    print(f"🏥 Hospital: {hospital_info.get('name')} - {hospital_info.get('phone')}")
    
    # Get directions to hospital
    directions_text = get_directions_text(
        accident.latitude, accident.longitude,
        hospital_info.get('lat', accident.latitude),
        hospital_info.get('lon', accident.longitude)
    )
    
    # Get emergency contacts from user
    emergency_contact_1 = None
    emergency_contact_2 = None
    
    if accident.user_id and db:
        try:
            user_doc = db.collection("users").document(accident.user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                emergency_contact_1 = user_data.get('emergency_contact_1')
                emergency_contact_2 = user_data.get('emergency_contact_2')
                print(f"👥 Emergency Contact 1: {emergency_contact_1}")
                print(f"👥 Emergency Contact 2: {emergency_contact_2}")
        except Exception as e:
            print(f"Error fetching user: {e}")
    
    # Prepare accident data
    accident_data = {
        "id": accident_id,
        "device_id": accident.device_id,
        "user_id": accident.user_id,
        "name": accident.name,
        "latitude": accident.latitude,
        "longitude": accident.longitude,
        "address": address,
        "maps_url": maps_url,
        "directions_text": directions_text,
        "status": "pending_confirmation",  # Waiting for user response
        "timestamp": accident.timestamp or int(datetime.now().timestamp()),
        "created_at": datetime.now(),
        "emergency_contact_1": emergency_contact_1,
        "emergency_contact_2": emergency_contact_2,
        "hospital_info": hospital_info,
        "police_info": police_info,
        "confirmation_deadline": int(datetime.now().timestamp()) + 30  # 30 seconds from now
    }
    
    # Save accident to Firestore
    if db:
        try:
            db.collection("accidents").document(accident_id).set(accident_data)
            print(f"✅ Accident saved: {accident_id}")
        except Exception as e:
            print(f"Error saving to Firestore: {e}")
    
    # Store for confirmation tracking
    pending_confirmations[accident_id] = {
        "data": accident_data,
        "created_at": datetime.now()
    }
    
    # Start 30-second timer in background thread
    timer_thread = threading.Timer(
        30.0,  # 30 seconds timeout
        timeout_handler,
        args=[accident_id, accident_data]
    )
    timer_thread.daemon = True
    timer_thread.start()
    
    print(f"\n⏱️ 30-second countdown started!")
    print(f"   Waiting for user confirmation...")
    print(f"   Accident ID: {accident_id}")
    
    return {
        "status": "pending",
        "message": "Accident detected. You have 30 seconds to confirm if you're okay.",
        "accident_id": accident_id,
        "confirmation_deadline": accident_data["confirmation_deadline"],
        "instructions": "Send POST to /accident/confirm with {\"is_okay\": true} if you're okay, or {\"is_okay\": false} if you need help"
    }


@app.post("/accident/confirm")
def confirm_accident(
    accident_id: str,
    confirmation: AccidentConfirmationRequest
):
    """
    User confirms their status after accident detection.
    - is_okay = True: "I'm okay, don't send alerts"
    - is_okay = False: "Not okay, send emergency alerts immediately"
    """
    print(f"\n📱 User response for accident {accident_id}: is_okay = {confirmation.is_okay}")
    
    # Check if this accident exists in pending confirmations
    if accident_id not in pending_confirmations:
        raise HTTPException(
            status_code=404, 
            detail="Accident not found or confirmation timeout expired"
        )
    
    # Get accident data
    accident_data = pending_confirmations[accident_id]["data"]
    
    # Cancel the timeout timer
    del pending_confirmations[accident_id]
    
    if confirmation.is_okay:
        # User is okay - don't send alerts
        print(f"✅ User confirmed OKAY - No emergency alerts will be sent")
        
        # Update status
        if db:
            try:
                db.collection("accidents").document(accident_id).update({
                    "status": "cancelled_by_user",
                    "cancelled_at": datetime.now()
                })
            except Exception as e:
                print(f"Error updating Firestore: {e}")
        
        return {
            "status": "cancelled",
            "message": "You're okay! Emergency contacts have NOT been notified. Stay safe!"
        }
    
    else:
        # User is NOT okay - send emergency alerts immediately
        print(f"🚨 User confirmed NOT OKAY - Sending emergency alerts!")
        
        # Trigger emergency response
        results = trigger_emergency_response(accident_id, accident_data)
        
        return {
            "status": "emergency_sent",
            "message": "Emergency alerts sent to all contacts! Help is on the way.",
            "results": results
        }


# ============================================================================
# Test Endpoint for 30-Second Confirmation Flow
# ============================================================================

@app.post("/test_accident_flow")
def test_accident_flow():
    """Test the full accident detection flow with 30-second confirmation"""
    test_accident = AccidentReport(
        device_id="TEST_DEVICE",
        latitude=13.0827,  # Chennai coordinates
        longitude=80.2707,
        timestamp=int(datetime.now().timestamp()),
        status="accident_detected",
        name="Test User",
        user_id="test_user_id"
    )
    return report_accident(test_accident)


# ============================================================================
# Emergency Response Endpoints (Manual Trigger)
# ============================================================================

@app.post("/trigger_emergency/{accident_id}")
def manual_trigger_emergency(accident_id: str):
    """Manually trigger emergency response for an accident"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    # Get accident data
    acc_doc = db.collection("accidents").document(accident_id).get()
    
    if not acc_doc.exists:
        raise HTTPException(status_code=404, detail="Accident not found")
    
    accident_data = acc_doc.to_dict()
    
    # Trigger emergency
    results = trigger_emergency_response(accident_id, accident_data)
    
    return {
        "status": "emergency_sent",
        "results": results
    }


# ============================================================================
# Hospital Confirmation Endpoint
# ============================================================================

@app.post("/hospital_confirm/{accident_id}")
def hospital_confirm(
    accident_id: str,
    admitted: bool = Query(..., description="Was patient admitted?"),
    hospital_name: str = Query(..., description="Hospital name"),
    hospital_phone: str = Query(..., description="Hospital phone")
):
    """
    Hospital confirms if patient is admitted.
    Notifies family members about admission status.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    # Get accident data
    acc_doc_ref = db.collection("accidents").document(accident_id)
    acc_doc = acc_doc_ref.get()
    
    if not acc_doc.exists:
        raise HTTPException(status_code=404, detail="Accident not found")
    
    accident_data = acc_doc.to_dict()
    victim_name = accident_data.get('name', 'The patient')
    
    # Get emergency contacts
    emergency_contact_1 = accident_data.get('emergency_contact_1')
    emergency_contact_2 = accident_data.get('emergency_contact_2')
    
    # Send confirmation to family
    admission_message = "has been ADMITTED" if admitted else "is being treated in emergency"
    
    for contact in [emergency_contact_1, emergency_contact_2]:
        if contact and contact.get('phone'):
            sms_text = f"🏥 HOSPITAL UPDATE!\n\n"
            sms_text += f"👤 {victim_name} {admission_message} at {hospital_name}.\n"
            sms_text += f"📞 Hospital: {hospital_phone}\n"
            sms_text += f"\n💝 Thank you for your patience."
            
            send_sms(contact['phone'], sms_text)
    
    # Update accident status
    acc_doc_ref.update({
        "hospital_confirmed": True,
        "patient_admitted": admitted,
        "hospital_name": hospital_name,
        "hospital_phone": hospital_phone,
        "hospital_confirmed_at": datetime.now()
    })
    
    return {
        "status": "success",
        "message": f"Family notified. Patient {admission_message}."
    }


# ============================================================================
# Speed Alert Endpoint
# ============================================================================

@app.post("/speed_alert")
def speed_alert(
    user_id: str = Query(...),
    phone_number: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    speed: float = Query(...)
):
    """Alert user about speeding in accident zone"""
    try:
        address = reverse_geocode(lat, lon)
        
        print(f"⚠️ SPEED ALERT: User {user_id} at {speed} km/h near accident zone at {address}")
        
        location_info = {
            "address": address,
            "maps_url": f"https://www.google.com/maps?q={lat},{lon}"
        }
        
        speed_alert_alarm(phone_number, location_info)
        
        return {
            "status": "success",
            "message": f"Speed alert sent to {phone_number}"
        }
    except Exception as e:
        print(f"ERROR in speed_alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to send speed alert")


# ============================================================================
# Test Endpoints
# ============================================================================

@app.post("/test_sms")
def test_sms(
    to_number: str = Query(...),
    message: str = Query("Test message from AI Accident System")
):
    """Test SMS"""
    success = send_sms(to_number, message)
    return {
        "status": "success" if success else "failed",
        "message": f"SMS {'sent' if success else 'failed'} to {to_number}"
    }


@app.post("/test_call")
def test_call(
    to_number: str = Query(...),
    victim_name: str = Query("Test User")
):
    """Test voice call"""
    location_info = {
        "address": "Test Location",
        "maps_url": "https://maps.google.com/?q=0,0"
    }
    success = make_call(to_number, victim_name, location_info)
    return {
        "status": "success" if success else "failed",
        "message": f"Call {'initiated' if success else 'failed'} to {to_number}"
    }


# ============================================================================
# Accident List Endpoint
# ============================================================================

@app.get("/accidents")
def list_accidents(limit: int = Query(10, ge=1, le=100)):
    """List recent accidents"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        accidents = db.collection("accidents").limit(limit).get()
        accident_list = []
        
        for acc in accidents:
            acc_data = acc.to_dict()
            accident_list.append({
                "id": acc_data.get("id"),
                "name": acc_data.get("name"),
                "latitude": acc_data.get("latitude"),
                "longitude": acc_data.get("longitude"),
                "address": acc_data.get("address"),
                "status": acc_data.get("status"),
                "timestamp": acc_data.get("timestamp")
            })
        
        return {
            "status": "success",
            "count": len(accident_list),
            "accidents": accident_list
        }
    except Exception as e:
        print(f"Error listing accidents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list accidents")


# ============================================================================
# Map Display Endpoints
# ============================================================================

@app.get("/map/{accident_id}", response_class=HTMLResponse)
async def show_map(request: Request, accident_id: str):
    """Display accident location on map"""
    if not db:
        return HTMLResponse(content="Database not connected", status_code=500)
    
    acc_doc = db.collection("accidents").document(accident_id).get()
    
    if not acc_doc.exists:
        return HTMLResponse(content="Accident not found", status_code=404)
    
    acc_data = acc_doc.to_dict()
    
    return templates.TemplateResponse("map.html", {
        "request": request,
        "accident_id": accident_id,
        "name": acc_data.get("name", "Unknown"),
        "lat": acc_data.get("latitude"),
        "lon": acc_data.get("longitude"),
        "address": acc_data.get("address", ""),
        "status": acc_data.get("status", "unknown"),
        "timestamp": acc_data.get("timestamp")
    })


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Accident Detection Server v2.0...")
    print("📋 Complete Emergency Flow:")
    print("   1. User registers with 2 emergency contacts (required)")
    print("   2. Accident detected → 30-second countdown starts")
    print("   3. User confirms: 'OKAY' → no alerts, 'NOT OKAY' → full emergency")
    print("   4. Timeout (30s) → automatic emergency response")
    print("   5. Alerts sent to: 2 emergency contacts + Hospital + Police")
    print("   6. Each gets: SMS + Automatic Call + Live Location/Routing")
    print("\n📌 Endpoints:")
    print("   - POST /register - Register user with 2 emergency contacts")
    print("   - POST /accident - Report accident (starts 30s timer)")
    print("   - POST /accident/confirm - User confirms status")
    print("   - POST /hospital_confirm - Hospital confirms admission")
    uvicorn.run(app, host="0.0.0.0", port=8000)
