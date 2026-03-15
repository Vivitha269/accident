from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from firebase_service import firebase_service
import os

security = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("userId")
        if user_id is None:
            raise credentials_exception
        # Verify Firebase token too
        firebase_uid = firebase_service.verify_id_token(credentials.credentials)
        if firebase_uid != user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_id
