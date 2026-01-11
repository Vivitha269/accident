import asyncio
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from firebase_admin import firestore

# Local imports
from config import db
from twilio_config import send_sms, make_call
from services.places import find_top_3_hospitals, find_nearest_police

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

@app.get("/")
def home():
    return {"status": "Accident Detection API is Live", "user": "Mono"}

# --- 1. PREVENTION: SPEED ALARM ---
@app.get("/check_speed_safety")
def check_speed_safety(lat: float, lon: float, speed: float):
    query = f'[out:json];node["highway"~"junction|stop"](around:500,{lat},{lon});out body;'
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=5).json()
        if response.get("elements") and speed > 60:
            return {
                "warning": "ALARM: SLOW DOWN!",
                "message": f"High speed ({speed}km/h) near junction. Please slow down!"
            }
    except:
        pass
    return {"status": "Safe"}

# --- 2. REGISTRATION & CONTACTS ---
class ContactUpdate(BaseModel):
    Contacts: List[str]

@app.post("/contacts")
def add_contacts(userId: str, data: ContactUpdate):
    user_ref = db.collection("Users").document(userId)
    user_ref.update({"emergencyContacts": data.Contacts})
    return {"message": "Contacts saved successfully"}

# --- 3. ACCIDENT FLOW WITH 30s ALARM ---
@app.post("/accident")
async def accident_report(userId: str, name: str, lat: float, lon: float, background_tasks: BackgroundTasks):
    acc_ref = db.collection("accidents").add({
        "userId": userId, "name": name, "latitude": lat, "longitude": lon,
        "status": "awaiting_confirmation", "timestamp": firestore.SERVER_TIMESTAMP
    })
    accident_id = acc_ref[1].id
    background_tasks.add_task(start_emergency_timer, accident_id)
    return {"accidentId": accident_id, "status": "30s buffer active"}

async def start_emergency_timer(accident_id: str):
    await asyncio.sleep(30)
    acc_ref = db.collection("accidents").document(accident_id)
    acc_doc = acc_ref.get().to_dict()
    
    if acc_doc and acc_doc.get("status") == "awaiting_confirmation":
        trigger_all_alerts(accident_id, acc_doc)

@app.post("/trigger_alerts/{accident_id}")
def manual_trigger(accident_id: str):
    acc_doc = db.collection("accidents").document(accident_id).get().to_dict()
    if not acc_doc: return {"error": "Not found"}
    trigger_all_alerts(accident_id, acc_doc)
    return {"message": "Alerts triggered manually"}

def trigger_all_alerts(accident_id: str, acc_doc: dict):
    # Find responders for Name and Location (even if we call 100/108)
    hospitals = find_top_3_hospitals(acc_doc['latitude'], acc_doc['longitude'])
    police = find_nearest_police(acc_doc['latitude'], acc_doc['longitude'])
    
    location_url = f"http://maps.google.com/maps?q={acc_doc['latitude']},{acc_doc['longitude']}"
    db.collection("accidents").document(accident_id).update({"status": "active"})

    victim_name = acc_doc.get('name', 'User')
    alert_msg = f"URGENT: Accident for {victim_name}. Location: {location_url}"
    
    # 1. Family Alerts (SMS + Call)
    user = db.collection("Users").document(acc_doc['userId']).get().to_dict()
    for contact in user.get("emergencyContacts", []):
        try:
            send_sms(contact, alert_msg)
            make_call(contact, victim_name)
        except: pass

    # 2. Responders (Direct Call Logic)
    # We use your +919342170059 number for the demo to avoid Twilio crash
    responder_numbers = ["+919342170059", "108", "100"] 

    for phone in responder_numbers:
        try:
            # Twilio SAFETY CHECK: Only SMS if the number is 10 digits or more
            if len(phone) >= 10:
                send_sms(phone, alert_msg)
            
            # Voice Call (Always attempt)
            make_call(phone, victim_name)
        except Exception as e:
            print(f"Twilio skipped {phone} to prevent crash: {e}")