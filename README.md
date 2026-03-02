# AI Accident Detection API

This repository provides a FastAPI service for detecting accidents and
notifying emergency contacts, nearby hospitals, and police via SMS and
voice calls (Twilio). It also includes a speed-alert mechanism for users
approaching accident-prone zones.

## Features

- Report accidents and trigger comprehensive alerts
- Automatic lookup of nearest hospitals/police via OpenStreetMap Overpass
- Routing and directions in SMS messages
- Emergency voice calls with customizable TwiML
- Speed alert notifications for high-speed approaches
- Pickup confirmation and status updates

## Requirements

- Python 3.9+
- A Firebase project with Firestore enabled (for storing accidents/users)
- Twilio account with SMS and calling capabilities
- Environment variables (see `.env.example`)

## Setup

```powershell
# create & activate virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and populate the values:

```
TWILIO_ACCOUNT_SID=<your_sid>
TWILIO_AUTH_TOKEN=<your_token>
TWILIO_PHONE_NUMBER=<+1234567890>
FIREBASE_CREDENTIALS="{...json...}"
# or set FIREBASE_CREDENTIALS_FILE=file.json
```

Place the Firebase service account JSON file in the repo root or set
`FIREBASE_CREDENTIALS_FILE` to its path.

## Running Locally

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The health endpoint is available at `http://127.0.0.1:8000/`.

### Example Requests

**Accident lookup**
```bash
curl "http://127.0.0.1:8000/accident?lat=37.77&lon=-122.42"
```

**Speed alert**
```bash
curl.exe -X POST "http://127.0.0.1:8000/speed_alert?user_id=test&phone_number=+1234567890&lat=37.77&lon=-122.42&speed=80"
```

**Report accident** (requires real Firestore user data):
```bash
curl -X POST http://127.0.0.1:8000/accident \
  -H "Content-Type: application/json" \
  -d '{"userId": "uid123","name": "Alice","lat":37.77,"lon":-122.42}'
```

## Testing

No automated tests are included yet. You can manually hit the endpoints
as shown above or write a small `pytest` suite targeting the FastAPI
app using `TestClient`.

## Notes

- The `services` module uses the Overpass API and OSRM for routing.
  Internet access is required.
- Phone numbers are validated to E.164 format; invalid numbers are skipped.
- Voice call messages are generated via TwiML templates.

---
Continue expanding this project with proper tests, authentication, and
storage of accident history as needed.