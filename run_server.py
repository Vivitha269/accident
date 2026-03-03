# Run the FastAPI server
import subprocess
import sys
import os

os.chdir(r"c:\Users\VIVITHA\OneDrive\Desktop\ai-accident")

# Run uvicorn
result = subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], 
                       capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)

