const { db } = require('../config/db');
const smsService = require('../services/smsService').smsService;
const Joi = require('joi');

const accidentSchema = Joi.object({
  userId: Joi.string().required(),
  latitude: Joi.number().required(),
  longitude: Joi.number().required(),
  speed: Joi.number().required(),
  timestamp: Joi.date()
});

const responseSchema = Joi.object({
  accidentId: Joi.string().required(),
  response: Joi.string().valid('1', '2').required()
});

// New schemas for required endpoints
const accidentV1Schema = Joi.object({
  userId: Joi.string().required(),
  name: Joi.string().min(2).required(),
  latitude: Joi.number().required(),
  longitude: Joi.number().required(),
  deviceId: Joi.string().required()
});

const accidentV2Schema = Joi.object({
  reportId: Joi.string().required(),
  userId: Joi.string().required(),
  latitude: Joi.number().required(),
  longitude: Joi.number().required(),
  timestamp: Joi.date()
});

exports.accidentAlert = async (req, res) => {
  try {
    const { error } = accidentSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const { userId, latitude, longitude, speed, timestamp = new Date() } = req.body;

    const userDoc = await db.collection('users').doc(userId).get();
    if (!userDoc.exists) {
      return res.status(404).json({ error: 'User not found' });
    }

    const userData = userDoc.data();
    const accidentId = db.collection('accidents').doc().id;

    const accidentData = {
      accidentId,
      userId,
      latitude,
      longitude,
      speed,
      timestamp,
      status: 'pending',
      emergencyNotified: false,
      ambulanceRequested: false
    };

    await db.collection('accidents').doc(accidentId).set(accidentData);

    if (userData.emergencyContacts && userData.emergencyContacts.length > 0) {
      const messageBody = `🚨 Accident for ${userData.name}! Lat: ${latitude}, Lng: ${longitude}. Reply 1=Send Ambulance, 2=No`;

      for (const contact of userData.emergencyContacts) {
        try {
          await smsService.sendSMS(contact.phone, messageBody);
        } catch (smsError) {
          console.error('SMS failed:', smsError);
        }
      }

      await db.collection('accidents').doc(accidentId).update({ emergencyNotified: true });
    }

    res.status(200).json({ message: 'Accident alert created & notifications sent', accidentId });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

exports.handleResponse = async (req, res) => {
  try {
    const { error } = responseSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const { accidentId, response } = req.body;
    const accidentRef = db.collection('accidents').doc(accidentId);
    
    await accidentRef.update({ 
      response: { response, timestamp: new Date() }, 
      status: response === '1' ? 'ambulance' : 'no_action' 
    });

    if (response === '1') {
      try {
        await smsService.sendSMS('8825597447', `🚑 Ambulance requested! Accident ID: ${accidentId}`);
        await smsService.sendSMS('7338903743', `🚨 Accident reported ID: ${accidentId}`);
        await accidentRef.update({ ambulanceRequested: true });
        res.json({ message: 'Ambulance requested - Hospital/Police notified' });
      } catch (error) {
        console.error('Emergency SMS failed:', error);
        res.status(500).json({ error: 'SMS failed but accident logged' });
      }
    } else {

    res.json({ message: 'Response recorded' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

exports.getAccident = async (req, res) => {
  try {
    const accidentId = req.params.id;
    const accidentDoc = await db.collection('accidents').doc(accidentId).get();
    if (!accidentDoc.exists) {
      return res.status(404).json({ error: 'Not found' });
    }
    res.json(accidentDoc.data());
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

// New endpoint 1: POST /accident (v1 immediate)
exports.reportAccidentV1 = async (req, res) => {
  try {
    const { error } = accidentV1Schema.validate(req.body);
    if (error) return res.status(400).json({ error: error.details[0].message });

    const { userId, name, latitude, longitude, deviceId } = req.body;
    const accidentId = db.collection('accidents').doc().id;

    const accidentData = {
      accidentId,
      userId,
      name,
      deviceId,
      latitude,
      longitude,
      speed: 0, // default for v1
      timestamp: new Date(),
      status: 'pending',
      emergencyNotified: false,
      ambulanceRequested: false
    };

    await db.collection('accidents').doc(accidentId).set(accidentData);

    // Optional: notify if user exists
    try {
      const userDoc = await db.collection('users').doc(userId).get();
      if (userDoc.exists && userDoc.data().emergencyContacts?.length > 0) {
        const userData = userDoc.data();
        const messageBody = `🚨 Accident for ${name}! Lat: ${latitude}, Lng: ${longitude}. Reply 1=Send Ambulance, 2=No`;
        for (const contact of userData.emergencyContacts) {
          await smsService.sendSMS(contact.phone, messageBody);
        }
        await db.collection('accidents').doc(accidentId).update({ emergencyNotified: true });
      }
    } catch (userError) {
      console.log('User notification skipped:', userError.message);
    }

    res.status(201).json({ message: 'Accident reported (v1)', accidentId });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

// New endpoint 2: POST /report_accident (v2 detailed)
exports.reportAccidentV2 = async (req, res) => {
  try {
    const { error } = accidentV2Schema.validate(req.body);
    if (error) return res.status(400).json({ error: error.details[0].message });

    const { reportId, userId, latitude, longitude, timestamp = new Date() } = req.body;
    const accidentId = db.collection('accidents').doc().id;

    const accidentData = {
      accidentId,
      reportId,
      userId,
      latitude,
      longitude,
      speed: 0, // default for v2
      timestamp,
      status: 'pending',
      emergencyNotified: false,
      ambulanceRequested: false
    };

    await db.collection('accidents').doc(accidentId).set(accidentData);

    res.status(201).json({ message: 'Accident reported (v2)', accidentId });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

// New endpoint 3: POST /trigger_alerts/{accident_id}
exports.triggerAlerts = async (req, res) => {
  try {
    const accidentId = req.params.accident_id;
    const accidentDoc = await db.collection('accidents').doc(accidentId).get();
    if (!accidentDoc.exists) {
      return res.status(404).json({ error: 'Accident not found' });
    }

    const accidentData = accidentDoc.data();
    const userDoc = await db.collection('users').doc(accidentData.userId).get();
    if (!userDoc.exists || !userDoc.data().emergencyContacts?.length) {
      return res.status(400).json({ error: 'User or contacts not found' });
    }

    const userData = userDoc.data();
    const messageBody = `🚨 EMERGENCY ALERT! Accident for ${accidentData.name || userData.name}! Lat: ${accidentData.latitude}, Lng: ${accidentData.longitude}. Action required!`;

    for (const contact of userData.emergencyContacts) {
      try {
        await smsService.sendSMS(contact.phone, messageBody);
      } catch (smsError) {
        console.error('SMS failed:', smsError);
      }
    }

    await db.collection('accidents').doc(accidentId).update({
      emergencyNotified: true,
      status: 'alerts_triggered',
      triggeredAt: new Date()
    });

    res.json({ message: 'Emergency alerts triggered successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
}}
