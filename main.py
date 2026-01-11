import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from firebase_admin import firestore

from config import db
from twilio_config import send_sms, make_call
from services.places import find_top_3_hospitals, find_nearest_police

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

@app.get("/")
def home():
    return {"status": "Accident API Live", "mode": "Direct Contact (No API)"}

# --- 1. REGISTRATION & CONTACTS ---
class ContactUpdate(BaseModel):
    Contacts: List[str]

@app.post("/contacts")
def add_contacts(userId: str, data: ContactUpdate):
    user_ref = db.collection("Users").document(userId)
    user_ref.update({"emergencyContacts": data.Contacts})
    return {"message": "Emergency contacts saved"}

# --- 2. ACCIDENT FLOW WITH 30s ALARM ---
@app.post("/accident")
async def accident_report(userId: str, name: str, lat: float, lon: float, background_tasks: BackgroundTasks):
    # Save to Firestore
    acc_ref = db.collection("accidents").add({
        "userId": userId, "name": name, "latitude": lat, "longitude": lon,
        "status": "awaiting_confirmation", "timestamp": firestore.SERVER_TIMESTAMP
    })
    accident_id = acc_ref[1].id
    
    # Start background timer
    background_tasks.add_task(start_emergency_timer, accident_id)
    return {"accidentId": accident_id, "status": "30s alarm active"}

async def start_emergency_timer(accident_id: str):
    await asyncio.sleep(30)
    acc_ref = db.collection("accidents").document(accident_id)
    acc_doc = acc_ref.get().to_dict()
    
    # Only trigger if user hasn't cancelled
    if acc_doc and acc_doc.get("status") == "awaiting_confirmation":
        trigger_all_alerts(accident_id, acc_doc)

@app.post("/cancel_accident/{accident_id}")
def cancel_accident(accident_id: str):
    db.collection("accidents").document(accident_id).update({"status": "cancelled"})
    return {"message": "Alerts stopped"}

# --- 3. THE TRIGGER LOGIC (Direct Mobile Numbers) ---
def trigger_all_alerts(accident_id: str, acc_doc: dict):
    # Get hardcoded responders from places.py
    hospitals = find_top_3_hospitals(acc_doc['latitude'], acc_doc['longitude'])
    police = find_nearest_police(acc_doc['latitude'], acc_doc['longitude'])
    
    location_url = f"https://www.google.com/maps?q={acc_doc['latitude']},{acc_doc['longitude']}"
    db.collection("accidents").document(accident_id).update({"status": "active"})

    victim_name = acc_doc.get('name', 'User')
    alert_msg = f"ALERT: Accident detected for {victim_name}. Location: {location_url}"

    # 1. Family Notification
    user = db.collection("Users").document(acc_doc['userId']).get().to_dict()
    for contact in user.get("emergencyContacts", []):
        send_sms(contact, alert_msg)
        make_call(contact, victim_name)

    # 2. Police Notification (Mobile Number)
    send_sms(police['phone'], f"POLICE: {alert_msg}")
    make_call(police['phone'], victim_name)

    # 3. Hospital Notification (Mobile Number)
    send_sms(hospitals[0]['phone'], f"HOSPITAL: {alert_msg}")
    make_call(hospitals[0]['phone'], victim_name)