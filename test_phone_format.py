"""
Test script to verify phone number formatting is working correctly.
Run this to check if "918825597447" gets converted to "+918825597447"
"""

# Import the format function from twilio_config
import sys
sys.path.insert(0, '.')

# Test the phone number formatting
test_cases = [
    "918825597447",      # 10 digits - should become +918825597447
    "+918825597447",     # Already has + - should stay +918825597447
    "0918825597447",     # 11 digits with 0 - should become +9188255597447
    "918 825 597447",    # With spaces - should become +918825597447
    "+1 555 123 4567",   # US number - should stay +15551234567
    "5551234567",         # 10 digits US - should become +15551234567
]

print("=" * 60)
print("Testing Phone Number Formatting")
print("=" * 60)

# Test format_phone_number function directly
from twilio_config import format_phone_number, is_valid_phone_number

for phone in test_cases:
    formatted = format_phone_number(phone)
    is_valid = is_valid_phone_number(phone)
    print(f"\nInput:  '{phone}'")
    print(f"Output: '{formatted}'")
    print(f"Valid:  {is_valid}")

print("\n" + "=" * 60)
print("Testing the specific case: 918825597447")
print("=" * 60)

result = format_phone_number("918825597447")
print(f"\nformat_phone_number('918825597447') = '{result}'")

if result == "+918825597447":
    print("\n✅ SUCCESS! Phone number is correctly formatted!")
else:
    print(f"\n❌ FAILED! Expected '+918825597447' but got '{result}'")

print("\n" + "=" * 60)
print("Testing is_valid_phone_number")
print("=" * 60)

test_valid = is_valid_phone_number("918825597447")
print(f"\nis_valid_phone_number('918825597447') = {test_valid}")
print(f"is_valid_phone_number('+918825597447') = {is_valid_phone_number('+918825597447')}")

