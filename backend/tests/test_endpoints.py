import json
import sys

import requests

# Ensure stdout encodes properly
sys.stdout.reconfigure(encoding='utf-8')

base_url = "http://127.0.0.1:8000/api/v1"
print("Logging in...")
try:
    resp = requests.post(f"{base_url}/auth/login", json={"email":"driver1@gmail.com", "password":"12345678"})
    if not resp.ok:
        print("Login failed:", resp.text)
        exit(1)
    token = resp.json().get("access_token")
    print("Token obtained.")

    print("Testing tracking drivers without token...")
    resp_unauth = requests.get(f"{base_url}/tracking/drivers")
    if resp_unauth.status_code == 401:
        print("Verified 401 Unauthorized working as expected.")
    else:
        print(f"Expected 401, got {resp_unauth.status_code}")

    print("Testing tracking drivers WITH token...")
    headers = {"Authorization": f"Bearer {token}"}
    resp_auth = requests.get(f"{base_url}/tracking/drivers", headers=headers)
    if resp_auth.ok:
        print("Verified 200 OK for tracking endpoint.")
        data = resp_auth.json()
        print("Drivers Data:", json.dumps(data, indent=2))
        
        # Check for driver location
        for d in data:
            loc = d.get("current_location")
            if loc:
                lat, lng = loc.split(",")
                print(f"Verified Driver {d.get('driver_name', d.get('name'))} has location: {lat}, {lng}")
    else:
        print(f"Expected 200, got {resp_auth.status_code}")
        print("Response:", resp_auth.text)

except Exception as e:
    print(f"Error connecting to backend: {e}")
