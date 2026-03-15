from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from models import UserCreate, UserLogin, UserOut, Token, EmergencyContact
from firebase_service import firebase_service
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import List
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-me")

async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )
    try:
        uid = firebase_service.verify_id_token(token)
        if uid is None:
            raise credentials_exception
        user_doc = firebase_service.db.collection('users').document(uid).get()
        if not user_doc.exists:
            raise credentials_exception
        user_data = user_doc.to_dict()
        user_data['userId'] = uid
        return user_data
    except JWTError:
        raise credentials_exception

@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user exists
    user_doc = firebase_service.db.collection('users').document(user.phoneNumber).get()
    if user_doc.exists:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash password
    hashed_password = pwd_context.hash(user.password)
    
    # Create Firebase auth user
    if not firebase_service.create_user(user.phoneNumber, user.email, user.phoneNumber):
        raise HTTPException(status_code=500, detail="Auth creation failed")
    
    # Store user data
    user_dict = user.dict()
    user_dict['password'] = hashed_password
    user_dict['createdAt'] = firestore.SERVER_TIMESTAMP
    user_dict['updatedAt'] = firestore.SERVER_TIMESTAMP
    await firebase_service.db.collection('users').document(user.phoneNumber).set(user_dict)
    
    # Generate JWT
    payload = {"userId": user.phoneNumber, "exp": datetime.utcnow() + timedelta(days=7)}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    # Find user
    user_snapshot = firebase_service.db.collection('users').where('email', '==', credentials.email).limit(1).stream()
    user = None
    for doc in user_snapshot:
        user = doc.to_dict()
        user['userId'] = doc.id
        break
    
    if not user or not pwd_context.verify(credentials.password, user['password']):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    payload = {"userId": user['userId'], "exp": datetime.utcnow() + timedelta(days=7)}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": token, "token_type": "bearer"}

@router.get("/profile", response_model=UserOut)
async def get_profile(current_user = Depends(get_current_user)):
    return UserOut(**current_user)

@router.put("/profile")
async def update_profile(update_data: dict, current_user = Depends(get_current_user)):
    update_data['updatedAt'] = firestore.SERVER_TIMESTAMP
    await firebase_service.db.collection('users').document(current_user['userId']).update(update_data)
    return {"message": "Profile updated"}

@router.post("/contacts")
async def add_contact(contact: EmergencyContact, current_user = Depends(get_current_user)):
    user_doc = firebase_service.db.collection('users').document(current_user['userId']).get()
    contacts = user_doc.to_dict().get('emergencyContacts', [])
    contacts.append(contact.dict())
    await firebase_service.db.collection('users').document(current_user['userId']).update({
        'emergencyContacts': contacts,
        'updatedAt': firestore.SERVER_TIMESTAMP
    })
    return {"message": "Contact added", "contacts": contacts}

@router.get("/contacts")
async def get_contacts(current_user = Depends(get_current_user)):
    return {"emergencyContacts": current_user.get('emergencyContacts', [])}

@router.post("/register_device")
async def register_device(payload: RegisterDevicePayload):
    try:
        user_ref = firebase_service.db.collection('users').document(payload.userId)
        user_doc = user_ref.get()
        
        update_data = {
            "name": payload.name,
            "fcmToken": payload.fcmToken,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        if user_doc.exists:
            await user_ref.update(update_data)
            message = "Device registered/updated"
        else:
            update_data["emergencyContacts"] = []
            update_data["createdAt"] = firestore.SERVER_TIMESTAMP
            await user_ref.set(update_data)
            message = "New device user created"
            
        return {"message": message, "userId": payload.userId}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from google.cloud import firestore  # Add import for SERVER_TIMESTAMP
