@echo off
cd /d c:\Users\VIVITHA\OneDrive\Desktop\ai-accident

echo Setting up git remote...
git remote set-url origin https://github.com/Vivitha269/accident.git

echo Adding all files...
git add -A

echo Committing changes...
git commit -m "Updated default police and hospital phone numbers - Added +917338903743 for police and +918825597447 for hospital"

echo Pushing to GitHub...
git push origin master

echo Done!
pause

