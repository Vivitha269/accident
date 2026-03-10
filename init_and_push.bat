@echo off
cd /d c:\Users\VIVITHA\OneDrive\Desktop\ai-accident

echo Initializing git if needed...
if not exist ".git" (
    echo No .git folder found. Initializing new repository...
    git init
    git branch -M master
)

echo Setting remote origin...
git remote add origin https://github.com/Vivitha269/accident.git 2>nul
git remote set-url origin https://github.com/Vivitha269/accident.git

echo Adding files...
git add -A

echo Committing...
git commit -m "Complete AI Accident Detection Backend with phone auto-formatting"

echo Pushing to GitHub...
git push -u origin master

echo.
echo ========================================
echo Push completed! Check your GitHub repo.
echo ========================================
pause
