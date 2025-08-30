#!/usr/bin/env python3
"""
Fixed test script for Stock Ledger API endpoints
"""

import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get JWT token with correct credentials"""
    login_data = {"username": "superadmin", "password": "admin123"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_stock_ledger_api():
    """Test Stock Ledger API with correct endpoints"""
    print("=== Fixed Stock Ledger API Test ===")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("✅ Authentication successful")
    
    # Test 1: GET stock ledger entries (correct path)
    print("\n1. Testing GET /api/stock-ledger")
    try:
        response = requests.get(f"{BASE_URL}/api/stock-ledger", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Found {len(data)} stock entries")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: GET stock summary
    print("\n2. Testing GET /api/stock-summary")
    try:
        response = requests.get(f"{BASE_URL}/api/stock-summary", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Found {len(data)} stock summaries")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check master data first
    print("\n3. Checking Master Data...")
    
    # Check raw materials
    try:
        response = requests.get(f"{BASE_URL}/api/raw-material-master/", headers=headers)
        if response.status_code == 200:
            materials = response.json()
            print(f"   Raw Materials: {len(materials)} found")
            if len(materials) > 0:
                material_id = materials[0]["id"]
                print(f"   Using material ID: {material_id}")
            else:
                material_id = None
                print("   ⚠️  No raw materials found")
        else:
            material_id = None
            print(f"   ❌ Could not fetch raw materials: {response.status_code}")
    except Exception as e:
        material_id = None
        print(f"   ❌ Error fetching raw materials: {e}")
    
    # Check sizes
    try:
        response = requests.get(f"{BASE_URL}/api/size-master/", headers=headers)
        if response.status_code == 200:
            sizes = response.json()
            print(f"   Sizes: {len(sizes)} found")
            if len(sizes) > 0:
                size_id = sizes[0]["id"]
                print(f"   Using size ID: {size_id}")
            else:
                size_id = None
                print("   ⚠️  No sizes found")
        else:
            size_id = None
            print(f"   ❌ Could not fetch sizes: {response.status_code}")
    except Exception as e:
        size_id = None
        print(f"   ❌ Error fetching sizes: {e}")
    
    # Test 4: Create stock entry (if master data exists)
    if material_id and size_id:
        print(f"\n4. Testing POST /api/stock-ledger (Creating entry)")
        sample_entry = {
            "raw_material_id": material_id,
            "size_id": size_id,
            "supplier_id": None,
            "transaction_date": str(date.today()),
            "transaction_type": "OpeningStock",
            "qty_in": "100.00",
            "qty_out": "0.00",
            "rate": "50.00"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/stock-ledger", headers=headers, json=sample_entry)
            print(f"   Status: {response.status_code}")
            if response.status_code == 201:
                data = response.json()
                print(f"   ✅ Success! Created entry with ID: {data.get('ledger_id')}")
                
                # Test GET specific entry
                ledger_id = data.get('ledger_id')
                response = requests.get(f"{BASE_URL}/api/stock-ledger/{ledger_id}", headers=headers)
                print(f"   GET specific entry - Status: {response.status_code}")
                
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print(f"\n4. ⚠️  Skipping stock entry creation - missing master data")
        print("   Create raw materials and sizes first!")
    
    return True

if __name__ == "__main__":
    success = test_stock_ledger_api()
    
    print("\n" + "="*50)
    if success:
        print("🎉 Stock Ledger API endpoints are working!")
        print("\n📋 Next Steps:")
        print("1. Create master data:")
        print("   - Raw materials: POST /api/raw-material-master/")
        print("   - Sizes: POST /api/size-master/")
        print("   - Categories: POST /api/category-master/")
        print("   - Units: POST /api/unit-master/")
        print("2. Then create stock entries: POST /api/stock-ledger")
    else:
        print("❌ Some issues remain. Check the server logs.")
    
    print(f"\n🔗 API Documentation: {BASE_URL}/docs")