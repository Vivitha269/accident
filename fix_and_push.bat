@echo off
cd /d c:\Users\VIVITHA\OneDrive\Desktop\ai-accident

echo Removing lock file if exists...
if exist ".git\index.lock" del ".git\index.lock"

echo Adding files...
git add -A

echo Committing...
git commit -m "Complete AI Accident Detection Backend with phone auto-formatting"

echo Pushing to GitHub...
git push origin master

echo.
echo ========================
echo DONE!
echo ========================
pause

