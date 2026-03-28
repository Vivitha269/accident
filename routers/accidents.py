from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict
from datetime import datetime
import uuid
import logging
import asyncio

# Firebase & Config
from google.cloud import firestore
from config import db
from firebase_service import firebase_service
from twilio_config import send_sms

# Models & Services
from models import AccidentAlert, AccidentResponse as UserResponse, HospitalResponse, CancelAccident
from emergency_service import start_accident_timer, trigger_emergency_alerts

logger = logging.getLogger(__name__)
router = APIRouter(tags=["accidents"])

# --- 1. ACCIDENT ALERT (START TIMER) ---
@router.post("/accident-alert")
async def report_accident(alert: AccidentAlert, background_tasks: BackgroundTasks):
    """
    Triggered by Android App when accident is detected.
    Saves to DB and starts a 30s background timer.
    """
    accident_id = str(uuid.uuid4())
    
    # Save the initial event to Firestore
    db.collection("accident_events").document(accident_id).set({
        "id": accident_id,
        "user_id": alert.user_id,
        "location": {"lat": alert.latitude, "lon": alert.longitude},
        "speed": alert.speed,
        "status": "detected", # Critical for the timer check
        "timestamp": datetime.utcnow(),
        "hospital_confirmed": False
    })

    # Start the 30s background timer logic
    background_tasks.add_task(start_accident_timer, accident_id)

    logger.warning(f"🚨 ACCIDENT DETECTED: user_id={alert.user_id}, id={accident_id} - 30s timer started")
    return {
        "status": "monitoring", 
        "accident_id": accident_id, 
        "message": "30s countdown active. Use /cancel-accident if safe."
    }

# --- 2. NEED HELP NOW (IMMEDIATE TRIGGER) ---
@router.post("/need-help-now")
async def immediate_help(accident_id: str):
    """
    Triggered if user clicks 'Need Help' button.
    Skips the remaining timer and sends alerts immediately.
    """
    doc_ref = db.collection("accident_events").document(accident_id)
    doc = doc_ref.get().to_dict()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Accident record not found")
    
    # Trigger alerts immediately
    await trigger_emergency_alerts(accident_id, doc)
    logger.info(f"🆘 IMMEDIATE HELP requested for accident_id={accident_id}")
    return {"status": "success", "message": "Alerts sent immediately!"}

# --- 3. CANCEL ACCIDENT (STOP ALERTS) ---
@router.post("/cancel-accident")
async def cancel_accident(cancel: CancelAccident):
    """
    Triggered if user clicks 'I am Safe'.
    Updates status to 'cancelled' so the background timer stops the alerts.
    """
    doc_ref = db.collection('accident_events').document(cancel.accident_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Accident not found")
    
    doc_ref.update({
        'status': 'cancelled',
        'cancelled_at': firestore.SERVER_TIMESTAMP
    })
    
    logger.info(f"✅ Accident {cancel.accident_id} cancelled by user.")
    return {"status": "success", "message": "Emergency alerts cancelled. Glad you are safe!"}

# --- 4. HOSPITAL RESPONSE (CONFIRM PICKUP) ---
@router.get("/api/hospital-confirm/{accident_id}")
async def handle_hospital_confirmation(accident_id: str):
    from config import DEFAULT_HOSPITAL_NUMBER # Ensure this is imported at the top or here

    doc_ref = db.collection("accident_events").document(accident_id)
    accident = doc_ref.get().to_dict()
    
    if not accident:
        raise HTTPException(status_code=404, detail="Accident record not found")

    # 1. Update Firestore
    doc_ref.update({
        "status": "hospital_confirmed", 
        "pickup_confirmed": True,
        "confirmed_at": firestore.SERVER_TIMESTAMP
    })

    # 2. Get the Victim's info and their Emergency Contacts
    user_id = accident.get('user_id')
    print(f"DEBUG: Searching for User ID: '{user_id}'") # ADD THIS
    user_doc = db.collection("users").document(user_id).get().to_dict()
    
    if not user_doc:
        print(f"DEBUG: No user found in Firebase with ID: '{user_id}'") # ADD THIS
        return {"status": "error", "message": "User profile not found"}
    if user_doc:
        victim_name = user_doc.get('name', 'The victim')
        contacts = user_doc.get('emergency_contacts', [])
        
        # --- NEW LOGIC: Format the contact info FOR THE HOSPITAL ---
        contact_details = "\n".join([f"- {c['contact_name']}: {c['contact_phone']}" for c in contacts])
        
        hospital_info_msg = (
            f"✅ Pickup Confirmed for {victim_name}.\n"
            f"Please contact the family immediately:\n{contact_details}"
        )
        
        # SEND THE SPECIFIC SMS ONLY TO THE HOSPITAL
        await send_sms(DEFAULT_HOSPITAL_NUMBER, hospital_info_msg)
        
        # 3. Also notify the family that the hospital has arrived
        for contact in contacts:
            phone = contact.get('contact_phone') or contact.get('phone')
            if phone:
                await send_sms(phone, f"UPDATE: The hospital has confirmed pickup for {victim_name}. They are in safe hands.")

    logger.info(f"🏥 Hospital confirmed pickup. Family details sent to Hospital phone.")
    return {"status": "success", "message": "✅Pickup confirmed. Family contact details sent via SMS."}
# --- 5. MANUAL USER RESPONSE (OPTIONAL) ---
# --- 5. MANUAL USER RESPONSE (CORRECTED) ---
@router.post("/response")
async def handle_user_response(response: UserResponse):
    """
    Handles specific SMS or App responses like 'Ambulance Requested'.
    """
    response_data = response.dict()
    response_data['timestamp'] = firestore.SERVER_TIMESTAMP
    
    db.collection('emergency_responses').add(response_data)
    
    if response.response == "Ambulance Requested":
        # FIX: Use response.accident_id instead of accident_id
        doc_ref = db.collection('accident_events').document(response.accident_id).get()
        if doc_ref.exists:
            data = doc_ref.to_dict()
            # FIX: Pass 'response.accident_id' and the dictionary 'data'
            await trigger_emergency_alerts(response.accident_id, data)
            
    return {"status": "response processed"}