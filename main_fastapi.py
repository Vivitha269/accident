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

# Internal Imports
from models import AccidentAlert, EmergencyContactCreate
from firebase_service import firebase_service
from config import db, MAX_SMS_RETRIES
from twilio_config import send_sms
from services.geocoding import reverse_geocode
from emergency_service import start_accident_timer, trigger_emergency_alerts # Ensure you created this service

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

templates = Jinja2Templates(directory="templates")

# --- CORE ACCIDENT LOGIC ENDPOINTS ---

@app.post("/api/accident-alert")
async def report_accident(data: AccidentAlert, background_tasks: BackgroundTasks):
    """
    1. Accident detected by Android App.
    2. Start 30s timer.
    3. If not cancelled, send alerts to Contacts, Police, and Hospital.
    """
    accident_id = str(uuid.uuid4())
    
    # Save to Firestore with 'detected' status [cite: 1]
    db.collection("accident_events").document(accident_id).set({
        "user_id": data.user_id,
        "location": {"lat": data.latitude, "lon": data.longitude},
        "status": "detected", 
        "timestamp": datetime.utcnow().isoformat(),
        "hospital_confirmed": False
    })

    # Start the 30s background process
    background_tasks.add_task(start_accident_timer, accident_id)

    return {
        "status": "monitoring", 
        "accident_id": accident_id, 
        "message": "30-second countdown started. Please cancel if safe."
    }

@app.post("/api/cancel-accident")
async def cancel_accident(accident_id: str):
    """User clicks 'I am Safe' - stops the timer alerts"""
    doc_ref = db.collection("accident_events").document(accident_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Accident record not found")
        
    doc_ref.update({"status": "cancelled"})
    return {"status": "success", "message": "Emergency alerts cancelled."}

@app.post("/api/need-help-now")
async def manual_trigger(accident_id: str):
    """User clicks 'Need Help' - skips the 30s timer"""
    doc = db.collection("accident_events").document(accident_id).get().to_dict()
    if not doc:
        raise HTTPException(status_code=404, detail="Accident record not found")
    
    # Trigger alerts immediately
    await trigger_emergency_alerts(accident_id, doc)
    return {"status": "success", "message": "Help is on the way. Alerts sent immediately."}

@app.get("/api/hospital-confirm/{accident_id}")
async def hospital_pickup_confirmation(accident_id: str):
    """Hospital confirms they picked up the person"""
    doc_ref = db.collection("accident_events").document(accident_id)
    accident = doc_ref.get().to_dict()
    
    if not accident:
        return "Accident ID not found."

    # Update status
    doc_ref.update({"status": "hospital_confirmed", "hospital_confirmed": True})

    # Notify Family
    user_id = accident['user_id']
    user_doc = db.collection("users").document(user_id).get().to_dict()
    contacts = user_doc.get("emergency_contacts", [])

    for contact in contacts:
        # Informing family that the hospital has confirmed pickup
        msg = f"UPDATE: The ambulance has confirmed pickup for your contact. They are being transported for care."
        send_sms(contact.get('contact_phone'), msg)

    return "Thank you! The family has been notified of the dispatch."

# --- ROUTER REGISTRATION ---

app.include_router(users_router, prefix="/api")
app.include_router(trips_router, prefix="/api")
app.include_router(accidents_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "AI Accident Backend Active", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy", "firebase": db is not None}

if __name__ == "__main__":
    import uvicorn
    # Make sure you use the filename correctly (main_fastapi.py)
    uvicorn.run(app, host="0.0.0.0", port=8000)

MAX_SMS_RETRIES = 3