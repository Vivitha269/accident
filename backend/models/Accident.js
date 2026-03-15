/**
 * Accident Model for Firestore 'accidents' collection
 */
const ACCIDENT_SCHEMA = {
  accidentId: '', // string (document ID)
  userId: '',
  name: '',
  deviceId: '',
  reportId: '',
  latitude: 0,
  longitude: 0,
  speed: 0,
  timestamp: new Date(),
  status: 'pending', // 'pending', 'confirmed', 'resolved'
  response: null, // {response: '1'|'2', timestamp: Date}
  emergencyNotified: false,
  ambulanceRequested: false
};

module.exports = {
  ACCIDENT_SCHEMA
};
