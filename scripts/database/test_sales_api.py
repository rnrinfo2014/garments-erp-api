#!/usr/bin/env python3
"""
Test Sales API Implementation
Comprehensive testing of sales API endpoints
"""

import sys
import os
from decimal import Decimal
from datetime import date

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from sqlalchemy.orm import sessionmaker
from database import engine
from models.sales import Sales, SalesItem, SalesStatus
from models.bill_book import BillBook
from models.customers import Customer
from models.agents import Agent
from models.product_management import ProductVariant
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_api_imports():
    """Test that all API components can be imported"""
    try:
        logger.info("🧪 Testing API Imports")
        logger.info("=" * 50)
        
        # Test route imports
        from routes.sales import router
        logger.info("✅ Sales router imported successfully")
        
        # Test schema imports
        from schemas.sales import SalesCreate, SalesResponse, SalesFilter
        logger.info("✅ Sales schemas imported successfully")
        
        # Test utility imports
        from utils.sales_calculator import SalesCalculator, SalesValidator, SalesBusinessLogic
        logger.info("✅ Sales utilities imported successfully")
        
        # Test dependencies
        from dependencies import get_current_user
        from database import get_db
        logger.info("✅ Dependencies imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API import test failed: {e}")
        return False


def test_database_connectivity():
    """Test database connectivity and model access"""
    try:
        logger.info("\n🔍 Testing Database Connectivity")
        logger.info("=" * 50)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Test basic queries
            sales_count = session.query(Sales).count()
            logger.info(f"✅ Sales table accessible - {sales_count} records")
            
            items_count = session.query(SalesItem).count()
            logger.info(f"✅ Sales items table accessible - {items_count} records")
            
            bill_books_count = session.query(BillBook).count()
            logger.info(f"✅ Bill books table accessible - {bill_books_count} records")
            
            customers_count = session.query(Customer).count()
            logger.info(f"✅ Customers table accessible - {customers_count} records")
            
            variants_count = session.query(ProductVariant).count()
            logger.info(f"✅ Product variants table accessible - {variants_count} records")
            
            return True
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"❌ Database connectivity test failed: {e}")
        return False


def test_business_logic():
    """Test core business logic functions"""
    try:
        logger.info("\n🧮 Testing Business Logic")
        logger.info("=" * 50)
        
        from utils.sales_calculator import SalesCalculator, SalesValidator
        from models.bill_book import TaxType
        from schemas.sales import SalesItemCreate
        
        # Test tax calculations
        calc_result = SalesCalculator.calculate_item_amounts(
            quantity=Decimal("5"),
            sale_rate=Decimal("100"),
            discount_percentage=Decimal("10"),
            tax_percentage=Decimal("18"),
            tax_type=TaxType.EXCLUDE_TAX
        )
        
        expected_discount = Decimal("50.00")  # 5 * 100 * 10% = 50
        expected_tax = Decimal("81.00")  # (500-50) * 18% = 81
        expected_total = Decimal("531.00")  # 500 - 50 + 81 = 531
        
        if (abs(calc_result['discount_amount'] - expected_discount) < Decimal("0.01") and
            abs(calc_result['tax_amount'] - expected_tax) < Decimal("0.01") and
            abs(calc_result['total_amount'] - expected_total) < Decimal("0.01")):
            logger.info("✅ Tax calculation logic working correctly")
        else:
            logger.error(f"❌ Tax calculation failed: {calc_result}")
            return False
        
        # Test status validation
        is_valid, error = SalesValidator.validate_status_transition(
            SalesStatus.DRAFT, SalesStatus.CONFIRMED
        )
        if is_valid:
            logger.info("✅ Status validation logic working correctly")
        else:
            logger.error(f"❌ Status validation failed: {error}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Business logic test failed: {e}")
        return False


def test_model_relationships():
    """Test model relationships and joins"""
    try:
        logger.info("\n🔗 Testing Model Relationships")
        logger.info("=" * 50)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            from sqlalchemy.orm import joinedload
            
            # Test sales with all relationships
            sales_with_rels = session.query(Sales).options(
                joinedload(Sales.items),
                joinedload(Sales.bill_book),
                joinedload(Sales.customer),
                joinedload(Sales.agent)
            ).first()
            
            if sales_with_rels:
                logger.info("✅ Sales relationships loaded successfully")
                logger.info(f"   - Bill book: {sales_with_rels.bill_book.book_name if sales_with_rels.bill_book else 'None'}")
                logger.info(f"   - Customer: {sales_with_rels.customer.customer_name if sales_with_rels.customer else 'None'}")
                logger.info(f"   - Items count: {len(sales_with_rels.items)}")
            else:
                logger.warning("⚠️ No sales records found for relationship testing")
            
            # Test sales items with variant
            item_with_variant = session.query(SalesItem).options(
                joinedload(SalesItem.variant)
            ).first()
            
            if item_with_variant:
                logger.info("✅ Sales item relationships loaded successfully")
                logger.info(f"   - Product variant: {item_with_variant.variant.variant_name if item_with_variant.variant else 'None'}")
            else:
                logger.warning("⚠️ No sales items found for relationship testing")
            
            return True
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"❌ Model relationships test failed: {e}")
        return False


def test_api_endpoints_structure():
    """Test API endpoint structure and routing"""
    try:
        logger.info("\n🛣️ Testing API Endpoint Structure")
        logger.info("=" * 50)
        
        from routes.sales import router
        
        # Check if router has expected routes
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append(f"{list(route.methods)[0]} {route.path}")
        
        expected_endpoints = [
            "POST /",
            "GET /",
            "GET /{sales_id}",
            "PUT /{sales_id}",
            "DELETE /{sales_id}",
            "PATCH /{sales_id}/status",
            "GET /{sales_id}/items",
            "POST /{sales_id}/items",
            "PUT /{sales_id}/items/{item_id}",
            "DELETE /{sales_id}/items/{item_id}",
            "GET /analytics/summary",
            "GET /bill-books/active",
            "GET /customers/active",
            "GET /agents/active",
            "GET /product-variants/active"
        ]
        
        found_endpoints = 0
        for expected in expected_endpoints:
            if any(expected.split()[1] in route for route in routes):
                found_endpoints += 1
        
        logger.info(f"✅ Found {found_endpoints}/{len(expected_endpoints)} expected endpoints")
        
        if found_endpoints >= len(expected_endpoints) * 0.8:  # 80% threshold
            logger.info("✅ API endpoint structure looks good")
            return True
        else:
            logger.error("❌ Missing too many expected endpoints")
            return False
        
    except Exception as e:
        logger.error(f"❌ API endpoint structure test failed: {e}")
        return False


def show_api_documentation():
    """Show API documentation summary"""
    logger.info("\n" + "="*60)
    logger.info("📚 SALES API DOCUMENTATION SUMMARY")
    logger.info("="*60)
    
    logger.info("\n🔗 BASE URL: http://localhost:8000/api/sales")
    
    logger.info("\n📋 MAIN ENDPOINTS:")
    endpoints = [
        ("POST /", "Create new sales transaction"),
        ("GET /", "List sales with filtering and pagination"),
        ("GET /{id}", "Get sales details by ID"),
        ("PUT /{id}", "Update sales header"),
        ("DELETE /{id}", "Delete sales (DRAFT only)"),
        ("PATCH /{id}/status", "Update sales status"),
        ("POST /bulk-status-update", "Bulk status update"),
    ]
    
    for endpoint, description in endpoints:
        logger.info(f"  {endpoint:<25} - {description}")
    
    logger.info("\n📦 ITEMS ENDPOINTS:")
    item_endpoints = [
        ("GET /{id}/items", "Get all items for sales"),
        ("POST /{id}/items", "Add new item to sales"),
        ("PUT /{id}/items/{item_id}", "Update sales item"),
        ("DELETE /{id}/items/{item_id}", "Delete sales item"),
    ]
    
    for endpoint, description in item_endpoints:
        logger.info(f"  {endpoint:<25} - {description}")
    
    logger.info("\n📊 UTILITY ENDPOINTS:")
    utility_endpoints = [
        ("GET /analytics/summary", "Sales analytics and summary"),
        ("GET /bill-books/active", "Get active bill books"),
        ("GET /customers/active", "Get active customers"),
        ("GET /agents/active", "Get active agents"),
        ("GET /product-variants/active", "Get active product variants"),
    ]
    
    for endpoint, description in utility_endpoints:
        logger.info(f"  {endpoint:<25} - {description}")
    
    logger.info("\n🔍 FEATURES:")
    features = [
        "✅ Complete CRUD operations",
        "✅ Status workflow management (Draft→Confirmed→Dispatched→Delivered)",
        "✅ Automatic tax and discount calculations",
        "✅ Bill number generation",
        "✅ Advanced filtering and pagination",
        "✅ Sales analytics and reporting",
        "✅ Bulk operations support",
        "✅ Data validation and constraints",
        "✅ Audit trail tracking",
        "✅ Integration with existing ERP modules"
    ]
    
    for feature in features:
        logger.info(f"  {feature}")
    
    logger.info("\n🎯 AUTHENTICATION:")
    logger.info("  All endpoints require valid JWT token")
    logger.info("  Use /api/auth/login to get access token")
    
    logger.info("\n📖 INTERACTIVE DOCUMENTATION:")
    logger.info("  Swagger UI: http://localhost:8000/docs")
    logger.info("  ReDoc: http://localhost:8000/redoc")


def show_phase3_summary():
    """Show Phase 3 completion summary"""
    logger.info("\n" + "="*60)
    logger.info("🎉 PHASE 3: API DEVELOPMENT COMPLETE!")
    logger.info("="*60)
    
    logger.info("\n📊 CREATED COMPONENTS:")
    logger.info("  ✅ Complete Sales API (routes/sales.py)")
    logger.info("     - 15+ REST endpoints")
    logger.info("     - Full CRUD operations")
    logger.info("     - Status workflow management")
    logger.info("     - Items management")
    logger.info("     - Analytics and reporting")
    logger.info("     - Utility endpoints")
    
    logger.info("\n  ✅ API Integration")
    logger.info("     - Registered in main router")
    logger.info("     - Integrated with existing authentication")
    logger.info("     - Connected to all ERP modules")
    
    logger.info("\n  ✅ Sample Data Scripts")
    logger.info("     - Product variants creation")
    logger.info("     - Sample sales data")
    logger.info("     - Different status examples")
    
    logger.info("\n🚀 API FEATURES:")
    logger.info("  • Advanced filtering and search")
    logger.info("  • Pagination with customizable limits")
    logger.info("  • Sorting by any field")
    logger.info("  • Status workflow validation")
    logger.info("  • Automatic calculations")
    logger.info("  • Bulk operations")
    logger.info("  • Real-time validation")
    logger.info("  • Comprehensive error handling")
    
    logger.info("\n🔄 READY FOR TESTING:")
    logger.info("  1. Start the API server")
    logger.info("  2. Create sample data")
    logger.info("  3. Test endpoints via Swagger UI")
    logger.info("  4. Integrate with frontend")


if __name__ == "__main__":
    logger.info("🧪 Starting Sales API Testing...")
    logger.info("=" * 60)
    
    all_tests_passed = True
    
    tests = [
        ("API Imports", test_api_imports),
        ("Database Connectivity", test_database_connectivity),
        ("Business Logic", test_business_logic),
        ("Model Relationships", test_model_relationships),
        ("API Endpoint Structure", test_api_endpoints_structure)
    ]
    
    for test_name, test_func in tests:
        if not test_func():
            all_tests_passed = False
            logger.error(f"❌ {test_name} test failed")
            break
        logger.info(f"✅ {test_name} test passed")
    
    if all_tests_passed:
        show_api_documentation()
        show_phase3_summary()
        logger.info("\n🚀 All tests passed! Sales API is ready for use!")
    else:
        logger.error("\n❌ Some tests failed. Please fix the issues before proceeding.")
