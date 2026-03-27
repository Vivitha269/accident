import os
import re
import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Twilio Credentials from .env or config
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio Client
client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio client initialized successfully")
    except Exception as e:
        print(f"⚠️ Twilio Init Error: {e}")
else:
    print("⚠️ Twilio credentials missing in environment variables")

def format_phone_number(phone: str) -> str:
    """Standardizes phone numbers to E.164 format (e.g., +919042389839)."""
    if not phone:
        return None
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', str(phone))
    if cleaned.startswith('+'):
        return cleaned
    # Default to India (+91) if 10 digits
    if len(cleaned) == 10:
        return f"+91{cleaned}"
    return f"+{cleaned}"

async def send_sms(to_number: str, message: str):
    """
    Sends an SMS asynchronously. 
    Trial accounts are limited to 160 characters.
    """
    if not client:
        logger.error("Twilio client not initialized")
        return False
    
    try:
        formatted_to = format_phone_number(to_number)
        
        # Trial account truncation to ensure links aren't broken
        body = (message[:157] + "...") if len(message) > 160 else message
        
        msg = client.messages.create(
            body=body,
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_to
        )
        print(f"✅ SMS sent to {formatted_to}, SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"❌ Twilio SMS Error to {to_number}: {e}")
        return False

async def make_call(to_number: str, voice_message: str):
    """
    Initiates an automatic voice call asynchronously.
    The voice_message string is what the person hears.
    """
    if not client:
        logger.error("Twilio client not initialized")
        return False
        
    try:
        formatted_to = format_phone_number(to_number)
        
        # Create TwiML for the voice response
        response = VoiceResponse()
        response.say(voice_message, voice="alice", language="en-IN")
        
        call = client.calls.create(
            twiml=str(response),
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_to
        )
        print(f"✅ Call initiated to {formatted_to}, SID: {call.sid}")
        return True
    except Exception as e:
        print(f"❌ Twilio Call Error to {to_number}: {e}")
        return False

# --- Advanced Functions (Optional/Extended) ---

async def send_emergency_alerts(victim_name, address, maps_url, contacts):
    """Utility to send alerts to multiple people at once."""
    for contact in contacts:
        phone = contact.get('contact_phone') or contact.get('phone')
        if phone:
            # Send SMS
            await send_sms(phone, f"🚨 EMERGENCY: {victim_name} in accident at {address}. Map: {maps_url}")
            # Trigger Call
            await make_call(phone, f"This is an emergency alert. {victim_name} has been in an accident.")