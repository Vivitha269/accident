/**
 * User Model for Firestore 'users' collection
 */
const USER_SCHEMA = {
  userId: '', // string (document ID)
  name: '',
  phoneNumber: '',
  email: '',
  vehicleType: '',
  emergencyContacts: [], // array of {phone: string, name: string, relation: string}
  fcmToken: '', // for notifications
  createdAt: new Date(),
  updatedAt: new Date()
};

const EMERGENCY_CONTACT_SCHEMA = {
  phone: '',
  name: '',
  relation: ''
};

module.exports = {
  USER_SCHEMA,
  EMERGENCY_CONTACT_SCHEMA
};
