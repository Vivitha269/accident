#!/usr/bin/env python3
"""Quick test to verify Twilio configuration and SMS setup"""

from twilio_config import normalize_phone_number, is_valid_phone_number
import os
from dotenv import load_dotenv

load_dotenv()

print('=== TWILIO CONNECTION TEST ===')
print(f'TWILIO_ACCOUNT_SID: {"✓ Set" if os.getenv("TWILIO_ACCOUNT_SID") else "✗ Missing"}')
print(f'TWILIO_AUTH_TOKEN: {"✓ Set" if os.getenv("TWILIO_AUTH_TOKEN") else "✗ Missing"}')
print(f'TWILIO_PHONE_NUMBER: {os.getenv("TWILIO_PHONE_NUMBER")}')

print()
print('=== PHONE NUMBER NORMALIZATION TEST ===')
test_numbers = [
    '+918838177899',
    '8838177899',
    '+1 415 353 1664',
    '9597157440'
]

for num in test_numbers:
    normalized = normalize_phone_number(num)
    is_valid = is_valid_phone_number(num)
    status = "✓ Valid" if is_valid else "✗ Invalid"
    print(f'{num:20} → {str(normalized):18} ({status})')

print()
print('✅ All checks completed!')
