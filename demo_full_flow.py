import requests
import time
import json

BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

print("=== AI Accident Full Flow Demo ===")

# 1. Register
resp = requests.post(f"{BASE_URL}/api/register", json={
    "name": "Test User", "phone": "9876543211", "email": "test@example.com"
}, headers=headers)
user_data = resp.json()
user_id = user_data["id"]
print(f"✅1. Registered user_id: {user_id}")

# 2. Add 2 emergency contacts
resp = requests.post(f"{BASE_URL}/api/emergency-contact", json={
    "user_id": user_id,
    "contacts": [
        {"contact_name": "Contact1", "contact_phone": "9999999991"},
        {"contact_name": "Contact2", "contact_phone": "9999999992"}
    ]
}, headers=headers)
print(f"✅2. Added 2 contacts: {resp.json()}")

# 3. Log trip
requests.post(f"{BASE_URL}/api/trip-data", json={
    "user_id": user_id, "speed": 50.0, "latitude": 13.0827, "longitude": 80.2707
}, headers=headers)
print("✅3. Trip logged")

print("\n🚨4. SIMULATE TWO SCENARIOS (run separately):")

print("\n--- SCENARIO A: USER CANCELS (within 30s) ---")
print("Run in another terminal:")
print(f'curl -X POST "{BASE_URL}/api/accident-alert" -H "Content-Type: application/json" -d \'{"user_id": "{user_id}", "speed": 0, "latitude": 13.0827, "longitude": 80.2707}\'')
print("Then within 30s:")
print(f'curl -X POST "{BASE_URL}/api/cancel-accident" -H "Content-Type: application/json" -d \'{"accident_id": "ACCIDENT_ID"}\'')
print("→ Check Firestore: status=cancelled, NO alert_logs")

print("\n--- SCENARIO B: TIMEOUT → AUTO ALERTS ---")
print(f'curl -X POST "{BASE_URL}/api/accident-alert" -H "Content-Type: application/json" -d \'{"user_id": "{user_id}", "speed": 0, "latitude": 13.0827, "longitude": 80.2707}\'')
print("Wait 35s → Check Twilio (SMS/calls to 2 contacts/police/hospital), Firestore alert_logs, accident_events status=alerts_triggered")

print("\n📊 Analytics:")
analytics = requests.get(f"{BASE_URL}/api/analytics/{user_id}", headers=headers).json()
print(json.dumps(analytics, indent=2))

