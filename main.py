from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import threading
import time

# Import config and services
from config import db, DEFAULT_HOSPITAL_NUMBER
from twilio_config import (
    send_sms, 
    make_call, 
    send_sms_to_family, 
    send_sms_to_police, 
    send_sms_to_hospital
)
from services.places import find_nearest_police, find_top_3_hospitals
from services.geocoding import reverse_geocode
from services.routing import get_directions_text

# Initialize FastAPI
app = FastAPI(title="AI Accident Detection System", version="2.0.0")

templates = Jinja2Templates(directory="templates")

pending_confirmations = {}
users_db = {}

# Store recent accidents for hospital SMS replies (key: hospital_phone -> accident_data)
recent_accidents = {}

class AccidentReport(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    name: Optional[str] = "User"
    user_id: Optional[str] = None

def send_emergency_alerts_complete(victim_name, address, maps_url, directions_text, accident_lat, accident_lon, emergency_contact_1=None, emergency_contact_2=None, hospital_info=None, police_info=None):
    results = {"sms_sent": [], "calls_made": [], "errors": []}
    
    # Force hospital info
    if not hospital_info or not hospital_info.get('phone'):
        hospital_info = {"name": "Emergency Hospital", "phone": DEFAULT_HOSPITAL_NUMBER}
    
    print(f"🏥 Sending to hospital: {hospital_info['phone']}")
    print(f"👮 Sending to police: {police_info.get('phone', 'No phone')}") 
    
    # Hospital SMS with confirmation
    phone = hospital_info['phone']
    sms_text = f"🏥 HOSPITAL ALERT! Patient: {victim_name}\\n📍 {address}\\n🗺️ {maps_url}\\nReply PICKED/NOT PICKED"
    success = send_sms(phone, sms_text)
    if success:
        results["sms_sent"].append(f"hospital ({hospital_info['name']})")
    else:
        results["errors"].append("hospital_sms")
    
    # Police SMS
    if police_info and police_info.get('phone'):
        phone = police_info['phone']
        sms_text = f"🚔 POLICE ALERT! {victim_name}\\n📍 {address}\\n🗺️ {maps_url}"
        success = send_sms(phone, sms_text)
        if success:
            results["sms_sent"].append(f"police")
    
    # Store for replies
    recent_accidents[ hospital_info['phone'] ] = {
        'emergency_contact_1': emergency_contact_1,
        'emergency_contact_2': emergency_contact_2,
        'name': victim_name
    }
    
    print(f"📱 Hospital replies stored for {hospital_info['phone']}")
    
    return results

def trigger_emergency_response(accident_id, accident_data):
    victim_name = accident_data.get('name', 'User')
    address = accident_data.get('address', 'Unknown')
    maps_url = accident_data.get('maps_url', '')
    directions_text = accident_data.get('directions_text', '')
    accident_lat = accident_data.get('latitude', 0)
    accident_lon = accident_data.get('longitude', 0)
    emergency_contact_1 = accident_data.get('emergency_contact_1')
    emergency_contact_2 = accident_data.get('emergency_contact_2')
    hospital_info = accident_data.get('hospital_info')
    police_info = accident_data.get('police_info')
    
    results = send_emergency_alerts_complete(
        victim_name, address, maps_url, directions_text, accident_lat, accident_lon,
        emergency_contact_1, emergency_contact_2, hospital_info, police_info
    )
    
    print(f"🚨 EMERGENCY SUMMARY: {results}")
    return results

@app.post("/sms-webhook")
async def sms_webhook(request: Request):
    form = await request.form()
    from_number = form.get("From")
    body = form.get("Body", "").strip().upper()
    
    print(f"📱 SMS from {from_number}: {body}")
    
    accident_data = recent_accidents.get(format_phone_number(from_number))
    if not accident_data:
        print("No accident for this hospital")
        return PlainTextResponse("OK")
    
    if 'PICKED' in body or 'CONFIRM' in body:
        contacts = []
        if accident_data.get('emergency_contact_1'):
            contacts.append(f"{accident_data['emergency_contact_1']['name']} ({accident_data['emergency_contact_1']['phone']})")
        if accident_data.get('emergency_contact_2'):
            contacts.append(f"{accident_data['emergency_contact_2']['name']} ({accident_data['emergency_contact_2']['phone']})")
        
        contacts_text = '; '.join(contacts) if contacts else 'No contacts'
        sms_text = f"✅ PICKED UP! Contacts: {contacts_text}"
        send_sms(from_number, sms_text)
        
        del recent_accidents[format_phone_number(from_number)]
        return PlainTextResponse("OK")
    
    return PlainTextResponse("OK")

@app.post("/accident")
def report_accident(accident: AccidentReport):
    print(f"🚨 Accident: {accident.device_id} at {accident.latitude},{accident.longitude}")
    
    if accident.latitude == 0 or accident.longitude == 0:
        return {"error": "Invalid location"}
    
    accident_id = str(uuid.uuid4())
    address = reverse_geocode(accident.latitude, accident.longitude)
    maps_url = f"https://maps.google.com/maps?q={accident.latitude},{accident.longitude}"
    
    police_info = find_nearest_police(accident.latitude, accident.longitude)
    hospitals = find_top_3_hospitals(accident.latitude, accident.longitude)
    
    hospital_info = hospitals[0] if hospitals and hospitals[0].get('phone') else {"name": "Emergency Hospital", "phone": DEFAULT_HOSPITAL_NUMBER}
    
    directions_text = get_directions_text(accident.latitude, accident.longitude, hospital_info.get('lat', accident.latitude), hospital_info.get('lon', accident.longitude))
    
    emergency_contact_1 = None
    emergency_contact_2 = None
    if accident.user_id:
        if accident.user_id in users_db:
            user_data = users_db[accident.user_id]
            emergency_contact_1 = user_data.get('emergency_contact_1')
            emergency_contact_2 = user_data.get('emergency_contact_2')
    
    accident_data = {
        "id": accident_id,
        "name": accident.name,
        "latitude": accident.latitude,
        "longitude": accident.longitude,
        "address": address,
        "maps_url": maps_url,
        "directions_text": directions_text,
        "emergency_contact_1": emergency_contact_1,
        "emergency_contact_2": emergency_contact_2,
        "hospital_info": hospital_info,
        "police_info": police_info
    }
    
    # Start 30s timer
    timer = threading.Timer(30.0, trigger_emergency_response, args=[accident_id, accident_data])
    timer.daemon = True
    timer.start()
    
    pending_confirmations[accident_id] = accident_data
    
    print(f"⏰ 30s timer started for {accident_id}. Hospital: {hospital_info['phone']}")
    
    return {
        "status": "pending",
        "accident_id": accident_id,
        "message": "30s to confirm OK or auto SMS to hospital/police"
    }

@app.post("/test_sms")
def test_sms(to_number: str = Query(...), message: str = Query("Test")):
    success = send_sms(to_number, message)
    return {"status": "sent" if success else "failed"}

@app.get("/")
def root():
    return {"message": "AI Accident API ready. POST /accident to test auto SMS."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
