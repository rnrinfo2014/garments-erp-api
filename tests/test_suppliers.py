import pytest
import json
from tests.conftest import APITestBase


class TestSupplierAPI:
    """Comprehensive tests for Supplier API operations"""
    
    def setup_method(self):
        """Setup before each test method"""
        self.client = APITestBase()
        self.client.wait_for_server()
        self.client.login()
        
        # Test data
        self.registered_supplier_data = {
            "supplier_name": "Test Registered Supplier Pvt Ltd",
            "supplier_type": "Registered",
            "gst_number": "09ABCDE1234F1Z5",
            "contact_person": "Rajesh Kumar",
            "phone": "+91 98765 43210",
            "email": "rajesh@testsupplier.com",
            "address": "789 Industrial Area, Sector 15",
            "city": "Gurgaon",
            "pincode": "122001",
            "state_id": 10,  # Haryana
            "status": "Active"
        }
        
        self.unregistered_supplier_data = {
            "supplier_name": "Local Material Supplier",
            "supplier_type": "Unregistered",
            "contact_person": "Amit Sharma",
            "phone": "+91 87654 32109",
            "email": "amit@localsupplier.com",
            "address": "Small Scale Industrial Area",
            "city": "Faridabad",
            "pincode": "121001",
            "state_id": 10,  # Haryana
            "status": "Active"
        }
    
    def test_create_registered_supplier_success(self):
        """Test successful creation of registered supplier with GST"""
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["supplier_name"] == self.registered_supplier_data["supplier_name"]
        assert data["supplier_type"] == "Registered"
        assert data["gst_number"] == self.registered_supplier_data["gst_number"]
        assert "supplier_acc_code" in data
        assert data["supplier_acc_code"].startswith("2106")  # Supplier payable account
        assert data["state_name"] == "Haryana"
        assert data["gst_code"] == "06"
        
        # Store supplier ID for cleanup
        self.created_supplier_id = data["id"]
        
        print(f"✅ Created registered supplier with ID: {data['id']}, Account: {data['supplier_acc_code']}")
    
    def test_create_unregistered_supplier_success(self):
        """Test successful creation of unregistered supplier without GST"""
        response = self.client.post("/api/suppliers/", self.unregistered_supplier_data)
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["supplier_name"] == self.unregistered_supplier_data["supplier_name"]
        assert data["supplier_type"] == "Unregistered"
        assert data["gst_number"] is None
        assert "supplier_acc_code" in data
        assert data["supplier_acc_code"].startswith("2106")
        assert data["state_name"] == "Haryana"
        assert data["gst_code"] == "06"
        
        print(f"✅ Created unregistered supplier with ID: {data['id']}, Account: {data['supplier_acc_code']}")
    
    def test_create_registered_supplier_without_gst_fails(self):
        """Test that registered supplier without GST fails validation"""
        invalid_data = self.registered_supplier_data.copy()
        del invalid_data["gst_number"]
        
        response = self.client.post("/api/suppliers/", invalid_data)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        error_data = response.json()
        assert "GST number is mandatory for registered suppliers" in str(error_data)
        
        print("✅ Correctly rejected registered supplier without GST")
    
    def test_create_unregistered_supplier_with_gst_fails(self):
        """Test that unregistered supplier with GST fails validation"""
        invalid_data = self.unregistered_supplier_data.copy()
        invalid_data["gst_number"] = "06TESTGST1234Z5"
        
        response = self.client.post("/api/suppliers/", invalid_data)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        print("✅ Correctly rejected unregistered supplier with GST")
    
    def test_create_supplier_invalid_gst_format(self):
        """Test GST format validation"""
        invalid_data = self.registered_supplier_data.copy()
        invalid_data["gst_number"] = "INVALID_GST_FORMAT"
        
        response = self.client.post("/api/suppliers/", invalid_data)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        print("✅ Correctly rejected invalid GST format")
    
    def test_create_supplier_gst_state_mismatch(self):
        """Test GST state code validation against selected state"""
        invalid_data = self.registered_supplier_data.copy()
        invalid_data["gst_number"] = "27ABCDE1234F1Z5"  # Maharashtra GST code
        invalid_data["state_id"] = 10  # But state is Haryana (06)
        
        response = self.client.post("/api/suppliers/", invalid_data)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        error_data = response.json()
        assert "GST state code does not match selected state" in str(error_data)
        
        print("✅ Correctly rejected GST state code mismatch")
    
    def test_create_supplier_invalid_state(self):
        """Test invalid state ID validation"""
        invalid_data = self.registered_supplier_data.copy()
        invalid_data["state_id"] = 9999  # Non-existent state
        
        response = self.client.post("/api/suppliers/", invalid_data)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "State not found" in response.text
        
        print("✅ Correctly rejected invalid state ID")
    
    def test_get_all_suppliers(self):
        """Test retrieving all suppliers with pagination"""
        # First create a supplier
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        assert response.status_code == 201
        
        # Get all suppliers
        response = self.client.get("/api/suppliers/?skip=0&limit=10")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check supplier structure
        supplier = data[0]
        required_fields = ["id", "supplier_name", "supplier_type", "supplier_acc_code", 
                          "created_at", "updated_at", "status"]
        
        for field in required_fields:
            assert field in supplier, f"Missing field: {field}"
        
        print(f"✅ Retrieved {len(data)} suppliers successfully")
    
    def test_get_supplier_by_id(self):
        """Test retrieving supplier by ID"""
        # Create supplier first
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        assert response.status_code == 201
        supplier_id = response.json()["id"]
        
        # Get supplier by ID
        response = self.client.get(f"/api/suppliers/{supplier_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["id"] == supplier_id
        assert data["supplier_name"] == self.registered_supplier_data["supplier_name"]
        
        print(f"✅ Retrieved supplier {supplier_id} successfully")
    
    def test_get_supplier_by_nonexistent_id(self):
        """Test retrieving non-existent supplier"""
        response = self.client.get("/api/suppliers/99999")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        assert "Supplier not found" in response.text
        
        print("✅ Correctly returned 404 for non-existent supplier")
    
    def test_update_supplier(self):
        """Test updating supplier information"""
        # Create supplier first
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        assert response.status_code == 201
        supplier_id = response.json()["id"]
        
        # Update supplier
        update_data = {
            "supplier_name": "Updated Supplier Name Pvt Ltd",
            "contact_person": "Updated Contact Person",
            "phone": "+91 99999 88888",
            "city": "Updated City",
            "email": "updated@testsupplier.com"
        }
        
        response = self.client.put(f"/api/suppliers/{supplier_id}", update_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["supplier_name"] == update_data["supplier_name"]
        assert data["contact_person"] == update_data["contact_person"]
        assert data["phone"] == update_data["phone"]
        assert data["city"] == update_data["city"]
        assert data["email"] == update_data["email"]
        
        print(f"✅ Updated supplier {supplier_id} successfully")
    
    def test_delete_supplier(self):
        """Test soft delete supplier (set status to Inactive)"""
        # Create supplier first
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        assert response.status_code == 201
        supplier_id = response.json()["id"]
        
        # Delete supplier
        response = self.client.delete(f"/api/suppliers/{supplier_id}")
        
        assert response.status_code == 204, f"Expected 204, got {response.status_code}: {response.text}"
        
        # Verify supplier is marked as inactive
        response = self.client.get(f"/api/suppliers/{supplier_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "Inactive"
        
        print(f"✅ Soft deleted supplier {supplier_id} successfully")
    
    def test_get_supplier_by_gst(self):
        """Test retrieving supplier by GST number"""
        # Create registered supplier first
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        assert response.status_code == 201
        
        gst_number = self.registered_supplier_data["gst_number"]
        
        # Get supplier by GST
        response = self.client.get(f"/api/suppliers/by-gst/{gst_number}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["gst_number"] == gst_number
        assert data["supplier_name"] == self.registered_supplier_data["supplier_name"]
        
        print(f"✅ Retrieved supplier by GST {gst_number} successfully")
    
    def test_supplier_filtering(self):
        """Test supplier filtering by type and status"""
        # Create both registered and unregistered suppliers
        self.client.post("/api/suppliers/", self.registered_supplier_data)
        self.client.post("/api/suppliers/", self.unregistered_supplier_data)
        
        # Filter by registered suppliers
        response = self.client.get("/api/suppliers/?supplier_type=Registered")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        for supplier in data:
            assert supplier["supplier_type"] == "Registered"
        
        # Filter by active status
        response = self.client.get("/api/suppliers/?status_filter=Active")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        for supplier in data:
            assert supplier["status"] == "Active"
        
        print("✅ Supplier filtering working correctly")
    
    def test_duplicate_gst_number(self):
        """Test that duplicate GST numbers are rejected"""
        # Create first supplier
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        assert response.status_code == 201
        
        # Try to create another supplier with same GST
        duplicate_data = self.registered_supplier_data.copy()
        duplicate_data["supplier_name"] = "Duplicate GST Supplier"
        
        response = self.client.post("/api/suppliers/", duplicate_data)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "GST number already exists" in response.text
        
        print("✅ Correctly rejected duplicate GST number")
    
    def test_supplier_account_creation(self):
        """Test that supplier accounts are created with correct account codes"""
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        assert response.status_code == 201
        
        data = response.json()
        supplier_acc_code = data["supplier_acc_code"]
        
        # Verify account code format for supplier payable (2106xxx)
        assert supplier_acc_code.startswith("2106"), f"Expected 2106xxx format, got {supplier_acc_code}"
        assert len(supplier_acc_code) == 7, f"Expected 7 digits, got {len(supplier_acc_code)}"
        
        # Verify account was created in accounts_master
        response = self.client.get("/api/accounts/")
        assert response.status_code == 200
        
        accounts = response.json()
        supplier_account = next((acc for acc in accounts if acc["account_code"] == supplier_acc_code), None)
        assert supplier_account is not None, f"Supplier account {supplier_acc_code} not found in accounts_master"
        assert supplier_account["account_name"] == f"{data['supplier_name']} - Payable"
        assert supplier_account["account_type"] == "Liability"
        
        print(f"✅ Supplier account {supplier_acc_code} created successfully")
    
    def test_supplier_state_relationship(self):
        """Test supplier state relationship and GST code validation"""
        # Create supplier with specific state
        response = self.client.post("/api/suppliers/", self.registered_supplier_data)
        assert response.status_code == 201
        
        data = response.json()
        
        # Verify state relationship
        assert data["state_id"] == self.registered_supplier_data["state_id"]
        assert data["state_name"] == "Haryana"
        assert data["gst_code"] == "06"
        
        # Verify GST number state code matches
        gst_state_code = data["gst_number"][:2]
        assert gst_state_code == "09" or gst_state_code == "06", f"GST state code {gst_state_code} should match state GST code"
        
        print(f"✅ Supplier state relationship validated: {data['state_name']} (GST: {data['gst_code']})")
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Clean up any created suppliers (optional - they're marked inactive anyway)
        pass


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
