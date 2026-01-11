import asyncio
from fastapi import FastAPI, BackgroundTasks
from firebase_admin import firestore
from pydantic import BaseModel
from typing import List

# Local imports
from config import db
from twilio_config import send_sms, make_call

app = FastAPI()

# --- 🚀 REPLACE THESE WITH YOUR TWO TEST MOBILE NUMBERS ---
POLICE_MOBILE = "+919342170059"  # First test phone
HOSPITAL_MOBILE = "+917338903743" # Second test phone

@app.get("/")
def home():
    """Health check for Render."""
    return {"status": "Accident Detection API Live", "mode": "Safe Demo"}

# --- 1. USER CONTACT REGISTRATION ---
class ContactUpdate(BaseModel):
    Contacts: List[str]

@app.post("/contacts")
def add_contacts(userId: str, data: ContactUpdate):
    """Saves family contacts to Firestore."""
    user_ref = db.collection("Users").document(userId)
    user_ref.update({"emergencyContacts": data.Contacts})
    return {"message": "Emergency contacts saved"}

# --- 2. ACCIDENT FLOW WITH 30s ALARM ---
@app.post("/accident")
async def accident_report(userId: str, name: str, lat: float, lon: float, background_tasks: BackgroundTasks):
    """Reports accident and starts 30-second background timer."""
    acc_ref = db.collection("accidents").add({
        "userId": userId, 
        "name": name, 
        "latitude": lat, 
        "longitude": lon,
        "status": "awaiting_confirmation", 
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    accident_id = acc_ref[1].id
    
    # Start the 30-second countdown task
    background_tasks.add_task(start_emergency_timer, accident_id)
    
    return {
        "accidentId": accident_id, 
        "status": "Alarm started. 30 seconds to cancel."
    }

async def start_emergency_timer(accident_id: str):
    """Waits 30s. If not cancelled, triggers alerts."""
    await asyncio.sleep(30) # Real-time delay
    
    acc_ref = db.collection("accidents").document(accident_id)
    acc_doc = acc_ref.get().to_dict()
    
    # Check if user marked it as 'cancelled'
    if acc_doc and acc_doc.get("status") == "awaiting_confirmation":
        trigger_all_alerts(accident_id, acc_doc)

@app.post("/cancel_accident/{accident_id}")
def cancel_accident(accident_id: str):
    """Allows user to stop alerts."""
    db.collection("accidents").document(accident_id).update({"status": "cancelled"})
    return {"message": "Alerts stopped successfully."}

# --- 3. THE TRIGGER LOGIC (Direct Mobile Contacts) ---
def trigger_all_alerts(accident_id: str, acc_doc: dict):
    """Sends SMS and Calls to Family, Police, and Hospital."""
    db.collection("accidents").document(accident_id).update({"status": "active"})
    
    victim_name = acc_doc.get('name', 'User')
    loc_url = f"http://maps.google.com/maps?q={acc_doc['latitude']},{acc_doc['longitude']}"
    msg = f"EMERGENCY: {victim_name} had an accident. Location: {loc_url}"

    # 1. Family (from Firestore)
    user_doc = db.collection("Users").document(acc_doc['userId']).get()
    if user_doc.exists:
        user = user_doc.to_dict()
        for contact in user.get("emergencyContacts", []):
            send_sms(contact, msg)
            make_call(contact, victim_name)

    # 2. Police (Hardcoded Mobile)
    send_sms(POLICE_MOBILE, f"POLICE ALERT: {msg}")
    make_call(POLICE_MOBILE, victim_name)

    # 3. Hospital (Hardcoded Mobile)
    send_sms(HOSPITAL_MOBILE, f"HOSPITAL ALERT: {msg}")
    make_call(HOSPITAL_MOBILE, victim_name)