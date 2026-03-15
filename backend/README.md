# AI Accident Backend

Node.js/Express backend with Firebase Firestore & FCM for Android Accident Detection app.

## Setup
1. Copy `ai-accident-firebase-adminsdk-fbsvc-0b4a184229.json` from root to `backend/`
2. Copy `.env.example` to `.env` and fill values
3. `cd backend && npm install`
4. `npm start`

## APIs
- POST /api/users/register
- POST /api/users/login  
- GET/PUT /api/users/profile
- POST/GET /api/users/contacts
- POST /api/accidents/alert
- POST /api/accidents/response
- POST /api/trips/data
- GET /api/trips/history/:userId
- GET /api/trips/analytics/:userId

## Collections
- users/{phoneNumber}
- accidents/{accidentId}
- trips/{userId}/{tripId}

## Test
Use Postman collection (see POSTMAN_GUIDE.md)

## Deploy
See DEPLOY.md
