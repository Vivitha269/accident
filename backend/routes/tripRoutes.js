const express = require('express');
const tripController = require('../controllers/tripController');
const authMiddleware = require('../middleware/auth');

const router = express.Router();

router.post('/data', authMiddleware, tripController.logTripData);
router.get('/history/:userId?', authMiddleware, tripController.getTripHistory);
router.get('/analytics/:userId?', authMiddleware, tripController.getAnalytics);

module.exports = router;
