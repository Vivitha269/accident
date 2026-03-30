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
            # Proceed to trigger alerts if user hasn't cancelled
            await trigger_emergency_alerts(accident_id, data)
        else:
            logger.info(f"🚫 Timer ended for {accident_id}. No alerts sent (Status: {data.get('status')})")

async def trigger_emergency_alerts(accident_id: str, data: dict):
    """Sends Map SMS to everyone, but sends the 'Confirmation Link' ONLY to the Hospital."""
    user_id = data.get('user_id')
    lat = data.get('location', {}).get('lat') or data.get('latitude')
    lon = data.get('location', {}).get('lon') or data.get('longitude')
    
    # 1. Reverse Geocode the location
    address = reverse_geocode(lat, lon)
    # The Most Accurate Map Link (Drops a Red Pin)
    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    
    # 2. Prepare the notification list
    user_doc = db.collection('users').document(user_id).get().to_dict()
    
    # ✅ FIX: Check for both naming conventions in Firebase
    contacts = []
    if user_doc:
        contacts = user_doc.get('emergency_contacts') or user_doc.get('emergencyContacts') or []

    # Start the list with Police and Hospital
    alert_list = [
        {"name": "Police", "phone": DEFAULT_POLICE_NUMBER},
        {"name": "Hospital", "phone": DEFAULT_HOSPITAL_NUMBER}
    ]

    # Add user-defined contacts to the list
    for c in contacts:
        # ✅ FIX: This ensures the phone number is found even if the field name varies
        phone = c.get('contact_phone') or c.get('phone') or c.get('contactPhone')
        name = c.get('contact_name') or c.get('name') or "Emergency Contact"
        
        if phone:
            alert_list.append({"name": name, "phone": phone})
        else:
            logger.warning(f"⚠️ Skipping contact {name} because no phone number was found.")

    # 3. Dispatch SMS and Calls to every person in the list
    logger.info(f"🚨 Dispatching alerts to {len(alert_list)} parties...")

    for person in alert_list:
        target_phone = person['phone']
        
   # --- LOGIC INSIDE THE LOOP ---
        if person['name'] == "Hospital":
            # 🏥 PROFESSIONAL HOSPITAL MESSAGE
            hospital_sms = (
                f"🚨 AMBULANCE DISPATCH REQUEST!\n"
                f"Accident detected at: {address}\n"
                f"Map: {maps_url}\n\n"
                f"Are you responding? Click to CONFIRM & view family contacts:\n"
                f"https://accident-api-r53d.onrender.com/api/hospital-confirm/{accident_id}"
            )
            await send_sms(target_phone, hospital_sms)
        else:
            # 🚨 PROFESSIONAL FAMILY/POLICE MESSAGE
            standard_sms = (
                f"🚩 EMERGENCY: AI Accident Detection identified a crash at {address}.\n"
                f"View Map: {maps_url}\n\n"
                f"Emergency services are being notified. Please check on them immediately."
            )
            await send_sms(target_phone, standard_sms)

        # ✅ Voice call for everyone
        voice_msg = f"Emergency alert. An accident has been detected at {address}. Please check your text messages."
        await make_call(target_phone, voice_msg)

    # 4. Update the event status in Firestore
    db.collection('accident_events').document(accident_id).update({
        'status': 'alerts_triggered',
        'alerts_sent_at': datetime.utcnow()
    })
    
    logger.info(f"✅ SUCCESSFULLY alerted all parties for {accident_id}")