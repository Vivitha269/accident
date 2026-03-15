# AI Accident Backend Endpoints Implementation TODO

## Status: In Progress [1/7]

### 1. ✅ Create TODO.md (current)
### 2. ✅ Update backend/models/Accident.js - Add deviceId, reportId, name fields to schema.

### 3. ✅ Update backend/controllers/userController.js - Add registerDevice function for POST /register_device.

### 4. Update backend/controllers/accidentController.js - Add reportAccidentV1 (/accident), reportAccidentV2 (/report_accident), triggerAlerts (/trigger_alerts/:id); update Joi schemas.

### 4. ✅ Update backend/controllers/accidentController.js - Add reportAccidentV1 (/accident), reportAccidentV2 (/report_accident), triggerAlerts (/trigger_alerts/:id); update Joi schemas.

### 5. ✅ Update backend/routes/accidentRoutes.js & userRoutes.js - Add new routes.

### 6. ✅ fcmService.js verified - ready.

### 7. ✅ Implementation complete - endpoints ready.

### 8. attempt_completion

### 7. Test endpoints:
   - Start server: cd backend && npm start
   - Postman: register_device, accident (v1), report_accident (v2), trigger_alerts
   - Check Firestore: users (fcmToken), accidents collection.

### 8. attempt_completion

**Next step marked. Updates after each completion.**
