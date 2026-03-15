# FastAPI Backend Endpoints Implementation TODO (REST API)

Status: Planning [0/6]

**Current:**
- /api/accidents/alert exists (close to v2)
- Need exact: /api/users/register_device, /api/accidents/accident, /api/accidents/report_accident, /api/accidents/trigger_alerts/{accident_id}

**Plan:**
1. ✅ models.py - Add Pydantic: RegisterDevicePayload, AccidentV1Payload, AccidentV2Payload

2. ✅ routers/users.py - Add POST /register_device (no auth)

3. ✅ routers/accidents.py - Add POST /accident, /report_accident, /trigger_alerts/{accident_id}

4. ✅ main_fastapi.py confirmed /api prefix
5. ✅ Tested - server running port 8000 (install pydantic[email] if needed)
6. Postman collection for FastAPI
6. Postman collection for FastAPI
4. main_fastapi.py - Ensure routers mounted /api prefix (already)
5. Test with uvicorn main_fastapi:app --reload (port 8000)
6. Postman collection for FastAPI

Next: Implement step 1-3.
