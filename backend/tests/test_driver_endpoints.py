import sys

import requests

sys.stdout.reconfigure(encoding='utf-8')
base_url = "http://127.0.0.1:8000/api/v1"

def test_endpoints():
    print("Testing Driver Endpoints...")
    
    # 1. Login
    print("\n--- 1. Auth ---")
    resp = requests.post(f"{base_url}/auth/login", json={"email":"driver1@gmail.com", "password":"12345678"})
    if not resp.ok:
        print("❌ Login failed:", resp.text)
        return
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # 2. Profile
    resp = requests.get(f"{base_url}/auth/me", headers=headers)
    print("✅ Profile (/auth/me):", "OK" if resp.ok else f"Failed {resp.status_code}")

    # 3. Vehicles
    print("\n--- 2. Vehicles ---")
    resp = requests.get(f"{base_url}/logistics/vehicles", headers=headers)
    print("✅ Vehicles (/logistics/vehicles):", "OK" if resp.ok else f"Failed {resp.status_code}")

    # 4. Check Dashboard
    print("\n--- 3. Dashboard ---")
    resp = requests.get(f"{base_url}/logistics/drivers/me/dashboard", headers=headers)
    print("✅ Dashboard (/logistics/drivers/me/dashboard):", "OK" if resp.ok else f"Failed {resp.status_code}")

    # 5. Orders
    print("\n--- 4. Orders ---")
    resp = requests.get(f"{base_url}/orders?page=1&page_size=10", headers=headers)
    print("✅ Orders (/orders):", "OK" if resp.ok else f"Failed {resp.status_code}")
    
    # 6. Location
    print("\n--- 5. Tracking ---")
    resp = requests.post(f"{base_url}/logistics/drivers/me/location", headers=headers, json={"latitude":19.1, "longitude":72.8, "timestamp":"2026-03-25T10:00:00Z"})
    print("✅ Location Update (/logistics/drivers/me/location):", "OK" if resp.ok else f"Failed {resp.status_code}")

    print("\n🎉 Basic endpoint health check complete!")

if __name__ == "__main__":
    try:
        test_endpoints()
    except Exception as e:
        print(f"Error connecting to backend: {e}")
