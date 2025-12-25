#!/usr/bin/env python3
"""Test the actual routing endpoint to see what error occurs."""

import requests
import json

# Test a simple route
url = "http://localhost:8000/routes/area-to-center"
params = {
    "center_id": 1,
    "area_id": 1,
    "modes": "driving",
    "include_geometry": "false"
}

print("Testing routing endpoint...")
print(f"URL: {url}")
print(f"Params: {params}\n")

try:
    response = requests.get(url, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response'):
        print(f"Response text: {e.response.text}")
