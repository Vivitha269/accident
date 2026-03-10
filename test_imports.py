"""Test script to check for import errors in the backend"""
import sys
import traceback

print("Testing imports...")
print("=" * 50)

# Test config
try:
    from config import db, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    print("✅ config.py imported successfully")
    print(f"   - Twilio SID: {'Configured' if TWILIO_ACCOUNT_SID else 'NOT SET'}")
    print(f"   - Database: {'Connected' if db else 'NOT Connected'}")
except Exception as e:
    print(f"❌ config.py import error: {e}")
    traceback.print_exc()

print("=" * 50)

# Test services
try:
    from services.geocoding import reverse_geocode
    print("✅ services.geocoding imported successfully")
except Exception as e:
    print(f"❌ services.geocoding import error: {e}")
    traceback.print_exc()

print("=" * 50)

try:
    from services.places import find_nearest_police, find_top_3_hospitals
    print("✅ services.places imported successfully")
except Exception as e:
    print(f"❌ services.places import error: {e}")
    traceback.print_exc()

print("=" * 50)

try:
    from services.routing import get_directions_text
    print("✅ services.routing imported successfully")
except Exception as e:
    print(f"❌ services.routing import error: {e}")
    traceback.print_exc()

print("=" * 50)

# Test twilio_config
try:
    from twilio_config import send_sms, make_call, format_phone_number
    print("✅ twilio_config imported successfully")
    
    # Test phone formatting
    test_result = format_phone_number("918825597447")
    print(f"   - Phone format test: {test_result}")
except Exception as e:
    print(f"❌ twilio_config import error: {e}")
    traceback.print_exc()

print("=" * 50)

# Test main
try:
    from main import app
    print("✅ main.py imported successfully")
    print(f"   - FastAPI app created")
except Exception as e:
    print(f"❌ main.py import error: {e}")
    traceback.print_exc()

print("=" * 50)
print("\nImport test completed!")
