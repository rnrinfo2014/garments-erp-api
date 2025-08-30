#!/usr/bin/env python3
"""
Create Sample Sales Data
Add test data for sales system development and testing
"""

import sys
import os
from decimal import Decimal
from datetime import date, datetime, timedelta

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from sqlalchemy.orm import sessionmaker
from database import engine
from models.sales import Sales, SalesItem, SalesStatus
from models.bill_book import BillBook, TaxType
from models.customers import Customer
from models.agents import Agent
from models.product_management import ProductVariant, Product
from utils.sales_calculator import SalesBusinessLogic
from schemas.sales import SalesCreate, SalesItemCreate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_product_variants(db):
    """Create sample product variants for testing"""
    try:
        logger.info("Creating sample product variants...")
        
        # Check if variants already exist
        existing_count = db.query(ProductVariant).count()
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing product variants")
            return
        
        # Create sample products first
        products_data = [
            {
                "product_name": "Cotton Shirt",
                "product_code": "CS001",
                "price_a": Decimal("200.00"),
                "price_b": Decimal("180.00"),
                "price_c": Decimal("160.00")
            },
            {
                "product_name": "Formal Shirt",
                "product_code": "FS001",
                "price_a": Decimal("300.00"),
                "price_b": Decimal("280.00"),
                "price_c": Decimal("260.00")
            },
            {
                "product_name": "Casual T-Shirt",
                "product_code": "CT001",
                "price_a": Decimal("150.00"),
                "price_b": Decimal("130.00"),
                "price_c": Decimal("110.00")
            }
        ]
        
        products = []
        for prod_data in products_data:
            product = Product(**prod_data)
            db.add(product)
            products.append(product)
        
        db.flush()
        
        # Create sample variants
        variants_data = [
            {
                "product_id": products[0].id,
                "size_id": 1,  # Assuming size 1 exists
                "sleeve_type_id": 1,  # Assuming sleeve type 1 exists
                "design_id": 1,  # Assuming design 1 exists
                "variant_name": "Cotton Shirt - M - Full Sleeve - Plain",
                "variant_code": "CS001-M-FS-PLN",
                "sku": "CS001M001",
                "hsn_code": "6205",
                "unit_type": "PCS",
                "price": Decimal("180.00"),
                "cost_price": Decimal("120.00"),
                "mrp": Decimal("200.00"),
                "stock_balance": Decimal("100.00")
            },
            {
                "product_id": products[0].id,
                "size_id": 2,  # Assuming size 2 exists
                "sleeve_type_id": 1,
                "design_id": 1,
                "variant_name": "Cotton Shirt - L - Full Sleeve - Plain",
                "variant_code": "CS001-L-FS-PLN",
                "sku": "CS001L001",
                "hsn_code": "6205",
                "unit_type": "PCS",
                "price": Decimal("180.00"),
                "cost_price": Decimal("120.00"),
                "mrp": Decimal("200.00"),
                "stock_balance": Decimal("80.00")
            },
            {
                "product_id": products[1].id,
                "size_id": 1,
                "sleeve_type_id": 1,
                "design_id": 2,  # Assuming design 2 exists
                "variant_name": "Formal Shirt - M - Full Sleeve - Checked",
                "variant_code": "FS001-M-FS-CHK",
                "sku": "FS001M002",
                "hsn_code": "6205",
                "unit_type": "PCS",
                "price": Decimal("280.00"),
                "cost_price": Decimal("200.00"),
                "mrp": Decimal("300.00"),
                "stock_balance": Decimal("50.00")
            },
            {
                "product_id": products[2].id,
                "size_id": 1,
                "sleeve_type_id": 2,  # Assuming sleeve type 2 exists
                "design_id": 1,
                "variant_name": "Casual T-Shirt - M - Half Sleeve - Plain",
                "variant_code": "CT001-M-HS-PLN",
                "sku": "CT001M001",
                "hsn_code": "6109",
                "unit_type": "PCS",
                "price": Decimal("130.00"),
                "cost_price": Decimal("80.00"),
                "mrp": Decimal("150.00"),
                "stock_balance": Decimal("200.00")
            }
        ]
        
        for variant_data in variants_data:
            variant = ProductVariant(**variant_data)
            db.add(variant)
        
        db.commit()
        logger.info(f"Created {len(variants_data)} sample product variants")
        
    except Exception as e:
        logger.error(f"Error creating sample product variants: {e}")
        db.rollback()


def create_sample_sales_data(db):
    """Create sample sales data for testing"""
    try:
        logger.info("Creating sample sales data...")
        
        # Check if sales already exist
        existing_count = db.query(Sales).count()
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing sales records")
            return
        
        # Get required master data
        bill_books = db.query(BillBook).filter(BillBook.status == "ACTIVE").all()
        customers = db.query(Customer).filter(Customer.status == "Active").limit(3).all()
        agents = db.query(Agent).filter(Agent.status == "Active").limit(2).all()
        variants = db.query(ProductVariant).filter(ProductVariant.is_active == True).limit(4).all()
        
        if not bill_books:
            logger.error("No active bill books found. Please create bill books first.")
            return
        
        if not customers:
            logger.error("No active customers found. Please create customers first.")
            return
        
        if not variants:
            logger.error("No active product variants found.")
            return
        
        logger.info(f"Found {len(bill_books)} bill books, {len(customers)} customers, {len(variants)} variants")
        
        # Sample sales data
        sales_data_list = [
            {
                "bill_book_id": bill_books[0].id,
                "customer_id": customers[0].id,
                "agent_id": agents[0].id if agents else None,
                "bill_date": date.today() - timedelta(days=5),
                "due_date": date.today() + timedelta(days=25),
                "additional_charges": Decimal("50.00"),
                "transport_details": "By road via ABC Transport",
                "llr_no": "LLR001",
                "llr_date": date.today() - timedelta(days=5),
                "items": [
                    {
                        "variant_id": variants[0].id,
                        "quantity": Decimal("5.000"),
                        "sale_rate": Decimal("180.00"),
                        "discount_percentage": Decimal("10.0"),
                        "tax_percentage": Decimal("18.0")
                    },
                    {
                        "variant_id": variants[1].id,
                        "quantity": Decimal("3.000"),
                        "sale_rate": Decimal("180.00"),
                        "discount_percentage": Decimal("5.0"),
                        "tax_percentage": Decimal("18.0")
                    }
                ]
            },
            {
                "bill_book_id": bill_books[0].id,
                "customer_id": customers[1].id if len(customers) > 1 else customers[0].id,
                "agent_id": agents[1].id if len(agents) > 1 else (agents[0].id if agents else None),
                "bill_date": date.today() - timedelta(days=3),
                "due_date": date.today() + timedelta(days=27),
                "additional_charges": Decimal("0.00"),
                "transport_details": "Customer pickup",
                "items": [
                    {
                        "variant_id": variants[2].id,
                        "quantity": Decimal("2.000"),
                        "sale_rate": Decimal("280.00"),
                        "discount_percentage": Decimal("15.0"),
                        "tax_percentage": Decimal("18.0")
                    }
                ]
            },
            {
                "bill_book_id": bill_books[0].id,
                "customer_id": customers[2].id if len(customers) > 2 else customers[0].id,
                "agent_id": None,
                "bill_date": date.today() - timedelta(days=1),
                "due_date": date.today() + timedelta(days=29),
                "additional_charges": Decimal("25.00"),
                "transport_details": "Express delivery",
                "items": [
                    {
                        "variant_id": variants[3].id,
                        "quantity": Decimal("10.000"),
                        "sale_rate": Decimal("130.00"),
                        "discount_percentage": Decimal("8.0"),
                        "tax_percentage": Decimal("12.0")
                    },
                    {
                        "variant_id": variants[0].id,
                        "quantity": Decimal("2.000"),
                        "sale_rate": Decimal("175.00"),
                        "discount_percentage": Decimal("0.0"),
                        "tax_percentage": Decimal("18.0")
                    }
                ]
            }
        ]
        
        # Create sales records
        created_sales = []
        for i, sales_data in enumerate(sales_data_list):
            try:
                # Convert to Pydantic schemas
                items = [SalesItemCreate(**item) for item in sales_data.pop("items")]
                sales_create = SalesCreate(**sales_data, items=items)
                
                # Create sales using business logic
                success, message, sales = SalesBusinessLogic.create_sales_transaction(
                    db=db,
                    sales_data=sales_create,
                    created_by="admin"
                )
                
                if success:
                    created_sales.append(sales)
                    logger.info(f"Created sample sales {i+1}: {sales.bill_number}")
                    
                    # Update status for some sales to show workflow
                    if i == 0:  # First sales - confirm it
                        sales.status = SalesStatus.CONFIRMED
                        sales.updated_by = "admin"
                    elif i == 1:  # Second sales - dispatch it
                        sales.status = SalesStatus.DISPATCHED
                        sales.updated_by = "admin"
                    # Third sales remains DRAFT
                    
                else:
                    logger.error(f"Failed to create sample sales {i+1}: {message}")
                    
            except Exception as e:
                logger.error(f"Error creating sample sales {i+1}: {e}")
        
        db.commit()
        
        logger.info(f"Successfully created {len(created_sales)} sample sales records")
        
        # Show summary
        for sales in created_sales:
            logger.info(f"  - {sales.bill_number}: {sales.customer.customer_name}, "
                       f"Status: {sales.status.value}, Amount: ₹{sales.total_amount}")
        
    except Exception as e:
        logger.error(f"Error creating sample sales data: {e}")
        db.rollback()


def show_sales_system_status(db):
    """Show current status of sales system"""
    try:
        logger.info("\n" + "="*60)
        logger.info("📊 SALES SYSTEM STATUS")
        logger.info("="*60)
        
        # Count records
        sales_count = db.query(Sales).count()
        items_count = db.query(SalesItem).count()
        bill_books_count = db.query(BillBook).filter(BillBook.status == "ACTIVE").count()
        customers_count = db.query(Customer).filter(Customer.status == "Active").count()
        variants_count = db.query(ProductVariant).filter(ProductVariant.is_active == True).count()
        
        logger.info(f"📋 Sales Records: {sales_count}")
        logger.info(f"📦 Sales Items: {items_count}")
        logger.info(f"📚 Active Bill Books: {bill_books_count}")
        logger.info(f"👥 Active Customers: {customers_count}")
        logger.info(f"🛍️ Active Product Variants: {variants_count}")
        
        if sales_count > 0:
            # Status breakdown
            logger.info("\n📊 Sales Status Breakdown:")
            for status in SalesStatus:
                count = db.query(Sales).filter(Sales.status == status).count()
                if count > 0:
                    logger.info(f"  {status.value}: {count}")
            
            # Recent sales
            recent_sales = db.query(Sales).order_by(Sales.created_at.desc()).limit(3).all()
            logger.info("\n🕒 Recent Sales:")
            for sales in recent_sales:
                logger.info(f"  {sales.bill_number}: ₹{sales.total_amount} ({sales.status.value})")
        
        logger.info("\n🚀 Sales system is ready for testing!")
        logger.info("You can now test the API endpoints at http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"Error showing sales system status: {e}")


if __name__ == "__main__":
    logger.info("🎯 Creating Sample Sales Data...")
    logger.info("=" * 60)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Create sample data
        create_sample_product_variants(session)
        create_sample_sales_data(session)
        
        # Show status
        show_sales_system_status(session)
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        session.rollback()
    finally:
        session.close()
    
    logger.info("\n✅ Sample data creation completed!")
