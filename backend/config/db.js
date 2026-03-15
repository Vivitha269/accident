const admin = require('firebase-admin');
const path = require('path');
const serviceAccountPath = path.join(__dirname, '../ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json'); // Copy from root

let db, messaging;

try {
  if (!admin.apps.length) {
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccountPath)
    });
  }
  db = admin.firestore();
  messaging = admin.messaging();
} catch (error) {
  console.error('Firebase init error:', error);
  process.exit(1);
}

module.exports = {
  db,
  messaging
};
