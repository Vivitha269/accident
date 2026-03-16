from fastapi import APIRouter, Depends, HTTPException
from models import AccidentAlert, AccidentResponse, AccidentV1Payload, AccidentV2Payload
from firebase_service import firebase_service
from dependencies import get_current_user
from twilio_config import send_sms
from typing import Dict

router = APIRouter(prefix="/accidents", tags=["accidents"])

HOSPITAL_PHONE = "8825597447"
POLICE_PHONE = "7338903743"

@router.post("/alert")
async def accident_alert(alert: AccidentAlert, current_user_id: str = Depends(get_current_user)):
    try:
        alert_dict = alert.dict()
        alert_dict['userId'] = current_user_id
        alert_dict['timestamp'] = alert_dict.get('timestamp', datetime.utcnow())
        alert_dict['status'] = 'pending'
        alert_dict['emergencyNotified'] = False
        alert_dict['ambulanceRequested'] = False
        
        accident_id = firebase_service.db.collection('accidents').document().id
        alert_dict['accidentId'] = accident_id
        
        await firebase_service.db.collection('accidents').document(accident_id).set(alert_dict)
        
        # Get user data for FCM/contacts
        user_doc = firebase_service.db.collection('users').document(current_user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            contacts = user_data.get('emergencyContacts', [])
            fcm_token = user_data.get('fcmToken', '')
            
            alert_msg = f"🚨 Accident alert for {user_data.get('name', 'User')}! Lat: {alert.latitude}, Lng: {alert.longitude}. Reply 1=ambulance, 2=no"
            
            # FCM first (silent push)
            if fcm_token:
                firebase_service.send_fcm(fcm_token, "🚨 Accident Detected", alert_msg, {
                    'type': 'accident_alert',
                    'accidentId': accident_id,
                    'lat': str(alert.latitude),
                    'lng': str(alert.longitude)
                })
            
            # SMS to contacts
            if contacts:
                for contact in contacts:
                    await send_sms(contact['phone'], alert_msg)
                await firebase_service.db.collection('accidents').document(accident_id).update({'emergencyNotified': True})
        
        return {"message": "Accident alert created, FCM+SMS sent", "accidentId": accident_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/response")
async def handle_response(response: AccidentResponse):
    try:
        accident_ref = firebase_service.db.collection('accidents').document(response.accidentId)
        response_dict = response.dict()
        response_dict['timestamp'] = datetime.utcnow()
        
        await accident_ref.update({
            'response': response_dict,
            'status': 'ambulance' if response.response == '1' else 'no_action'
        })
        
        if response.response == '1':
            # Notify hospital/police
            hospital_msg = f"Ambulance requested! Accident ID: {response.accidentId}"
            police_msg = f"Accident reported ID: {response.accidentId}. Check hospital."
            await send_sms(HOSPITAL_PHONE, hospital_msg)
            await send_sms(POLICE_PHONE, police_msg)
            await accident_ref.update({'ambulanceRequested': True})
        
        return {"message": "Response processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/accident")
async def report_accident_v1(payload: AccidentV1Payload):
    try:
        accident_id = firebase_service.db.collection('accidents').document().id
        accident_data = payload.dict()
        accident_data['accidentId'] = accident_id
        accident_data['timestamp'] = datetime.utcnow()
        accident_data['speed'] = 0.0
        accident_data['status'] = 'pending'
        accident_data['emergencyNotified'] = False
        accident_data['ambulanceRequested'] = False
        
        await firebase_service.db.collection('accidents').document(accident_id).set(accident_data)
        
        # Optional notify
        try:
            user_doc = firebase_service.db.collection('users').document(payload.userId).get()
            if user_doc.exists and 'emergencyContacts' in user_doc.to_dict():
                user_data = user_doc.to_dict()
                contacts = user_data.get('emergencyContacts', [])
                if contacts:
                    message = f"🚨 Accident for {payload.name}! Lat: {payload.latitude}, Lng: {payload.longitude}. Reply 1=ambulance, 2=no"
                    for contact in contacts:
                        await send_sms(contact['phone'], message)
                    await firebase_service.db.collection('accidents').document(accident_id).update({'emergencyNotified': True})
        except:
            pass  # optional
            
        return {"message": "Accident v1 reported", "accidentId": accident_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report_accident")
async def report_accident_v2(payload: AccidentV2Payload):
    try:
        accident_id = firebase_service.db.collection('accidents').document().id
        accident_data = payload.dict()
        accident_data['accidentId'] = accident_id
        accident_data['timestamp'] = payload.timestamp or datetime.utcnow()
        accident_data['speed'] = 0.0
        accident_data['status'] = 'pending'
        accident_data['emergencyNotified'] = False
        accident_data['ambulanceRequested'] = False
        
        await firebase_service.db.collection('accidents').document(accident_id).set(accident_data)
        return {"message": "Accident v2 reported", "accidentId": accident_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger_alerts/{accident_id}")
async def trigger_alerts(accident_id: str):
    try:
        accident_doc = firebase_service.db.collection('accidents').document(accident_id).get()
        if not accident_doc.exists:
            raise HTTPException(status_code=404, detail="Accident not found")
        
        accident_data = accident_doc.to_dict()
        user_doc = firebase_service.db.collection('users').document(accident_data['userId']).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        contacts = user_data.get('emergencyContacts', [])
        fcm_token = user_data.get('fcmToken', '')
        
        if not contacts and not fcm_token:
            raise HTTPException(status_code=400, detail="No emergency contacts or FCM token")
        
        message_title = "🚨 EMERGENCY ALERT!"
        message_body = f"Accident ID: {accident_id} | Lat: {accident_data['latitude']}, Lng: {accident_data['longitude']}"
        
        # Send FCM push notifications
        if fcm_token:
            firebase_service.send_fcm(fcm_token, message_title, message_body, {
                'type': 'emergency',
                'accidentId': accident_id,
                'lat': str(accident_data['latitude']),
                'lng': str(accident_data['longitude'])
            })
        
        # SMS fallback
        for contact in contacts:
            await send_sms(contact['phone'], f"{message_title} {message_body}")
        
        await firebase_service.db.collection('accidents').document(accident_id).update({
            'emergencyNotified': True,
            'status': 'alerts_triggered',
            'fcmSent': True
        })
        
        return {"message": "SMS + FCM alerts triggered", "fcm_token_used": bool(fcm_token), "contacts_notified": len(contacts)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
