@echo off
cd /d "c:\Users\VIVITHA\OneDrive\Desktop\ai-accident"
echo Installing dependencies...
pip install -r requirements.txt
echo Starting FastAPI server on port 8000...
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
pause
