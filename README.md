# AI Accident Detection Backend

FastAPI-based backend for accident detection and emergency response with Twilio integration.

## Features

- 🚨 **Automatic Accident Detection** - Receives accident reports from Android app
- 📱 **SMS Alerts** - Sends emergency SMS with live location to:
  - Emergency contacts
  - Police
  - Hospital
  - Ambulance
- 📞 **Automatic Calls** - Makes voice calls to emergency responders
- 🗺️ **Live Location** - Shows exact accident location with Google Maps
- 🛣️ **Route Directions** - Provides turn-by-turn directions to responders
- 🔔 **Speed Alerts** - Warns users speeding through accident zones
- 🚑 **Ambulance Pickup Confirmation** - Confirms and notifies family

## Default Emergency Numbers

The backend uses these default numbers (configure in environment variables):

- Emergency Contact: `+1234567890`
- Police: `+1000000000`
- Ambulance: `+1000000001`
- Hospital: `+1000000002`

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```env
# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email

# Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number

# Default Emergency Numbers (optional)
DEFAULT_EMERGENCY_CONTACT=+1234567890
DEFAULT_POLICE_NUMBER=+1000000000
DEFAULT_AMBULANCE_NUMBER=+1000000001
DEFAULT_HOSPITAL_NUMBER=+1000000002
```

3. Run the server:
```bash
python main.py
```

Or use uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/accident` | Report accident (from Android app) |
| GET | `/health` | Health check |
| GET | `/map` | Display accident on map |

### Emergency Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/speed_alert` | Send speed warning |
| POST | `/trigger_alarm/{id}` | Trigger emergency alarm |
| POST | `/confirm_pickup/{id}` | Confirm ambulance pickup |
| POST | `/accept_emergency/{id}` | Accept and dispatch |

### Test Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/test_accident` | Test accident report |
| POST | `/test_sms` | Test SMS sending |
| POST | `/test_call` | Test voice call |

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Create user |
| GET | `/users/{id}` | Get user |

### Accident Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/accidents` | List accidents |
| GET | `/accidents/{id}` | Get accident |

## Example Request

### Report Accident (from Android app)

```json
POST /accident
{
  "device_id": "USER123",
  "latitude": 12.91234,
  "longitude": 80.12345,
  "timestamp": 1710000000,
  "status": "accident_detected",
  "name": "John Doe",
  "user_id": "user-123"
}
```

## Response

```json
{
  "status": "success",
  "message": "Emergency alerts sent successfully",
  "accident_id": "uuid-here",
  "location": {
    "latitude": 12.91234,
    "longitude": 80.12345,
    "address": "123 Main St, Chennai",
    "maps_url": "https://maps.google.com/?q=12.91234,80.12345"
  },
  "responders": {
    "police": {"name": "Police Station", "phone": "+1000000000"},
    "hospital": {"name": "City Hospital", "phone": "+1000000002"}
  }
}
```

## Map Interface

Access the map at:
- `/map?lat=12.91234&lon=80.12345&name=John`
- `/map/{accident_id}` - After accident is reported

## Notes

- SMS and calls include exact location address
- Directions are provided using OSRM (Open Source Routing Machine)
- Police and hospitals are found using Overpass API
- All calls include voice message with location details

