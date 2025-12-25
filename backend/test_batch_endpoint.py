#!/usr/bin/env python3
"""Test the batch routing endpoint."""

import requests
import json

# Test batch route calculation
url = "http://localhost:8000/routes/areas-to-center"
payload = {
    "center_id": 1,
    "modes": ["driving"],
    "threshold_minutes": 30,
    "approx_speed_kmh": 40
}

print("Testing batch routing endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\nFull Response:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error Response:\n{response.text}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
