#!/usr/bin/env python3
"""Test accident endpoint with both field formats"""

import json
import urllib.request

# Test 1: Using lat/lon format
print("=" * 50)
print("Test 1: Using lat/lon format")
print("=" * 50)

data1 = {
    "userId": "testuser123",
    "name": "Test User",
    "lat": 12.9716,
    "lon": 77.5946
}

req1 = urllib.request.Request(
    "http://localhost:8000/accident",
    data=json.dumps(data1).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req1) as response:
        result = json.loads(response.read().decode())
        print("Result:", json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode())

# Test 2: Using latitude/longitude format (for Android app)
print("\n" + "=" * 50)
print("Test 2: Using latitude/longitude format")
print("=" * 50)

data2 = {
    "userId": "testuser123",
    "name": "Test User",
    "latitude": 12.9716,
    "longitude": 77.5946
}

req2 = urllib.request.Request(
    "http://localhost:8000/accident",
    data=json.dumps(data2).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req2) as response:
        result = json.loads(response.read().decode())
        print("Result:", json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode())

