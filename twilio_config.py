import os
import re
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def normalize_phone_number(phone):
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


def is_valid_phone_number(phone):
    """
    Validate phone number format.
    Accepts E.164 format: +[country code][number]
    Also accepts 10-digit Indian numbers (will be normalized to +91).
    """
    if not phone:
        return False
    
    normalized = normalize_phone_number(phone)
    return normalized is not None

def send_sms(to_number, body):
    """
    Send SMS with proper validation and normalization to prevent errors.
    """
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    try:
        msg = client.messages.create(
            body=body, 
            from_=os.getenv('TWILIO_PHONE_NUMBER'), 
            to=normalized_number
        )
        print(f"SMS sent successfully to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        # TwilioRestException carries a code attribute we can inspect
        err_code = getattr(e, 'code', None)
        err_msg  = getattr(e, 'msg', str(e))
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        # common error codes:
        # 21608 - trial account cannot send to unverified number
        # 21610 - recipient has unsubscribed
        # 21611 - daily message limit reached
        # 20429 - too many requests (rate limit)
        return None


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
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
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
        msg = client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Enhanced SMS with route sent successfully to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        err_code = getattr(e, 'code', None)
        err_msg = getattr(e, 'msg', str(e))
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        return None


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
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
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
        msg = client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Family SMS sent successfully to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        err_code = getattr(e, 'code', None)
        err_msg = getattr(e, 'msg', str(e))
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        return None


def send_sms_to_police(to_number, victim_name, address, maps_url, directions_text, accident_lat, accident_lon):
    """
    Send enhanced SMS to police with accurate location and directions.
    """
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
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
        msg = client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Police SMS sent successfully to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        err_code = getattr(e, 'code', None)
        err_msg = getattr(e, 'msg', str(e))
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        return None


def send_sms_to_hospital(to_number, victim_name, address, maps_url, directions_text, police_station_info=None):
    """
    Send enhanced SMS to hospital with accurate location and directions.
    """
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
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
        msg = client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Hospital SMS sent successfully to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        err_code = getattr(e, 'code', None)
        err_msg = getattr(e, 'msg', str(e))
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        return None


def send_pickup_confirmation(to_number, victim_name, hospital_name, accident_location, maps_url):
    """
    Send SMS confirming ambulance has picked up the victim.
    """
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    sms_text = f"✅ AMBULANCE PICKUP CONFIRMED!\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"🏥 Hospital: {hospital_name}\n"
    sms_text += f"📍 Pickup Location: {accident_location}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n\n"
    sms_text += f"💝 The victim is now being transported to the hospital."
    
    try:
        msg = client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Pickup confirmation SMS sent to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        err_code = getattr(e, 'code', None)
        err_msg = getattr(e, 'msg', str(e))
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        return None


def play_alarm(to_number, victim_name="User", location_info=None):
    """
    Make emergency alarm call to alert about accident.
    Plays loud alarm sound to notify everyone nearby.
    
    Args:
        to_number: The phone number to call
        victim_name: Name of the victim
        location_info: Dictionary with 'address' and 'maps_url' keys
    """
    # Normalize phone number before attempting to call
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
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
    
    # Insert actual location text into the TwiML and initiate the call
    twiml_content = twiml_content.replace("{locationText}", location_text)

    try:
        client.calls.create(
            twiml=twiml_content,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Alarm call initiated successfully to {normalized_number}")
    except Exception as e:
        print(f"Twilio Alarm Call Error: {e}")


def make_call(to_number, victim_name="User", location_info=None):
    """
    Make a concise emergency voice call providing victim name and location.
    This is a general-purpose call used for notifying family, police, or hospitals.
    """
    # Normalize phone number before attempting to call
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping call to invalid number: {to_number}")
        return

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
        client.calls.create(
            twiml=twiml,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Call initiated successfully to {normalized_number}")
    except Exception as e:
        print(f"Twilio Call Error: {e}")


def speed_alert_alarm(to_number, location_info=None):
    """
    Make speed alert call to warn about speeding in accident zone.
    
    Args:
        to_number: Phone number to call
        location_info: Dictionary with zone info
    """
    # Normalize phone number before attempting to call
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
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
            to=normalized_number
        )
        print(f"Speed alert call initiated to {normalized_number}")
    except Exception as e:
        print(f"Twilio Speed Alert Error: {e}")


def send_hospital_confirmation(to_number, victim_name, hospital_name, hospital_phone, accident_location, maps_url):
    """
    Send SMS confirming hospital has been dispatched/confirmed for the accident.
    This is sent to the family to inform them which hospital is responding.
    
    Args:
        to_number: Family member's phone number
        victim_name: Name of the victim: Name of confirmed
        hospital_name hospital
        hospital_phone: Hospital phone number
        accident_location: Human-readable accident location
        maps_url: Google Maps link to accident
    """
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    sms_text = f"✅ HOSPITAL CONFIRMED - {victim_name}'s Accident\n\n"
    sms_text += f"🏥 Hospital: {hospital_name}\n"
    sms_text += f"📞 Hospital Phone: {hospital_phone}\n"
    sms_text += f"📍 Accident Location: {accident_location}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n\n"
    sms_text += f"💝 The hospital has been notified and ambulance is being dispatched. "
    sms_text += f"Please stay at the location or contact the hospital for updates."
    
    try:
        msg = client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Hospital confirmation SMS sent to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        err_code = getattr(e, 'code', None)
        err_msg = getattr(e, 'msg', str(e))
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        return None


def send_hospital_acknowledgment(to_number, victim_name, accident_location, maps_url, contact_name=None, contact_phone=None):
    """
    Send acknowledgment SMS to hospital confirming their response has been received.
    
    Args:
        to_number: Hospital's phone number
        victim_name: Name of the victim
        accident_location: Human-readable accident location
        maps_url: Google Maps link to accident
        contact_name: Name of emergency contact (optional)
        contact_phone: Phone of emergency contact (optional)
    """
    # Normalize phone number before attempting to send
    normalized_number = normalize_phone_number(to_number)
    if not normalized_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return
    
    sms_text = f"✅ HOSPITAL RESPONSE CONFIRMED\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"📍 Accident Location: {accident_location}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if contact_name and contact_phone:
        sms_text += f"\n👤 Family Contact: {contact_name} ({contact_phone})"
    
    sms_text += f"\n\n✅ Your hospital has been selected for this emergency. "
    sms_text += f"The victim's family has been notified of your dispatch."
    
    try:
        msg = client.messages.create(
            body=sms_text,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=normalized_number
        )
        print(f"Hospital acknowledgment SMS sent to {normalized_number} (sid={msg.sid})")
        return msg.sid
    except Exception as e:
        err_code = getattr(e, 'code', None)
        err_msg = getattr(e, 'msg', str(e))
        print(f"Twilio SMS Error (code={err_code}): {err_msg}")
        return None
