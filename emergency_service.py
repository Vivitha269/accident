import asyncio
import logging
from datetime import datetime
from config import db, DEFAULT_POLICE_NUMBER, DEFAULT_HOSPITAL_NUMBER
from twilio_config import send_sms, make_call
from services.geocoding import reverse_geocode

logger = logging.getLogger(__name__)

async def start_accident_timer(accident_id: str):
    """Waits 30s. If status is still 'detected', triggers alerts."""
    logger.info(f"⏳ Timer started for {accident_id}. Waiting 30s...")
    await asyncio.sleep(30)
    
    doc_ref = db.collection('accident_events').document(accident_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        if data.get('status') == 'detected':
            await trigger_emergency_alerts(accident_id, data)
        else:
            logger.info(f"🚫 Timer ended for {accident_id}. No alerts sent (Status: {data.get('status')})")

async def trigger_emergency_alerts(accident_id: str, data: dict):
    """Sends Map SMS to everyone, but sends the 'Confirmation Link' ONLY to the Hospital."""
    user_id = data.get('user_id')
    lat = data.get('location', {}).get('lat') or data.get('latitude')
    lon = data.get('location', {}).get('lon') or data.get('longitude')
    
    address = reverse_geocode(lat, lon)
    # The Most Accurate Map Link
    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    
    # 1. Prepare Alert List
    user_doc = db.collection('users').document(user_id).get().to_dict()
    contacts = user_doc.get('emergency_contacts', []) if user_doc else []

    alert_list = [
        {"name": "Police", "phone": DEFAULT_POLICE_NUMBER},
        {"name": "Hospital", "phone": DEFAULT_HOSPITAL_NUMBER}
    ]
    for c in contacts:
        alert_list.append({"name": c.get('contact_name'), "phone": c.get('contact_phone')})

    # 2. Loop through and send the CORRECT message
    for person in alert_list:
        target_phone = person['phone']
        
        if person['name'] == "Hospital":
            # --- THE HOSPITAL 'QUESTION' MESSAGE ---
            hospital_sms = (
                f"🚨 ACCIDENT PICKUP REQUEST!\n"
                f"Location: {address}\n"
                f"Map: {maps_url}\n\n"
                f"Are you picking up this victim? Click below to confirm and GET FAMILY CONTACTS:\n"
                f"http://YOUR_SERVER_IP:8000/api/hospital-confirm/{accident_id}"
            )
            await send_sms(target_phone, hospital_sms)
        else:
            # --- STANDARD MESSAGE FOR POLICE/FAMILY ---
            standard_sms = f"EMERGENCY: Accident at {address}. View Map: {maps_url}"
            await send_sms(target_phone, standard_sms)

        # Voice call for everyone
        await make_call(target_phone, f"Emergency alert. Accident detected at {address}.")