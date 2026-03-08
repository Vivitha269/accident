# Task: Update Backend Keywords to Match Frontend

## TODO List

- [x] 1. Update AccidentReport Pydantic model in main.py
  - Add timestamp: int field (Long - Unix timestamp in milliseconds)
  - Make latitude: Optional[float] (can be null)
  - Make longitude: Optional[float] (can be null)

- [x] 2. Change endpoint from /accident to /alert

- [x] 3. Update database storage to include timestamp from request

- [x] 4. Verify the changes work with frontend JSON format

