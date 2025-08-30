# Sales API Testing Requirements
install_dependencies = """
pip install playwright pytest-asyncio
python -m playwright install
"""

# API Testing Configuration
API_BASE_URL = "http://localhost:8000/api"
CREDENTIALS = {
    "username": "rnrinfo",
    "password": "rnrinfo"
}

# Test Data Templates
test_customer = {
    "customer_name": "Playwright Test Customer",
    "contact_person": "API Tester",
    "phone": "+1-555-TEST",
    "email": "apitest@rnrinfo.com",
    "address": "123 API Test Street, Test City, TC 12345",
    "customer_type": "RETAIL",
    "credit_limit": 25000.00,
    "payment_terms": "NET30",
    "is_active": True
}

test_sale = {
    "sale_type": "REGULAR", 
    "reference_number": "PW-TEST-001",
    "notes": "Playwright API Test Sale",
    "sale_items": [
        {
            "product_variant_id": 1,
            "quantity": 10.0,
            "unit_price": 250.00,
            "discount_percentage": 15.0,
            "tax_percentage": 18.0,
            "item_description": "Test Product A - API Testing"
        },
        {
            "product_variant_id": 1,
            "quantity": 5.0,
            "unit_price": 400.00,
            "discount_percentage": 8.0,
            "tax_percentage": 18.0,
            "item_description": "Test Product B - API Testing"
        }
    ]
}

test_payment = {
    "payment_amount": 1000.00,
    "payment_method": "BANK_TRANSFER",
    "payment_reference": "PW-PAY-001",
    "notes": "Playwright test payment"
}
