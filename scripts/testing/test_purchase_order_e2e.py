"""
End-to-End Testing for Purchase Order API using Playwright
Tests the complete Purchase Order workflow including authentication, CRUD operations, and validation
"""

import asyncio
import json
import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any

# Test Configuration
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "superadmin"
TEST_PASSWORD = "admin123"

class PurchaseOrderE2ETest:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_po_id = None
        self.test_po_number = None
        
    async def authenticate(self) -> str:
        """Authenticate and get JWT token"""
        print("🔐 Step 1: Authenticating...")
        
        # Using browser automation for authentication
        try:
            # Import playwright here to avoid issues if not installed
            from playwright.async_api import async_playwright
        except ImportError:
            print("❌ Playwright not installed. Installing...")
            import subprocess
            subprocess.run(["pip", "install", "playwright"], check=True)
            subprocess.run(["playwright", "install"], check=True)
            from playwright.async_api import async_playwright
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to docs page and test authentication
            await page.goto(f"{self.base_url}/docs")
            await page.wait_for_load_state("networkidle")
            
            # Check if the API docs loaded
            title = await page.title()
            assert "FastAPI" in title, "API documentation not loaded"
            print("✅ API documentation loaded successfully")
            
            # Test login endpoint directly via API call
            page.on("response", self._handle_response)
            
            # Use page.evaluate to make API call
            login_response = await page.evaluate(f"""
                async () => {{
                    const response = await fetch('{self.base_url}/token', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }},
                        body: 'username={TEST_USERNAME}&password={TEST_PASSWORD}'
                    }});
                    const data = await response.json();
                    return {{ status: response.status, data: data }};
                }}
            """)
            
            await browser.close()
            
            if login_response['status'] == 200:
                self.token = login_response['data']['access_token']
                self.headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                }
                print("✅ Authentication successful")
                return self.token
            else:
                raise Exception(f"Authentication failed: {login_response}")
    
    async def _handle_response(self, response):
        """Handle page responses for debugging"""
        if response.status >= 400:
            print(f"⚠️ HTTP {response.status}: {response.url}")
    
    async def test_purchase_order_creation(self):
        """Test creating a new purchase order"""
        print("📝 Step 2: Testing Purchase Order Creation...")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Prepare test data
            test_po_data = {
                "po_number": f"PO-TEST-{int(time.time())}",
                "supplier_id": 1,  # Assuming supplier ID 1 exists
                "po_date": date.today().isoformat(),
                "due_date": (date.today() + timedelta(days=30)).isoformat(),
                "transport_details": "Test transport via truck",
                "tax_amount": "100.00",
                "discount_amount": "50.00",
                "remarks": "Test purchase order created via E2E test",
                "items": [
                    {
                        "material_id": 1,  # Assuming material ID 1 exists
                        "supplier_material_name": "Test Raw Material",
                        "description": "High quality test material",
                        "quantity": "100.00",
                        "unit_id": 1,  # Assuming unit ID 1 exists
                        "rate": "25.50"
                    },
                    {
                        "material_id": 1,
                        "supplier_material_name": "Test Raw Material 2",
                        "description": "Another test material",
                        "quantity": "50.00",
                        "unit_id": 1,
                        "rate": "15.75"
                    }
                ]
            }
            
            # Create purchase order via API
            create_response = await page.evaluate(f"""
                async (data) => {{
                    const response = await fetch('{self.base_url}/purchase-orders', {{
                        method: 'POST',
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    const responseData = await response.json();
                    return {{ status: response.status, data: responseData }};
                }}
            """, test_po_data)
            
            await browser.close()
            
            if create_response['status'] == 201:
                self.test_po_id = create_response['data']['id']
                self.test_po_number = create_response['data']['po_number']
                print(f"✅ Purchase Order created successfully: {self.test_po_number} (ID: {self.test_po_id})")
                
                # Validate response data
                po_data = create_response['data']
                assert po_data['po_number'] == test_po_data['po_number']
                assert len(po_data['items']) == 2
                assert po_data['status'] == 'Draft'
                assert float(po_data['total_amount']) > 0
                print("✅ Purchase Order data validation passed")
                
                return po_data
            else:
                raise Exception(f"PO Creation failed: {create_response}")
    
    async def test_purchase_order_retrieval(self):
        """Test retrieving purchase orders"""
        print("📖 Step 3: Testing Purchase Order Retrieval...")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Test get all purchase orders
            list_response = await page.evaluate(f"""
                async () => {{
                    const response = await fetch('{self.base_url}/purchase-orders', {{
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }}
                    }});
                    const data = await response.json();
                    return {{ status: response.status, data: data }};
                }}
            """)
            
            if list_response['status'] == 200:
                pos = list_response['data']
                assert isinstance(pos, list)
                assert len(pos) > 0
                print(f"✅ Retrieved {len(pos)} purchase orders")
                
                # Find our test PO
                test_po = next((po for po in pos if po['id'] == self.test_po_id), None)
                assert test_po is not None, "Test PO not found in list"
                print("✅ Test PO found in list")
            else:
                raise Exception(f"PO List retrieval failed: {list_response}")
            
            # Test get specific purchase order
            detail_response = await page.evaluate(f"""
                async () => {{
                    const response = await fetch('{self.base_url}/purchase-orders/{self.test_po_id}', {{
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }}
                    }});
                    const data = await response.json();
                    return {{ status: response.status, data: data }};
                }}
            """)
            
            await browser.close()
            
            if detail_response['status'] == 200:
                po_detail = detail_response['data']
                assert po_detail['id'] == self.test_po_id
                assert po_detail['po_number'] == self.test_po_number
                assert 'supplier' in po_detail
                assert 'items' in po_detail
                print("✅ Purchase Order detail retrieval successful")
                return po_detail
            else:
                raise Exception(f"PO Detail retrieval failed: {detail_response}")
    
    async def test_purchase_order_update(self):
        """Test updating purchase order"""
        print("✏️ Step 4: Testing Purchase Order Update...")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Update data
            update_data = {
                "remarks": "Updated via E2E test",
                "transport_details": "Updated transport details - Express delivery"
            }
            
            update_response = await page.evaluate(f"""
                async (data) => {{
                    const response = await fetch('{self.base_url}/purchase-orders/{self.test_po_id}', {{
                        method: 'PUT',
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    const responseData = await response.json();
                    return {{ status: response.status, data: responseData }};
                }}
            """, update_data)
            
            await browser.close()
            
            if update_response['status'] == 200:
                updated_po = update_response['data']
                assert updated_po['remarks'] == update_data['remarks']
                assert updated_po['transport_details'] == update_data['transport_details']
                print("✅ Purchase Order update successful")
                return updated_po
            else:
                raise Exception(f"PO Update failed: {update_response}")
    
    async def test_purchase_order_status_update(self):
        """Test updating purchase order status"""
        print("🔄 Step 5: Testing Purchase Order Status Update...")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Update status to Pending
            status_data = {
                "status": "Pending",
                "remarks": "Status updated to Pending via E2E test"
            }
            
            status_response = await page.evaluate(f"""
                async (data) => {{
                    const response = await fetch('{self.base_url}/purchase-orders/{self.test_po_id}/status', {{
                        method: 'PUT',
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    const responseData = await response.json();
                    return {{ status: response.status, data: responseData }};
                }}
            """, status_data)
            
            await browser.close()
            
            if status_response['status'] == 200:
                updated_po = status_response['data']
                assert updated_po['status'] == 'Pending'
                print("✅ Purchase Order status update successful")
                return updated_po
            else:
                raise Exception(f"PO Status update failed: {status_response}")
    
    async def test_purchase_order_statistics(self):
        """Test purchase order statistics endpoint"""
        print("📊 Step 6: Testing Purchase Order Statistics...")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            stats_response = await page.evaluate(f"""
                async () => {{
                    const response = await fetch('{self.base_url}/purchase-orders-stats', {{
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }}
                    }});
                    const data = await response.json();
                    return {{ status: response.status, data: data }};
                }}
            """)
            
            await browser.close()
            
            if stats_response['status'] == 200:
                stats = stats_response['data']
                assert 'total_purchase_orders' in stats
                assert 'total_value' in stats
                assert 'by_status' in stats
                assert isinstance(stats['by_status'], list)
                print("✅ Purchase Order statistics retrieval successful")
                print(f"   Total POs: {stats['total_purchase_orders']}")
                print(f"   Total Value: {stats['total_value']}")
                return stats
            else:
                raise Exception(f"PO Statistics failed: {stats_response}")
    
    async def test_purchase_order_deletion(self):
        """Test deleting purchase order (only if status is Draft)"""
        print("🗑️ Step 7: Testing Purchase Order Deletion...")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # First, update status back to Draft to allow deletion
            status_data = {
                "status": "Draft",
                "remarks": "Reset to Draft for deletion test"
            }
            
            await page.evaluate(f"""
                async (data) => {{
                    const response = await fetch('{self.base_url}/purchase-orders/{self.test_po_id}/status', {{
                        method: 'PUT',
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    return await response.json();
                }}
            """, status_data)
            
            # Now delete the PO
            delete_response = await page.evaluate(f"""
                async () => {{
                    const response = await fetch('{self.base_url}/purchase-orders/{self.test_po_id}', {{
                        method: 'DELETE',
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }}
                    }});
                    const data = await response.json();
                    return {{ status: response.status, data: data }};
                }}
            """)
            
            await browser.close()
            
            if delete_response['status'] == 200:
                print("✅ Purchase Order deletion successful")
                
                # Verify deletion by trying to retrieve the PO
                await self.verify_po_deleted()
                return True
            else:
                raise Exception(f"PO Deletion failed: {delete_response}")
    
    async def verify_po_deleted(self):
        """Verify that the purchase order was deleted"""
        print("🔍 Step 8: Verifying Purchase Order Deletion...")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Try to retrieve deleted PO - should return 404
            verify_response = await page.evaluate(f"""
                async () => {{
                    const response = await fetch('{self.base_url}/purchase-orders/{self.test_po_id}', {{
                        headers: {{
                            'Authorization': 'Bearer {self.token}',
                            'Content-Type': 'application/json'
                        }}
                    }});
                    const data = await response.json();
                    return {{ status: response.status, data: data }};
                }}
            """)
            
            await browser.close()
            
            if verify_response['status'] == 404:
                print("✅ Purchase Order deletion verified - PO not found")
                return True
            else:
                raise Exception(f"PO still exists after deletion: {verify_response}")
    
    async def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🚀 Starting Purchase Order API End-to-End Tests")
        print("=" * 60)
        
        try:
            # Step 1: Authentication
            await self.authenticate()
            
            # Step 2: Create Purchase Order
            await self.test_purchase_order_creation()
            
            # Step 3: Retrieve Purchase Orders
            await self.test_purchase_order_retrieval()
            
            # Step 4: Update Purchase Order
            await self.test_purchase_order_update()
            
            # Step 5: Update Status
            await self.test_purchase_order_status_update()
            
            # Step 6: Get Statistics
            await self.test_purchase_order_statistics()
            
            # Step 7: Delete Purchase Order
            await self.test_purchase_order_deletion()
            
            print("=" * 60)
            print("🎉 ALL TESTS PASSED! Purchase Order API is working correctly!")
            print("=" * 60)
            
        except Exception as e:
            print("=" * 60)
            print(f"❌ TEST FAILED: {str(e)}")
            print("=" * 60)
            raise

async def main():
    """Main function to run the tests"""
    # Check if server is running
    print("🔍 Checking if server is running...")
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(f"{BASE_URL}/docs", timeout=5000)
            print("✅ Server is running")
        except:
            print("❌ Server is not running. Please start the server with: python main.py")
            return
        finally:
            await browser.close()
    
    # Run the tests
    tester = PurchaseOrderE2ETest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
