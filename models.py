from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum

# --- User Models ---
class UserCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr

class EmergencyContactCreate(BaseModel):
    contact_name: str
    contact_phone: str

class EmergencyContactsCreate(BaseModel):
    user_id: str
    contacts: List[EmergencyContactCreate]

# --- Trip Models ---
class TripData(BaseModel):
    user_id: str
    speed: float
    latitude: float
    longitude: float
    timestamp: Optional[float] = None # Support numeric Unix timestamps

class TripOut(BaseModel):
    id: str
    user_id: str
    speed: float
    timestamp: datetime

class AnalyticsOut(BaseModel):
    average_speed: float
    max_speed: float
    trip_count: int
    safety_score: int

# --- Accident Models ---
class AccidentAlert(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    speed: float
    timestamp: Optional[int] = None

class AccidentResponse(BaseModel):
    accident_id: str
    response: str

class HospitalResponse(BaseModel):
    accident_id: str
    response: str

class CancelAccident(BaseModel):
    accident_id: str