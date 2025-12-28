import firebase_admin
from firebase_admin import credentials, firestore,messaging
cred=credentials.Certificate("ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json")
firebase_admin.initialize_app(cred)
db=firestore.client()