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


def send_sms_with_route(to_number, victim_name, address, maps_url, directions_text, emergency_contact_info=None):
    """
    Send enhanced SMS with location, routing/directions, and emergency contact info.
    
    Args:
        to_number: Phone number to send SMS to
        victim_name: Name of the victim
        address: Human-readable address of accident
        maps_url: Google Maps link
        directions_text: Turn-by-turn directions
        emergency_contact_info: Dict with 'name' and 'phone' of emergency contact
    """
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    # Build the SMS message
    sms_text = f"🚨 EMERGENCY! {victim_name} has been in an accident.\n"
    sms_text += f"📍 Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    # Add directions if available
    if directions_text:
        sms_text += f"\n{directions_text}\n"
    
    # Add emergency contact info
    if emergency_contact_info:
        contact_name = emergency_contact_info.get('name', 'Family')
        contact_phone = emergency_contact_info.get('phone', '')
        if contact_phone:
            sms_text += f"\n👤 Emergency Contact: {contact_name} ({contact_phone})"
    
    try:
        client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        print(f"Enhanced SMS with route sent successfully to {to_number}")
    except Exception as e:
        print(f"Twilio SMS Error: {e}")


def send_sms_to_family(to_number, victim_name, address, maps_url, directions_text, hospital_name, hospital_phone):
    """
    Send SMS to family with location, routing, directions, and hospital info.
    
    Args:
        to_number: Family member's phone number
        victim_name: Name of the victim
        address: Human-readable address
        maps_url: Google Maps link
        directions_text: Turn-by-turn directions
        hospital_name: Name of hospital
        hospital_phone: Hospital phone number
    """
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    sms_text = f"🚨 URGENT! {victim_name} has been in an accident!\n\n"
    sms_text += f"📍 Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n{directions_text}\n"
    
    sms_text += f"\n🏥 Ambulance dispatched to: {hospital_name}\n"
    sms_text += f"📞 Hospital Phone: {hospital_phone}\n"
    sms_text += f"\n💝 Please rush to the hospital if possible!"
    
    try:
        client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        print(f"Family SMS sent successfully to {to_number}")
    except Exception as e:
        print(f"Twilio SMS Error: {e}")


def send_sms_to_police(to_number, victim_name, address, maps_url, directions_text, accident_lat, accident_lon):
    """
    Send enhanced SMS to police with accurate location and directions.
    """
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    sms_text = f"🚔 POLICE ALERT! Accident Emergency!\n\n"
    sms_text += f"👤 Victim: {victim_name}\n"
    sms_text += f"📍 Location: {address}\n"
    sms_text += f"📌 Coordinates: {accident_lat}, {accident_lon}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n🧭 Route to accident:\n{directions_text}\n"
    
    sms_text += f"\n⚠️ IMMEDIATE RESPONSE REQUIRED!"
    
    try:
        client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        print(f"Police SMS sent successfully to {to_number}")
    except Exception as e:
        print(f"Twilio SMS Error: {e}")


def send_sms_to_hospital(to_number, victim_name, address, maps_url, directions_text, police_station_info=None):
    """
    Send enhanced SMS to hospital with accurate location and directions.
    """
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    sms_text = f"🏥 HOSPITAL ALERT! Accident Emergency!\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"📍 Accident Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n🧭 Route to accident:\n{directions_text}\n"
    
    if police_station_info:
        sms_text += f"\n🚔 Police also notified: {police_station_info.get('name', 'Local Police')}"
    
    sms_text += f"\n\n⚠️ PREPARED FOR EMERGENCY ADMISSION!"
    
    try:
        client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        print(f"Hospital SMS sent successfully to {to_number}")
    except Exception as e:
        print(f"Twilio SMS Error: {e}")


def send_pickup_confirmation(to_number, victim_name, hospital_name, accident_location, maps_url):
    """
    Send SMS confirming ambulance has picked up the victim.
    """
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    sms_text = f"✅ AMBULANCE PICKUP CONFIRMED!\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"🏥 Hospital: {hospital_name}\n"
    sms_text += f"📍 Pickup Location: {accident_location}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n\n"
    sms_text += f"💝 The victim is now being transported to the hospital."
    
    try:
        client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        print(f"Pickup confirmation SMS sent to {to_number}")
    except Exception as e:
        print(f"Twilio SMS Error: {e}")


def play_alarm(to_number, victim_name="User", location_info=None):
    """
    Make emergency alarm call to alert about accident.
    Plays loud alarm sound to notify everyone nearby.
    
    Args:
        to_number: The phone number to call
        victim_name: Name of the victim
        location_info: Dictionary with 'address' and 'maps_url' keys
    """
    # Validate phone number before attempting to call
    if not is_valid_phone_number(to_number):
        print(f"Skipping alarm call to invalid number: {to_number}")
        return
    
    # Build location details for alarm message
    location_text = ""
    if location_info:
        address = location_info.get('address', 'Unknown location')
        maps_url = location_info.get('maps_url', '')
        location_text = f" Accident location: {address}. Google maps: {maps_url}"
    
    # Alarm TwiML - uses loud, urgent tones and repeated messages
    twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Play digits="wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww"/>
        <Say voice="alice" language="en-US" rate="80">
            EMERGENCY ALERT! EMERGENCY ALERT!
            {victim_name} has been in a serious accident!
            This is an emergency alarm. Immediate attention required!
            {location_text}
            Please send emergency services immediately!
            This is a life threatening emergency!
            RESPOND NOW!
        </Say>
        <Play digits="wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww"/>
        <Say voice="alice" language="en-US" rate="80">
            IMMEDIATE EMERGENCY RESPONSE REQUIRED!
            {victim_name} needs help now!
            {locationText}
            This is a critical emergency! Send help immediately!
        </Say>
        <Play digits="wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww"/>
    </Response>
    """
    
    # Fix the variable name in the TwiML
    twiml_content = twiml_content.replace("{locationText}", "{location_text}")
    
    try:
        client.calls.create(
            twiml=twiml_content,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        print(f"Alarm call initiated successfully to {to_number}")
    except Exception as e:
        print(f"Twilio Alarm Call Error: {e}")


def speed_alert_alarm(to_number, location_info=None):
    """
    Make speed alert call to warn about speeding in accident zone.
    
    Args:
        to_number: Phone number to call
        location_info: Dictionary with zone info
    """
    if not is_valid_phone_number(to_number):
        print(f"Skipping speed alert to invalid number: {to_number}")
        return
    
    zone_info = ""
    if location_info:
        zone_info = f" You are entering an accident alert zone at {location_info.get('address', 'this location')}."
    
    twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US" rate="80">
            WARNING! WARNING!
            You are traveling at high speed in an accident zone!
            {zone_info}
            SLOW DOWN IMMEDIATELY!
            There has been an accident nearby. Drive carefully!
            This is a safety warning. Please reduce your speed!
        </Say>
    </Response>
    """
    
    try:
        client.calls.create(
            twiml=twiml_content,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        print(f"Speed alert call initiated to {to_number}")
    except Exception as e:
        print(f"Twilio Speed Alert Error: {e}")
