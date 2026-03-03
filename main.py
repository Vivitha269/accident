import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from firebase_admin import firestore
from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local imports
from config import db
from twilio_config import (
    send_sms, make_call, play_alarm, speed_alert_alarm,
    send_sms_to_family, send_sms_to_police, send_sms_to_hospital,
    send_pickup_confirmation, send_hospital_confirmation, send_hospital_acknowledgment
)
from services.places import find_nearest_police, find_top_3_hospitals
from services.geocoding import reverse_geocode
from services.routing import get_route, get_directions_text

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================================
# Pydantic Models
# ============================================================================

class AccidentReport(BaseModel):
    """Pydantic model for accident reporting with validation."""
    userId: str
    name: str
    lat: float
    lon: float

    @field_validator('lat')
    @classmethod
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('lon')
    @classmethod
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class LocationQuery(BaseModel):
    """Pydantic model for location queries with validation."""
    lat: float
    lon: float

    @field_validator('lat')
    @classmethod
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('lon')
    @classmethod
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/")
@app.head("/")
def home():
    """Health check for Render."""
    return {"status": "Accident Detection API Live", "mode": "Full API"}


# ============================================================================
# Accident Reporting Endpoints
# ============================================================================

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
            "latitude": report.lat,
            "longitude": report.lon,
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


@app.post("/trigger_alerts/{accident_id}")
def trigger_all_alerts(accident_id: str):
    """
    This function is called by the Android app after its internal delay.
    It fetches all data itself and triggers all alerts.
    """
    print(f"--- Triggering alerts for accident_id: {accident_id} ---")

    try:
        # 1. Retrieve Accident Data from Firestore
        acc_doc_ref = db.collection("accidents").document(accident_id)
        acc_doc = acc_doc_ref.get()
        if not acc_doc.exists:
            print(f"ERROR: Accident ID {accident_id} not found.")
            raise HTTPException(status_code=404, detail="Accident record not found")

        acc_data = acc_doc.to_dict()
        acc_doc_ref.update({"status": "active"}) # Mark as active
        
        # Prepare message with actual address
        victim_name = acc_data.get('name', 'A user')
        lat = acc_data['latitude']
        lon = acc_data['longitude']
        
        # Get human-readable address
        address = reverse_geocode(lat, lon)
        location_url = f"https://www.google.com/maps?q={lat},{lon}"
        
        # SMS with full address + Google Maps link
        sms_text = f"🚨 EMERGENCY! {victim_name} has been in an accident.\n📍 Address: {address}\n🗺️ Maps: {location_url}"
        
        # Location info for voice calls
        location_info = {
            "address": address,
            "maps_url": location_url
        }
        
        # 2. Get Responders from Overpass API (real locations)
        hospital = find_top_3_hospitals(acc_data['latitude'], acc_data['longitude'])[0]
        police = find_nearest_police(acc_data['latitude'], acc_data['longitude'])

        # 2.a Compute directions text for messages (limit to a few steps)
        try:
            directions_to_hospital = get_directions_text(lat, lon, hospital.get('lat'), hospital.get('lon'))
        except Exception:
            directions_to_hospital = None

        try:
            directions_to_police = get_directions_text(lat, lon, police.get('lat'), police.get('lon'))
        except Exception:
            directions_to_police = None

        # 3. Notify Family (from Firestore)
        try:
            user_doc = db.collection("users").document(acc_data['userId']).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                print(f"DEBUG: User data retrieved: {user_data}")
                
                # Handle different contact data formats
                contacts_raw = user_data.get("emergencyContacts", [])
                print(f"DEBUG: Raw contacts data: {contacts_raw} (type: {type(contacts_raw)})")
                
                # Parse contacts based on data structure
                contacts: List[Dict[str, str]] = []
                
                if isinstance(contacts_raw, list):
                    for item in contacts_raw:
                        if isinstance(item, dict):
                            contacts.append(item)
                        elif isinstance(item, str):
                            # Handle case where contacts are stored as strings
                            print(f"WARNING: Contact as string (old format): {item}")
                            if item.startswith('+'):
                                contacts.append({"phone": item, "name": "Emergency Contact"})
                        else:
                            print(f"WARNING: Unknown contact format: {item}")
                elif isinstance(contacts_raw, dict):
                    # Handle single contact as dict
                    contacts.append(contacts_raw)
                
                print(f"DEBUG: Parsed contacts: {contacts}")
                print(f"Found {len(contacts)} emergency contacts.")
                
                for i, contact_map in enumerate(contacts):
                    print(f"DEBUG: Processing contact {i}: {contact_map} (type: {type(contact_map)})")
                    
                    # Try different key names for phone
                    phone_number = (contact_map.get("phone") or 
                                   contact_map.get("phoneNumber") or 
                                   contact_map.get("mobile") or
                                   contact_map.get("telephone"))
                    
                    if phone_number:
                        print(f"   - Alerting family contact at {phone_number}")
                        # Send enhanced SMS with routing to hospital and hospital info
                        try:
                            send_sms_to_family(
                                phone_number,
                                victim_name,
                                address,
                                location_url,
                                directions_to_hospital,
                                hospital.get('name'),
                                hospital.get('phone')
                            )
                        except Exception as e:
                            print(f"Warning: send_sms_to_family failed for {phone_number}: {e}")

                        # Also place a short voice call summarizing the situation
                        try:
                            make_call(phone_number, victim_name, location_info)
                        except Exception as e:
                            print(f"Warning: make_call failed for family {phone_number}: {e}")
                    else:
                        print(f"   - WARNING: Contact map without valid phone key: {contact_map}")
            else:
                print(f"WARNING: User document for userId {acc_data['userId']} not found.")
        except Exception as e:
            print(f"ERROR during family alert notifications: {e}")
            import traceback
            traceback.print_exc()

        # 4. Notify Police (from Overpass API)
        try:
            police_phone = police.get('phone')
            print(f"   - Alerting police at {police_phone}")
            police_address = police.get('address', 'Unknown police station')
            try:
                send_sms_to_police(
                    police_phone,
                    victim_name,
                    address,
                    location_url,
                    directions_to_police,
                    lat,
                    lon
                )
            except Exception as e:
                print(f"Warning: send_sms_to_police failed: {e}")

            try:
                make_call(police_phone, victim_name, location_info)
            except Exception as e:
                print(f"Warning: make_call to police failed: {e}")
        except Exception as e:
            print(f"ERROR during police alert notification: {e}")

        # 5. Notify Hospital (from Overpass API)
        try:
            hospital_phone = hospital.get('phone')
            print(f"   - Alerting hospital at {hospital_phone}")
            hospital_address = hospital.get('address', 'Unknown hospital')
            try:
                send_sms_to_hospital(
                    hospital_phone,
                    victim_name,
                    address,
                    location_url,
                    directions_to_hospital,
                    police
                )
            except Exception as e:
                print(f"Warning: send_sms_to_hospital failed: {e}")

            try:
                make_call(hospital_phone, victim_name, location_info)
            except Exception as e:
                print(f"Warning: make_call to hospital failed: {e}")
        except Exception as e:
            print(f"ERROR during hospital alert notification: {e}")

        print(f"--- Process completed successfully for {accident_id} ---")
        return {"message": "All alerts processed successfully."}

    except Exception as e:
        print(f"FATAL ERROR in trigger_all_alerts: {e}")
        # This will catch any other unexpected errors and prevent a crash
        raise HTTPException(status_code=500, detail="An internal server error occurred during alert processing.")


@app.post("/accept_emergency/{accident_id}")
def accept_emergency(accident_id: str, hospital_name: str):
    """
    Called when emergency responder accepts the accident.
    Updates the accident status and notifies the victim.
    """
    # Input validation
    if not hospital_name or len(hospital_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Invalid hospital name")

    try:
        # Get accident data
        acc_doc_ref = db.collection("accidents").document(accident_id)
        acc_doc = acc_doc_ref.get()

        if not acc_doc.exists:
            raise HTTPException(status_code=404, detail="Accident record not found")

        acc_data = acc_doc.to_dict()
        victim_name = acc_data.get('name', 'A user')
        victim_phone = acc_data.get('phone', None)  # Assuming phone is stored

        # Update accident status
        acc_doc_ref.update({
            "status": "dispatched",
            "hospital_name": hospital_name,
            "dispatch_timestamp": firestore.SERVER_TIMESTAMP
        })

        print(f" Emergency accepted for {accident_id}. Dispatching: {hospital_name}")

        # Notify victim if phone available
        if victim_phone:
            location_url = f"https://www.google.com/maps?q={acc_data['latitude']},{acc_data['longitude']}"
            sms_text = f"Good news! {hospital_name} is dispatched to help you. Location: {location_url}"
            try:
                send_sms(victim_phone, sms_text)
            except Exception as e:
                print(f"Warning: Could not notify victim: {e}")

        return {
            "status": "success",
            "accident_id": accident_id,
            "hospital": hospital_name,
            "message": f"Ambulance from {hospital_name} has been dispatched."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in accept_emergency: {e}")
        raise HTTPException(status_code=500, detail="Failed to process emergency acceptance.")


# ============================================================================
# Location and Map Endpoints
# ============================================================================

@app.get("/accident")
def accident(
    lat: float = Query(..., description="Latitude of the accident location", ge=-90, le=90),
    lon: float = Query(..., description="Longitude of the accident location", ge=-180, le=180)
):
    """Get accident location details, nearest hospital, and route."""
    try:
        address = reverse_geocode(lat, lon)
        hospitals = find_top_3_hospitals(lat, lon)
        hospital = hospitals[0]
        route = get_route(lat, lon, hospital["lat"], hospital["lon"])

        return {
            "accident_location": address,
            "nearest_hospital": hospital,
            "alternative_hospitals": hospitals[1:],
            "route": route
        }
    except Exception as e:
        logger.error(f"Error in accident endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to process accident data")


@app.get("/map", response_class=HTMLResponse)
def show_map(request: Request, lat: float, lon: float, accident_id: str = None, name: str = "Unknown", status: str = "pending"):
    """Show map with accident location."""
    # Validate coordinates
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    return templates.TemplateResponse(
        "map.html",
        {
            "request": request,
            "lat": lat,
            "lon": lon,
            "accident_id": accident_id or "",
            "name": name,
            "status": status
        }
    )


# ============================================================================
# Speed Alert Endpoints
# ============================================================================

@app.post("/speed_alert")
def speed_alert(
    user_id: str = Query(..., description="User ID"),
    phone_number: str = Query(..., description="Phone number to alert"),
    lat: float = Query(..., description="Latitude of accident zone", ge=-90, le=90),
    lon: float = Query(..., description="Longitude of accident zone", ge=-180, le=180),
    speed: float = Query(..., description="Current speed in km/h")
):
    """
    Alert a user when they are speeding through an accident zone.
    Triggers an alarm call to warn them about the accident zone.
    """
    try:
        # Get address of the accident zone
        address = reverse_geocode(lat, lon)
        
        print(f"⚠️ SPEED ALERT: User {user_id} at {speed} km/h near accident zone at {address}")
        
        # Prepare location info for the alert
        location_info = {
            "address": address,
            "maps_url": f"https://www.google.com/maps?q={lat},{lon}"
        }
        
        # Trigger speed alert alarm call
        speed_alert_alarm(phone_number, location_info)
        
        return {
            "status": "success",
            "message": f"Speed alert sent to {phone_number}. Warning about accident zone at {address}",
            "zone_location": address,
            "detected_speed": speed
        }
        
    except Exception as e:
        print(f"ERROR in speed_alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to send speed alert")


@app.post("/trigger_alarm/{accident_id}")
def trigger_alarm(accident_id: str):
    """
    Trigger emergency alarm for an accident to alert everyone nearby.
    """
    try:
        # Get accident data
        acc_doc_ref = db.collection("accidents").document(accident_id)
        acc_doc = acc_doc_ref.get()
        
        if not acc_doc.exists:
            raise HTTPException(status_code=404, detail="Accident record not found")
        
        acc_data = acc_doc.to_dict()
        victim_name = acc_data.get('name', 'A user')
        lat = acc_data['latitude']
        lon = acc_data['longitude']
        
        # Get address
        address = reverse_geocode(lat, lon)
        location_url = f"https://www.google.com/maps?q={lat},{lon}"
        
        location_info = {
            "address": address,
            "maps_url": location_url
        }
        
        # Get responders
        hospital = find_top_3_hospitals(lat, lon)[0]
        police = find_nearest_police(lat, lon)
        
        # Trigger alarm to all responders
        play_alarm(police['phone'], victim_name, location_info)
        play_alarm(hospital['phone'], victim_name, location_info)
        
        # Update accident status
        acc_doc_ref.update({
            "alarm_triggered": True,
            "alarm_timestamp": firestore.SERVER_TIMESTAMP
        })
        
        print(f"🚨 ALARM TRIGGERED for accident {accident_id}")
        
        return {
            "status": "success",
            "message": "Emergency alarm triggered to all responders",
            "accident_id": accident_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in trigger_alarm: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger alarm")


# ============================================================================
# Ambulance Pickup Confirmation Endpoints
# ============================================================================

@app.post("/confirm_pickup/{accident_id}")
def confirm_pickup(
    accident_id: str,
    hospital_name: str = Query(..., description="Hospital name"),
    hospital_phone: str = Query(..., description="Hospital phone number")
):
    """
    Confirm that ambulance has picked up the victim.
    Sends confirmation SMS to family and updates accident status.
    """
    try:
        # Get accident data
        acc_doc_ref = db.collection("accidents").document(accident_id)
        acc_doc = acc_doc_ref.get()
        
        if not acc_doc.exists:
            raise HTTPException(status_code=404, detail="Accident record not found")
        
        acc_data = acc_doc.to_dict()
        victim_name = acc_data.get('name', 'A user')
        user_id = acc_data.get('userId')
        lat = acc_data['latitude']
        lon = acc_data['longitude']
        
        # Get address
        address = reverse_geocode(lat, lon)
        location_url = f"https://www.google.com/maps?q={lat},{lon}"
        
        # Update accident status
        acc_doc_ref.update({
            "status": "picked_up",
            "pickup_timestamp": firestore.SERVER_TIMESTAMP,
            "hospital_name": hospital_name,
            "hospital_phone": hospital_phone
        })
        
        # Get user and notify family
        if user_id:
            try:
                user_doc = db.collection("users").document(user_id).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    contacts_raw = user_data.get("emergencyContacts", [])
                    
                    # Parse contacts
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
                    
                    # Send pickup confirmation to all family contacts
                    for contact_map in contacts:
                        phone_number = (contact_map.get("phone") or 
                                      contact_map.get("phoneNumber") or 
                                      contact_map.get("mobile") or
                                      contact_map.get("telephone"))
                        
                        if phone_number:
                            send_pickup_confirmation(
                                phone_number, 
                                victim_name, 
                                hospital_name, 
                                address, 
                                location_url
                            )
                            
            except Exception as e:
                print(f"ERROR sending pickup confirmation to family: {e}")
        
        print(f"✅ PICKUP CONFIRMED for accident {accident_id} by {hospital_name}")
        
        return {
            "status": "success",
            "message": "Ambulance pickup confirmed. Family notified.",
            "accident_id": accident_id,
            "hospital": hospital_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in confirm_pickup: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm pickup")


# ============================================================================
# Hospital Confirmation Endpoints (NEW)
# ============================================================================

@app.post("/hospital_confirm/{accident_id}")
def hospital_confirm(
    accident_id: str,
    hospital_name: str = Query(..., description="Name of selected hospital"),
    hospital_phone: str = Query(..., description="Phone number of selected hospital")
):
    """
    Confirm that a hospital has been selected/picked for the accident.
    Saves the hospital info to Firebase and sends confirmation SMS to family.
    
    This is called when the user/hospital selects which hospital will respond.
    """
    # Input validation
    if not hospital_name or len(hospital_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Invalid hospital name")
    
    if not hospital_phone:
        raise HTTPException(status_code=400, detail="Invalid hospital phone")
    
    try:
        # Get accident data
        acc_doc_ref = db.collection("accidents").document(accident_id)
        acc_doc = acc_doc_ref.get()
        
        if not acc_doc.exists:
            raise HTTPException(status_code=404, detail="Accident record not found")
        
        acc_data = acc_doc.to_dict()
        victim_name = acc_data.get('name', 'A user')
        user_id = acc_data.get('userId')
        lat = acc_data['latitude']
        lon = acc_data['longitude']
        
        # Get address
        address = reverse_geocode(lat, lon)
        location_url = f"https://www.google.com/maps?q={lat},{lon}"
        
        # Update accident with confirmed hospital info
        acc_doc_ref.update({
            "hospital_confirmed": True,
            "hospital_confirmed_timestamp": firestore.SERVER_TIMESTAMP,
            "hospital_name": hospital_name,
            "hospital_phone": hospital_phone
        })
        
        print(f"🏥 HOSPITAL CONFIRMED for accident {accident_id}: {hospital_name}")
        
        # Send confirmation SMS to family
        if user_id:
            try:
                user_doc = db.collection("users").document(user_id).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    contacts_raw = user_data.get("emergencyContacts", [])
                    
                    # Parse contacts
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
                    
                    # Send hospital confirmation to all family contacts
                    for contact_map in contacts:
                        phone_number = (contact_map.get("phone") or 
                                      contact_map.get("phoneNumber") or 
                                      contact_map.get("mobile") or
                                      contact_map.get("telephone"))
                        
                        if phone_number:
                            try:
                                send_hospital_confirmation(
                                    phone_number,
                                    victim_name,
                                    hospital_name,
                                    hospital_phone,
                                    address,
                                    location_url
                                )
                            except Exception as e:
                                print(f"Warning: send_hospital_confirmation failed: {e}")
                    
                    print(f"✅ Hospital confirmation SMS sent to family for accident {accident_id}")
                            
            except Exception as e:
                print(f"ERROR sending hospital confirmation to family: {e}")
        
        # Send acknowledgment SMS to hospital
        try:
            send_hospital_acknowledgment(
                hospital_phone,
                victim_name,
                address,
                location_url
            )
            print(f"✅ Hospital acknowledgment SMS sent to {hospital_name}")
        except Exception as e:
            print(f"Warning: send_hospital_acknowledgment failed: {e}")
        
        return {
            "status": "success",
            "message": f"Hospital {hospital_name} confirmed. Family notified.",
            "accident_id": accident_id,
            "hospital": {
                "name": hospital_name,
                "phone": hospital_phone
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in hospital_confirm: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm hospital")


@app.get("/hospital_status/{accident_id}")
def hospital_status(accident_id: str):
    """
    Get the hospital confirmation status for an accident.
    Returns whether a hospital has been confirmed and the hospital details.
    """
    try:
        # Get accident data
        acc_doc_ref = db.collection("accidents").document(accident_id)
        acc_doc = acc_doc_ref.get()
        
        if not acc_doc.exists:
            raise HTTPException(status_code=404, detail="Accident record not found")
        
        acc_data = acc_doc.to_dict()
        
        # Check if hospital is confirmed
        hospital_confirmed = acc_data.get('hospital_confirmed', False)
        
        # Get hospital info if confirmed
        hospital_info = None
        if hospital_confirmed:
            hospital_info = {
                "name": acc_data.get('hospital_name'),
                "phone": acc_data.get('hospital_phone'),
                "confirmed_at": acc_data.get('hospital_confirmed_timestamp')
            }
        
        return {
            "accident_id": accident_id,
            "hospital_confirmed": hospital_confirmed,
            "hospital": hospital_info,
            "accident_status": acc_data.get('status', 'unknown')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in hospital_status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get hospital status")

