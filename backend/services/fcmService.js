const { messaging } = require('../config/db');

/**
 * FCM Service using Firebase Cloud Messaging (free tier)
 */
class FCMService {
  async sendToToken(token, message) {
    try {
      const response = await messaging.send({
        token,
        notification: message.notification,
        data: message.data || {}
      });
      console.log('FCM sent:', response);
      return response;
    } catch (error) {
      console.error('FCM error:', error);
      throw error;
    }
  }

  async sendToPhone(phone, message) {
    // Implement phone to FCM token mapping if needed
    // For now, log for SMS fallback
    console.log('FCM to phone:', phone, message);
  }

  async sendMulticast(tokens, message) {
    try {
      const response = await messaging.sendMulticast({
        tokens,
        notification: message.notification,
        data: message.data || {}
      });
      return response;
    } catch (error) {
      console.error('Multicast error:', error);
      throw error;
    }
  }
}

module.exports = { fcmService: new FCMService() };
