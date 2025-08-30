#!/usr/bin/env python3
"""
Test script to verify the new three price fields in products API
"""

import requests
import json
from decimal import Decimal

BASE_URL = "http://localhost:8000"

def login():
    """Login and get token"""
    login_data = {
        "username": "rnrinfo",
        "password": "rnrinfo"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Login failed: {response.text}")
        return None

def test_product_creation_with_three_prices():
    """Test creating a product with three price fields"""
    token = login()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a test product with three prices
    product_data = {
        "product_name": "Test Product Three Prices",
        "product_code": "TPTP001",
        "category_id": "test_category",
        "description": "Test product with three price points",
        "price_a": "100.50",
        "price_b": "200.75", 
        "price_c": "300.99",
        "base_price": "150.00",
        "is_active": True
    }
    
    print("🧪 Testing product creation with three prices...")
    response = requests.post(
        f"{BASE_URL}/api/products/products/", 
        json=product_data,
        headers=headers
    )
    
    if response.status_code == 200:
        product = response.json()
        print("✅ Product created successfully!")
        print(f"   Product ID: {product.get('id')}")
        print(f"   Product Name: {product.get('product_name')}")
        print(f"   Price A: ${product.get('price_a')}")
        print(f"   Price B: ${product.get('price_b')}")
        print(f"   Price C: ${product.get('price_c')}")
        print(f"   Base Price: ${product.get('base_price')}")
        return product.get('id')
    else:
        print(f"❌ Product creation failed: {response.text}")
        return None

def test_product_update_with_three_prices(product_id):
    """Test updating a product with three price fields"""
    token = login()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Update the product prices
    update_data = {
        "price_a": "110.50",
        "price_b": "220.75", 
        "price_c": "330.99"
    }
    
    print(f"\n🔄 Testing product update with three prices (ID: {product_id})...")
    response = requests.put(
        f"{BASE_URL}/api/products/products/{product_id}", 
        json=update_data,
        headers=headers
    )
    
    if response.status_code == 200:
        product = response.json()
        print("✅ Product updated successfully!")
        print(f"   Updated Price A: ${product.get('price_a')}")
        print(f"   Updated Price B: ${product.get('price_b')}")
        print(f"   Updated Price C: ${product.get('price_c')}")
    else:
        print(f"❌ Product update failed: {response.text}")

def test_product_retrieval(product_id):
    """Test retrieving a product to see three price fields"""
    token = login()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n📋 Testing product retrieval (ID: {product_id})...")
    response = requests.get(
        f"{BASE_URL}/api/products/products/{product_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        product = response.json()
        print("✅ Product retrieved successfully!")
        print(f"   Product: {product.get('product_name')}")
        print(f"   Price A: ${product.get('price_a')}")
        print(f"   Price B: ${product.get('price_b')}")
        print(f"   Price C: ${product.get('price_c')}")
        print(f"   Base Price: ${product.get('base_price')}")
    else:
        print(f"❌ Product retrieval failed: {response.text}")

def test_products_list():
    """Test listing products to see three price fields"""
    token = login()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n📋 Testing products list...")
    response = requests.get(
        f"{BASE_URL}/api/products/products/?page=1&per_page=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        print(f"✅ Products list retrieved successfully! ({len(products)} products)")
        
        for product in products[:2]:  # Show first 2 products
            print(f"   • {product.get('product_name')}")
            print(f"     Price A: ${product.get('price_a', 'N/A')}")
            print(f"     Price B: ${product.get('price_b', 'N/A')}")  
            print(f"     Price C: ${product.get('price_c', 'N/A')}")
    else:
        print(f"❌ Products list failed: {response.text}")

if __name__ == "__main__":
    print("🚀 Testing Products API with Three Price Fields")
    print("=" * 50)
    
    # Test product creation
    product_id = test_product_creation_with_three_prices()
    
    if product_id:
        # Test product update
        test_product_update_with_three_prices(product_id)
        
        # Test product retrieval  
        test_product_retrieval(product_id)
    
    # Test products list
    test_products_list()
    
    print("\n🎉 Three price fields testing completed!")
