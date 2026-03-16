from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import firebase_admin.firestore as firestore


from models import *
from firebase_service import firebase_service
from dependencies import get_current_user
from routers.users import router as users_router
from routers.trips import router as trips_router
from routers.accidents import router as accidents_router

from config import db as firestore_db  # existing
from twilio_config import send_sms
from services.places import find_nearest_police, find_top_3_hospitals
from services.geocoding import reverse_geocode
from services.routing import get_directions_text

import uuid
import threading
import time

app = FastAPI(title="AI Accident Detection - FastAPI Backend", version="1.0.0")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda e, _: PlainTextResponse("Rate limit exceeded", status_code=429))

templates = Jinja2Templates(directory="templates")

# Existing accident logic (keep)
pending_confirmations = {}
recent_accidents = {}

# Mount routers
app.include_router(users_router, prefix="/api")
app.include_router(trips_router, prefix="/api")
app.include_router(accidents_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "FastAPI Accident Backend ready - http://localhost:8000/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy", "firebase": firebase_service.db is not None}

# Existing accident endpoint (enhanced)
@app.post("/accident")
@app.state.limiter.limit("10/minute")
async def report_accident(request: Request, accident: AccidentReport):
    accident_id = str(uuid.uuid4())
    address = reverse_geocode(accident.latitude, accident.longitude)
    maps_url = f"https://maps.google.com/maps?q={accident.latitude},{accident.longitude}"
    
    police_info = await find_nearest_police(accident.latitude, accident.longitude)
    hospitals = await find_top_3_hospitals(accident.latitude, accident.longitude)
    hospital_info = hospitals[0] if hospitals else {"name": "Emergency", "phone": "8825597447"}
    
    # Store accident
    accident_data = accident.dict()
    accident_data.update({
        "id": accident_id,
        "address": address,
        "maps_url": maps_url,
        "hospital_info": hospital_info,
        "police_info": police_info,
"timestamp": firebase_admin.firestore.SERVER_TIMESTAMP
    })
    
    if firestore_db:
        firestore_db.collection('accidents').document(accident_id).set(accident_data)
    
    pending_confirmations[accident_id] = accident_data
    
    # 30s timer
    threading.Timer(30.0, lambda: trigger_emergency_response(accident_id, accident_data)).start()
    
    return {"accident_id": accident_id, "message": "30s to cancel or auto-alert"}

# Existing webhook etc. kept...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
