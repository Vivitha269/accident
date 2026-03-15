from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    DRIVER = "driver"

class EmergencyContact(BaseModel):
    name: str
    phone: str
    relation: Optional[str] = None

class UserCreate(BaseModel):
    name: str
    phoneNumber: str
    email: EmailStr
    vehicleType: str
    password: str
    emergencyContacts: Optional[List[EmergencyContact]] = []

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    userId: str
    name: str
    phoneNumber: str
    email: str
    vehicleType: str
    emergencyContacts: Optional[List[EmergencyContact]] = []

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AccidentAlert(BaseModel):
    userId: str
    latitude: float
    longitude: float
    speed: float
    timestamp: Optional[datetime] = None

class AccidentResponse(BaseModel):
    accidentId: str
    response: str  # '1' or '2'

class RegisterDevicePayload(BaseModel):
    userId: str
    name: str
    fcmToken: Optional[str] = ""

class AccidentV1Payload(BaseModel):
    userId: str
    name: str
    latitude: float
    longitude: float
    deviceId: str

class AccidentV2Payload(BaseModel):
    reportId: str
    userId: str
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None

class TripData(BaseModel):
    userId: str
    speed: float
    latitude: float
    longitude: float
    accidentDetected: bool = False

class AnalyticsQuery(BaseModel):
    days: int = 7

class TripOut(BaseModel):
    tripId: str
    speed: float
    latitude: float
    longitude: float
    timestamp: datetime
    accidentDetected: bool

class AccidentReport(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    name: Optional[str] = "User"
    user_id: Optional[str] = None

