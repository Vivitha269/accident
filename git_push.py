#!/usr/bin/env python3
"""
Push to GitHub using subprocess
"""
import subprocess
import os

os.chdir(r"c:\Users\VIVITHA\OneDrive\Desktop\ai-accident")

print("=" * 50)
print("Pushing to GitHub")
print("=" * 50)

# Add all files
print("\n1. Adding all files...")
result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)

# Check status
print("\n2. Checking git status...")
result = subprocess.run(["git", "status"], capture_output=True, text=True)
print(result.stdout)

# Commit
print("\n3. Committing changes...")
result = subprocess.run(
    ["git", "commit", "-m", "Complete AI Accident Detection Backend with phone auto-formatting"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr)

# Push
print("\n4. Pushing to GitHub...")
result = subprocess.run(["git", "push", "origin", "master"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)

print("\n" + "=" * 50)
print("Done! Check your GitHub repository.")
print("=" * 50)
