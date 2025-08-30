#!/usr/bin/env python3
"""
Test script to demonstrate both authentication methods in the FastAPI application.
"""

import requests
import base64
import json

BASE_URL = "http://localhost:8000/api"

# Test credentials (adjust according to your database)
USERNAME = "admin"  # Change to your actual username
PASSWORD = "admin"  # Change to your actual password

def test_token_authentication():
    """Test JWT token authentication"""
    print("=== Testing JWT Token Authentication ===")
    
    # 1. Login to get token
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print(f"✅ Login successful! Token: {token[:20]}...")
            
            # 2. Use token to access protected endpoint
            headers = {"Authorization": f"Bearer {token}"}
            user_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                print(f"✅ Token auth successful! User: {user_data['username']}")
                return True
            else:
                print(f"❌ Token auth failed: {user_response.text}")
                return False
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during token auth: {e}")
        return False

def test_basic_authentication():
    """Test HTTP Basic authentication"""
    print("\n=== Testing Basic Authentication ===")
    
    try:
        # Create Basic Auth header
        credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
        headers = {"Authorization": f"Basic {credentials}"}
        
        # Test basic auth endpoint
        response = requests.get(f"{BASE_URL}/auth/me-basic", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Basic auth successful! User: {user_data['username']}")
            return True
        else:
            print(f"❌ Basic auth failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during basic auth: {e}")
        return False

def test_basic_auth_endpoints():
    """Test endpoints that use basic authentication"""
    print("\n=== Testing Basic Auth Endpoints ===")
    
    try:
        credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
        headers = {"Authorization": f"Basic {credentials}"}
        
        # Test users endpoint with basic auth
        response = requests.get(f"{BASE_URL}/users-basic", headers=headers)
        
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Basic auth users endpoint successful! Found {len(users)} users")
            return True
        else:
            print(f"❌ Basic auth users endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during basic auth endpoint test: {e}")
        return False

if __name__ == "__main__":
    print("FastAPI Authentication Test")
    print("=" * 40)
    
    # Test both authentication methods
    token_success = test_token_authentication()
    basic_success = test_basic_authentication()
    basic_endpoint_success = test_basic_auth_endpoints()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Token Authentication: {'✅ PASSED' if token_success else '❌ FAILED'}")
    print(f"Basic Authentication: {'✅ PASSED' if basic_success else '❌ FAILED'}")
    print(f"Basic Auth Endpoints: {'✅ PASSED' if basic_endpoint_success else '❌ FAILED'}")
    
    if token_success and basic_success:
        print("\n🎉 All authentication methods working!")
    else:
        print(f"\n⚠️  Some authentication methods failed. Check your credentials:")
        print(f"   Username: {USERNAME}")
        print(f"   Password: {PASSWORD}")
        print(f"   Make sure the user exists in your database.")
