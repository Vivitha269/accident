const express = require('express');
const userController = require('../controllers/userController');
const authMiddleware = require('../middleware/auth');

const router = express.Router();

router.post('/register', userController.register);
router.post('/login', userController.login);

router.get('/profile', authMiddleware, userController.getProfile);
router.put('/profile', authMiddleware, userController.updateProfile);

router.post('/contacts', authMiddleware, userController.addEmergencyContact);
router.get('/contacts', authMiddleware, userController.getEmergencyContacts);

router.post('/register_device', userController.registerDevice);

module.exports = router;
