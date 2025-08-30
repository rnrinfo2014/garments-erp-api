#!/usr/bin/env python3
"""
Test script for StockLedger API endpoints.
"""

import requests
import base64
import json
from datetime import date, datetime
from decimal import Decimal

BASE_URL = "http://localhost:8001/api"

# Test credentials (adjust according to your database)
USERNAME = "admin"  # Change to your actual username
PASSWORD = "admin"  # Change to your actual password

def get_basic_auth_header():
    """Create Basic Auth header"""
    credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

def test_create_stock_ledger_entry():
    """Test creating a stock ledger entry"""
    print("=== Testing Stock Ledger Entry Creation ===")
    
    # Sample stock ledger entry
    stock_entry = {
        "raw_material_id": "RM001",  # Make sure this exists in your raw_material_master
        "size_id": "SIZE001",        # Make sure this exists in your size_master
        "supplier_id": None,         # NULL for opening stock
        "transaction_date": str(date.today()),
        "transaction_type": "OpeningStock",
        "reference_table": None,
        "reference_id": None,
        "qty_in": "100.00",
        "qty_out": "0.00",
        "rate": "50.00",
        "created_by": USERNAME
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/stock-ledger",
            headers=get_basic_auth_header(),
            data=json.dumps(stock_entry)
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Stock entry created successfully! ID: {data['ledger_id']}")
            return data['ledger_id']
        else:
            print(f"❌ Failed to create stock entry: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating stock entry: {e}")
        return None

def test_get_stock_ledger_entries():
    """Test retrieving stock ledger entries"""
    print("\n=== Testing Stock Ledger Retrieval ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/stock-ledger",
            headers=get_basic_auth_header()
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {len(data)} stock entries")
            if data:
                print(f"   First entry: ID {data[0]['ledger_id']}, Material: {data[0]['raw_material_id']}")
            return True
        else:
            print(f"❌ Failed to retrieve stock entries: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error retrieving stock entries: {e}")
        return False

def test_get_stock_summary():
    """Test getting stock summary"""
    print("\n=== Testing Stock Summary ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/stock-summary",
            headers=get_basic_auth_header()
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved stock summary for {len(data)} material-size combinations")
            for item in data:
                print(f"   Material: {item['raw_material_id']}, Size: {item['size_id']}, Stock: {item['current_stock']}")
            return True
        else:
            print(f"❌ Failed to retrieve stock summary: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error retrieving stock summary: {e}")
        return False

def test_current_stock():
    """Test getting current stock for specific material and size"""
    print("\n=== Testing Current Stock Query ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/current-stock/RM001/SIZE001",
            headers=get_basic_auth_header()
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Current stock for RM001/SIZE001: {data['current_stock']}")
            return True
        else:
            print(f"❌ Failed to get current stock: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting current stock: {e}")
        return False

def test_purchase_entry():
    """Test creating a purchase entry"""
    print("\n=== Testing Purchase Entry ===")
    
    purchase_entry = {
        "raw_material_id": "RM001",
        "size_id": "SIZE001",
        "supplier_id": 1,  # Assuming supplier ID 1 exists
        "transaction_date": str(date.today()),
        "transaction_type": "Purchase",
        "reference_table": "purchase_orders",
        "reference_id": 1001,
        "qty_in": "50.00",
        "qty_out": "0.00",
        "rate": "55.00"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/stock-ledger",
            headers=get_basic_auth_header(),
            data=json.dumps(purchase_entry)
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Purchase entry created! ID: {data['ledger_id']}")
            return data['ledger_id']
        else:
            print(f"❌ Failed to create purchase entry: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating purchase entry: {e}")
        return None

def test_issue_entry():
    """Test creating an issue entry"""
    print("\n=== Testing Issue Entry ===")
    
    issue_entry = {
        "raw_material_id": "RM001",
        "size_id": "SIZE001",
        "supplier_id": None,
        "transaction_date": str(date.today()),
        "transaction_type": "Issue",
        "reference_table": "production_orders",
        "reference_id": 2001,
        "qty_in": "0.00",
        "qty_out": "25.00",
        "rate": "52.50"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/stock-ledger",
            headers=get_basic_auth_header(),
            data=json.dumps(issue_entry)
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Issue entry created! ID: {data['ledger_id']}")
            return data['ledger_id']
        else:
            print(f"❌ Failed to create issue entry: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating issue entry: {e}")
        return None

if __name__ == "__main__":
    print("StockLedger API Test")
    print("=" * 40)
    
    # Test all endpoints
    created_id = test_create_stock_ledger_entry()
    entries_success = test_get_stock_ledger_entries()
    summary_success = test_get_stock_summary()
    current_stock_success = test_current_stock()
    
    # Test different transaction types
    purchase_id = test_purchase_entry()
    issue_id = test_issue_entry()
    
    # Final summary
    print("\n" + "=" * 40)
    print("FINAL STOCK SUMMARY:")
    test_get_stock_summary()
    test_current_stock()
    
    print("\n" + "=" * 40)
    print("TEST RESULTS:")
    print(f"Create Entry: {'✅ PASSED' if created_id else '❌ FAILED'}")
    print(f"Get Entries: {'✅ PASSED' if entries_success else '❌ FAILED'}")
    print(f"Stock Summary: {'✅ PASSED' if summary_success else '❌ FAILED'}")
    print(f"Current Stock: {'✅ PASSED' if current_stock_success else '❌ FAILED'}")
    print(f"Purchase Entry: {'✅ PASSED' if purchase_id else '❌ FAILED'}")
    print(f"Issue Entry: {'✅ PASSED' if issue_id else '❌ FAILED'}")
    
    print(f"\n📝 NOTE: Make sure you have raw material 'RM001' and size 'SIZE001' in your database")
    print(f"📝 NOTE: Also ensure supplier with ID 1 exists for purchase transactions")
