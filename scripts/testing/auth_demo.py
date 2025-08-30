#!/usr/bin/env python3
"""
API Authentication and Authorization Demo
This script demonstrates how to authenticate and access protected endpoints.
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def login_and_get_token(username: str, password: str):
    """Login and get access token."""
    login_url = f"{BASE_URL}/api/auth/login"
    
    login_data = {
        "username": username,
        "password": password
    }
    
    print(f"🔐 Attempting login for user: {username}")
    
    try:
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful!")
            print(f"Token type: {token_data['token_type']}")
            print(f"Access token: {token_data['access_token'][:20]}...")
            return token_data['access_token']
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return None

def get_current_user(token: str):
    """Get current user information."""
    url = f"{BASE_URL}/api/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n👤 Getting current user info...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User info retrieved successfully!")
            print(f"ID: {user_data['id']}")
            print(f"Username: {user_data['username']}")
            print(f"Role: {user_data['role']}")
            print(f"Status: {user_data['status']}")
            return user_data
        else:
            print(f"❌ Failed to get user info: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return None

def access_protected_vendors_endpoint(token: str):
    """Access the protected vendors endpoint."""
    url = f"{BASE_URL}/api/vendors/"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📋 Accessing vendors endpoint...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            vendors = response.json()
            print(f"✅ Vendors retrieved successfully! Found {len(vendors)} vendors.")
            for vendor in vendors[:3]:  # Show first 3 vendors
                print(f"  - {vendor['name']} ({vendor['company_name']}) - {vendor['status']}")
            return vendors
        else:
            print(f"❌ Failed to access vendors: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return None

def create_test_vendor(token: str):
    """Create a test vendor using authenticated API."""
    url = f"{BASE_URL}/api/vendors/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    vendor_data = {
        "id": "VENDOR001",
        "name": "John Smith",
        "company_name": "Smith Trading Co.",
        "address": "123 Business Street, Mumbai, Maharashtra 400001",
        "phone": "9876543210",
        "gst": "27ABCDE1234F1Z5",
        "services": "Raw materials supply, Fabric trading, Logistics support",
        "status": "Active"
    }
    
    print("\n➕ Creating test vendor...")
    
    try:
        response = requests.post(url, headers=headers, json=vendor_data)
        
        if response.status_code == 201:
            vendor = response.json()
            print("✅ Vendor created successfully!")
            print(f"  ID: {vendor['id']}")
            print(f"  Name: {vendor['name']}")
            print(f"  Company: {vendor['company_name']}")
            print(f"  Account Code: {vendor['acc_code']}")
            return vendor
        elif response.status_code == 400:
            print("⚠️ Vendor already exists!")
            print(f"Details: {response.text}")
            return None
        else:
            print(f"❌ Failed to create vendor: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return None

def demo_authentication_flow():
    """Demonstrate the complete authentication flow."""
    print("=" * 60)
    print("🚀 FastAPI Authentication & Authorization Demo")
    print("=" * 60)
    
    # Step 1: Login
    token = login_and_get_token("superadmin", "admin123")
    
    if not token:
        print("\n❌ Authentication failed. Make sure the server is running!")
        return
    
    # Step 2: Get current user info
    user_info = get_current_user(token)
    
    if not user_info:
        print("\n❌ Failed to get user info with token!")
        return
    
    # Step 3: Access protected vendors endpoint
    vendors = access_protected_vendors_endpoint(token)
    
    # Step 4: Create a test vendor
    new_vendor = create_test_vendor(token)
    
    # Step 5: Access vendors again to see the new vendor
    if new_vendor:
        print("\n🔄 Refreshing vendors list...")
        access_protected_vendors_endpoint(token)
    
    print("\n" + "=" * 60)
    print("✅ Authentication & Authorization Demo Complete!")
    print("=" * 60)
    
    print("\n💡 Key Points:")
    print("1. Login with username/password to get JWT token")
    print("2. Include 'Authorization: Bearer <token>' header in protected requests")
    print("3. Token expires in 30 minutes (configurable)")
    print("4. Different user roles have different access levels")
    print("5. All CRUD operations on vendors require authentication")

if __name__ == "__main__":
    demo_authentication_flow()
