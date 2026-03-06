# AI Accident Detection System - Backend Documentation

## Overview
This is a **FastAPI-based backend system** that automatically detects accidents and sends emergency alerts to family members, police, and hospitals with accurate location information.

---

## Resources & Technologies Used

### 1. **Cloud & Database**
- **Firebase Firestore** - Real-time database for storing accident reports and user data
- **Firebase Admin SDK** - For server-side Firebase authentication

### 2. **SMS & Voice Calls**
- **Twilio** - Primary service for sending SMS and making emergency voice calls
  - Note: Trial accounts can only send to verified numbers
  - Upgrade to paid account for unlimited messaging

### 3. **Location Services**
- **Nominatim (OpenStreetMap)** - Reverse geocoding to convert GPS coordinates to human-readable addresses
- **Overpass API (OpenStreetMap)** - Finding nearest police stations and hospitals
- **OSRM (Open Source Routing Machine)** - Route calculation and directions

### 4. **Backend Framework**
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server for running FastAPI
- **Python-dotenv** - Environment variable management

---

## How It Works

### Step-by-Step Flow:

```
1. Android App detects accident → Sends GPS coordinates to /accident endpoint
                         ↓
2. Server saves accident to Firebase Firestore
                         ↓
3. Android app calls /trigger_alerts after 30-second buffer
                         ↓
4. Server fetches:
   - User's emergency contacts from Firestore
   - Nearest police station (Overpass API)
   - Nearest hospitals (Overpass API)
   - Accurate address (Nominatim)
   - Route directions (OSRM)
                         ↓
5. Server sends SMS & makes calls to:
   - Family members
   - Police
   - Hospitals
                         ↓
6. Android app shows map with accident location
```

---

## Location Accuracy

### How Accurate is the Location?

| Component | Accuracy | Details |
|-----------|----------|---------|
| **GPS Coordinates** | High | Depends on phone's GPS (typically 5-50 meters) |
| **Address (Geocoding)** | High | Uses Nominatim with OpenStreetMap data |
| **Google Maps Link** | Exact | Links directly to lat/lon coordinates |
| **Hospital/Police Search** | High | Uses Overpass API with 10-15km radius |

### Address Format in SMS:
```
📍 Location: Vittal Mallya Road, D'Souza Layout, Shanthala Nagar, 
             Ashokanagar, Bengaluru Central City Corporation, 
             Bengaluru, Bangalore North, Bengaluru Urban, 
             Karnataka, 560001, India

🗺️ Maps: https://www.google.com/maps?q=12.9716,77.5946
```

---

## Timing - How Long Does It Take?

### Typical Response Times:

| Step | Time | Description |
|------|------|-------------|
| **Accident Report** | ~1 second | Saves to Firestore |
| **Geocoding** | ~1-2 seconds | Nominatim API call |
| **Find Police/Hospitals** | ~2-3 seconds | Overpass API query |
| **Route Calculation** | ~1-2 seconds | OSRM routing |
| **SMS to Family** | ~2-5 seconds | Twilio API |
| **SMS to Police** | ~2-5 seconds | Twilio API |
| **SMS to Hospital** | ~2-5 seconds | Twilio API |
| **Voice Calls** | ~5-10 seconds | Twilio API |

### **Total Time: ~15-30 seconds** from trigger to all alerts sent

---

## API Endpoints

### Main Endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/accident` | POST | Report new accident |
| `/trigger_alerts/{id}` | POST | Send all emergency alerts |
| `/accident` | GET | Get accident details & nearest hospital |
| `/map` | GET | Display accident on map |
| `/diagnose_sms` | GET | Check SMS configuration |
| `/test_sms/{phone}` | GET | Send test SMS |
| `/speed_alert` | POST | Alert about speeding in accident zone |
| `/hospital_confirm/{id}` | POST | Confirm hospital dispatch |
| `/confirm_pickup/{id}` | POST | Confirm ambulance pickup |

---

## SMS & Call Messages

### Family SMS:
```
🚨 URGENT! [Victim Name] has been in an accident!

📍 Location: [Full Address]
🗺️ Maps: [Google Maps Link]

[Route Directions]

🏥 Ambulance dispatched to: [Hospital Name]
📞 Hospital Phone: [Hospital Phone]

💝 Please rush to the hospital if possible!
```

### Police SMS:
```
🚔 POLICE ALERT! Accident Emergency!

👤 Victim: [Victim Name]
📍 Location: [Full Address]
📌 Coordinates: [Lat], [Lon]
🗺️ Maps: [Google Maps Link]

🧭 Route to accident:
[Turn-by-turn directions]

⚠️ IMMEDIATE RESPONSE REQUIRED!
```

### Hospital SMS:
```
🏥 HOSPITAL ALERT! Accident Emergency!

👤 Patient: [Victim Name]
📍 Accident Location: [Full Address]
🗺️ Maps: [Google Maps Link]

🧭 Route to accident:
[Turn-by-turn directions]

⚠️ PREPARED FOR EMERGENCY ADMISSION!
```

---

## Current Status

### ✅ Working Components:
- Accident reporting to Firebase
- Location geocoding (accurate addresses)
- Finding nearest police/hospitals via Overpass API
- Route calculation via OSRM
- SMS sending (with correct code - see note below)
- Voice calls
- Map display

### ⚠️ Known Limitation:
- **Twilio Trial Account**: Can only send SMS/calls to verified phone numbers
- Solution: Upgrade to paid Twilio account or verify emergency numbers

---

## Quick Test Commands

```bash
# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Test SMS configuration
# Visit: http://localhost:8000/diagnose_sms

# Send test SMS
# Visit: http://localhost:8000/test_sms/+918838177899
```

---

## File Structure

```
ai-accident/
├── main.py              # FastAPI application & endpoints
├── twilio_config.py    # SMS & call functions
├── config.py           # Firebase configuration
├── run_server.py       # Server startup script
├── requirements.txt    # Python dependencies
├── services/
│   ├── geocoding.py    # Address lookup (Nominatim)
│   ├── places.py       # Find police/hospitals (Overpass)
│   ├── routing.py      # Route calculation (OSRM)
│   └── distance.py     # Distance calculations
├── templates/
│   └── map.html        # Map display template
└── static/
    └── map.html        # Static map files
```

---

## Conclusion

This backend system provides:
- **Fast response** (~15-30 seconds for all alerts)
- **Accurate location** (exact GPS + precise address)
- **Multiple notifications** (SMS + voice calls to family, police, hospital)
- **Route guidance** (helps responders find the location quickly)

The system is production-ready once you upgrade your Twilio account!

