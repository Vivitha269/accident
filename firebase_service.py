import firebase_admin
from firebase_admin import credentials, firestore, messaging, auth
from firebase_admin.exceptions import FirebaseError
from config import db, firebase_initialized
import os
from dotenv import load_dotenv

load_dotenv()

class FirebaseService:
    def __init__(self):
        self.db = db
        self.firebase_initialized = firebase_initialized
        if self.db:
            global messaging, auth  # already imported if initialized
            self.messaging = messaging
            self.auth = auth
        else:
            self.messaging = None
            self.auth = None
            print("⚠️ FirebaseService mock mode - no DB/auth/FCM")

    def create_user(self, uid, email, phone):
        if not self.auth:
            print("⚠️ Firebase auth not available")
            return False
        try:
            self.auth.create_user(
                uid=uid,
                email=email,
                phone_number=phone
            )
            return True
        except FirebaseError as e:
            print(f'Auth create error: {e}')
            return False

    def verify_id_token(self, token):
        if not self.auth:
            return None
        try:
            decoded = self.auth.verify_id_token(token)
            return decoded['uid']
        except:
            return None

    def send_fcm(self, token, title, body, data=None):
        if not self.messaging:
            print("⚠️ FCM not available")
            return None
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token
            )
            response = self.messaging.send(message)
            return response
        except Exception as e:
            print(f'FCM error: {e}')
            return None

    def send_multicast(self, tokens, title, body):
        if not self.messaging:
            print("⚠️ Multicast FCM not available")
            return 0
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                tokens=tokens
            )
            response = self.messaging.send_multicast(message)
            return response.success_count
        except Exception as e:
            print(f'Multicast error: {e}')
            return 0

firebase_service = FirebaseService()
