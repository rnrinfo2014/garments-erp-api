#!/usr/bin/env python3
"""
Simple test for opening stock API without CORS issues
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_opening_stock():
    """Test opening stock creation with proper data"""
    print("=== Testing Opening Stock API ===")
    
    # Step 1: Login to get JWT token
    print("1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "rnrinfo", "password": "rnrinfo"}
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"Login successful! Token: {token[:50]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Check what raw materials exist
    print("\n2. Checking available raw materials...")
    rm_response = requests.get(f"{BASE_URL}/raw-material-master/?skip=0&limit=5", headers=headers)
    if rm_response.status_code == 200:
        raw_materials = rm_response.json()
        print(f"Found {len(raw_materials)} raw materials")
        if raw_materials:
            print(f"First raw material: {raw_materials[0]['id']}")
    else:
        print(f"Failed to get raw materials: {rm_response.status_code}")
    
    # Step 3: Check what sizes exist
    print("\n3. Checking available sizes...")
    size_response = requests.get(f"{BASE_URL}/size-master/?skip=0&limit=5", headers=headers)
    if size_response.status_code == 200:
        sizes = size_response.json()
        print(f"Found {len(sizes)} sizes")
        if sizes:
            print(f"First size: {sizes[0]['id']}")
    else:
        print(f"Failed to get sizes: {size_response.status_code}")
    
    # Step 4: Test opening stock creation with NULL supplier
    print("\n4. Testing opening stock creation...")
    opening_stock_data = {
        "raw_material_id": "RM001",
        "size_id": "SIZ001", 
        "supplier_id": None,  # NULL for opening stock
        "transaction_date": "2025-08-24",
        "transaction_type": "OpeningStock",
        "reference_table": "opening_stock",
        "reference_id": None,
        "qty_in": 100.00,
        "qty_out": 0.00,
        "rate": 25.50
    }
    
    create_response = requests.post(
        f"{BASE_URL}/opening-stock/",
        json=opening_stock_data,
        headers=headers
    )
    
    print(f"Create response status: {create_response.status_code}")
    if create_response.status_code == 201:
        result = create_response.json()
        print(f"Opening stock created successfully!")
        print(f"Ledger ID: {result['ledger_id']}")
        print(f"Raw Material: {result['raw_material_id']}")
        print(f"Quantity: {result['qty_in']}")
    else:
        print(f"Failed to create opening stock: {create_response.text}")
    
    # Step 5: Test GET opening stock
    print("\n5. Testing GET opening stock...")
    get_response = requests.get(f"{BASE_URL}/opening-stock/?skip=0&limit=10", headers=headers)
    print(f"GET response status: {get_response.status_code}")
    if get_response.status_code == 200:
        entries = get_response.json()
        print(f"Found {len(entries)} opening stock entries")
    else:
        print(f"Failed to get opening stock: {get_response.text}")

if __name__ == "__main__":
    test_opening_stock()
