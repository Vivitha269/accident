from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def send_sms(to_number, body):
    client.messages.create(body=body, from_=os.getenv('TWILIO_PHONE_NUMBER'), to=to_number)

def make_call(to_number, victim_name):
    # The call now speaks the specific name of the user who had the accident
    twiml_content = f"""
    <Response>
        <Pause length="1"/>
        <Speak voice="alice">
            Emergency alert! An accident has been detected for {victim_name}. 
            A message with the exact Google Maps location has been sent to this number. 
            Please respond immediately.
        </Speak>
    </Response>
    """
    client.calls.create(
        twiml=twiml_content,
        from_=os.getenv('TWILIO_PHONE_NUMBER'),
        to=to_number
    )
