@echo off
cd /d c:\Users\VIVITHA\OneDrive\Desktop\ai-accident

echo Initializing git...
git init
git branch -M master

echo Setting remote origin...
git remote add origin https://github.com/Vivitha269/accident.git 2>nul
git remote set-url origin https://github.com/Vivitha269/accident.git

echo Adding files...
git add -A

echo Committing...
git commit -m "Complete AI Accident Detection Backend with phone auto-formatting"

echo Force pushing to GitHub (may overwrite existing files)...
git push -u origin master --force

echo.
echo ========================================
echo Push completed!
echo ========================================
pause
</parameter>
</create_file>
