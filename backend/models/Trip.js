/**
 * Trip Model for Firestore 'trips' collection: trips/{userId}/{tripId}
 */
const TRIP_SCHEMA = {
  tripId: '', // string (document ID)
  userId: '',
  speed: 0,
  latitude: 0,
  longitude: 0,
  timestamp: new Date(),
  accidentDetected: false,
  duration: 0 // seconds
};

module.exports = {
  TRIP_SCHEMA
};
