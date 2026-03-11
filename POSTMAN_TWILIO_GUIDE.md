
# Complete Postman Testing Guide for AI Accident System

This guide will help you test all the Twilio SMS and Call features using Postman.

---

## Prerequisites

1. **Server must be running:**
   ```bash
   python main.py
   ```
   Server runs at: `http://localhost:8000`

2. **Twilio credentials in .env file:**
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   ```

---

## All Available Endpoints

| # | Method | URL | Description |
|---|--------|-----|-------------|
| 1 | GET | `/health` | Check server health |
| 2 | GET | `/` | API information |
| 3 | POST | `/test_sms` | Send test SMS |
| 4 | POST | `/test_call` | Make test call |
| 5 | POST | `/speed_alert` | Send speed alert |
| 6 | POST | `/accident` | Report accident |
| 7 | POST | `/accident/confirm` | Confirm accident |
| 8 | POST | `/register` | Register user |
| 9 | GET | `/accidents` | List accidents |

---

## Step-by-Step Testing with Postman

### Test 1: Health Check (GET)
**Purpose:** Verify server is running

1. Open Postman
2. Select **GET** method
3. Enter: `http://localhost:8000/health`
4. Click **Send**
5. Expected Response:
```json
{
  "status": "healthy",
  "database": "disconnected",
  "timestamp": "2024-..."
}
```

---

### Test 2: Test SMS (POST)
**Purpose:** Send a simple SMS to test Twilio

1. Select **POST** method
2. Enter: `http://localhost:8000/test_sms`
3. Go to **Params** tab
4. Add parameters:
   - `to_number` = `+1234567890` (your phone)
   - `message` = `Hello from AI Accident System!`
5. Click **Send**
6. Expected Response:
```json
{
  "status": "success",
  "message": "SMS sent to +1234567890"
}
```

**You should receive an SMS on your phone!**

---

### Test 3: Test Voice Call (POST)
**Purpose:** Make a test voice call

1. Select **POST** method
2. Enter: `http://localhost:8000/test_call`
3. Go to **Params** tab
4. Add parameters:
   - `to_number` = `+1234567890` (your phone)
   - `victim_name` = `John Doe`
5. Click **Send**
6. Expected Response:
```json
{
  "status": "success",
  "message": "Call initiated to +1234567890"
}
```

**You should receive a call with an emergency message!**

---

### Test 4: Send SMS to Family (POST)
**Purpose:** Test sending SMS to family with location

1. Select **POST** method
2. Enter: `http://localhost:8000/test_sms`
3. Go to **Params** tab
4. Add parameters:
   - `to_number` = `+1234567890`
   - `message` = `🚨 URGENT! John Doe has been in an accident!

📍 Location: Chennai, Tamil Nadu
🗺️ Maps: https://maps.google.com/?q=13.0827,80.2707

🏥 Ambulance dispatched to: City Hospital

💝 Please rush to the hospital if possible!`
5. Click **Send**

---

### Test 5: Test Speed Alert (POST)
**Purpose:** Test speed alert call

1. Select **POST** method
2. Enter: `http://localhost:8000/speed_alert`
3. Go to **Params** tab
4. Add parameters:
   - `user_id` = `user123`
   - `phone_number` = `+1234567890`
   - `lat` = `13.0827`
   - `lon` = `80.2707`
   - `speed` = `80`
5. Click **Send**
6. Expected Response:
```json
{
  "status": "success",
  "message": "Speed alert sent to +1234567890"
}
```

---

### Test 6: Report Accident (POST) - Full Flow
**Purpose:** Test the complete accident detection flow

1. Select **POST** method
2. Enter: `http://localhost:8000/accident`
3. Go to **Body** → **raw** → **JSON**
4. Paste this:
```json
{
  "device_id": "ANDROID_PHONE_001",
  "latitude": 13.0827,
  "longitude": 80.2707,
  "status": "accident_detected",
  "name": "John Doe",
  "user_id": "test-user-123"
}
```
5. Click **Send**
6. Expected Response:
```json
{
  "status": "pending",
  "message": "Accident detected. You have 30 seconds to confirm if you're okay.",
  "accident_id": "abc-123-uuid",
  "confirmation_deadline": 1234567890,
  "instructions": "Send POST to /accident/confirm..."
}
```

**In your terminal, you'll see:**
```
🚨 ACCIDENT DETECTED!
Device: ANDROID_PHONE_001
Location: 13.0827, 80.2707
📍 Address: Chennai, Tamil Nadu
👮 Police: Egmore Police Station - +1000000000
🏥 Hospital: City Hospital - +1000000002

⏱️ 30-second countdown started!
```

---

### Test 7: Confirm User is OKAY (POST)
**Purpose:** Simulate user clicking "I'm Okay"

1. Copy the `accident_id` from previous response
2. Select **POST** method
3. Enter: `http://localhost:8000/accident/confirm?accident_id=YOUR_ACCIDENT_ID&is_okay=true`
4. Or go to **Params** and add:
   - `accident_id` = (paste from step 6)
   - `is_okay` = `true`
5. Click **Send**
6. Expected Response:
```json
{
  "status": "cancelled",
  "message": "You're okay! Emergency contacts have NOT been notified."
}
```

---

### Test 8: Confirm User Needs Help (POST)
**Purpose:** Simulate user clicking "Not Okay" - sends all alerts!

1. Report a new accident (Test 6)
2. Select **POST** method
3. Enter: `http://localhost:8000/accident/confirm`
4. Go to **Params** and add:
   - `accident_id` = (new accident_id)
   - `is_okay` = `false`
5. Click **Send**
6. Expected Response:
```json
{
  "status": "emergency_sent",
  "message": "Emergency alerts sent to all contacts! Help is on the way.",
  "results": {
    "sms_sent": ["emergency_contact_1", "emergency_contact_2", "hospital", "police"],
    "calls_made": ["emergency_contact_1", "emergency_contact_2", "hospital", "police"],
    "errors": []
  }
}
```

**You will receive:**
- 4 SMS messages (2 family + hospital + police)
- 4 voice calls (each with emergency message)

---

### Test 9: Automatic Timeout (30 seconds)
**Purpose:** If user doesn't respond within 30 seconds

1. Report an accident (Test 6)
2. **DO NOT** confirm - just wait 30 seconds
3. After 30 seconds, you'll see in terminal:
```
⏰ TIMEOUT! No response for accident abc-123
🚀 Triggering emergency response automatically...
```
4. Emergency alerts will be sent automatically!

---

## Complete Emergency Flow Summary

```
1. POST /accident
   ↓
2. Server finds nearest police & hospital
   ↓
3. 30-second countdown starts
   ↓
   ┌─────────────────────────────────────┐
   │ User Response:                     │
   ├─────────────────────────────────────┤
   │ is_okay=true  → No alerts sent     │
   │ is_okay=false → Send all alerts    │
   │ Timeout (30s) → Auto send alerts   │
   └─────────────────────────────────────┘
   ↓
4. Send to ALL:
   - Emergency Contact 1: SMS + Call
   - Emergency Contact 2: SMS + Call
   - Hospital: SMS + Call
   - Police: SMS + Call
   ↓
5. Each receives:
   - Victim name
   - Exact location (address + GPS)
   - Google Maps link
   - Route directions
   - Voice call with all details
```

---

## Troubleshooting

### SMS not sending?
1. Check Twilio credentials in `.env`
2. Verify phone number format: `+1234567890` (with +)
3. Check terminal for error messages

### Call not working?
1. Verify Twilio phone number is verified (for trial account)
2. Check terminal for error messages
3. Make sure phone number is correct

### Server errors?
1. Make sure server is running (`python main.py`)
2. Check all imports are working
3. Verify database connection (Firebase)

---

## Quick Reference - JSON Formats

### Register User (Requires 2 Emergency Contacts)
```json
{
  "name": "John Doe",
  "phone": "+1234567890",
  "emergency_contact_1": {
    "name": "Jane Doe",
    "phone": "+9876543210",
    "relationship": "Wife"
  },
  "emergency_contact_2": {
    "name": "Bob Smith",
    "phone": "+1234567891",
    "relationship": "Brother"
  }
}
```

### Report Accident
```json
{
  "device_id": "PHONE_001",
  "latitude": 13.0827,
  "longitude": 80.2707,
  "status": "accident_detected",
  "name": "John Doe",
  "user_id": "user-id-here"
}
```

### Confirm Accident
```json
{
  "is_okay": false
}
```

---

## Next Steps

After testing, you can:

1. **Deploy to Render:** Follow `BACKEND_FLOW.md`
2. **Connect Android App:** Use the deployed URL
3. **Setup Firebase:** Add credentials to use database features

Happy Testing! 🎉

