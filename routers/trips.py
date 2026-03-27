from fastapi import APIRouter, HTTPException
from models import TripData, TripOut, AnalyticsOut
from firebase_service import firebase_service
from datetime import datetime, timedelta
from google.cloud import firestore
import statistics
import logging
logger = logging.getLogger(__name__)
from config import db  # Add this line
router = APIRouter(tags=["trips"])

@router.post("/trip-data")
async def log_trip_data(trip: TripData):
    data = trip.dict()
    ts = trip.timestamp

    try:
        if ts is None:
            data['timestamp'] = datetime.utcnow()
        # Check if it's a number (int or float)
        elif isinstance(ts, (int, float)):
            data['timestamp'] = datetime.fromtimestamp(ts)
        # Check if it's a string that contains a number (like '1710000000.0')
        elif isinstance(ts, str) and ts.replace('.', '', 1).isdigit():
            data['timestamp'] = datetime.fromtimestamp(float(ts))
        else:
            # Otherwise, treat it as an ISO string
            data['timestamp'] = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    except Exception as e:
        logger.error(f"Timestamp conversion failed for {ts}: {e}")
        data['timestamp'] = datetime.utcnow()

    # Save to Firestore
    db.collection('trips').add(data)
    return {"status": "trip logged"}
  

@router.get("/trips/{user_id}")
async def get_trips(user_id: str):
    trips = list(firebase_service.db.collection('trips').where('user_id', '==', user_id).order_by('timestamp').limit(100).stream())
    list_trips = []
    for doc in trips:
        data = doc.to_dict()
        data['id'] = doc.id
        list_trips.append(TripOut(**data))
    logger.info(f"Fetched {len(list_trips)} trips for user_id={user_id}")
    return {"trips": list_trips}

@router.get("/analytics/{user_id}")
async def get_analytics(user_id: str):
    cutoff = datetime.utcnow() - timedelta(days=7)
    trips = list(firebase_service.db.collection('trips').where('user_id', '==', user_id).where('timestamp', '>=', cutoff).stream())
    speeds = []
    for doc in trips:
        speeds.append(doc.to_dict()['speed'])
    avg = statistics.mean(speeds) if speeds else 0
    mx = max(speeds) if speeds else 0
    count = len(speeds)
    score = 100 if avg < 50 else 80
    logger.info(f"Analytics for user_id={user_id}: avg={avg:.1f}, max={mx:.1f}, score={score}")
    return AnalyticsOut(average_speed=avg, max_speed=mx, trip_count=count, safety_score=score)
