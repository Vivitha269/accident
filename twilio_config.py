
import os
import re
from twilio.rest import Client
try:
    from twilio.twiml import VoiceResponse
except ImportError:
    from twilio.twiml.voice_response import VoiceResponse
from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    DEFAULT_EMERGENCY_CONTACT,
    DEFAULT_POLICE_NUMBER,
    DEFAULT_AMBULANCE_NUMBER,
    DEFAULT_HOSPITAL_NUMBER,
    MAX_SMS_RETRIES,
    CALL_RETRY_DELAY
)

# Initialize Twilio client
client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio client initialized successfully")
    except Exception as e:
        print(f"⚠️ Twilio initialization error: {e}")
else:
    print("⚠️ Twilio credentials not configured")


def format_phone_number(phone_number):
    """
    Format phone number to international format.
    Adds + prefix if missing (assumes India +91 if 10 digits).
    """
    if not phone_number:
        return None
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    # If already has +, return as is
    if cleaned.startswith('+'):
        return cleaned
    
    # If 10 digits (Indian mobile), add +91
    if len(cleaned) == 10:
        return '+91' + cleaned
    
    # If 11 digits starting with 0, replace 0 with +91
    if len(cleaned) == 11 and cleaned.startswith('0'):
        return '+91' + cleaned[1:]
    
    # If 12 digits (no +), assume +91
    if len(cleaned) == 12:
        return '+' + cleaned
    
    # Otherwise, just add +
    return '+' + cleaned


def is_valid_phone_number(phone_number):
    """Validate phone number format."""
    if not phone_number:
        return False
    
    # Format the number first
    formatted = format_phone_number(phone_number)
    if not formatted:
        return False
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', formatted)
    # Check minimum length (7 digits) and maximum (15 digits)
    if len(cleaned) < 7 or len(cleaned) > 15:
        return False
    # Must start with + for international format
    return cleaned.startswith('+')


def get_default_numbers():
    """Get default emergency numbers."""
    return {
        "emergency_contact": DEFAULT_EMERGENCY_CONTACT,
        "police": DEFAULT_POLICE_NUMBER,
        "ambulance": DEFAULT_AMBULANCE_NUMBER,
        "hospital": DEFAULT_HOSPITAL_NUMBER
    }


def send_sms(to_number, body, retry_count=0):
    """
    Send basic SMS message.
    """
    if not client:
        print("⚠️ Twilio client not initialized - SMS not sent")
        return False
    
    # Format the phone number to international format
    formatted_number = format_phone_number(to_number)
    if not formatted_number:
        print(f"Skipping SMS to invalid number: {to_number}")
        return False
    
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return False
    
    try:
        message = client.messages.create(
            body=body,
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_number
        )
        print(f"✅ SMS sent successfully to {formatted_number}, SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Twilio SMS Error: {e}")
        
        # Retry logic
        if retry_count < MAX_SMS_RETRIES:
            import time
            print(f"Retrying SMS ({retry_count + 1}/{MAX_SMS_RETRIES})...")
            time.sleep(1)
            return send_sms(to_number, body, retry_count + 1)
        
        print(f"❌ SMS failed after {MAX_SMS_RETRIES} retries")
        return False


def make_call(to_number, victim_name="User", location_info=None, retry_count=0):
    """
    Make voice call with proper validation.
    """
    if not client:
        print("⚠️ Twilio client not initialized - Call not made")
        return False
    
    if not is_valid_phone_number(to_number):
        print(f"Skipping call to invalid number: {to_number}")
        return False
    
    # Format the phone number to international format
    formatted_number = format_phone_number(to_number)
    if not formatted_number:
        print(f"Skipping call to invalid number: {to_number}")
        return False
    
    # Build location details for voice message
    location_text = ""
    if location_info:
        address = location_info.get('address', 'Unknown location')
        maps_url = location_info.get('maps_url', '')
        location_text = f" The accident location is {address}. Google maps link: {maps_url}"
    
    # TwiML with voice message
    twiml_response = VoiceResponse()
    twiml_response.say(
        voice="alice",
        language="en-US",
        rate="80"
    )
    
    # First message
    twiml_response.say(
        voice="alice",
        language="en-US"
    )
    twiml_response.say(
        f"Emergency alert! {victim_name} has been in an accident. "
        f"This is an urgent emergency call. Please respond immediately.{location_text} "
        f"Please send help to this location right away.",
        voice="alice",
        language="en-US"
    )
    
    # Second message with emphasis
    twiml_response.say(
        f"This is a life threatening emergency. "
        f"Please send emergency services immediately! "
        f"Every second counts. Please act now!",
        voice="alice",
        language="en-US",
        rate="85"
    )
    
    try:
        call = client.calls.create(
            twiml=str(twiml_response),
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_number
        )
        print(f"✅ Call initiated successfully to {formatted_number}, SID: {call.sid}")
        return True
    except Exception as e:
        print(f"Twilio Call Error: {e}")
        
        # Retry logic for calls
        if retry_count < MAX_SMS_RETRIES:
            import time
            print(f"Retrying call ({retry_count + 1}/{MAX_SMS_RETRIES}) after {CALL_RETRY_DELAY}s...")
            time.sleep(CALL_RETRY_DELAY)
            return make_call(to_number, victim_name, location_info, retry_count + 1)
        
        print(f"❌ Call failed after {MAX_SMS_RETRIES} retries")
        return False


def send_sms_with_route(to_number, victim_name, address, maps_url, directions_text=None, emergency_contact_info=None):
    """Send enhanced SMS with location and routing."""
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return False
    
    sms_text = f"🚨 EMERGENCY! {victim_name} has been in an accident.\n\n"
    sms_text += f"📍 Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n{directions_text}\n"
    
    if emergency_contact_info:
        contact_name = emergency_contact_info.get('name', 'Family')
        contact_phone = emergency_contact_info.get('phone', '')
        if contact_phone:
            sms_text += f"\n👤 Emergency Contact: {contact_name} ({contact_phone})"
    
    return send_sms(to_number, sms_text)


def send_sms_to_family(to_number, victim_name, address, maps_url, directions_text=None, hospital_name=None, hospital_phone=None):
    """Send SMS to family with location and hospital info."""
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return False
    
    sms_text = f"🚨 URGENT! {victim_name} has been in an accident!\n\n"
    sms_text += f"📍 Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n{directions_text}\n"
    
    if hospital_name:
        sms_text += f"\n🏥 Ambulance dispatched to: {hospital_name}\n"
    if hospital_phone:
        sms_text += f"📞 Hospital Phone: {hospital_phone}\n"
    
    sms_text += f"\n💝 Please rush to the hospital if possible!"
    
    return send_sms(to_number, sms_text)


def send_sms_to_police(to_number, victim_name, address, maps_url, directions_text=None, accident_lat=None, accident_lon=None):
    """Send enhanced SMS to police."""
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return False
    
    sms_text = f"🚔 POLICE ALERT! Accident Emergency!\n\n"
    sms_text += f"👤 Victim: {victim_name}\n"
    sms_text += f"📍 Location: {address}\n"
    
    if accident_lat and accident_lon:
        sms_text += f"📌 Coordinates: {accident_lat}, {accident_lon}\n"
    
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n🧭 Route to accident:\n{directions_text}\n"
    
    sms_text += f"\n⚠️ IMMEDIATE RESPONSE REQUIRED!"
    
    return send_sms(to_number, sms_text)


def send_sms_to_hospital(to_number, victim_name, address, maps_url, directions_text=None, police_station_info=None):
    """Send enhanced SMS to hospital."""
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return False
    
    sms_text = f"🏥 HOSPITAL ALERT! Accident Emergency!\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"📍 Accident Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n🧭 Route to accident:\n{directions_text}\n"
    
    if police_station_info:
        sms_text += f"\n🚔 Police also notified: {police_station_info.get('name', 'Local Police')}"
    
    sms_text += f"\n\n⚠️ PREPARED FOR EMERGENCY ADMISSION!"
    
    return send_sms(to_number, sms_text)


def send_sms_to_ambulance(to_number, victim_name, address, maps_url, directions_text=None):
    """Send SMS to ambulance service."""
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return False
    
    sms_text = f"🚑 AMBULANCE ALERT! Accident Emergency!\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"📍 Accident Location: {address}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n"
    
    if directions_text:
        sms_text += f"\n🧭 Route to accident:\n{directions_text}\n"
    
    sms_text += f"\n⚠️ URGENT! Please dispatch immediately!"
    
    return send_sms(to_number, sms_text)


def send_pickup_confirmation(to_number, victim_name, hospital_name, accident_location, maps_url):
    """Send SMS confirming ambulance pickup."""
    if not is_valid_phone_number(to_number):
        print(f"Skipping SMS to invalid number: {to_number}")
        return False
    
    sms_text = f"✅ AMBULANCE PICKUP CONFIRMED!\n\n"
    sms_text += f"👤 Patient: {victim_name}\n"
    sms_text += f"🏥 Hospital: {hospital_name}\n"
    sms_text += f"📍 Pickup Location: {accident_location}\n"
    sms_text += f"🗺️ Maps: {maps_url}\n\n"
    sms_text += f"💝 The victim is now being transported to the hospital."
    
    return send_sms(to_number, sms_text)


def play_alarm(to_number, victim_name="User", location_info=None):
    """Make emergency alarm call."""
    if not is_valid_phone_number(to_number):
        print(f"Skipping alarm call to invalid number: {to_number}")
        return False
    
    # Format the phone number
    formatted_number = format_phone_number(to_number)
    if not formatted_number:
        print(f"Skipping alarm call to invalid number: {to_number}")
        return False
    
    location_text = ""
    if location_info:
        address = location_info.get('address', 'Unknown location')
        maps_url = location_info.get('maps_url', '')
        location_text = f" Accident location: {address}. Google maps: {maps_url}"
    
    twiml_response = VoiceResponse()
    twiml_response.pause(length=1)
    
    twiml_response.say(
        f"Emergency alert! {victim_name} has been in an accident. "
        f"This is an urgent emergency call. Please respond immediately.",
        voice="alice",
        language="en-US"
    )
    
    twiml_response.play(digits="wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
    
    twiml_response.say(
        f"EMERGENCY ALERT! EMERGENCY ALERT! {victim_name} has been in a serious accident! "
        f"This is an emergency alarm. Immediate attention required! {location_text} "
        f"Please send help to this location right away. This is a life threatening emergency. "
        f"Please send emergency services immediately! This is a life threatening emergency! RESPOND NOW!",
        voice="alice",
        language="en-US",
        rate="80"
    )
    
    twiml_response.play(digits="wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
    
    twiml_response.say(
        f"IMMEDIATE EMERGENCY RESPONSE REQUIRED! {victim_name} needs help now! "
        f"{location_text} This is a critical emergency! Send help immediately!",
        voice="alice",
        language="en-US",
        rate="80"
    )
    
    twiml_response.play(digits="wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
    
    try:
        call = client.calls.create(
            twiml=str(twiml_response),
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_number
        )
        print(f"✅ Alarm call initiated successfully to {formatted_number}, SID: {call.sid}")
        return True
    except Exception as e:
        print(f"Twilio Alarm Call Error: {e}")
        return False


def speed_alert_alarm(to_number, location_info=None):
    """Make speed alert call."""
    if not is_valid_phone_number(to_number):
        print(f"Skipping speed alert to invalid number: {to_number}")
        return False
    
    # Format the phone number
    formatted_number = format_phone_number(to_number)
    if not formatted_number:
        print(f"Skipping speed alert to invalid number: {to_number}")
        return False
    
    zone_info = ""
    if location_info:
        zone_info = f" You are entering an accident alert zone at {location_info.get('address', 'this location')}."
    
    twiml_response = VoiceResponse()
    twiml_response.say(
        f"WARNING! WARNING! You are traveling at high speed in an accident zone! "
        f"{zone_info} SLOW DOWN IMMEDIATELY! "
        f"There has been an accident nearby. Drive carefully! "
        f"This is a safety warning. Please reduce your speed!",
        voice="alice",
        language="en-US",
        rate="80"
    )
    
    try:
        call = client.calls.create(
            twiml=str(twiml_response),
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_number
        )
        print(f"✅ Speed alert call initiated to {formatted_number}, SID: {call.sid}")
        return True
    except Exception as e:
        print(f"Twilio Speed Alert Error: {e}")
        return False


def send_emergency_alerts(victim_name, address, maps_url, directions_text=None, 
                          accident_lat=None, accident_lon=None,
                          emergency_contact_phone=None, hospital_info=None, police_info=None):
    """Send emergency alerts to all responders."""
    results = {
        "sms_sent": [],
        "calls_made": [],
        "errors": []
    }
    
    location_info = {
        "address": address,
        "maps_url": maps_url
    }
    
    # 1. Send SMS to emergency contact
    if emergency_contact_phone:
        success = send_sms_to_family(
            emergency_contact_phone, 
            victim_name, 
            address, 
            maps_url, 
            directions_text,
            hospital_info.get('name') if hospital_info else None,
            hospital_info.get('phone') if hospital_info else None
        )
        if success:
            results["sms_sent"].append("emergency_contact")
        else:
            results["errors"].append("emergency_contact_sms")
    
    # 2. Send SMS to police
    if police_info and police_info.get('phone'):
        success = send_sms_to_police(
            police_info['phone'],
            victim_name,
            address,
            directions_text=directions_text,
            accident_lat=accident_lat,
            accident_lon=accident_lon
        )
        if success:
            results["sms_sent"].append("police")
        else:
            results["errors"].append("police_sms")
        
        success = make_call(police_info['phone'], victim_name, location_info)
        if success:
            results["calls_made"].append("police")
        else:
            results["errors"].append("police_call")
    
    # 3. Send SMS to hospital
    if hospital_info and hospital_info.get('phone'):
        success = send_sms_to_hospital(
            hospital_info['phone'],
            victim_name,
            address,
            directions_text=directions_text,
            police_station_info=police_info
        )
        if success:
            results["sms_sent"].append("hospital")
        else:
            results["errors"].append("hospital_sms")
        
        success = make_call(hospital_info['phone'], victim_name, location_info)
        if success:
            results["calls_made"].append("hospital")
        else:
            results["errors"].append("hospital_call")
    
    # 4. Use default numbers
    defaults = get_default_numbers()
    
    if not emergency_contact_phone and defaults["emergency_contact"]:
        success = send_sms_to_family(
            defaults["emergency_contact"],
            victim_name,
            address,
            maps_url,
            directions_text
        )
        if success:
            results["sms_sent"].append("default_emergency")
    
    if not (police_info and police_info.get('phone')) and defaults["police"]:
        success = send_sms_to_police(
            defaults["police"],
            victim_name,
            address,
            maps_url,
            directions_text,
            accident_lat,
            accident_lon
        )
        if success:
            results["sms_sent"].append("default_police")
        
        make_call(defaults["police"], victim_name, location_info)
    
    if not (hospital_info and hospital_info.get('phone')):
        if defaults["ambulance"]:
            success = send_sms_to_ambulance(
                defaults["ambulance"],
                victim_name,
                address,
                maps_url,
                directions_text
            )
            if success:
                results["sms_sent"].append("default_ambulance")
            
            make_call(defaults["ambulance"], victim_name, location_info)
        
        if defaults["hospital"]:
            success = send_sms_to_hospital(
                defaults["hospital"],
                victim_name,
                address,
                maps_url,
                directions_text
            )
            if success:
                results["sms_sent"].append("default_hospital")
    
    print(f"📊 Emergency alerts summary: {results}")
    return results

