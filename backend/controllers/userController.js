const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { db } = require('../config/db');
const User = require('../models/User');
const Joi = require('joi');

const registerSchema = Joi.object({
  name: Joi.string().min(2).required(),
  phoneNumber: Joi.string().min(10).required(),
  email: Joi.string().email().required(),
  vehicleType: Joi.string().required(),
  password: Joi.string().min(6).required(),
  emergencyContacts: Joi.array().items(Joi.object({
    phone: Joi.string().min(10).required(),
    name: Joi.string().min(2).required(),
    relation: Joi.string()
  })).min(1)
});

const loginSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(6).required()
});

const registerDeviceSchema = Joi.object({
  userId: Joi.string().required(),
  name: Joi.string().min(2).required(),
  fcmToken: Joi.string().allow('')
});

const generateToken = (userId) => {
  return jwt.sign({ userId }, process.env.JWT_SECRET, { expiresIn: '7d' });
};

exports.register = async (req, res) => {
  try {
    const { error } = registerSchema.validate(req.body);
    if (error) return res.status(400).json({ error: error.details[0].message });

    const { name, phoneNumber, email, vehicleType, password, emergencyContacts } = req.body;
    const hashedPassword = await bcrypt.hash(password, 12);

    const userRef = db.collection('users').doc(phoneNumber); // use phone as ID for uniqueness
    const userDoc = await userRef.get();

    if (userDoc.exists) {
      return res.status(400).json({ error: 'User already exists' });
    }

    const userData = {
      name,
      phoneNumber,
      email,
      vehicleType,
      password: hashedPassword,
      emergencyContacts: emergencyContacts || [],
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await userRef.set(userData);
    const token = generateToken(phoneNumber);

    res.status(201).json({
      message: 'User registered successfully',
      token,
      user: { id: phoneNumber, name, phoneNumber, email, vehicleType }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

exports.login = async (req, res) => {
  try {
    const { error } = loginSchema.validate(req.body);
    if (error) return res.status(400).json({ error: error.details[0].message });

    const { email, password } = req.body;
    const userSnapshot = await db.collection('users').where('email', '==', email).limit(1).get();

    if (userSnapshot.empty) {
      return res.status(400).json({ error: 'Invalid credentials' });
    }

    const userDoc = userSnapshot.docs[0];
    const userData = userDoc.data();

    const isMatch = await bcrypt.compare(password, userData.password);
    if (!isMatch) {
      return res.status(400).json({ error: 'Invalid credentials' });
    }

    const token = generateToken(userDoc.id);
    res.json({
      token,
      user: { id: userDoc.id, name: userData.name, phoneNumber: userData.phoneNumber, email, vehicleType: userData.vehicleType }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

exports.getProfile = async (req, res) => {
  try {
    res.json(req.user);
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
};

exports.updateProfile = async (req, res) => {
  try {
    const updateData = { ...req.body, updatedAt: new Date() };
    await db.collection('users').doc(req.user.id).update(updateData);
    res.json({ message: 'Profile updated', user: { ...req.user, ...updateData } });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

exports.addEmergencyContact = async (req, res) => {
  try {
    const { phone, name, relation } = req.body;
    const contacts = req.user.emergencyContacts || [];
    contacts.push({ phone, name, relation });
    
    await db.collection('users').doc(req.user.id).update({
      emergencyContacts: contacts,
      updatedAt: new Date()
    });
    
    res.json({ message: 'Contact added', emergencyContacts: contacts });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};

exports.getEmergencyContacts = async (req, res) => {
  try {
    res.json({ emergencyContacts: req.user.emergencyContacts || [] });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
};

exports.registerDevice = async (req, res) => {
  try {
    const { error } = registerDeviceSchema.validate(req.body);
    if (error) return res.status(400).json({ error: error.details[0].message });

    const { userId, name, fcmToken } = req.body;

    const userRef = db.collection('users').doc(userId);
    const userDoc = await userRef.get();

    let userData;
    if (userDoc.exists) {
      // Update existing user
      userData = userDoc.data();
      const updateData = { name, fcmToken, updatedAt: new Date() };
      await userRef.update(updateData);
    } else {
      // Create minimal user for device registration
      userData = {
        userId,
        name,
        fcmToken,
        emergencyContacts: [],
        createdAt: new Date(),
        updatedAt: new Date()
      };
      await userRef.set(userData);
    }

    res.status(200).json({
      message: 'Device registered successfully',
      user: { userId, name, fcmToken: fcmToken || null }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
};
