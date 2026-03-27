# Postman Test Collection for AI Accident Backend

Import this into Postman and set base URL to `http://localhost:8000/api`

## 1. Register User
```
POST /register
Content-Type: application/json

{
  "name": "John Doe",
  "phone": "9876543210",
  "email": "john@example.com"
}
```

Expected: `{"status": "user created", "id": "..."}`

## 2. Add Emergency Contact
```
POST /emergency-contact
Content-Type: application/json

{
  "user_id": "USER_PHONE_ID_FROM_REGISTER",
  "contact_name": "Emergency Contact",
  "contact_phone": "9999999999"
}
```

## 3. Log Trip Data
```
POST /trip-data
Content-Type: application/json

{
  "user_id": "USER_ID",
  "speed": 45.5,
  "latitude": 13.0827,
  "longitude": 80.2707,
  "timestamp": 1710000000
}
```

Expected: `{"status": "trip logged", "id": "..."}`

## 4. Accident Alert
```
POST /accident-alert
Content-Type: application/json

{
  "user_id": "USER_ID",
  "speed": 0.0,
  "latitude": 13.0827,
  "longitude": 80.2707,
  "timestamp": 1710000100
}
```

Expected: `{"status": "alert received", "accident_id": "..."}`

## 5. User Response
```
POST /response
Content-Type: application/json

{
  "accident_id": "ACCIDENT_ID_FROM_ALERT",
  "response": "Ambulance Requested"
}
```

## 6. Get Trips History
```
GET /trips/USER_ID
```

## 7. Get Analytics
```
GET /analytics/USER_ID
```

Expected example:
```
{
  "average_speed": 45.2,
  "max_speed": 78.4,
  "trip_count": 32,
  "safety_score": 92
}
```

## NEW FEATURES TEST (🚨 Full Flow)

### 8. **Hospital Response** (after accident timeout)
```
POST /accidents/hospital-response
Content-Type: application/json

{
  "accident_id": "ACCIDENT_ID_FROM_ALERT",
  "response": "YES"
}
```

Expected: `{"status": "hospital response processed"}`
→ Check emergency contacts get hospital SMS!

### 9. **Verify Firestore Logs**
```
- alert_logs: All SMS/call results + OSRM routes
- hospital_responses: Hospital YES/NO
- accident_events: status=alerts_triggered + hospital_confirmed=True
```

## Base URL: http://localhost:8000/api
Swagger UI: http://localhost:8000/docs
