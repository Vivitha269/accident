# Dual Emergency Contacts + User Cancel Timer Implementation

## 1. PLAN CONFIRMATION ✅ (User approved via feedback)
- Dual contacts (2 members)
- Accident detection → 30s countdown
- User cancel within time
- Timeout → auto SMS/call to 2 contacts + hospital + police

## 2. CODE UPDATES (Next)
### 2.1 models.py ✅
- [x] Add `EmergencyContactsCreate` (list[EmergencyContactCreate], max 2)

### 2.2 routers/users.py ✅
- [x] `/emergency-contact` → accept/store list of 2 in Firestore user doc

### 2.3 routers/accidents.py ✅
- [x] `POST /cancel-accident` {accident_id}

### 2.4 emergency_service.py ✅
- [x] `start_accident_timer`: asyncio 30s, check cancel flag in Firestore
- [x] Timeout → `trigger_emergency_alerts` (2 contacts + police/hospital, parallel SMS/call)

### 2.5 POSTMAN_TESTS.md + demo script ✅
- [x] Update tests/demo + created demo_full_flow.py

## 3. TESTING
- [ ] Demo: register → 2 contacts → accident → cancel (no alert) vs timeout (alerts)

## 4. DEPLOY
- [ ] Restart uvicorn

