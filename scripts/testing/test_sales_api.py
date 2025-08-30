#!/usr/bin/env python3
"""
Comprehensive Sales API Testing with Playwright
Tests real-time data, business logic, and ledger transactions
"""

import asyncio
import json
from datetime import date, datetime
from decimal import Decimal
from playwright.async_api import async_playwright, Playwright
import pytest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SalesAPITester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api"
        self.access_token = None
        self.customer_id = None
        self.product_variant_id = None
        self.sale_id = None
        self.account_code = None
        
    async def setup_browser(self, playwright: Playwright):
        """Setup browser and page"""
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
    async def login(self):
        """Login with provided credentials"""
        logger.info("🔐 Logging in with credentials...")
        
        login_data = {
            "username": "rnrinfo",
            "password": "rnrinfo"
        }
        
        response = await self.page.request.post(
            f"{self.api_base}/auth/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"username={login_data['username']}&password={login_data['password']}"
        )
        
        if response.status == 200:
            result = await response.json()
            self.access_token = result.get("access_token")
            logger.info("✅ Login successful")
            return True
        else:
            logger.error(f"❌ Login failed: {response.status}")
            text = await response.text()
            logger.error(f"Response: {text}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def setup_test_data(self):
        """Setup required test data - customer, product, account"""
        logger.info("🔧 Setting up test data...")
        
        # Get or create a customer
        await self.setup_customer()
        
        # Get or create a product variant
        await self.setup_product()
        
        # Get an account for payments
        await self.setup_account()
    
    async def setup_customer(self):
        """Get or create a test customer"""
        # First, try to get existing customers
        response = await self.page.request.get(
            f"{self.api_base}/customers/",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            customers = await response.json()
            if customers and len(customers) > 0:
                self.customer_id = customers[0]["id"]
                logger.info(f"✅ Using existing customer ID: {self.customer_id}")
                return
        
        # Create a new customer if none exist
        customer_data = {
            "customer_name": "Test Customer for Sales API",
            "contact_person": "John Doe",
            "phone": "+1-555-0123",
            "email": "testcustomer@example.com",
            "address": "123 Test Street, Test City, TC 12345",
            "customer_type": "RETAIL",
            "credit_limit": 50000.00,
            "payment_terms": "NET30",
            "gst_number": "TESTGST123",
            "is_active": True
        }
        
        response = await self.page.request.post(
            f"{self.api_base}/customers/",
            headers=self.get_headers(),
            data=json.dumps(customer_data)
        )
        
        if response.status == 200:
            customer = await response.json()
            self.customer_id = customer["id"]
            logger.info(f"✅ Created new customer ID: {self.customer_id}")
        else:
            logger.error(f"❌ Failed to create customer: {response.status}")
            text = await response.text()
            logger.error(f"Response: {text}")
    
    async def setup_product(self):
        """Get or create a test product variant"""
        # Try to get existing product variants
        response = await self.page.request.get(
            f"{self.api_base}/products/variants/",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            variants = await response.json()
            if variants and len(variants) > 0:
                self.product_variant_id = variants[0]["id"]
                logger.info(f"✅ Using existing product variant ID: {self.product_variant_id}")
                return
        
        logger.warning("⚠️ No product variants found. You may need to create products first.")
        # For now, we'll use ID 1 assuming it exists
        self.product_variant_id = 1
    
    async def setup_account(self):
        """Get an account for payment testing"""
        response = await self.page.request.get(
            f"{self.api_base}/accounts/",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            accounts = await response.json()
            # Look for a bank or cash account
            for account in accounts:
                if account.get("account_type") in ["BANK", "CASH"]:
                    self.account_code = account["account_code"]
                    logger.info(f"✅ Using account: {self.account_code}")
                    break
            
            if not self.account_code and accounts:
                self.account_code = accounts[0]["account_code"]
                logger.info(f"✅ Using first available account: {self.account_code}")
    
    async def test_create_sale(self):
        """Test creating a new sale with items"""
        logger.info("🛒 Testing sale creation...")
        
        sale_data = {
            "customer_id": self.customer_id,
            "sale_date": date.today().isoformat(),
            "sale_type": "REGULAR",
            "reference_number": "TEST-SALE-001",
            "notes": "Test sale created via API testing",
            "sale_items": [
                {
                    "product_variant_id": self.product_variant_id,
                    "quantity": 5.0,
                    "unit_price": 100.00,
                    "discount_percentage": 10.0,
                    "tax_percentage": 18.0,
                    "item_description": "Test Product Item 1"
                },
                {
                    "product_variant_id": self.product_variant_id,
                    "quantity": 3.0,
                    "unit_price": 150.00,
                    "discount_percentage": 5.0,
                    "tax_percentage": 18.0,
                    "item_description": "Test Product Item 2"
                }
            ]
        }
        
        response = await self.page.request.post(
            f"{self.api_base}/sales/",
            headers=self.get_headers(),
            data=json.dumps(sale_data)
        )
        
        if response.status == 200:
            sale = await response.json()
            self.sale_id = sale["id"]
            logger.info(f"✅ Sale created successfully - ID: {self.sale_id}")
            logger.info(f"   Sale Number: {sale['sale_number']}")
            logger.info(f"   Total Amount: ${sale['total_amount']}")
            logger.info(f"   Status: {sale['status']}")
            logger.info(f"   Items Count: {len(sale['sale_items'])}")
            
            # Verify calculations
            expected_subtotal = (5 * 100 * 0.9) + (3 * 150 * 0.95)  # After discounts
            logger.info(f"   Subtotal: ${sale['subtotal']} (Expected: ${expected_subtotal})")
            
            return True
        else:
            logger.error(f"❌ Failed to create sale: {response.status}")
            text = await response.text()
            logger.error(f"Response: {text}")
            return False
    
    async def test_get_sale_details(self):
        """Test getting sale details"""
        logger.info("📋 Testing get sale details...")
        
        if not self.sale_id:
            logger.error("❌ No sale ID available for testing")
            return False
        
        response = await self.page.request.get(
            f"{self.api_base}/sales/{self.sale_id}",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            sale = await response.json()
            logger.info(f"✅ Retrieved sale details:")
            logger.info(f"   Sale Number: {sale['sale_number']}")
            logger.info(f"   Customer: {sale['customer']['customer_name']}")
            logger.info(f"   Total Amount: ${sale['total_amount']}")
            logger.info(f"   Payment Status: {sale['payment_status']}")
            logger.info(f"   Balance Amount: ${sale['balance_amount']}")
            return True
        else:
            logger.error(f"❌ Failed to get sale details: {response.status}")
            return False
    
    async def test_update_sale(self):
        """Test updating sale details"""
        logger.info("✏️ Testing sale update...")
        
        if not self.sale_id:
            logger.error("❌ No sale ID available for testing")
            return False
        
        update_data = {
            "notes": "Updated test sale via API testing - Modified",
            "reference_number": "TEST-SALE-001-UPDATED"
        }
        
        response = await self.page.request.put(
            f"{self.api_base}/sales/{self.sale_id}",
            headers=self.get_headers(),
            data=json.dumps(update_data)
        )
        
        if response.status == 200:
            sale = await response.json()
            logger.info(f"✅ Sale updated successfully:")
            logger.info(f"   Updated Notes: {sale['notes']}")
            logger.info(f"   Updated Reference: {sale['reference_number']}")
            return True
        else:
            logger.error(f"❌ Failed to update sale: {response.status}")
            text = await response.text()
            logger.error(f"Response: {text}")
            return False
    
    async def test_confirm_sale(self):
        """Test confirming a sale (business logic - stock deduction)"""
        logger.info("✅ Testing sale confirmation (stock deduction)...")
        
        if not self.sale_id:
            logger.error("❌ No sale ID available for testing")
            return False
        
        response = await self.page.request.post(
            f"{self.api_base}/sales/{self.sale_id}/confirm",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            result = await response.json()
            logger.info(f"✅ Sale confirmed successfully:")
            logger.info(f"   Message: {result.get('message', 'Sale confirmed')}")
            
            # Check if sale status changed
            sale_response = await self.page.request.get(
                f"{self.api_base}/sales/{self.sale_id}",
                headers=self.get_headers()
            )
            
            if sale_response.status == 200:
                sale = await sale_response.json()
                logger.info(f"   Updated Status: {sale['status']}")
                logger.info(f"   Stock Deducted: Check sale items for stock_deducted flag")
            
            return True
        else:
            logger.error(f"❌ Failed to confirm sale: {response.status}")
            text = await response.text()
            logger.error(f"Response: {text}")
            return False
    
    async def test_create_payment(self):
        """Test creating a payment for the sale"""
        logger.info("💳 Testing payment creation...")
        
        if not self.sale_id:
            logger.error("❌ No sale ID available for testing")
            return False
        
        payment_data = {
            "payment_date": date.today().isoformat(),
            "payment_amount": 500.00,
            "payment_method": "CASH",
            "payment_reference": "CASH-PAY-001",
            "bank_account_id": self.account_code,
            "notes": "Partial payment via API testing"
        }
        
        response = await self.page.request.post(
            f"{self.api_base}/sales/{self.sale_id}/payments/",
            headers=self.get_headers(),
            data=json.dumps(payment_data)
        )
        
        if response.status == 200:
            payment = await response.json()
            logger.info(f"✅ Payment created successfully:")
            logger.info(f"   Payment Amount: ${payment['payment_amount']}")
            logger.info(f"   Payment Method: {payment['payment_method']}")
            logger.info(f"   Payment Status: {payment['payment_status']}")
            logger.info(f"   Transaction ID: {payment.get('transaction_id', 'N/A')}")
            return True
        else:
            logger.error(f"❌ Failed to create payment: {response.status}")
            text = await response.text()
            logger.error(f"Response: {text}")
            return False
    
    async def test_list_payments(self):
        """Test listing payments for a sale"""
        logger.info("📜 Testing payment listing...")
        
        if not self.sale_id:
            logger.error("❌ No sale ID available for testing")
            return False
        
        response = await self.page.request.get(
            f"{self.api_base}/sales/{self.sale_id}/payments/",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            payments = await response.json()
            logger.info(f"✅ Retrieved {len(payments)} payments:")
            for payment in payments:
                logger.info(f"   - ${payment['payment_amount']} via {payment['payment_method']} on {payment['payment_date']}")
            return True
        else:
            logger.error(f"❌ Failed to list payments: {response.status}")
            return False
    
    async def test_sales_reports(self):
        """Test sales reporting endpoints"""
        logger.info("📊 Testing sales reports...")
        
        # Test summary report
        response = await self.page.request.get(
            f"{self.api_base}/sales/reports/summary",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            summary = await response.json()
            logger.info("✅ Sales Summary Report:")
            logger.info(f"   Total Sales: {summary.get('total_sales', 0)}")
            logger.info(f"   Total Amount: ${summary.get('total_amount', 0)}")
            logger.info(f"   Paid Amount: ${summary.get('paid_amount', 0)}")
            logger.info(f"   Outstanding: ${summary.get('outstanding_amount', 0)}")
        else:
            logger.error(f"❌ Failed to get summary report: {response.status}")
        
        # Test status summary report
        response = await self.page.request.get(
            f"{self.api_base}/sales/reports/status-summary",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            status_summary = await response.json()
            logger.info("✅ Sales Status Summary:")
            for status in status_summary.get('status_breakdown', []):
                logger.info(f"   {status['status']}: {status['count']} sales (${status['total_amount']})")
            return True
        else:
            logger.error(f"❌ Failed to get status summary: {response.status}")
            return False
    
    async def test_ledger_transactions(self):
        """Test if ledger transactions were created"""
        logger.info("📚 Testing ledger transactions integration...")
        
        # Get ledger transactions related to our sale
        response = await self.page.request.get(
            f"{self.api_base}/ledger/transactions/",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            transactions = await response.json()
            
            # Look for transactions related to our sale
            sale_transactions = [
                t for t in transactions 
                if t.get('reference_type') == 'SALE' and str(t.get('reference_id')) == str(self.sale_id)
            ]
            
            logger.info(f"✅ Found {len(sale_transactions)} ledger transactions for sale {self.sale_id}:")
            for trans in sale_transactions:
                logger.info(f"   - {trans['description']}: ${trans.get('debit_amount', 0)} debit, ${trans.get('credit_amount', 0)} credit")
            
            return len(sale_transactions) > 0
        else:
            logger.error(f"❌ Failed to get ledger transactions: {response.status}")
            return False
    
    async def test_list_sales(self):
        """Test listing all sales with filtering"""
        logger.info("📋 Testing sales listing with filters...")
        
        # Test basic listing
        response = await self.page.request.get(
            f"{self.api_base}/sales/",
            headers=self.get_headers()
        )
        
        if response.status == 200:
            sales = await response.json()
            logger.info(f"✅ Retrieved {len(sales)} sales")
            
            # Test with date filter
            today = date.today().isoformat()
            response = await self.page.request.get(
                f"{self.api_base}/sales/?from_date={today}&to_date={today}",
                headers=self.get_headers()
            )
            
            if response.status == 200:
                filtered_sales = await response.json()
                logger.info(f"✅ Filtered by today's date: {len(filtered_sales)} sales")
            
            # Test with customer filter
            if self.customer_id:
                response = await self.page.request.get(
                    f"{self.api_base}/sales/?customer_id={self.customer_id}",
                    headers=self.get_headers()
                )
                
                if response.status == 200:
                    customer_sales = await response.json()
                    logger.info(f"✅ Filtered by customer {self.customer_id}: {len(customer_sales)} sales")
            
            return True
        else:
            logger.error(f"❌ Failed to list sales: {response.status}")
            return False
    
    async def run_all_tests(self):
        """Run all API tests"""
        logger.info("🚀 Starting Sales API Testing Suite...")
        
        async with async_playwright() as playwright:
            await self.setup_browser(playwright)
            
            try:
                # Authentication
                if not await self.login():
                    return False
                
                # Setup test data
                await self.setup_test_data()
                
                # Run tests in sequence
                tests = [
                    ("Create Sale", self.test_create_sale),
                    ("Get Sale Details", self.test_get_sale_details),
                    ("Update Sale", self.test_update_sale),
                    ("Confirm Sale", self.test_confirm_sale),
                    ("Create Payment", self.test_create_payment),
                    ("List Payments", self.test_list_payments),
                    ("List Sales", self.test_list_sales),
                    ("Sales Reports", self.test_sales_reports),
                    ("Ledger Transactions", self.test_ledger_transactions)
                ]
                
                results = {}
                for test_name, test_func in tests:
                    logger.info(f"\n{'='*50}")
                    logger.info(f"🧪 Running Test: {test_name}")
                    logger.info(f"{'='*50}")
                    
                    try:
                        result = await test_func()
                        results[test_name] = result
                        if result:
                            logger.info(f"✅ {test_name} - PASSED")
                        else:
                            logger.error(f"❌ {test_name} - FAILED")
                    except Exception as e:
                        logger.error(f"❌ {test_name} - ERROR: {str(e)}")
                        results[test_name] = False
                    
                    # Small delay between tests
                    await asyncio.sleep(1)
                
                # Print summary
                logger.info(f"\n{'='*50}")
                logger.info("📊 TEST SUMMARY")
                logger.info(f"{'='*50}")
                
                passed = sum(1 for result in results.values() if result)
                total = len(results)
                
                for test_name, result in results.items():
                    status = "✅ PASSED" if result else "❌ FAILED"
                    logger.info(f"{test_name}: {status}")
                
                logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
                
                if passed == total:
                    logger.info("🎉 All tests passed! Sales API is working correctly.")
                else:
                    logger.warning(f"⚠️ {total-passed} tests failed. Please check the issues above.")
                
            finally:
                await self.browser.close()

async def main():
    """Main test runner"""
    tester = SalesAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
