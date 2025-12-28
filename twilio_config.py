from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def send_sms(to_number, body):
    client.messages.create(body=body, from_=os.getenv('TWILIO_PHONE_NUMBER'), to=to_number)

def make_call(to_number):
    # This uses a standard Twilio demo XML that speaks a message to the receiver
    client.calls.create(
        twiml='<Response><Speak> Emergency alert! An accident has been detected for your contact Vivitha. Please check your messages for the location map.</Speak></Response>',
        from_=os.getenv('TWILIO_PHONE_NUMBER'),
        to=to_number
    )