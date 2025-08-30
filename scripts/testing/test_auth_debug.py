#!/usr/bin/env python3
"""
Debug script to test authentication on stock-ledger endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def get_jwt_token():
    """Get JWT token by logging in"""
    print("=== Getting JWT Token ===")
    
    login_data = {
        "username": "rnrinfo",
        "password": "rnrinfo"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"Token received: {token[:50]}..." if token else "No token in response")
            return token
        else:
            print(f"Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_endpoint_with_bearer_token(endpoint, token):
    """Test an endpoint with Bearer token"""
    print(f"\n=== Testing {endpoint} with Bearer Token ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}?skip=0&limit=10",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text[:500]}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Request error: {e}")
        return False

def test_endpoint_with_basic_auth(endpoint):
    """Test an endpoint with Basic auth (for comparison)"""
    print(f"\n=== Testing {endpoint} with Basic Auth ===")
    
    import base64
    credentials = base64.b64encode("rnrinfo:rnrinfo".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}?skip=0&limit=10",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text[:500]}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Request error: {e}")
        return False

def main():
    print("Stock Ledger Authentication Debug Test")
    print("=" * 50)
    
    # Get JWT token
    token = get_jwt_token()
    if not token:
        print("Failed to get JWT token. Exiting.")
        return
    
    # Test endpoints that work
    print("\n" + "=" * 50)
    print("Testing WORKING endpoints:")
    test_endpoint_with_bearer_token("/raw-material-master", token)
    test_endpoint_with_bearer_token("/unit-master", token)
    
    # Test endpoints that don't work
    print("\n" + "=" * 50)
    print("Testing PROBLEMATIC endpoints:")
    test_endpoint_with_bearer_token("/stock-ledger", token)
    test_endpoint_with_bearer_token("/opening-stock", token)
    
    # Test with Basic auth for comparison
    print("\n" + "=" * 50)
    print("Testing with Basic Auth (should fail):")
    test_endpoint_with_basic_auth("/stock-ledger")
    test_endpoint_with_basic_auth("/opening-stock")

if __name__ == "__main__":
    main()
