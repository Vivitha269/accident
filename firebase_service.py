import firebase_admin
from firebase_admin import credentials, firestore, messaging, auth
from firebase_admin.exceptions import FirebaseError
import os
from dotenv import load_dotenv

load_dotenv()

class FirebaseService:
    def __init__(self):
        cred_path = 'ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json'
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f'Copy {cred_path} to root directory')
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.messaging = messaging
        self.auth = auth

    def create_user(self, uid, email, phone):
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
        try:
            decoded = self.auth.verify_id_token(token)
            return decoded['uid']
        except:
            return None

    def send_fcm(self, token, title, body, data=None):
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
