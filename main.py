import asyncio
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from firebase_admin import firestore

# Local imports from your project files
from config import db
from twilio_config import send_sms, make_call
from services.places import find_top_3_hospitals, find_nearest_police

app = FastAPI()

# Mount static folder for map.html
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

def _query_overpass(query: str):
    """Internal helper to fetch junction data for prevention logic."""
    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data=query)
    return response.json()

# --- 1. PREVENTION: SPEED ALARM ---
@app.get("/check_speed_safety")
def check_speed_safety(lat: float, lon: float, speed: float):
    """Warns user if they are speeding near a high-risk junction."""
    query = f'[out:json];node["highway"~"junction|stop"](around:500,{lat},{lon});out body;'
    data = _query_overpass(query) #
    
    if data.get("elements") and speed > 60:
        return {
            "warning": "ALARM: SLOW DOWN!",
            "message": f"High speed ({speed}km/h) detected near junction. Please slow down!"
        }
    return {"status": "Safe"}

# --- 2. REGISTRATION & CONTACTS ---
@app.post("/register_device")
def register_device(userId: str, token: str):
    """Saves notification token to Firestore Users collection."""
    db.collection("Users").document(userId).set({
        "deviceTokens": firestore.ArrayUnion([token]),
        "prevention_enabled": True
    }, merge=True)
    return {"message": "Registered"}

class ContactUpdate(BaseModel):
    Contacts: List[str]

@app.post("/contacts")
def add_contacts(userId: str, data: ContactUpdate):
    """Saves emergency contact numbers in Users collection."""
    user_ref = db.collection("Users").document(userId)
    user_ref.update({"emergencyContacts": data.Contacts})
    return {"message": f"Successfully added {len(data.Contacts)} contacts for {userId}"}

# --- 3. ACCIDENT FLOW WITH 30s ALARM ---
@app.post("/accident")
async def accident_report(userId: str, name: str, lat: float, lon: float, background_tasks: BackgroundTasks):
    """Creates accident record and starts a 30s confirmation window."""
    user_doc = db.collection("Users").document(userId).get()
    if not user_doc.exists:
        return {"error": "User not found. Register first."}
    
    acc_ref = db.collection("accidents").add({
        "userId": userId, 
        "name": name, 
        "latitude": lat, 
        "longitude": lon,
        "status": "awaiting_confirmation", 
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    accident_id = acc_ref[1].id

    # Start the 30-second background alarm process
    background_tasks.add_task(start_emergency_timer, accident_id)

    return {
        "accidentId": accident_id, 
        "status": "ALARM TRIGGERED: 30s to cancel before emergency alerts are sent."
    }

async def start_emergency_timer(accident_id: str):
    """Waits 30s; if user hasn't cancelled, triggers all alerts."""
    await asyncio.sleep(30) # Real-time delay
    
    acc_ref = db.collection("accidents").document(accident_id)
    acc_doc = acc_ref.get().to_dict()
    
    # Only proceed if the user didn't cancel it
    if acc_doc and acc_doc.get("status") == "awaiting_confirmation":
        trigger_all_alerts(accident_id, acc_doc)

@app.post("/cancel_accident/{accident_id}")
def cancel_accident(accident_id: str):
    """Allows the user to stop the alarm before alerts go out."""
    acc_ref = db.collection("accidents").document(accident_id)
    acc_ref.update({"status": "cancelled"})
    return {"message": "Emergency alerts cancelled. You are safe!"}

def trigger_all_alerts(accident_id: str, acc_doc: dict):
    """Internal logic to find responders and send SMS/Calls."""
    hospitals = find_top_3_hospitals(acc_doc['latitude'], acc_doc['longitude'])
    police = find_nearest_police(acc_doc['latitude'], acc_doc['longitude'])
    location_url = f"https://www.google.com/maps?q={acc_doc['latitude']},{acc_doc['longitude']}"
    
    db.collection("accidents").document(accident_id).update({"status": "active"})

    victim_name = acc_doc['name']
    alert_msg = f"URGENT: Accident for {victim_name}. Location: {location_url}"
    
    # 1. Family Alerts (SMS + Call)
    user = db.collection("Users").document(acc_doc['userId']).get().to_dict()
    for contact in user.get("emergencyContacts", []):
        send_sms(contact, alert_msg)
        make_call(contact, victim_name)

    # 2. Police Notification (Call ONLY - to avoid Short Code error)
    if police:
        # Only send SMS if the phone number is longer than 5 digits
        if len(police['phone']) > 5:
            send_sms(police['phone'], alert_msg)
        make_call(police['phone'], victim_name)

    # 3. Hospital Notification
    if hospitals:
        nearest_hosp = hospitals[0]
        # Only send SMS if it's a real mobile/landline number, not '108'
        if len(nearest_hosp['phone']) > 5:
            send_sms(nearest_hosp['phone'], alert_msg)
        make_call(nearest_hosp['phone'], victim_name)

# --- 4. HOSPITAL COORDINATION ---
@app.get("/map/{accident_id}")
async def get_map(request: Request, accident_id: str):
    acc_doc = db.collection("accidents").document(accident_id).get().to_dict()
    return templates.TemplateResponse("map.html", {
        "request": request, "accident_id": accident_id, 
        "lat": acc_doc['latitude'], "lon": acc_doc['longitude'], "name": acc_doc['name']
    })

@app.post("/accept_emergency/{accident_id}")
def accept_emergency(accident_id: str, hospital_name: str, hospital_phone: str):
    acc_ref = db.collection("accidents").document(accident_id)
    acc_ref.update({
        "status": "accepted", 
        "responding_hospital": hospital_name, 
        "hospital_phone": hospital_phone
    })
    
    acc_data = acc_ref.get().to_dict()
    user = db.collection("Users").document(acc_data['userId']).get().to_dict()
    
    update_msg = f"Update: {hospital_name} is responding. Contact: {hospital_phone}"
    for c in user.get("emergencyContacts", []):
        send_sms(c, update_msg)
        
    return {"status": "Responders dispatched."}