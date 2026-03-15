from fastapi import APIRouter, Depends, HTTPException
from models import TripData, TripOut, AnalyticsQuery
from firebase_service import firebase_service
from typing import List
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/trips", tags=["trips"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/data")
@limiter.limit("100/minute")
async def log_trip_data(trip: TripData, current_user_id: str = Depends(get_current_user)):
    try:
        trip_dict = trip.dict()
        trip_dict['userId'] = current_user_id
        trip_dict['timestamp'] = datetime.utcnow()
        trip_id = firebase_service.db.collection(f"trips/{current_user_id}").document().id
        trip_dict['tripId'] = trip_id
        
        await firebase_service.db.collection(f"trips/{current_user_id}").document(trip_id).set(trip_dict)
        
        return {"message": "Trip data logged", "tripId": trip_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_trip_history(limit: int = 100, current_user_id: str = Depends(get_current_user)):
    try:
        trips_ref = firebase_service.db.collection(f"trips/{current_user_id}").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        trips = []
        for doc in trips_ref.stream():
            data = doc.to_dict()
            data['tripId'] = doc.id
            trips.append(TripOut(**data))
        return {"trips": trips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_analytics(days: int = 7, current_user_id: str = Depends(get_current_user)):
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trips_ref = firebase_service.db.collection(f"trips/{current_user_id}").where("timestamp", ">=", cutoff)
        
        total_trips = 0
        total_speed = 0
        risk_events = 0
        
        for doc in trips_ref.stream():
            data = doc.to_dict()
            total_trips += 1
            total_speed += data.get('speed', 0)
            if data.get('accidentDetected', False):
                risk_events += 1
        
        average_speed = total_speed / total_trips if total_trips > 0 else 0
        safety_score = max(0, 100 - (risk_events / total_trips * 100)) if total_trips > 0 else 100
        
        return {
            "weeklySafetyScore": round(safety_score, 2),
            "averageSpeed": round(average_speed, 2),
            "totalTrips": total_trips,
            "riskEvents": risk_events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
