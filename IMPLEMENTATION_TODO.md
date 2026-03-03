# Implementation TODO - Hospital Confirmation Feature

## Status: ✅ COMPLETED

### Task 1: Speed Alert (Already Implemented ✅)
- Already working: `/speed_alert` endpoint
- Already working: `speed_alert_alarm()` function
- **Functionality**: When user goes through high speed in accident zone, sends alarm notification to warn the user

### Task 2: Hospital Confirmation Feature

#### Step 1: Add new SMS function in twilio_config.py ✅
- [x] Added `send_hospital_confirmation()` - SMS to confirm hospital dispatch to family
- [x] Added `send_hospital_acknowledgment()` - SMS to acknowledge hospital response

#### Step 2: Add endpoints in main.py ✅
- [x] Added `/hospital_confirm/{accident_id}` endpoint
  - Accepts hospital_name, hospital_phone
  - Saves selected hospital to Firebase
  - Sends confirmation SMS to family
  - Sends acknowledgment SMS to hospital
- [x] Added `/hospital_status/{accident_id}` endpoint
  - Returns current hospital confirmation status

#### Step 3: Firebase Storage ✅
- [x] Saves hospital_name to Firebase when confirmed
- [x] Saves hospital_phone to Firebase when confirmed
- [x] Tracks hospital_confirmed timestamp

## New API Endpoints:

### POST /hospital_confirm/{accident_id}
Confirms a hospital has been picked for the accident.
- **Parameters**: 
  - `hospital_name` (query): Name of selected hospital
  - `hospital_phone` (query): Phone number of selected hospital
- **Actions**:
  - Saves hospital info to Firebase
  - Sends confirmation SMS to family
  - Sends acknowledgment SMS to hospital

### GET /hospital_status/{accident_id}
Gets the hospital confirmation status for an accident.
- **Returns**:
  - `hospital_confirmed`: boolean
  - `hospital`: {name, phone, confirmed_at}
  - `accident_status`: string

### POST /speed_alert
Already implemented - sends alarm call when user goes through high speed in accident zone.

