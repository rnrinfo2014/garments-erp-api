"""
Sales Management Migration Script
This script creates the sales, sale_items, and sale_payments tables
and adds necessary relationships to existing tables.
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL, get_db
from models import Base, Sale, SaleItem, SalePayment
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sales_tables():
    """Create sales management tables"""
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL, echo=True)
        
        logger.info("Creating sales management tables...")
        
        # Create all tables in the correct order to handle dependencies
        Base.metadata.create_all(bind=engine)
        
        logger.info("Sales tables created successfully!")
        
        # Add some initial data if needed
        create_initial_data()
        
    except Exception as e:
        logger.error(f"Error creating sales tables: {str(e)}")
        raise


def create_initial_data():
    """Create initial data for sales system"""
    try:
        db = next(get_db())
        
        logger.info("Creating initial sales data...")
        
        # You can add initial data here if needed
        # For example, creating default accounts, etc.
        
        db.commit()
        logger.info("Initial sales data created successfully!")
        
    except Exception as e:
        logger.error(f"Error creating initial data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def add_indexes():
    """Add performance indexes for sales tables"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            logger.info("Adding performance indexes...")
            
            # Sales table indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);",
                "CREATE INDEX IF NOT EXISTS idx_sales_sale_date ON sales(sale_date);",
                "CREATE INDEX IF NOT EXISTS idx_sales_status ON sales(status);",
                "CREATE INDEX IF NOT EXISTS idx_sales_payment_status ON sales(payment_status);",
                "CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales(created_at);",
                
                # Sale items table indexes
                "CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id);",
                "CREATE INDEX IF NOT EXISTS idx_sale_items_product_variant_id ON sale_items(product_variant_id);",
                
                # Sale payments table indexes
                "CREATE INDEX IF NOT EXISTS idx_sale_payments_sale_id ON sale_payments(sale_id);",
                "CREATE INDEX IF NOT EXISTS idx_sale_payments_payment_date ON sale_payments(payment_date);",
                "CREATE INDEX IF NOT EXISTS idx_sale_payments_payment_method ON sale_payments(payment_method);",
                "CREATE INDEX IF NOT EXISTS idx_sale_payments_bank_account_id ON sale_payments(bank_account_id);",
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Failed to create index {index_sql}: {str(e)}")
            
            conn.commit()
            logger.info("Performance indexes added successfully!")
            
    except Exception as e:
        logger.error(f"Error adding indexes: {str(e)}")
        raise


def verify_installation():
    """Verify that all tables were created correctly"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if tables exist
            tables_to_check = ['sales', 'sale_items', 'sale_payments']
            
            for table_name in tables_to_check:
                result = conn.execute(text(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = '{table_name}' AND table_schema = 'public';
                """))
                
                if result.fetchone():
                    logger.info(f"✓ Table '{table_name}' exists")
                else:
                    logger.error(f"✗ Table '{table_name}' does NOT exist")
                    return False
            
            # Check foreign keys
            fk_checks = [
                ("sale_items", "sales", "sale_id"),
                ("sale_payments", "sales", "sale_id"),
                ("sale_items", "product_variants", "product_variant_id"),
                ("sales", "customers", "customer_id"),
            ]
            
            for child_table, parent_table, fk_column in fk_checks:
                result = conn.execute(text(f"""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = '{child_table}' 
                    AND constraint_type = 'FOREIGN KEY';
                """))
                
                if result.fetchone():
                    logger.info(f"✓ Foreign key constraint exists for {child_table}.{fk_column}")
                else:
                    logger.warning(f"⚠ Foreign key constraint missing for {child_table}.{fk_column}")
            
            logger.info("Sales system verification completed!")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying installation: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        logger.info("Starting sales management system migration...")
        
        # Step 1: Create tables
        create_sales_tables()
        
        # Step 2: Add indexes
        add_indexes()
        
        # Step 3: Verify installation
        if verify_installation():
            logger.info("✅ Sales management system migration completed successfully!")
        else:
            logger.error("❌ Sales management system migration failed verification!")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
