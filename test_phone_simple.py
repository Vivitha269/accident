"""
Simple test to verify phone number formatting.
"""
import re

def format_phone_number(phone_number):
    """Format phone number to international format."""
    if not phone_number:
        return None
    
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    if cleaned.startswith('+'):
        return cleaned
    
    if len(cleaned) == 10:
        return '+91' + cleaned
    
    if len(cleaned) == 11 and cleaned.startswith('0'):
        return '+91' + cleaned[1:]
    
    if len(cleaned) == 12:
        return '+' + cleaned
    
    return '+' + cleaned


# Test cases
tests = [
    ("918825597447", "+918825597447"),
    ("+918825597447", "+918825597447"),
    ("0918825597447", "+918825597447"),
]

print("Testing phone number formatting:")
print("-" * 40)

for input_phone, expected in tests:
    result = format_phone_number(input_phone)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    print(f"{status}: '{input_phone}' -> '{result}' (expected: '{expected}')")

print("-" * 40)
print(f"\nSpecific test for 918825597447:")
result = format_phone_number("918825597447")
print(f"Result: {result}")
print(f"Expected: +918825597447")
print(f"Match: {result == '+918825597447'}")

