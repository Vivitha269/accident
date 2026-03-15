const express = require('express');
const accidentController = require('../controllers/accidentController');
const authMiddleware = require('../middleware/auth');

const router = express.Router();

router.post('/alert', authMiddleware, accidentController.accidentAlert);
router.post('/response', accidentController.handleResponse);
router.get('/:id', authMiddleware, accidentController.getAccident);

router.post('/accident', accidentController.reportAccidentV1);
router.post('/report_accident', accidentController.reportAccidentV2);
router.post('/trigger_alerts/:accident_id', accidentController.triggerAlerts);

module.exports = router;
