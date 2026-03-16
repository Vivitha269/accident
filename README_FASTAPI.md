# AI Accident Detection - FastAPI REST API Backend (Port 8000 ONLY)

✅ **Migrated to FastAPI-only REST API**. Node.js backend deprecated.

## 🚀 Quick Start (Port 8000)

```bash
# Install & Run (updated run_test.bat)
.\run_test.bat
```

Or manually:
```bash
pip install -r requirements.txt
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

**Swagger Docs:** http://localhost:8000/docs  
**Health:** http://localhost:8000/health

## Features (Complete REST API)

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `POST /api/users/register` | No | User signup |
| `POST /api/users/login` | No | JWT login |
| `POST /api/users/contacts` | Yes | Add emergency contact |
| `POST /api/users/register_device` | No | Store FCM token |
| `POST /api/trips/data` | Yes | Log trip GPS |
| `GET /api/trips/history` | Yes | Trip history |
| `POST /api/accidents/alert` | Yes | **🚨 Accident detection** (FCM + SMS) |
| `POST /api/accidents/trigger_alerts/{id}` | No | Manual emergency trigger |
| `POST /accident` | No | Simple accident report (30s timer) |

## Tech Stack

- **FastAPI** (REST API, /docs auto)
- **Firebase** (Auth/DB/FCM push)
- **Twilio** (SMS/Calls w/ retries, location-aware)
- **Overpass API** (async nearest police/hospitals)
- **OSRM** (routing directions)
- **Nominatim** (geocoding addresses)

## Config (.env)

```
# Firebase (auto from JSON file)
# Twilio (required for SMS/calls)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+...

# Defaults (India)
DEFAULT_POLICE_NUMBER=+917338903743
DEFAULT_HOSPITAL_NUMBER=+918825597447
```

## Test Flow

1. **Register device** `/api/users/register_device` (FCM token)
2. **Trip data** `/api/trips/data` (live GPS)
3. **ACCIDENT** `/api/accidents/alert` → **FCM push + SMS** to contacts
4. **Timer expires** → Police/Hospital SMS + calls
5. **Manual trigger** `/api/accidents/trigger_alerts/{id}`

## Postman Collection

Import `POSTMAN_FASTAPI.json` - full coverage.

## Deprecated (Node.js)

- `backend/server.js` (port 5000) - **DO NOT USE**
- Run FastAPI **ONLY** on port 8000

## Production

```bash
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --workers 4
```

**Complete!** Project now works **only** FastAPI REST API on port 8000.
