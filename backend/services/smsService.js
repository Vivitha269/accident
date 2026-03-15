const twilio = require('twilio');
require('dotenv').config();

let client;

try {
  client = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);
} catch (error) {
  console.error('Twilio init error:', error);
}

class SMSService {
  async sendSMS(to, message) {
    if (!client) {
      console.log('Twilio not configured, skipping SMS');
      return;
    }

    try {
      const response = await client.messages.create({
        body: message,
        from: process.env.TWILIO_PHONE_NUMBER,
        to
      });
      console.log('SMS sent:', response.sid);
      return response;
    } catch (error) {
      console.error('SMS error:', error);
      throw error;
    }
  }
}

module.exports = { smsService: new SMSService() };
