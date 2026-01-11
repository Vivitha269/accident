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
from twilio_config import send_sms, make_call
from services.places import find_nearest_police, find_top_3_hospitals
from services.geocoding import reverse_geocode
from services.routing import get_route

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
        
        # Prepare message and location URL
        victim_name = acc_data.get('name', 'A user')
        location_url = f"https://www.google.com/maps?q={acc_data['latitude']},{acc_data['longitude']}"
        sms_text = f"EMERGENCY! {victim_name} has been in an accident. Location: {location_url}"
        
        # 2. Get Hardcoded Responders (No external API call)
        hospital = find_top_3_hospitals(acc_data['latitude'], acc_data['longitude'])[0]
        police = find_nearest_police(acc_data['latitude'], acc_data['longitude'])

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
                        send_sms(phone_number, sms_text)
                        make_call(phone_number, victim_name)
                    else:
                        print(f"   - WARNING: Contact map without valid phone key: {contact_map}")
            else:
                print(f"WARNING: User document for userId {acc_data['userId']} not found.")
        except Exception as e:
            print(f"ERROR during family alert notifications: {e}")
            import traceback
            traceback.print_exc()

        # 4. Notify Police (Hardcoded Mobile)
        try:
            print(f"   - Alerting police at {police['phone']}")
            send_sms(police['phone'], f"POLICE ALERT: {sms_text}")
            make_call(police['phone'], victim_name)
        except Exception as e:
            print(f"ERROR during police alert notification: {e}")

        # 5. Notify Hospital (Hardcoded Mobile)
        try:
            print(f"   - Alerting hospital at {hospital['phone']}")
            send_sms(hospital['phone'], f"HOSPITAL ALERT: {sms_text}")
            make_call(hospital['phone'], victim_name)
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

        print(f"✅ Emergency accepted for {accident_id}. Dispatching: {hospital_name}")

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

