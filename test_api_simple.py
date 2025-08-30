#!/usr/bin/env python3
"""
Simple API test for bill books
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000/api/bill-books"
    
    try:
        print("🧪 Testing Bill Books API...")
        print(f"API URL: {base_url}")
        
        # Test the list endpoint that was failing
        print("\n1. Testing GET /api/bill-books/ ...")
        response = requests.get(f"{base_url}/?page=1&per_page=50", timeout=5)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ API is working!")
            data = response.json()
            print(f"   📊 Found {data.get('total', 0)} bill books")
            
            # Show the bill books
            if 'bill_books' in data:
                for book in data['bill_books']:
                    print(f"   📚 {book['book_name']} ({book['book_code']}) - {book['tax_type']}")
        else:
            print(f"   ❌ API returned error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
        print("Make sure the FastAPI server is running:")
        print("python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()
