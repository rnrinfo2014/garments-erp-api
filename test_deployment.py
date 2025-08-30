#!/usr/bin/env python3
"""
Quick deployment test for Garments ERP API
Tests all major endpoints to ensure the API is working correctly
"""

import requests
import json
import sys
from datetime import date

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.access_token = None
        
    def test_health(self):
        """Test API health endpoints"""
        print("🔍 Testing API health...")
        
        try:
            # Test root endpoint
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint: {data['message']}")
                print(f"   Version: {data['version']}")
                print(f"   Features: {len(data.get('features', []))} available")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False
                
            # Test health endpoint
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                
            # Test docs endpoint
            response = requests.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                print("✅ API documentation accessible")
            else:
                print(f"⚠️ API docs not accessible: {response.status_code}")
                
            return True
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to API at {self.base_url}")
            return False
        except Exception as e:
            print(f"❌ Health check failed: {str(e)}")
            return False
    
    def test_login(self):
        """Test authentication"""
        print("\n🔐 Testing authentication...")
        
        try:
            login_data = {
                "username": "rnrinfo",
                "password": "rnrinfo"
            }
            
            response = requests.post(
                f"{self.api_base}/auth/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data="username=rnrinfo&password=rnrinfo"
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                print("✅ Authentication successful")
                print(f"   Token type: {result.get('token_type', 'bearer')}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication test failed: {str(e)}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def test_sales_bills_endpoints(self):
        """Test sales bills API endpoints"""
        print("\n🧾 Testing Sales Bills API...")
        
        if not self.access_token:
            print("❌ No access token available")
            return False
            
        try:
            # Test list sales bills
            response = requests.get(
                f"{self.api_base}/sales-bills/",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                total = result.get("total", 0)
                print(f"✅ Sales bills listing works: {total} total bills")
            else:
                print(f"❌ Sales bills listing failed: {response.status_code}")
                return False
            
            # Test calculations endpoint
            calc_data = {
                "items": [
                    {
                        "quantity": 10,
                        "rate": 100,
                        "discount_percentage": 5,
                        "tax_percentage": 18
                    }
                ],
                "tax_type": "INCLUDE_TAX",
                "discount_percentage": 5
            }
            
            response = requests.post(
                f"{self.api_base}/sales-bills/calculate",
                headers=self.get_headers(),
                json=calc_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Tax calculations work: Net amount ${result.get('net_amount', 0)}")
            else:
                print(f"❌ Tax calculations failed: {response.status_code}")
                
            return True
            
        except Exception as e:
            print(f"❌ Sales bills test failed: {str(e)}")
            return False
    
    def test_other_endpoints(self):
        """Test other major endpoints"""
        print("\n🔧 Testing other endpoints...")
        
        if not self.access_token:
            print("❌ No access token available")
            return False
            
        endpoints_to_test = [
            ("Customers", f"{self.api_base}/customers/"),
            ("Agents", f"{self.api_base}/agents/"),
            ("Products", f"{self.api_base}/products/variants/"),
            ("Bill Books", f"{self.api_base}/bill-books/"),
            ("Accounts", f"{self.api_base}/accounts/"),
        ]
        
        working_endpoints = 0
        
        for name, url in endpoints_to_test:
            try:
                response = requests.get(url, headers=self.get_headers())
                if response.status_code == 200:
                    print(f"✅ {name} endpoint working")
                    working_endpoints += 1
                else:
                    print(f"⚠️ {name} endpoint returned {response.status_code}")
            except Exception as e:
                print(f"❌ {name} endpoint failed: {str(e)}")
        
        print(f"\n📊 {working_endpoints}/{len(endpoints_to_test)} endpoints working")
        return working_endpoints > 0
    
    def run_all_tests(self):
        """Run all deployment tests"""
        print("🚀 Garments ERP API Deployment Tests")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 4
        
        # Test 1: Health check
        if self.test_health():
            tests_passed += 1
        
        # Test 2: Authentication
        if self.test_login():
            tests_passed += 1
            
        # Test 3: Sales bills API
        if self.test_sales_bills_endpoints():
            tests_passed += 1
            
        # Test 4: Other endpoints
        if self.test_other_endpoints():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {tests_passed}/{total_tests}")
        print(f"❌ Failed: {total_tests - tests_passed}/{total_tests}")
        
        if tests_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! Your API is ready for production.")
            print(f"📍 API URL: {self.base_url}")
            print(f"📚 Documentation: {self.base_url}/docs")
            print(f"📖 ReDoc: {self.base_url}/redoc")
        else:
            print(f"\n⚠️ {total_tests - tests_passed} tests failed. Please check the API configuration.")
        
        return tests_passed == total_tests

if __name__ == "__main__":
    # Allow custom URL via command line
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = APITester(url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
