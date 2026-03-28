from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid
import logging
from datetime import datetime
from google.cloud import firestore

# Internal Imports
from models import AccidentAlert, EmergencyContactCreate
from firebase_service import firebase_service
from config import db, MAX_SMS_RETRIES, DEFAULT_HOSPITAL_NUMBER
from twilio_config import send_sms
from services.geocoding import reverse_geocode
from emergency_service import start_accident_timer, trigger_emergency_alerts

# Routers
from routers.users import router as users_router
from routers.trips import router as trips_router
from routers.accidents import router as accidents_router

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Accident Detection - FastAPI Backend", version="1.1.0")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda e, _: PlainTextResponse("Rate limit exceeded", status_code=429))

# --- CORE ACCIDENT LOGIC ENDPOINTS ---

@app.post("/api/accident-alert")
async def report_accident(data: AccidentAlert, background_tasks: BackgroundTasks):
    """Accident detected - Start 30s timer"""
    accident_id = str(uuid.uuid4())
    
    db.collection("accident_events").document(accident_id).set({
        "user_id": data.user_id,
        "location": {"lat": data.latitude, "lon": data.longitude},
        "status": "detected", 
        "timestamp": datetime.utcnow().isoformat(),
        "hospital_confirmed": False
    })

    background_tasks.add_task(start_accident_timer, accident_id)

    return {
        "status": "monitoring", 
        "accident_id": accident_id, 
        "message": "30-second countdown started."
    }

@app.get("/api/hospital-confirm/{accident_id}")
async def hospital_pickup_confirmation(accident_id: str):
    """
    1. Hospital clicks link.
    2. Hospital gets family numbers.
    3. Family gets 'Safe' update.
    """
    # Clean ID of any accidental spaces
    clean_id = accident_id.strip()
    doc_ref = db.collection("accident_events").document(clean_id)
    accident = doc_ref.get().to_dict()
    
    if not accident:
        return "Error: Accident record not found."

    # 1. Update status in Firebase
    doc_ref.update({
        "status": "hospital_confirmed", 
        "hospital_confirmed": True,
        "confirmed_at": datetime.utcnow()
    })

    # 2. Get User and Family Details
    user_id = accident['user_id']
    user_doc = db.collection("users").document(user_id).get().to_dict()
    
    if user_doc:
        victim_name = user_doc.get('name', 'The victim')
        contacts = user_doc.get("emergency_contacts", [])

        # Format family list for the Hospital
        contact_list_str = "\n".join([f"- {c.get('contact_name')}: {c.get('contact_phone')}" for c in contacts])
        
        hospital_msg = (
            f"✅ Pickup Confirmed for {victim_name}.\n"
            f"Please contact the family immediately:\n{contact_list_str}"
        )
        
        # SEND SMS TO HOSPITAL (With await!)
        await send_sms(DEFAULT_HOSPITAL_NUMBER, hospital_msg)

        # 3. NOTIFY FAMILY (With await!)
        for contact in contacts:
            phone = contact.get('contact_phone') or contact.get('phone')
            if phone:
                family_msg = f"UPDATE: The hospital has confirmed pickup for {victim_name}. They are in safe hands."
                await send_sms(phone, family_msg)

    logger.info(f"🏥 Hospital confirmation successful for {clean_id}")
    return "✅ Confirmation Successful. Family contact details have been sent to your phone via SMS."

# --- OTHER ENDPOINTS ---

@app.post("/api/cancel-accident")
async def cancel_accident(accident_id: str):
    db.collection("accident_events").document(accident_id).update({"status": "cancelled"})
    return {"status": "success", "message": "Emergency alerts cancelled."}

@app.get("/")
async def root():
    return {"message": "AI Accident Backend Active", "docs": "/docs"}

# Router Registration
app.include_router(users_router, prefix="/api")
app.include_router(trips_router, prefix="/api")
app.include_router(accidents_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)