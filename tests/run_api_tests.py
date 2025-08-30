"""
Direct API test runner for Customer and Supplier APIs
"""
import requests
import json
import time

class SimpleAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.headers = {}
        
    def wait_for_server(self, max_attempts=10):
        """Wait for server to be ready"""
        for i in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Server is ready")
                    return True
            except:
                print(f"⏳ Waiting for server... ({i+1}/{max_attempts})")
                time.sleep(1)
        print("❌ Server not responding")
        return False
    
    def login(self):
        """Login and get JWT token"""
        login_data = {
            "username": "superadmin",
            "password": "admin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            self.headers["Authorization"] = f"Bearer {token_data['access_token']}"
            print("✅ Logged in successfully")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_customer_creation(self):
        """Test customer creation"""
        print("\n🧪 Testing Customer Creation")
        
        # Test data for registered customer
        registered_customer = {
            "customer_name": "Test Registered Customer Ltd",
            "customer_type": "Registered",
            "gst_number": "27ABCDE1234F1Z5",
            "contact_person": "John Doe",
            "phone": "+91 98765 43210",
            "email": "john@testcustomer.com",
            "address": "123 Test Street, Business District",
            "city": "Mumbai",
            "pincode": "400001",
            "state_id": 19,  # Maharashtra
            "agent_id": 1,
            "status": "Active"
        }
        
        # Create registered customer
        response = requests.post(f"{self.base_url}/api/customers/", 
                               json=registered_customer, headers=self.headers)
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Created registered customer: {data['customer_name']}")
            print(f"   📊 Account Code: {data['customer_acc_code']}")
            print(f"   🏢 GST Number: {data['gst_number']}")
            print(f"   📍 State: {data['state_name']} (GST Code: {data['gst_code']})")
            return data['id']
        else:
            print(f"❌ Failed to create registered customer: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    
    def test_unregistered_customer_creation(self):
        """Test unregistered customer creation"""
        print("\n🧪 Testing Unregistered Customer Creation")
        
        unregistered_customer = {
            "customer_name": "Test Unregistered Customer",
            "customer_type": "Unregistered",
            "contact_person": "Jane Smith",
            "phone": "+91 87654 32109",
            "email": "jane@testcustomer.com",
            "address": "456 Test Avenue",
            "city": "Delhi",
            "pincode": "110001",
            "state_id": 7,  # Delhi
            "status": "Active"
        }
        
        response = requests.post(f"{self.base_url}/api/customers/", 
                               json=unregistered_customer, headers=self.headers)
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Created unregistered customer: {data['customer_name']}")
            print(f"   📊 Account Code: {data['customer_acc_code']}")
            print(f"   📍 State: {data['state_name']} (GST Code: {data['gst_code']})")
            return data['id']
        else:
            print(f"❌ Failed to create unregistered customer: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    
    def test_supplier_creation(self):
        """Test supplier creation"""
        print("\n🧪 Testing Supplier Creation")
        
        # Test data for registered supplier
        registered_supplier = {
            "supplier_name": "Test Registered Supplier Pvt Ltd",
            "supplier_type": "Registered",
            "gst_number": "06ABCDE1234F1Z5",  # Haryana GST
            "contact_person": "Rajesh Kumar",
            "phone": "+91 98765 43210",
            "email": "rajesh@testsupplier.com",
            "address": "789 Industrial Area, Sector 15",
            "city": "Gurgaon",
            "pincode": "122001",
            "state_id": 10,  # Haryana
            "status": "Active"
        }
        
        response = requests.post(f"{self.base_url}/api/suppliers/", 
                               json=registered_supplier, headers=self.headers)
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Created registered supplier: {data['supplier_name']}")
            print(f"   📊 Account Code: {data['supplier_acc_code']}")
            print(f"   🏢 GST Number: {data['gst_number']}")
            print(f"   📍 State: {data['state_name']} (GST Code: {data['gst_code']})")
            return data['id']
        else:
            print(f"❌ Failed to create registered supplier: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    
    def test_customer_retrieval(self, customer_id):
        """Test customer retrieval"""
        print(f"\n🧪 Testing Customer Retrieval (ID: {customer_id})")
        
        response = requests.get(f"{self.base_url}/api/customers/{customer_id}", headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved customer: {data['customer_name']}")
            return True
        else:
            print(f"❌ Failed to retrieve customer: {response.status_code}")
            return False
    
    def test_supplier_retrieval(self, supplier_id):
        """Test supplier retrieval"""
        print(f"\n🧪 Testing Supplier Retrieval (ID: {supplier_id})")
        
        response = requests.get(f"{self.base_url}/api/suppliers/{supplier_id}", headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved supplier: {data['supplier_name']}")
            return True
        else:
            print(f"❌ Failed to retrieve supplier: {response.status_code}")
            return False
    
    def test_validation_errors(self):
        """Test validation scenarios"""
        print("\n🧪 Testing Validation Scenarios")
        
        # Test registered customer without GST
        invalid_customer = {
            "customer_name": "Invalid Customer",
            "customer_type": "Registered",
            # Missing GST number
            "contact_person": "Test Person",
            "phone": "+91 98765 43210",
            "state_id": 19,
            "status": "Active"
        }
        
        response = requests.post(f"{self.base_url}/api/customers/", 
                               json=invalid_customer, headers=self.headers)
        
        if response.status_code == 422:
            print("✅ Correctly rejected registered customer without GST")
        else:
            print(f"❌ Expected 422, got {response.status_code}")
    
    def test_list_operations(self):
        """Test list operations"""
        print("\n🧪 Testing List Operations")
        
        # Test get all customers
        response = requests.get(f"{self.base_url}/api/customers/?skip=0&limit=10", headers=self.headers)
        if response.status_code == 200:
            customers = response.json()
            print(f"✅ Retrieved {len(customers)} customers")
        else:
            print(f"❌ Failed to get customers: {response.status_code}")
        
        # Test get all suppliers  
        response = requests.get(f"{self.base_url}/api/suppliers/?skip=0&limit=10", headers=self.headers)
        if response.status_code == 200:
            suppliers = response.json()
            print(f"✅ Retrieved {len(suppliers)} suppliers")
        else:
            print(f"❌ Failed to get suppliers: {response.status_code}")
    
    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🚀 Starting Customer & Supplier API Tests")
        print("=" * 50)
        
        # Wait for server
        if not self.wait_for_server():
            return False
        
        # Login
        if not self.login():
            return False
        
        # Test customer operations
        customer_id = self.test_customer_creation()
        if customer_id:
            self.test_customer_retrieval(customer_id)
        
        self.test_unregistered_customer_creation()
        
        # Test supplier operations
        supplier_id = self.test_supplier_creation()
        if supplier_id:
            self.test_supplier_retrieval(supplier_id)
        
        # Test validation
        self.test_validation_errors()
        
        # Test list operations
        self.test_list_operations()
        
        print("\n" + "=" * 50)
        print("🎉 API Testing Complete!")
        return True


if __name__ == "__main__":
    tester = SimpleAPITester()
    tester.run_all_tests()
