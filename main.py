import asyncio
from fastapi import FastAPI, BackgroundTasks
from firebase_admin import firestore
from pydantic import BaseModel
from typing import List

# Local imports
from config import db
from twilio_config import send_sms, make_call
from services.places import find_nearest_police, find_top_3_hospitals

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

@app.post("/trigger_alerts/{accident_id}")
# --- 3. THE TRIGGER LOGIC (Direct Mobile Contacts) ---
def trigger_all_alerts(accident_id: str, acc_doc: dict):
    print(f"--- Triggering alerts for accident_id: {accident_id} ---")

    try:
        # 1. Retrieve Accident Data
        acc_doc_ref = db.collection("accidents").document(accident_id)
        acc_doc = acc_doc_ref.get()
        if not acc_doc.exists:
            print(f"ERROR: Accident ID {accident_id} not found.")
            return {"error": "Record not found"}
        
        acc_data = acc_doc.to_dict()

        # 2. Get Hardcoded Responders (No API call)
        hospitals = find_top_3_hospitals(acc_data['latitude'], acc_data['longitude'])
        police = find_nearest_police(acc_data['latitude'], acc_data['longitude'])

        # 3. Update Status & Prepare Message
        acc_doc_ref.update({"status": "active"})
        location_url = f"https://www.google.com/maps?q={acc_data['latitude']},{acc_data['longitude']}"
        sms_text = f"EMERGENCY! {acc_data.get('name', 'User')} in accident. Location: {location_url}"

        # 4. Notify Family (from Firestore)
        try:
            user_doc = db.collection("Users").document(acc_data['userId']).get()
            if user_doc.exists:
                contacts = user_doc.to_dict().get("emergencyContacts", [])
                for contact in contacts:
                    send_sms(contact, sms_text)
                    make_call(contact, acc_data.get('name', 'User'))
        except Exception as e:
            print(f"Family Alert Error: {e}")

        # 5. Notify Police (Hardcoded Mobile)
        try:
            send_sms(police['phone'], f"POLICE ALERT: {sms_text}")
            make_call(police['phone'], acc_data.get('name', 'User'))
        except Exception as e:
            print(f"Police Alert Error: {e}")

        # 6. Notify Hospital (Hardcoded Mobile)
        try:
            if hospitals:
                send_sms(hospitals[0]['phone'], f"HOSPITAL ALERT: {sms_text}")
                make_call(hospitals[0]['phone'], acc_data.get('name', 'User'))
        except Exception as e:
            print(f"Hospital Alert Error: {e}")

        print(f"--- Process completed for {accident_id} ---")
        return {"message": "All alerts processed successfully."}

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        return {"error": "Internal Server Error"}, 500