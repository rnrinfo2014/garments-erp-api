#!/usr/bin/env python3
"""
Create sample master data required for Stock Ledger API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get JWT token"""
    login_data = {"username": "superadmin", "password": "admin123"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def create_master_data():
    """Create sample master data"""
    print("=== Creating Sample Master Data ===")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Create Categories
    print("\n1. Creating Categories...")
    categories = [
        {"id": "CAT001", "category_name": "Fabric", "description": "Fabric materials"},
        {"id": "CAT002", "category_name": "Thread", "description": "Thread materials"},
        {"id": "CAT003", "category_name": "Accessories", "description": "Garment accessories"}
    ]
    
    for category in categories:
        try:
            response = requests.post(f"{BASE_URL}/api/category-master/", headers=headers, json=category)
            if response.status_code in [200, 201]:
                print(f"   ✅ Created category: {category['category_name']}")
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"   ℹ️  Category already exists: {category['category_name']}")
            else:
                print(f"   ❌ Failed to create category {category['category_name']}: {response.text}")
        except Exception as e:
            print(f"   ❌ Error creating category: {e}")
    
    # 2. Create Units
    print("\n2. Creating Units...")
    units = [
        {"id": "UNIT001", "unit_name": "Meter", "description": "Length in meters"},
        {"id": "UNIT002", "unit_name": "Piece", "description": "Individual pieces"},
        {"id": "UNIT003", "unit_name": "Kilogram", "description": "Weight in kilograms"}
    ]
    
    for unit in units:
        try:
            response = requests.post(f"{BASE_URL}/api/unit-master/", headers=headers, json=unit)
            if response.status_code in [200, 201]:
                print(f"   ✅ Created unit: {unit['unit_name']}")
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"   ℹ️  Unit already exists: {unit['unit_name']}")
            else:
                print(f"   ❌ Failed to create unit {unit['unit_name']}: {response.text}")
        except Exception as e:
            print(f"   ❌ Error creating unit: {e}")
    
    # 3. Create Sizes
    print("\n3. Creating Sizes...")
    sizes = [
        {"id": "SIZE001", "size_name": "Small", "description": "Small size"},
        {"id": "SIZE002", "size_name": "Medium", "description": "Medium size"},
        {"id": "SIZE003", "size_name": "Large", "description": "Large size"},
        {"id": "SIZE004", "size_name": "XL", "description": "Extra Large size"}
    ]
    
    for size in sizes:
        try:
            response = requests.post(f"{BASE_URL}/api/size-master/", headers=headers, json=size)
            if response.status_code in [200, 201]:
                print(f"   ✅ Created size: {size['size_name']}")
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"   ℹ️  Size already exists: {size['size_name']}")
            else:
                print(f"   ❌ Failed to create size {size['size_name']}: {response.text}")
        except Exception as e:
            print(f"   ❌ Error creating size: {e}")
    
    # 4. Create Raw Materials
    print("\n4. Creating Raw Materials...")
    materials = [
        {
            "id": "RM001",
            "material_name": "Cotton Fabric",
            "description": "High quality cotton fabric",
            "category_id": "CAT001",
            "unit_id": "UNIT001",
            "rate": "100.00"
        },
        {
            "id": "RM002", 
            "material_name": "Polyester Thread",
            "description": "Strong polyester thread",
            "category_id": "CAT002",
            "unit_id": "UNIT001",
            "rate": "50.00"
        },
        {
            "id": "RM003",
            "material_name": "Buttons",
            "description": "Plastic buttons",
            "category_id": "CAT003",
            "unit_id": "UNIT002",
            "rate": "5.00"
        }
    ]
    
    for material in materials:
        try:
            response = requests.post(f"{BASE_URL}/api/raw-material-master/", headers=headers, json=material)
            if response.status_code in [200, 201]:
                print(f"   ✅ Created material: {material['material_name']}")
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"   ℹ️  Material already exists: {material['material_name']}")
            else:
                print(f"   ❌ Failed to create material {material['material_name']}: {response.text}")
        except Exception as e:
            print(f"   ❌ Error creating material: {e}")
    
    # 5. Create Suppliers
    print("\n5. Creating Suppliers...")
    suppliers = [
        {
            "supplier_name": "ABC Textiles",
            "supplier_type": "Fabric Supplier",
            "contact_person": "John Doe",
            "phone": "+91 9876543210",
            "email": "contact@abctextiles.com",
            "address": "123 Textile Street, Mumbai",
            "gst_number": "27ABCDE1234F1Z5",
            "state_id": 14  # Maharashtra
        }
    ]
    
    for supplier in suppliers:
        try:
            response = requests.post(f"{BASE_URL}/api/suppliers/", headers=headers, json=supplier)
            if response.status_code in [200, 201]:
                print(f"   ✅ Created supplier: {supplier['supplier_name']}")
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"   ℹ️  Supplier already exists: {supplier['supplier_name']}")
            else:
                print(f"   ❌ Failed to create supplier {supplier['supplier_name']}: {response.text}")
        except Exception as e:
            print(f"   ❌ Error creating supplier: {e}")
    
    print("\n✅ Master data creation completed!")
    return True

if __name__ == "__main__":
    success = create_master_data()
    if success:
        print("\n🎉 Now you can test the Stock Ledger API!")
        print("Run: python test_stock_ledger_fixed.py")
    else:
        print("\n❌ Master data creation failed")