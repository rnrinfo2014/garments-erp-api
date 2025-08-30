import pytest
import json
from tests.conftest import APITestBase


class TestCustomerAPI:
    """Comprehensive tests for Customer API operations"""
    
    def setup_method(self):
        """Setup before each test method"""
        self.client = APITestBase()
        self.client.wait_for_server()
        self.client.login()
        
        # Test data
        self.registered_customer_data = {
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
        
        self.unregistered_customer_data = {
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
    
    def test_create_registered_customer_success(self):
        """Test successful creation of registered customer with GST"""
        response = self.client.post("/api/customers/", self.registered_customer_data)
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["customer_name"] == self.registered_customer_data["customer_name"]
        assert data["customer_type"] == "Registered"
        assert data["gst_number"] == self.registered_customer_data["gst_number"]
        assert "customer_acc_code" in data
        assert data["customer_acc_code"].startswith("1301")  # Customer receivable account
        assert data["state_name"] == "Maharashtra"
        assert data["gst_code"] == "27"
        
        # Store customer ID for cleanup
        self.created_customer_id = data["id"]
        
        print(f"✅ Created registered customer with ID: {data['id']}, Account: {data['customer_acc_code']}")
    
    def test_create_unregistered_customer_success(self):
        """Test successful creation of unregistered customer without GST"""
        response = self.client.post("/api/customers/", self.unregistered_customer_data)
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["customer_name"] == self.unregistered_customer_data["customer_name"]
        assert data["customer_type"] == "Unregistered"
        assert data["gst_number"] is None
        assert "customer_acc_code" in data
        assert data["customer_acc_code"].startswith("1301")
        assert data["state_name"] == "Delhi"
        assert data["gst_code"] == "07"
        
        print(f"✅ Created unregistered customer with ID: {data['id']}, Account: {data['customer_acc_code']}")
    
    def test_create_registered_customer_without_gst_fails(self):
        """Test that registered customer without GST fails validation"""
        invalid_data = self.registered_customer_data.copy()
        del invalid_data["gst_number"]
        
        response = self.client.post("/api/customers/", invalid_data)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        error_data = response.json()
        assert "GST number is mandatory for registered customers" in str(error_data)
        
        print("✅ Correctly rejected registered customer without GST")
    
    def test_create_unregistered_customer_with_gst_fails(self):
        """Test that unregistered customer with GST fails validation"""
        invalid_data = self.unregistered_customer_data.copy()
        invalid_data["gst_number"] = "27TESTGST1234Z5"
        
        response = self.client.post("/api/customers/", invalid_data)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        print("✅ Correctly rejected unregistered customer with GST")
    
    def test_create_customer_invalid_gst_format(self):
        """Test GST format validation"""
        invalid_data = self.registered_customer_data.copy()
        invalid_data["gst_number"] = "INVALID_GST"
        
        response = self.client.post("/api/customers/", invalid_data)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        print("✅ Correctly rejected invalid GST format")
    
    def test_create_customer_invalid_state(self):
        """Test invalid state ID validation"""
        invalid_data = self.registered_customer_data.copy()
        invalid_data["state_id"] = 9999  # Non-existent state
        
        response = self.client.post("/api/customers/", invalid_data)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "State not found" in response.text
        
        print("✅ Correctly rejected invalid state ID")
    
    def test_get_all_customers(self):
        """Test retrieving all customers with pagination"""
        # First create a customer
        response = self.client.post("/api/customers/", self.registered_customer_data)
        assert response.status_code == 201
        
        # Get all customers
        response = self.client.get("/api/customers/?skip=0&limit=10")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check customer structure
        customer = data[0]
        required_fields = ["id", "customer_name", "customer_type", "customer_acc_code", 
                          "created_at", "updated_at", "status"]
        
        for field in required_fields:
            assert field in customer, f"Missing field: {field}"
        
        print(f"✅ Retrieved {len(data)} customers successfully")
    
    def test_get_customer_by_id(self):
        """Test retrieving customer by ID"""
        # Create customer first
        response = self.client.post("/api/customers/", self.registered_customer_data)
        assert response.status_code == 201
        customer_id = response.json()["id"]
        
        # Get customer by ID
        response = self.client.get(f"/api/customers/{customer_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["id"] == customer_id
        assert data["customer_name"] == self.registered_customer_data["customer_name"]
        
        print(f"✅ Retrieved customer {customer_id} successfully")
    
    def test_get_customer_by_nonexistent_id(self):
        """Test retrieving non-existent customer"""
        response = self.client.get("/api/customers/99999")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        assert "Customer not found" in response.text
        
        print("✅ Correctly returned 404 for non-existent customer")
    
    def test_update_customer(self):
        """Test updating customer information"""
        # Create customer first
        response = self.client.post("/api/customers/", self.registered_customer_data)
        assert response.status_code == 201
        customer_id = response.json()["id"]
        
        # Update customer
        update_data = {
            "customer_name": "Updated Customer Name Ltd",
            "contact_person": "Updated Contact Person",
            "phone": "+91 99999 88888",
            "city": "Updated City"
        }
        
        response = self.client.put(f"/api/customers/{customer_id}", update_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["customer_name"] == update_data["customer_name"]
        assert data["contact_person"] == update_data["contact_person"]
        assert data["phone"] == update_data["phone"]
        assert data["city"] == update_data["city"]
        
        print(f"✅ Updated customer {customer_id} successfully")
    
    def test_delete_customer(self):
        """Test soft delete customer (set status to Inactive)"""
        # Create customer first
        response = self.client.post("/api/customers/", self.registered_customer_data)
        assert response.status_code == 201
        customer_id = response.json()["id"]
        
        # Delete customer
        response = self.client.delete(f"/api/customers/{customer_id}")
        
        assert response.status_code == 204, f"Expected 204, got {response.status_code}: {response.text}"
        
        # Verify customer is marked as inactive
        response = self.client.get(f"/api/customers/{customer_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "Inactive"
        
        print(f"✅ Soft deleted customer {customer_id} successfully")
    
    def test_get_customer_by_gst(self):
        """Test retrieving customer by GST number"""
        # Create registered customer first
        response = self.client.post("/api/customers/", self.registered_customer_data)
        assert response.status_code == 201
        
        gst_number = self.registered_customer_data["gst_number"]
        
        # Get customer by GST
        response = self.client.get(f"/api/customers/by-gst/{gst_number}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["gst_number"] == gst_number
        assert data["customer_name"] == self.registered_customer_data["customer_name"]
        
        print(f"✅ Retrieved customer by GST {gst_number} successfully")
    
    def test_customer_filtering(self):
        """Test customer filtering by type and status"""
        # Create both registered and unregistered customers
        self.client.post("/api/customers/", self.registered_customer_data)
        self.client.post("/api/customers/", self.unregistered_customer_data)
        
        # Filter by registered customers
        response = self.client.get("/api/customers/?customer_type=Registered")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        for customer in data:
            assert customer["customer_type"] == "Registered"
        
        # Filter by active status
        response = self.client.get("/api/customers/?status_filter=Active")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        for customer in data:
            assert customer["status"] == "Active"
        
        print("✅ Customer filtering working correctly")
    
    def test_duplicate_gst_number(self):
        """Test that duplicate GST numbers are rejected"""
        # Create first customer
        response = self.client.post("/api/customers/", self.registered_customer_data)
        assert response.status_code == 201
        
        # Try to create another customer with same GST
        duplicate_data = self.registered_customer_data.copy()
        duplicate_data["customer_name"] = "Duplicate GST Customer"
        
        response = self.client.post("/api/customers/", duplicate_data)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "GST number already exists" in response.text
        
        print("✅ Correctly rejected duplicate GST number")
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Clean up any created customers (optional - they're marked inactive anyway)
        pass


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
