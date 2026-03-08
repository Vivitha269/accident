"""
Twilio Configuration Module
Handles SMS sending and voice calls for the Accident Detection System.
"""

import os
import re
from typing import Optional
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Lazy initialization of Twilio client
_twilio_client: Optional[Client] = None


def get_twilio_client() -> Client:
    """Get or create Twilio client with lazy initialization."""
    global _twilio_client
    if _twilio_client is None:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        if not account_sid or not auth_token:
            raise ValueError("Twilio credentials not configured. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        _twilio_client = Client(account_sid, auth_token)
    return _twilio_client


def normalize_phone_number(phone: str) -> Optional[str]:
    """
    Normalize phone number to E.164 format for Twilio.
    Converts Indian numbers (10-digit or +91) to proper E.164 format.
    
    Returns formatted number or None if invalid.
    """
    if not phone:
        return None
    
    # Convert to string if not already
    phone_str = str(phone).strip()
    
    # Remove spaces, hyphens, parentheses
    phone_str = phone_str.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # If it already starts with +, validate it
    if phone_str.startswith('+'):
        digits = phone_str[1:]
        if digits.isdigit() and 10 <= len(digits) <= 15:
            return phone_str
        else:
            print(f"Invalid phone format: {phone}")
            return None
    
    # If it's exactly 10 digits, assume Indian number
    if phone_str.isdigit() and len(phone_str) == 10:
        return f"+91{phone_str}"
    
    # If it's 12 digits starting with 91 (India country code)
    if phone_str.isdigit() and len(phone_str) == 12 and phone_str.startswith('91'):
        return f"+{phone_str}"
    
    # If it's 11-13 digits, assume country code is included
    if phone_str.isdigit() and 11 <= len(phone_str) <= 13:
        return f"+{phone_str}"
    
    print(f"Cannot normalize phone number: {phone}")
    return None


def is_valid_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    Accepts E.164 format: +[country code][number]
    Also accepts 10-digit Indian numbers (will be normalized to +91).
    """
    if not phone:
        return False
    
    normalized = normalize_phone_number(phone)
    return normalized is not None


def send_sms(to_number: str, body: str) -> Optional[str]:
    """
    Send SMS with proper validation and normalization to prevent errors.
    Returns message SID on success, None on failure.
    """
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return None
    
    try:
        client = get_twilio_client()
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        if not from_number:
            print("TWILIO_PHONE_NUMBER not configured")
            return None
            
        msg = client.messages.create(
            body=body, 
            from_=from_number, 
            to=normalized_number
        )
        print(f"SMS sent successfully to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        # TwilioRestException carries a code attribute we can inspect
        err_code = getattr(e, 'code', None)
        err_msg = str(e)
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        # common error codes:
        # 21608 - trial account cannot send to unverified number
        # 21610 - recipient has unsubscribed
        # 21611 - daily message limit reached
        # 20429 - too many requests (rate limit)
        return None


def send_sms_with_route(to_number: str, victim_name: str, address: str, 
                        maps_url: str, directions_text: str = None, 
                        emergency_contact_info: dict = None) -> Optional[str]:
    """
    Send enhanced SMS with location, routing/directions, and emergency contact info.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return None
    
    # Build the SMS message
    sms_text = f"🚨 EMERGENCY! {victim_name} has been in an accident.\n"
    sms_text += f"📍 Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n{directions_text}\n"
    
    if emergency_contact_info:
        contact_name = emergency_contact_info.get('name', 'Family')
        contact_phone = emergency_contact_info.get('phone', '')
        if contact_phone:
            sms_text += f"\n👤 Emergency Contact: {contact_name} ({contact_phone})"
    
    return send_sms(normalized_number, sms_text)


def send_sms_to_family(to_number: str, victim_name: str, address: str, 
                       maps_url: str, directions_text: str = None,
                       hospital_name: str = None, hospital_phone: str = None) -> Optional[str]:
    """
    Send SMS to family with location, routing, directions, and hospital info.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return None
    
    sms_text = f"🚨 URGENT! {victim_name} has been in an accident!\n\n"
    sms_text += f"📍 Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n{directions_text}\n"
    
    if hospital_name and hospital_phone:
        sms_text += f"\n🏥 Ambulance dispatched to: {hospital_name}\n"
        sms_text += f"📞 Hospital Phone: {hospital_phone}\n"
    
    sms_text += f"\n💝 Please rush to the hospital if possible!"
    
    return send_sms(normalized_number, sms_text)


def send_sms_to_police(to_number: str, victim_name: str, address: str, 
                       maps_url: str, directions_text: str = None,
                       accident_lat: float = None, accident_lon: float = None) -> Optional[str]:
    """
    Send enhanced SMS to police with accurate location and directions.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return None
    
    sms_text = f"🚔 POLICE ALERT! Accident Emergency!\n\n"
    sms_text += f"👤 Victim: {victim_name}\n"
    sms_text += f"📍 Location: {address}\n"
    if accident_lat and accident_lon:
        sms_text += f"📌 Coordinates: {accident_lat}, {accident_lon}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n🧭 Route to accident:\n{directions_text}\n"
    
    sms_text += f"\n⚠️ IMMEDIATE RESPONSE REQUIRED!"
    
    return send_sms(normalized_number, sms_text)


def send_sms_to_hospital(to_number: str, victim_name: str, address: str, 
                         maps_url: str, directions_text: str = None,
                         police_station_info: dict = None) -> Optional[str]:
    """
    Send enhanced SMS to hospital with accurate location and directions.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return None
    
    sms_text = f"🏥 HOSPITAL ALERT! Accident Emergency!\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"📍 Accident Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n🧭 Route to accident:\n{directions_text}\n"
    
    if police_station_info:
        sms_text += f"\n🚔 Police also notified: {police_station_info.get('name', 'Local Police')}"
    
    sms_text += f"\n\n⚠️ PREPARED FOR EMERGENCY ADMISSION!"
    
    return send_sms(normalized_number, sms_text)


def send_pickup_confirmation(to_number: str, victim_name: str, hospital_name: str, 
                              accident_location: str, maps_url: str) -> Optional[str]:
    """
    Send SMS confirming ambulance has picked up the victim.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return None
    
    sms_text = f"✅ AMBULANCE PICKUP CONFIRMED!\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"🏥 Hospital: {hospital_name}\n"
    sms_text += f"📍 Pickup Location: {accident_location}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n\n"
    sms_text += f"💝 The victim is now being transported to the hospital."
    
    return send_sms(normalized_number, sms_text)


def play_alarm(to_number: str, victim_name: str = "User", location_info: dict = None) -> bool:
    """
    Make emergency alarm call to alert about accident.
    Plays loud alarm sound to notify everyone nearby.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping alarm call to invalid number: {to_number}")
        return False
    
    # Build location details for alarm message
    location_text = ""
    if location_info:
        address = location_info.get('address', 'Unknown location')
        maps_url = location_info.get('maps_url', '')
        location_text = f" Accident location: {address}. Google maps: {maps_url}"
    
    # Alarm TwiML
    twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US" rate="80">
            EMERGENCY ALERT! EMERGENCY ALERT!
            {victim_name} has been in a serious accident!
            This is an emergency alarm. Immediate attention required!
            {location_text}
            Please send emergency services immediately!
            This is a life threatening emergency!
            RESPOND NOW!
        </Say>
    </Response>
    """
    
    try:
        client = get_twilio_client()
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        if not from_number:
            print("TWILIO_PHONE_NUMBER not configured")
            return False
            
        client.calls.create(
            twiml=twiml_content,
            from_=from_number,
            to=normalized_number
        )
        print(f"Alarm call initiated successfully to {normalized_number}")
        return True
    except Exception as e:
        print(f"Twilio Alarm Call Error: {e}")
        return False


def make_call(to_number: str, victim_name: str = "User", location_info: dict = None) -> bool:
    """
    Make a concise emergency voice call providing victim name and location.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping call to invalid number: {to_number}")
        return False
    
    address = "Unknown location"
    maps = ""
    if location_info:
        address = location_info.get('address', address)
        maps = location_info.get('maps_url', '')
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US" rate="80">
            Emergency notification. {victim_name} has been in an accident at {address}.
            {(' Google Maps link: ' + maps) if maps else ''}
            Please respond immediately and contact emergency services.
        </Say>
    </Response>
    """
    
    try:
        client = get_twilio_client()
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        if not from_number:
            print("TWILIO_PHONE_NUMBER not configured")
            return False
            
        client.calls.create(
            twiml=twiml,
            from_=from_number,
            to=normalized_number
        )
        print(f"Call initiated successfully to {normalized_number}")
        return True
    except Exception as e:
        print(f"Twilio Call Error: {e}")
        return False


def speed_alert_alarm(to_number: str, location_info: dict = None) -> bool:
    """
    Make speed alert call to warn about speeding in accident zone.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping speed alert to invalid number: {to_number}")
        return False
    
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
        client = get_twilio_client()
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        if not from_number:
            print("TWILIO_PHONE_NUMBER not configured")
            return False
            
        client.calls.create(
            twiml=twiml_content,
            from_=from_number,
            to=normalized_number
        )
        print(f"Speed alert call initiated to {normalized_number}")
        return True
    except Exception as e:
        print(f"Twilio Speed Alert Error: {e}")
        return False


def send_hospital_confirmation(to_number: str, victim_name: str, hospital_name: str, 
                               hospital_phone: str, accident_location: str, 
                               maps_url: str) -> Optional[str]:
    """
    Send SMS confirming hospital has been dispatched for the accident.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return None
    
    sms_text = f"✅ HOSPITAL CONFIRMED - {victim_name}'s Accident\n\n"
    sms_text += f"🏥 Hospital: {hospital_name}\n"
    sms_text += f"📞 Hospital Phone: {hospital_phone}\n"
    sms_text += f"📍 Accident Location: {accident_location}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n\n"
    sms_text += f"💝 The hospital has been notified and ambulance is being dispatched. "
    sms_text += f"Please stay at the location or contact the hospital for updates."
    
    return send_sms(normalized_number, sms_text)


def send_hospital_acknowledgment(to_number: str, victim_name: str, accident_location: str, 
                                   maps_url: str, contact_name: str = None, 
                                   contact_phone: str = None) -> Optional[str]:
    """
    Send acknowledgment SMS to hospital confirming their response has been received.
    """
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return None
    
    sms_text = f"✅ HOSPITAL RESPONSE CONFIRMED\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"📍 Accident Location: {accident_location}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if contact_name and contact_phone:
        sms_text += f"\n👤 Family Contact: {contact_name} ({contact_phone})"
    
    sms_text += f"\n\n✅ Your hospital has been selected for this emergency. "
    sms_text += f"The victim's family has been notified of your dispatch."
    
    return send_sms(normalized_number, sms_text)

