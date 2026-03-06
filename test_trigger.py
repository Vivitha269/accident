#!/usr/bin/env python3
"""Test trigger_alerts endpoint"""

import json
import urllib.request

# Use the accident ID from previous test
accident_id = "Q6T98Nntnd7DGjrIA9U3"

# Create request
req = urllib.request.Request(
    f"http://localhost:8000/trigger_alerts/{accident_id}",
    headers={},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print("Result:", json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode())

