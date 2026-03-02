#!/usr/bin/env python
"""Test script to simulate sending SMS alerts for an accident."""

from twilio_config import send_sms_to_family, send_sms_to_police, send_sms_to_hospital

# Test data
test_numbers = [
    "+918838177899",    # Valid E.164
    "8838177899",       # 10-digit Indian (needs normalization)
    "+1 415 353 1664"   # US number with spaces
]

print("Testing SMS sending to various phone formats...\n")

victim_name = "Test User"
address = "123 Main Street, San Francisco"
maps_url = "https://maps.google.com"
directions = "Drive 2 miles west"
hospital_name = "General Hospital"
hospital_phone = "+16027734000"

for phone in test_numbers:
    print(f"\n--- Testing: {phone} ---")
    try:
        send_sms_to_family(
            phone,
            victim_name,
            address,
            maps_url,
            directions,
            hospital_name,
            hospital_phone
        )
        print(f"✓ SMS to family sent successfully")
    except Exception as e:
        print(f"✗ Error sending SMS: {e}")

print("\n" + "="*60)
print("SMS Test Complete!")
print("="*60)
