#!/usr/bin/env python3
"""
Test script for Opening Stock API endpoints
"""
import requests
import json
from datetime import date
from decimal import Decimal

# API Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def get_jwt_token():
    """Get JWT token by logging in"""
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None


def test_opening_stock_api():
    """Test all opening stock API endpoints"""
    
    print("🧪 Testing Opening Stock API Endpoints")
    print("=" * 50)
    
    # Get JWT token
    print("🔑 Getting JWT Token...")
    token = get_jwt_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    # Set headers with JWT token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test data for opening stock
    opening_stock_data = {
        "raw_material_id": "RM001",
        "size_id": "SIZE001", 
        "supplier_id": 1,
        "transaction_date": str(date.today()),
        "qty_in": 100.00,
        "rate": 25.50
    }
    
    print("\n1. 📝 Creating Opening Stock Entry")
    print("-" * 30)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/opening-stock/",
            json=opening_stock_data,
            headers=headers
        )
        
        if response.status_code == 200:
            opening_stock = response.json()
            print("✅ Opening stock entry created successfully!")
            print(f"   Ledger ID: {opening_stock['ledger_id']}")
            print(f"   Material: {opening_stock['raw_material_id']}")
            print(f"   Quantity: {opening_stock['qty_in']}")
            print(f"   Rate: {opening_stock['rate']}")
            print(f"   Amount: {float(opening_stock['qty_in']) * float(opening_stock['rate'])}")
            ledger_id = opening_stock['ledger_id']
        else:
            print(f"❌ Failed to create opening stock: {response.status_code}")
            print(f"   Error: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error creating opening stock: {e}")
        return
    
    print("\n2. 📋 Getting All Opening Stock Entries")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/opening-stock/?skip=0&limit=10",
            headers=headers
        )
        
        if response.status_code == 200:
            entries = response.json()
            print(f"✅ Retrieved {len(entries)} opening stock entries")
            for entry in entries:
                print(f"   ID: {entry['ledger_id']} | Material: {entry['raw_material_id']} | Qty: {entry['qty_in']}")
        else:
            print(f"❌ Failed to get entries: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting entries: {e}")
    
    print("\n3. 🔍 Getting Specific Opening Stock Entry")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/opening-stock/{ledger_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            entry = response.json()
            print("✅ Retrieved opening stock entry details:")
            print(f"   Ledger ID: {entry['ledger_id']}")
            print(f"   Transaction Type: {entry['transaction_type']}")
            print(f"   Date: {entry['transaction_date']}")
            print(f"   Material: {entry['raw_material_id']}")
            print(f"   Size: {entry['size_id']}")
            print(f"   Quantity In: {entry['qty_in']}")
            print(f"   Quantity Out: {entry['qty_out']}")
            print(f"   Rate: {entry['rate']}")
        else:
            print(f"❌ Failed to get entry: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting entry: {e}")
    
    print("\n4. ✏️ Updating Opening Stock Entry")
    print("-" * 30)
    
    update_data = {
        "qty_in": 150.00,
        "rate": 28.75
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/opening-stock/{ledger_id}",
            json=update_data,
            headers=headers
        )
        
        if response.status_code == 200:
            updated_entry = response.json()
            print("✅ Opening stock entry updated successfully!")
            print(f"   New Quantity: {updated_entry['qty_in']}")
            print(f"   New Rate: {updated_entry['rate']}")
            print(f"   New Amount: {float(updated_entry['qty_in']) * float(updated_entry['rate'])}")
        else:
            print(f"❌ Failed to update entry: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error updating entry: {e}")
    
    print("\n5. 📊 Getting Opening Stock Summary by Material")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/opening-stock/summary/by-material",
            headers=headers
        )
        
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Retrieved summary for {len(summary)} materials:")
            for item in summary:
                print(f"   Material: {item['raw_material_id']}")
                print(f"   Total Qty: {item['total_opening_qty']}")
                print(f"   Total Value: {item['total_opening_value']:.2f}")
                print(f"   Avg Rate: {item['avg_rate']:.2f}")
                print(f"   Entries: {item['entry_count']}")
                print()
        else:
            print(f"❌ Failed to get summary: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting summary: {e}")
    
    print("\n6. 📊 Getting Opening Stock Summary by Size")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/opening-stock/summary/by-size?raw_material_id=RM001",
            headers=headers
        )
        
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Retrieved size summary for {len(summary)} entries:")
            for item in summary:
                print(f"   Material: {item['raw_material_id']} | Size: {item['size_id']}")
                print(f"   Qty: {item['total_opening_qty']} | Value: {item['total_opening_value']:.2f}")
                print()
        else:
            print(f"❌ Failed to get size summary: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting size summary: {e}")
    
    print("\n7. 🗑️ Testing Delete Opening Stock Entry")
    print("-" * 30)
    
    # Create another entry first for deletion test
    test_delete_data = {
        "raw_material_id": "RM002",
        "size_id": "SIZE002", 
        "transaction_date": str(date.today()),
        "qty_in": 50.00,
        "rate": 30.00
    }
    
    try:
        # Create entry to delete
        response = requests.post(
            f"{BASE_URL}/api/opening-stock/",
            json=test_delete_data,
            headers=headers
        )
        
        if response.status_code == 200:
            delete_entry = response.json()
            delete_id = delete_entry['ledger_id']
            print(f"✅ Created test entry for deletion (ID: {delete_id})")
            
            # Now delete it
            response = requests.delete(
                f"{BASE_URL}/api/opening-stock/{delete_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
            else:
                print(f"❌ Failed to delete entry: {response.status_code}")
        else:
            print(f"❌ Failed to create test entry: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in delete test: {e}")
    
    print("\n🎉 Opening Stock API Testing Complete!")
    print("=" * 50)


def test_opening_stock_validations():
    """Test opening stock validation scenarios"""
    
    print("\n🧪 Testing Opening Stock Validations")
    print("=" * 50)
    
    # Get JWT token
    token = get_jwt_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n1. Testing Duplicate Opening Stock Prevention")
    print("-" * 30)
    
    # Try to create duplicate opening stock
    duplicate_data = {
        "raw_material_id": "RM001",
        "size_id": "SIZE001", 
        "transaction_date": str(date.today()),
        "qty_in": 75.00,
        "rate": 20.00
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/opening-stock/",
            json=duplicate_data,
            headers=headers
        )
        
        if response.status_code == 400:
            print("✅ Duplicate prevention working correctly")
            print(f"   Error: {response.json()['detail']}")
        else:
            print(f"❌ Duplicate prevention failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing duplicate: {e}")
    
    print("\n2. Testing Negative Quantity Validation")
    print("-" * 30)
    
    negative_qty_data = {
        "raw_material_id": "RM003",
        "size_id": "SIZE003", 
        "transaction_date": str(date.today()),
        "qty_in": -10.00,
        "rate": 25.00
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/opening-stock/",
            json=negative_qty_data,
            headers=headers
        )
        
        if response.status_code == 400:
            print("✅ Negative quantity validation working correctly")
            print(f"   Error: {response.json()['detail']}")
        else:
            print(f"❌ Negative quantity validation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing negative quantity: {e}")


if __name__ == "__main__":
    print("Starting Opening Stock API Tests...")
    
    # Wait for server to be ready
    import time
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        # Test basic functionality
        test_opening_stock_api()
        
        # Test validations
        test_opening_stock_validations()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
    
    print("\nDone! 🏁")
