from fastapi import APIRouter, HTTPException
from pydantic import EmailStr
from models import UserCreate, EmergencyContactCreate, EmergencyContactsCreate # 
from firebase_service import firebase_service
from twilio_config import format_phone_number
from datetime import datetime
from google.cloud import firestore
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["users"])

@router.post("/register")
async def register(user: UserCreate):
    phone = format_phone_number(user.phone)
    if not phone:
        raise HTTPException(400, "Invalid phone number format. Use E.164 (e.g. +91...)")
    
    doc_ref = firebase_service.db.collection('users').document(phone)
    if doc_ref.get().exists:
        raise HTTPException(400, "User already exists with this phone number")
    
    data = user.dict()
    data['phone'] = phone
    data['id'] = doc_ref.id
    data['created_at'] = firestore.SERVER_TIMESTAMP
    
    doc_ref.set(data)
    logger.info(f"User registered: id={doc_ref.id}, phone={phone}, name={user.name}")
    return {"status": "user created", "id": doc_ref.id}

@router.post("/emergency-contact")
async def add_emergency_contacts(contacts: EmergencyContactsCreate):
    # Search for user by ID (which is the formatted phone number) 
    user_ref = firebase_service.db.collection('users').document(contacts.user_id)
    if not user_ref.get().exists:
        raise HTTPException(404, "User not found")
    
    formatted_contacts = []
    # Logic for dual contacts (max 2) 
    for c in contacts.contacts[:2]:  
        phone = format_phone_number(c.contact_phone)
        if not phone:
            raise HTTPException(400, f"Invalid contact phone: {c.contact_phone}")
        
        formatted_contacts.append({
            'contact_name': c.contact_name,
            'contact_phone': phone
        })
    
    # Update the user document in Firestore 
    user_ref.update({
        'emergency_contacts': formatted_contacts, # Use consistent naming
        'updated_at': firestore.SERVER_TIMESTAMP
    })
    
    logger.info(f"Added {len(formatted_contacts)} emergency contacts for user_id={contacts.user_id}")
    return {"status": "contacts added", "count": len(formatted_contacts)}