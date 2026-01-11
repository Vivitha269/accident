import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def send_sms(to_number, body):
    # SAFETY CHECK: Only send if it's a real 10-digit mobile number
    if len(str(to_number)) < 10:
        print(f"Skipping SMS to short code: {to_number}")
        return
    
    try:
        client.messages.create(
            body=body, 
            from_=os.getenv('TWILIO_PHONE_NUMBER'), 
            to=to_number
        )
    except Exception as e:
        print(f"Twilio SMS Error: {e}")

def make_call(to_number, victim_name="User"):
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
    except Exception as e:
        print(f"Twilio Call Error: {e}")