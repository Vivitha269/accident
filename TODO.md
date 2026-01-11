# Fix Deployment 404 Issue - TODO

## Problem Analysis
- `main.py` contains TWO FastAPI app definitions causing route conflicts
- Only the second app's routes are being registered
- This causes 404 errors on root requests

## Fix Plan
1. [x] Analyze the duplicate FastAPI app definitions
2. [x] Consolidate both apps into a single FastAPI app
3. [x] Merge all endpoints and models
4. [ ] Deploy and verify

## Changes Made:
- Removed duplicate `app = FastAPI()` definition
- Combined all endpoints into one app at the top of the file
- Merged `LocationQuery` and `AccidentReport` models
- Added imports for `reverse_geocode` and `get_route` from services
- Kept single `/` health check endpoint
- All original endpoints preserved:
  - `/` - Health check
  - `/accident` (POST) - Report accident
  - `/trigger_alerts/{accident_id}` - Trigger alerts
  - `/accept_emergency/{accident_id}` - Accept emergency
  - `/accident` (GET) - Get location details
  - `/map` - Show map view

