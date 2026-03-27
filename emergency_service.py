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
    """Sends Map SMS and Voice Calls to ALL 4 parties at once."""
    user_id = data.get('user_id')
    lat = data.get('location', {}).get('lat') or data.get('latitude')
    lon = data.get('location', {}).get('lon') or data.get('longitude')
    
    address = reverse_geocode(lat, lon)
    # Most reliable map link for mobile phones
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    
    # 1. Fetch Emergency Contacts from Firestore
    user_doc = db.collection('users').document(user_id).get().to_dict()
    contacts = user_doc.get('emergency_contacts', []) if user_doc else []

    # 2. Prepare Alert List
    # We add Police and Hospital to the list of people to be notified
    alert_list = [
        {"name": "Police", "phone": DEFAULT_POLICE_NUMBER},
        {"name": "Hospital", "phone": DEFAULT_HOSPITAL_NUMBER}
    ]
    
    # Add your 2 emergency contacts to the list
    for c in contacts:
        phone = c.get('contact_phone') or c.get('phone')
        if phone:
            alert_list.append({"name": c.get('contact_name', 'Family'), "phone": phone})

    # 3. TRIGGER ALL ALERTS
    logger.info(f"🚨 Dispatching alerts to {len(alert_list)} parties...")
    
    for person in alert_list:
        target_phone = person['phone']
    
    # SPECIAL MESSAGE FOR HOSPITAL
    if person['name'] == "Hospital":
        hospital_sms = (
            f"🚨 ACCIDENT PICKUP REQUEST!\n"
            f"Location: {address}\n"
            f"Map: {maps_url}\n"
            f"Click YES to confirm pickup and GET FAMILY CONTACTS: "
            f"http://YOUR_SERVER_IP:8000/api/hospital-confirm/{accident_id}"
        )
        await send_sms(target_phone, hospital_sms)
    else:
        # STANDARD MESSAGE FOR POLICE AND FAMILY
        standard_sms = f"EMERGENCY: Accident at {address}. View Map: {maps_url}"
        await send_sms(target_phone, standard_sms)

    # Voice call for everyone
    voice_msg = f"Emergency alert. An accident has been detected at {address}."
    await make_call(target_phone, voice_msg)

    # 4. Final Status Update
    db.collection('accident_events').document(accident_id).update({
        'status': 'alerts_triggered',
        'alerts_sent_at': datetime.utcnow()
    })
    logger.info(f"✅ SUCCESSFULLY alerted all contacts, police, and hospital for {accident_id}")