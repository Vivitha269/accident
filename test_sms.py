#!/usr/bin/env python
"""Test script to diagnose SMS sending issues."""

from config import db
from twilio_config import is_valid_phone_number, send_sms
import os

print("=" * 60)
print("SMS SENDING DIAGNOSIS")
print("=" * 60)

# Check Twilio credentials
print("\n1. CHECKING TWILIO CREDENTIALS:")
print(f"   Account SID: {os.getenv('TWILIO_ACCOUNT_SID')[:10]}...")
print(f"   Auth Token: {os.getenv('TWILIO_AUTH_TOKEN')[:10]}...")
print(f"   From Number: {os.getenv('TWILIO_PHONE_NUMBER')}")

# Check users and their emergency contacts
print("\n2. CHECKING FIRESTORE USER CONTACTS:")
users = db.collection('users').stream()
user_count = 0
valid_phones = 0
invalid_phones = 0

for user in users:
    user_data = user.to_dict()
    user_count += 1
    print(f"\n   User ID: {user.id}")
    contacts = user_data.get('emergencyContacts', [])
    print(f"   Emergency Contacts: {contacts}")
    
    # Check if contacts are valid
    if isinstance(contacts, list):
        for i, contact in enumerate(contacts):
            if isinstance(contact, dict):
                phone = contact.get('phone') or contact.get('phoneNumber') or contact.get('mobile')
                is_valid = is_valid_phone_number(phone)
                print(f"      Contact {i}: {phone} - Valid: {is_valid}")
                if is_valid:
                    valid_phones += 1
                else:
                    invalid_phones += 1

print(f"\n   SUMMARY: {user_count} users, {valid_phones} valid phones, {invalid_phones} invalid phones")

# Check police and hospital numbers
print("\n3. CHECKING OVERPASS API PHONE NUMBERS:")
from services.places import find_nearest_police, find_top_3_hospitals

try:
    # Test with a sample location (San Francisco)
    test_lat, test_lon = 37.7749, -122.4194
    
    police = find_nearest_police(test_lat, test_lon)
    if police:
        police_phone = police.get('phone')
        print(f"\n   Nearest Police:")
        print(f"      Name: {police.get('name')}")
        print(f"      Phone: {police_phone}")
        print(f"      Valid: {is_valid_phone_number(police_phone)}")
    
    hospitals = find_top_3_hospitals(test_lat, test_lon)
    if hospitals:
        hospital = hospitals[0]
        hospital_phone = hospital.get('phone')
        print(f"\n   Top Hospital:")
        print(f"      Name: {hospital.get('name')}")
        print(f"      Phone: {hospital_phone}")
        print(f"      Valid: {is_valid_phone_number(hospital_phone)}")
        
except Exception as e:
    print(f"   ERROR testing Overpass API: {e}")
    import traceback
    traceback.print_exc()

# Test actual SMS sending with a test number (if available)
print("\n4. TESTING SMS SENDING:")
test_number = os.getenv('TEST_PHONE_NUMBER')
if test_number:
    print(f"   Sending test SMS to: {test_number}")
    try:
        send_sms(test_number, "Test SMS from accident detection system")
        print("   SMS sent successfully!")
    except Exception as e:
        print(f"   ERROR: {e}")
else:
    print("   No TEST_PHONE_NUMBER in .env file")
    print("   Add TEST_PHONE_NUMBER='+1234567890' to .env to test SMS sending")

print("\n" + "=" * 60)
