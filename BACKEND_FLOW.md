# AI Accident Detection Backend - Complete Flow

## Overview
This backend implements a complete emergency response system with 30-second confirmation timeout.

---

## Complete Flow

### Step 1: User Registration (Required)
```
POST /register
{
    "name": "John Doe",
    "phone": "+919999999999",
    "emergency_contact_1": {
        "name": "Father",
        "phone": "+919999999998",
        "relationship": "Father"
    },
    "emergency_contact_2": {
        "name": "Mother", 
        "phone": "+919999999997",
        "relationship": "Mother"
    }
}
```
⚠️ **Both emergency contacts are REQUIRED** - User cannot register without both.

---

### Step 2: Accident Detection
```
POST /accident
{
    "device_id": "phone123",
    "latitude": 13.0827,
    "longitude": 80.2707,
    "name": "John Doe",
    "user_id": "user_id_from_registration"
}
```

**What happens:**
1. Accident is recorded in database
2. 30-second countdown STARTS
3. User receives notification asking "Are you okay?"
4. Response endpoint is provided

---

### Step 3: User Response (Within 30 seconds)

**Option A: User is OKAY** (No emergency sent)
```
POST /accident/confirm?accident_id=xxx
{
    "is_okay": true
}
```

**Option B: User is NOT OKAY** (Emergency alerts sent immediately)
```
POST /accident/confirm?accident_id=xxx
{
    "is_okay": false
}
```

---

### Step 4: If No Response (30 seconds timeout)
- Emergency alerts are sent AUTOMATICALLY to all contacts

---

### Step 5: Emergency Alerts Sent To:

#### 1. Emergency Contact 1 (SMS + Call)
- Name, Relationship, Live Location, Google Maps Link
- Phone call with voice message about accident

#### 2. Emergency Contact 2 (SMS + Call)
- Same as above

#### 3. Hospital (SMS + Call + Confirmation Request)
- Patient info, Location, Google Maps Link
- **Quickest route/directions** to reach exact location
- Request to confirm if patient can be admitted
- Phone call with emergency details

#### 4. Police (SMS + Call + Live Location + Routing)
- Victim info, Exact location with coordinates
- **Live Google Maps link**
- **Quickest route for fastest response**
- Phone call with emergency details

---

## SMS Content Examples

### Emergency Contact SMS:
```
🚨 URGENT! John Doe has been in an accident!

📍 Location: Chennai, Tamil Nadu
🗺️ Maps: https://maps.google.com/?q=13.0827,80.2707

🏥 Ambulance dispatched to: City Hospital
📞 Hospital Phone: +910000000002

💝 Please rush to the hospital if possible!
```

### Hospital SMS:
```
🏥 HOSPITAL ALERT! Accident Emergency!

👤 Patient: John Doe
📍 Location: Chennai, Tamil Nadu
🗺️ Maps: https://maps.google.com/?q=13.0827,80.2707

🧭 Route to accident:
Head east on MGR Road, turn right at the signal...

⚠️ Please confirm if patient can be admitted.
Reply with CONFIRM or call victim's family.
```

### Police SMS:
```
🚔 POLICE ALERT! Accident Emergency!

👤 Victim: John Doe
📍 Location: Chennai, Tamil Nadu
📌 Coordinates: 13.0827, 80.2707
🗺️ Maps: https://maps.google.com/?q=13.0827,80.2707

🧭 QUICKEST ROUTE TO SCENE:
Take NH32 east, exit at Chennai...

⚠️ IMMEDIATE RESPONSE REQUIRED! Life at risk!
```

---

## API Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/register` | POST | Register user with 2 emergency contacts |
| `/user/{user_id}` | GET | Get user info |
| `/accident` | POST | Report accident (starts 30s timer) |
| `/accident/confirm` | POST | User confirms status |
| `/trigger_emergency/{id}` | POST | Manual emergency trigger |
| `/hospital_confirm` | POST | Hospital confirms admission |
| `/health` | GET | Health check |
| `/accidents` | GET | List accidents |

---

## Running the Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Server runs on: `http://localhost:8000`

---

## Test the Flow

```bash
# 1. Register a user
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "phone": "+919999999999",
    "emergency_contact_1": {"name": "Father", "phone": "+919999999998", "relationship": "Father"},
    "emergency_contact_2": {"name": "Mother", "phone": "+919999999997", "relationship": "Mother"}
  }'

# 2. Report accident (starts 30s timer)
curl -X POST http://localhost:8000/accident \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test123",
    "latitude": 13.0827,
    "longitude": 80.2707,
    "name": "Test User"
  }'

# 3. Confirm (within 30 seconds)
curl -X POST "http://localhost:8000/accident/confirm?accident_id=YOUR_ACCIDENT_ID" \
  -H "Content-Type: application/json" \
  -d '{"is_okay": false}'
```

---

## Configuration

Edit `.env` file:
```env
# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-email

# Twilio
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=your-phone-number
```

---

## Key Features

✅ User registration with 2 mandatory emergency contacts  
✅ 30-second confirmation timeout  
✅ User can cancel by confirming "OKAY"  
✅ Automatic emergency if no response in 30s  
✅ SMS + Call to 2 emergency contacts  
✅ SMS + Call + Routing to Hospital  
✅ SMS + Call + Live Location + Routing to Police  
✅ Phone number auto-formatting (+91 for India)  
✅ Firestore database storage
