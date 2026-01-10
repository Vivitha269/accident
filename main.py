from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from config import db
from twilio_config import send_sms, make_call
from firebase_admin import messaging, firestore
from services.places import find_top_3_hospitals, find_nearest_police
import requests
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Mount static folder for map.html
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

def _query_overpass(query: str):
    """Internal helper to fetch junction data for prevention."""
    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data=query)
    return response.json()

# --- 1. REGISTRATION ---
@app.post("/register_device")
def register_device(userId: str, token: str):
    """Saves notification token to Firestore."""
    db.collection("users").document(userId).set({
        "deviceTokens": firestore.ArrayUnion([token]),
        "prevention_enabled": True
    }, merge=True)
    return {"message": "Registered"}
#define JSON model for contacts
class ContactUpdate(BaseModel):
    Contacts :List[str]
@app.post("/contacts")
def add_contacts(userId: str, data:ContactUpdate):
    """Saves emergency contact numbers."""
    user_ref=db.collection("users").document(userId)
    user_ref.update({"emergencyContacts": data.Contacts})
    return {"message": f" Successfully Emergyency Contacts {len(data.Contacts)} added for {userId}"}

# --- 2. ACCIDENT FLOW ---
@app.post("/accident")
async def accident_report(userId: str, name: str, lat: float, lon: float):
    """Creates accident record with safety check for user existence."""
    user_doc = db.collection("users").document(userId).get()
    if not user_doc.exists:
        return {"error": "User not found. Register first."}
    
    acc_ref = db.collection("accidents").add({
        "userId": userId, "name": name, "latitude": lat, "longitude": lon,
        "status": "awaiting_confirmation", "timestamp": firestore.SERVER_TIMESTAMP
    })
    return {"accidentId": acc_ref[1].id, "status": "User notified. 30s buffer started."}

@app.post("/trigger_alerts/{accident_id}")
def trigger_alerts(accident_id: str):
    # Retrieve the accident details from Firestore
    acc_doc = db.collection("accidents").document(accident_id).get().to_dict()
    if not acc_doc: 
        return {"error": "Record not found"}

    # Fetch responder details
    hospitals = find_top_3_hospitals(acc_doc['latitude'], acc_doc['longitude'])
    police = find_nearest_police(acc_doc['latitude'], acc_doc['longitude'])
    
    # Generate a clickable Google Maps URL
    # format: https://www.google.com/maps?q=lat,lon
    location_url = f"https://www.google.com/maps?q={acc_doc['latitude']},{acc_doc['longitude']}"
    
    # 1. Update Firestore status
    db.collection("accidents").document(accident_id).update({"status": "active"})

    # 2. Notify Family with Location
    user = db.collection("users").document(acc_doc['userId']).get().to_dict()
    
    # Detailed message including the location link
    sms_text = (
        f"EMERGENCY! {acc_doc['name']} has been in an accident. "
        f"Location: {location_url} "
        f"Nearest Police: {police['name']} ({police['phone']})"
    )

    for contact in user.get("emergencyContacts", []):
        send_sms(contact, sms_text) # Sends the link via Twilio
        make_call(contact) # Initiates automated voice call

    # 3. Automatic calls to responders
    make_call(police['phone'])
    if hospitals:
        make_call(hospitals[0]['phone'])

    return {"message": "Location link and alerts sent successfully", "url": location_url}

# --- 3. HOSPITAL COORDINATION ---
@app.get("/map/{accident_id}")
async def get_map(request: Request, accident_id: str):
    """Serves the Leaflet map dashboard."""
    acc_doc = db.collection("accidents").document(accident_id).get().to_dict()
    return templates.TemplateResponse("map.html", {
        "request": request, "accident_id": accident_id, 
        "lat": acc_doc['latitude'], "lon": acc_doc['longitude'], "name": acc_doc['name']
    })

@app.post("/accept_emergency/{accident_id}")
def accept_emergency(accident_id: str, hospital_name: str, hospital_phone: str):
    """Mandatory phone required to update family."""
    acc_ref = db.collection("accidents").document(accident_id)
    acc_ref.update({"status": "accepted", "responding_hospital": hospital_name, "hospital_phone": hospital_phone})
    
    acc_data = acc_ref.get().to_dict()
    user = db.collection("users").document(acc_data['userId']).get().to_dict()
    
    update_msg = f"Update: {hospital_name} is responding. Contact: {hospital_phone}"
    for c in user.get("emergencyContacts", []):
        send_sms(c, update_msg)
    return {"status": "Responders dispatched."}
