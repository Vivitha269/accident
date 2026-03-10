# PowerShell script to push to GitHub
Set-Location "c:\Users\VIVITHA\OneDrive\Desktop\ai-accident"

Write-Host "Adding all files..."
git add -A

Write-Host "Checking status..."
git status

Write-Host "Committing changes..."
git commit -m "Complete AI Accident Detection Backend with phone auto-formatting"

Write-Host "Pushing to GitHub..."
git push origin master

Write-Host "Done!"
