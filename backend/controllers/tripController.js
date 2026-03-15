const { db } = require('../config/db');
const Trip = require('../models/Trip');
const Joi = require('joi');

const tripDataSchema = Joi.object({
  userId: Joi.string().required(),
  speed: Joi.number().required(),
  latitude: Joi.number().required(),
  longitude: Joi.number().required(),
  accidentDetected: Joi.boolean().default(false)
});

const analyticsSchema = Joi.object({
  days: Joi.number().default(7)
});

exports.logTripData = async (req, res) => {
  try {
    const { error } = tripDataSchema.validate(req.body);
    if (error) return res.status(400).json({ error: error.details[0].message });

    const { userId, speed, latitude, longitude, accidentDetected = false } = req.body;
    const timestamp = new Date();
    const tripId = db.collection(`trips/${userId}`).doc().id; // subcollection

    const tripData = {
      tripId,
      userId,
      speed,
      latitude,
      longitude,
      timestamp,
      accidentDetected,
      duration: 0 // updated on trip end if needed
    };

    await db.collection(`trips/${userId}`).doc(tripId).set(tripData);

    res.json({ message: 'Trip data logged', tripId });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

exports.getTripHistory = async (req, res) => {
  try {
    const userId = req.params.userId || req.user.id;
    const limit = parseInt(req.query.limit) || 100;

    const snapshot = await db.collection(`trips/${userId}`).orderBy('timestamp', 'desc').limit(limit).get();
    
    const trips = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));

    res.json({ trips });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

exports.getAnalytics = async (req, res) => {
  try {
    const userId = req.params.userId || req.user.id;
    const days = parseInt(req.query.days) || 7;
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

    const tripsSnapshot = await db.collection(`trips/${userId}`)
      .where('timestamp', '>=', cutoff)
      .get();

    let totalTrips = 0;
    let totalSpeed = 0;
    let riskEvents = 0;

    tripsSnapshot.forEach(doc => {
      const data = doc.data();
      totalTrips++;
      totalSpeed += data.speed || 0;
      if (data.accidentDetected) riskEvents++;
    });

    const averageSpeed = totalTrips > 0 ? (totalSpeed / totalTrips).toFixed(2) : 0;
    const weeklySafetyScore = totalTrips > 0 ? Math.max(0, 100 - (riskEvents / totalTrips * 100)).toFixed(2) : 100;

    res.json({
      weeklySafetyScore: parseFloat(weeklySafetyScore),
      averageSpeed: parseFloat(averageSpeed),
      totalTrips,
      riskEvents
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};
