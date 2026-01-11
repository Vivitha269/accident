import os
import re
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def is_valid_phone_number(phone):
    """
    Validate phone number format.
    Accepts E.164 format: +[country code][number]
    Must be at least 10 digits, starting with +
    """
    if not phone:
        return False
    
    # Convert to string if not already
    phone_str = str(phone).strip()
    
    # Check if it starts with + (E.164 format)
    if not phone_str.startswith('+'):
        print(f"Skipping invalid phone (not E.164 format): {phone_str}")
        return False
    
    # Remove + and check if remaining is digits (10-15 digits)
    digits = phone_str[1:]
    if not digits.isdigit() or len(digits) < 10 or len(digits) > 15:
        print(f"Skipping invalid phone (wrong digit count): {phone_str}")
        return False
    
    return True

def send_sms(to_number, body):
    """
    Send SMS with proper validation to prevent Short Code errors.
    """
    # Validate phone number before attempting to send
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    try:
        client.messages.create(
            body=body, 
            from_=os.getenv('TWILIO_PHONE_NUMBER'), 
            to=to_number
        )
        print(f"SMS sent successfully to {to_number}")
    except Exception as e:
        print(f"Twilio SMS Error: {e}")

def make_call(to_number, victim_name="User"):
    """
    Make voice call with proper validation to prevent Short Code errors.
    """
    # Validate phone number before attempting to call
    if not is_valid_phone_number(to_number):
        print(f"Skipping call to invalid number: {to_number}")
        return
    
    # TwiML logic that speaks immediately
    twiml_content = f"""
    <Response>
        <Pause length="1"/>
        <Speak voice="alice">
            Emergency alert! {victim_name} has been in an accident. 
            Location details have been sent via SMS. Please help immediately.
        </Speak>
    </Response>
    """
    try:
        client.calls.create(
            twiml=twiml_content,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        print(f"Call initiated successfully to {to_number}")
    except Exception as e:
        print(f"Twilio Call Error: {e}")
