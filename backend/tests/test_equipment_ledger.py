"""
Test script to verify equipment_ledger is being returned from the backend
"""

import requests

# Configuration
BASE_URL = "http://127.0.0.1:8000"  # Adjust if your backend runs on a different port

def test_equipment_ledger():
    print("Testing Equipment Ledger API...")
    print("=" * 60)
    
    # First, we need to login to get a token
    login_url = f"{BASE_URL}/api/v1/auth/login"
    
    # Try with logistics manager credentials (adjust as needed)
    login_data = {
        "email": "logisticmanager@gmail.com",
        "password": "12345678"
    }
    
    print(f"\n1. Logging in to {login_url}...")
    try:
        login_response = requests.post(login_url, json=login_data)
        login_response.raise_for_status()
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        print("✓ Login successful! Got access token")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        print("\nPlease update the login credentials in test_equipment_ledger.py")
        return
    
    # Now call the bootstrap endpoint
    bootstrap_url = f"{BASE_URL}/api/v1/logistics/bootstrap"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n2. Fetching bootstrap data from {bootstrap_url}...")
    try:
        response = requests.get(bootstrap_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Check if equipment_ledger exists in the response
        equipment_ledger = data.get("equipment_ledger", [])
        
        print("✓ Bootstrap data received!")
        print("\n3. Equipment Ledger Status:")
        print(f"   - equipment_ledger key exists: {('equipment_ledger' in data)}")
        print(f"   - Number of records: {len(equipment_ledger)}")
        
        if equipment_ledger:
            print("\n4. Sample Equipment Ledger Records:")
            for idx, eq in enumerate(equipment_ledger[:5], 1):  # Show first 5
                print(f"\n   Record {idx}:")
                print(f"   - ID: {eq.get('id')}")
                print(f"   - Item Type: {eq.get('item_type')}")
                print(f"   - Issued Count: {eq.get('issued_count')}")
                print(f"   - Returned Count: {eq.get('returned_count')}")
                print(f"   - Reference Code: {eq.get('reference_code')}")
                print(f"   - Status: {eq.get('status')}")
        else:
            print("\n   ⚠ WARNING: equipment_ledger is EMPTY!")
            print("   This means the backend is not returning any equipment ledger data.")
            print("\n   Possible causes:")
            print("   1. Database has no equipment ledger records")
            print("   2. Data seeding hasn't run")
            print("   3. Query filter excluding all records")
            
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        print(f"   Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
    except Exception as e:
        print(f"✗ Error fetching bootstrap: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_equipment_ledger()
