# TODO: Fix GET request 404 errors on Render

## Issues Identified:
1. Duplicate FastAPI apps in main.py and mapmain.py
2. Query parameter handling issue in /accident endpoint
3. Missing static file serving configuration

## Tasks:
- [x] Fix main.py: Add static file serving and fix query parameters
- [x] Fix mapmain.py: Remove duplicate app instance to prevent conflicts
- [ ] Test the endpoints to verify 404 errors are resolved

## Changes Made:
1. **main.py**:
   - Added `Query` import from fastapi
   - Added `StaticFiles` import from fastapi.staticfiles
   - Added `Optional` to typing imports
   - Added `app.mount("/static", StaticFiles(directory="static"), name="static")` for static file serving
   - Fixed `/accident` endpoint to use `Query()` parameters instead of `LocationQuery` model for proper GET query parameter handling

2. **mapmain.py**:
   - Removed duplicate FastAPI app definition to prevent routing conflicts
   - Added documentation noting this file should not be run directly

