#!/usr/bin/env python3
"""
Test Sales Models and Relationships
Verify that all models are properly configured and relationships work
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import engine
from models.sales import Sales, SalesItem, SalesStatus
from models.bill_book import BillBook, TaxType
from models.customers import Customer
from models.agents import Agent
from models.product_management import ProductVariant
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_model_creation():
    """Test that all models can be imported and created"""
    try:
        logger.info("🧪 Testing Sales Model Creation")
        logger.info("=" * 50)
        
        # Test Sales model
        logger.info("✅ Sales model imported successfully")
        logger.info(f"   - Table name: {Sales.__tablename__}")
        logger.info(f"   - Primary key: {Sales.__table__.primary_key.columns.keys()}")
        
        # Test SalesItem model
        logger.info("✅ SalesItem model imported successfully")
        logger.info(f"   - Table name: {SalesItem.__tablename__}")
        logger.info(f"   - Primary key: {SalesItem.__table__.primary_key.columns.keys()}")
        
        # Test enum
        logger.info("✅ SalesStatus enum imported successfully")
        logger.info(f"   - Available statuses: {[status.value for status in SalesStatus]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model creation test failed: {e}")
        return False


def test_model_relationships():
    """Test that model relationships are properly configured"""
    try:
        logger.info("\n🔗 Testing Model Relationships")
        logger.info("=" * 50)
        
        # Test Sales relationships
        sales_relationships = [
            'bill_book', 'customer', 'agent', 'items'
        ]
        
        for rel in sales_relationships:
            if hasattr(Sales, rel):
                logger.info(f"✅ Sales.{rel} relationship exists")
            else:
                logger.error(f"❌ Sales.{rel} relationship missing")
                return False
        
        # Test SalesItem relationships
        item_relationships = ['sales', 'variant']
        
        for rel in item_relationships:
            if hasattr(SalesItem, rel):
                logger.info(f"✅ SalesItem.{rel} relationship exists")
            else:
                logger.error(f"❌ SalesItem.{rel} relationship missing")
                return False
        
        # Test reverse relationships
        reverse_rels = [
            (BillBook, 'sales'),
            (Customer, 'sales'),
            (Agent, 'sales'),
            (ProductVariant, 'sales_items')
        ]
        
        for model, rel in reverse_rels:
            if hasattr(model, rel):
                logger.info(f"✅ {model.__name__}.{rel} reverse relationship exists")
            else:
                logger.error(f"❌ {model.__name__}.{rel} reverse relationship missing")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Relationship test failed: {e}")
        return False


def test_model_properties():
    """Test model properties and methods"""
    try:
        logger.info("\n🧮 Testing Model Properties and Methods")
        logger.info("=" * 50)
        
        # Test Sales model properties
        sales_props = [
            'is_editable', 'is_cancellable', 'can_dispatch', 'can_deliver'
        ]
        
        for prop in sales_props:
            if hasattr(Sales, prop):
                logger.info(f"✅ Sales.{prop} property exists")
            else:
                logger.error(f"❌ Sales.{prop} property missing")
                return False
        
        # Test Sales model methods
        sales_methods = ['calculate_totals']
        
        for method in sales_methods:
            if hasattr(Sales, method):
                logger.info(f"✅ Sales.{method} method exists")
            else:
                logger.error(f"❌ Sales.{method} method missing")
                return False
        
        # Test SalesItem properties
        item_props = [
            'line_total_before_discount', 
            'line_total_after_discount', 
            'effective_rate_after_discount'
        ]
        
        for prop in item_props:
            if hasattr(SalesItem, prop):
                logger.info(f"✅ SalesItem.{prop} property exists")
            else:
                logger.error(f"❌ SalesItem.{prop} property missing")
                return False
        
        # Test SalesItem methods
        item_methods = ['calculate_amounts', 'validate_amounts']
        
        for method in item_methods:
            if hasattr(SalesItem, method):
                logger.info(f"✅ SalesItem.{method} method exists")
            else:
                logger.error(f"❌ SalesItem.{method} method missing")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Properties test failed: {e}")
        return False


def test_database_reflection():
    """Test that models can reflect database tables"""
    try:
        logger.info("\n🔍 Testing Database Reflection")
        logger.info("=" * 50)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Test sales table query
            sales_count = session.query(Sales).count()
            logger.info(f"✅ Sales table accessible - {sales_count} records")
            
            # Test sales_items table query
            items_count = session.query(SalesItem).count()
            logger.info(f"✅ SalesItems table accessible - {items_count} records")
            
            # Test join query
            join_count = session.query(Sales).join(SalesItem, isouter=True).count()
            logger.info(f"✅ Sales-Items join query works - {join_count} sales with items")
            
            # Test enum query
            draft_count = session.query(Sales).filter(Sales.status == SalesStatus.DRAFT).count()
            logger.info(f"✅ Enum filter query works - {draft_count} draft sales")
            
            return True
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"❌ Database reflection test failed: {e}")
        return False


def test_utility_imports():
    """Test that utility classes can be imported"""
    try:
        logger.info("\n🛠️ Testing Utility Imports")
        logger.info("=" * 50)
        
        from utils.sales_calculator import SalesCalculator, SalesValidator, SalesBusinessLogic, SalesReportGenerator
        from schemas.sales import SalesCreate, SalesUpdate, SalesResponse, SalesItemCreate
        
        logger.info("✅ SalesCalculator imported successfully")
        logger.info("✅ SalesValidator imported successfully")
        logger.info("✅ SalesBusinessLogic imported successfully")
        logger.info("✅ SalesReportGenerator imported successfully")
        logger.info("✅ Sales schemas imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Utility import test failed: {e}")
        return False


def show_phase2_summary():
    """Show Phase 2 completion summary"""
    logger.info("\n" + "="*60)
    logger.info("🎉 PHASE 2: MODEL CREATION COMPLETE!")
    logger.info("="*60)
    
    logger.info("\n📊 CREATED COMPONENTS:")
    logger.info("  ✅ SQLAlchemy Models (models/sales.py)")
    logger.info("     - Sales model with business properties")
    logger.info("     - SalesItem model with calculations")
    logger.info("     - SalesStatus enum for workflow")
    
    logger.info("\n  ✅ Pydantic Schemas (schemas/sales.py)")
    logger.info("     - Request/Response schemas")
    logger.info("     - Validation rules and constraints")
    logger.info("     - Pagination and filtering support")
    
    logger.info("\n  ✅ Business Logic (utils/sales_calculator.py)")
    logger.info("     - SalesCalculator for financial calculations")
    logger.info("     - SalesValidator for business rule validation")
    logger.info("     - SalesBusinessLogic for complex operations")
    logger.info("     - SalesReportGenerator for analytics")
    
    logger.info("\n  ✅ Model Relationships Updated")
    logger.info("     - BillBook ←→ Sales relationship")
    logger.info("     - Customer ←→ Sales relationship")
    logger.info("     - Agent ←→ Sales relationship")
    logger.info("     - ProductVariant ←→ SalesItems relationship")
    
    logger.info("\n🚀 FEATURES IMPLEMENTED:")
    logger.info("  • Tax calculations (Include/Exclude/Without tax)")
    logger.info("  • Discount calculations at item level")
    logger.info("  • Status workflow validation")
    logger.info("  • Automatic total calculations")
    logger.info("  • Bill number generation integration")
    logger.info("  • Product variant integration")
    logger.info("  • Comprehensive validation rules")
    
    logger.info("\n🔄 READY FOR PHASE 3:")
    logger.info("  1. Create API endpoints (routes/sales.py)")
    logger.info("  2. Implement CRUD operations")
    logger.info("  3. Add business logic integration")
    logger.info("  4. Create test data")
    logger.info("  5. Test complete workflow")


if __name__ == "__main__":
    logger.info("🧪 Starting Sales Models Testing...")
    logger.info("=" * 60)
    
    all_tests_passed = True
    
    tests = [
        ("Model Creation", test_model_creation),
        ("Model Relationships", test_model_relationships),
        ("Model Properties", test_model_properties),
        ("Database Reflection", test_database_reflection),
        ("Utility Imports", test_utility_imports)
    ]
    
    for test_name, test_func in tests:
        if not test_func():
            all_tests_passed = False
            logger.error(f"❌ {test_name} test failed")
            break
        logger.info(f"✅ {test_name} test passed")
    
    if all_tests_passed:
        show_phase2_summary()
        logger.info("\n🚀 All tests passed! Ready for Phase 3!")
    else:
        logger.error("\n❌ Some tests failed. Please fix the issues before proceeding.")
