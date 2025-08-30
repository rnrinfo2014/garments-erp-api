#!/usr/bin/env python3
"""
Sales Tables Migration Script
Creates sales and sales_items tables with proper relationships and constraints
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from database import DATABASE_URL, engine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sales_tables():
    """Create sales and sales_items tables"""
    try:
        logger.info("🚀 Creating sales management tables...")
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Create sales status enum
                logger.info("Creating sales status enum...")
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'salesstatus') THEN
                            CREATE TYPE salesstatus AS ENUM (
                                'DRAFT', 
                                'CONFIRMED', 
                                'DISPATCHED', 
                                'DELIVERED', 
                                'CANCELLED'
                            );
                        END IF;
                    END $$;
                """))
                
                # Create sales table
                logger.info("Creating sales table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sales (
                        id SERIAL PRIMARY KEY,
                        
                        -- Bill book and customer info
                        bill_book_id INTEGER NOT NULL REFERENCES bill_books(id),
                        customer_id INTEGER NOT NULL REFERENCES customers(id),
                        agent_id INTEGER NULL REFERENCES agents(id),
                        
                        -- Bill details
                        bill_number VARCHAR(50) NOT NULL UNIQUE,
                        bill_date DATE NOT NULL,
                        due_date DATE NULL,
                        
                        -- Summary fields (calculated from items)
                        item_count INTEGER DEFAULT 0,
                        total_qty DECIMAL(15,3) DEFAULT 0.000,
                        gross_amount DECIMAL(15,2) DEFAULT 0.00,
                        discount_amount DECIMAL(15,2) DEFAULT 0.00,
                        tax_amount DECIMAL(15,2) DEFAULT 0.00,
                        additional_charges DECIMAL(15,2) DEFAULT 0.00,
                        total_amount DECIMAL(15,2) DEFAULT 0.00,
                        
                        -- Transport details
                        transport_details TEXT NULL,
                        llr_no VARCHAR(100) NULL,
                        llr_date DATE NULL,
                        
                        -- Status and audit
                        status salesstatus DEFAULT 'DRAFT',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_by VARCHAR(50) NOT NULL,
                        updated_by VARCHAR(50) NULL
                    );
                """))
                
                # Create sales_items table
                logger.info("Creating sales_items table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sales_items (
                        id SERIAL PRIMARY KEY,
                        sales_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
                        variant_id INTEGER NOT NULL REFERENCES product_variants(id),
                        
                        -- Product details (captured at time of sale)
                        product_name VARCHAR(200) NOT NULL,
                        hsn_code VARCHAR(20) NULL,
                        unit_type VARCHAR(50) NOT NULL,
                        
                        -- Quantity and pricing
                        quantity DECIMAL(15,3) NOT NULL CHECK (quantity > 0),
                        mrp DECIMAL(15,2) NOT NULL CHECK (mrp >= 0),
                        sale_rate DECIMAL(15,2) NOT NULL CHECK (sale_rate >= 0),
                        
                        -- Tax calculations
                        tax_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (tax_percentage >= 0 AND tax_percentage <= 100),
                        tax_amount DECIMAL(15,2) DEFAULT 0.00,
                        
                        -- Discount calculations
                        discount_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (discount_percentage >= 0 AND discount_percentage <= 100),
                        discount_amount DECIMAL(15,2) DEFAULT 0.00,
                        
                        -- Total amount for this item
                        total_amount DECIMAL(15,2) NOT NULL,
                        
                        -- Audit
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
                
                # Create indexes for better performance
                logger.info("Creating indexes...")
                
                # Sales table indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_bill_number ON sales(bill_number);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_agent ON sales(agent_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_bill_book ON sales(bill_book_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(bill_date);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_status ON sales(status);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales(created_at);"))
                
                # Sales items table indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_items_sales_id ON sales_items(sales_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_items_variant ON sales_items(variant_id);"))
                
                # Create trigger for updated_at
                logger.info("Creating update triggers...")
                conn.execute(text("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """))
                
                # Apply triggers
                conn.execute(text("""
                    DROP TRIGGER IF EXISTS update_sales_updated_at ON sales;
                    CREATE TRIGGER update_sales_updated_at
                        BEFORE UPDATE ON sales
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                """))
                
                conn.execute(text("""
                    DROP TRIGGER IF EXISTS update_sales_items_updated_at ON sales_items;
                    CREATE TRIGGER update_sales_items_updated_at
                        BEFORE UPDATE ON sales_items
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                """))
                
                trans.commit()
                logger.info("✅ Sales tables created successfully!")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Error creating tables: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False


def verify_tables():
    """Verify that all tables are created properly"""
    try:
        logger.info("🔍 Verifying sales tables...")
        
        with engine.connect() as conn:
            # Check sales table
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'sales' AND table_schema = 'public'
            """))
            sales_exists = result.fetchone()
            
            # Check sales_items table
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'sales_items' AND table_schema = 'public'
            """))
            items_exists = result.fetchone()
            
            if sales_exists and items_exists:
                logger.info("✅ All sales tables verified successfully")
                
                # Show table structures
                logger.info("📋 Sales table structure:")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'sales' 
                    ORDER BY ordinal_position
                """))
                
                for row in result:
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {row[3]}" if row[3] else ""
                    logger.info(f"  - {row[0]}: {row[1]} ({nullable}){default}")
                
                logger.info("📋 Sales items table structure:")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'sales_items' 
                    ORDER BY ordinal_position
                """))
                
                for row in result:
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    logger.info(f"  - {row[0]}: {row[1]} ({nullable})")
                
                # Show foreign key relationships
                logger.info("🔗 Foreign key relationships:")
                result = conn.execute(text("""
                    SELECT 
                        tc.table_name, 
                        kcu.column_name, 
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM 
                        information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name IN ('sales', 'sales_items')
                """))
                
                for row in result:
                    logger.info(f"  {row[0]}.{row[1]} → {row[2]}.{row[3]}")
                
                return True
            else:
                logger.error("❌ Sales tables verification failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {e}")
        return False


def show_integration_summary():
    """Show summary of sales system integration"""
    logger.info("\n" + "="*60)
    logger.info("🎉 SALES BILLING SYSTEM SETUP COMPLETE!")
    logger.info("="*60)
    
    logger.info("\n📊 CREATED TABLES:")
    logger.info("  ✅ sales - Main sales/invoice table")
    logger.info("  ✅ sales_items - Individual line items")
    logger.info("  ✅ salesstatus enum - Status workflow")
    
    logger.info("\n🔗 INTEGRATIONS:")
    logger.info("  ✅ bill_books - Bill number generation")
    logger.info("  ✅ customers - Customer management")
    logger.info("  ✅ agents - Sales agent tracking")
    logger.info("  ✅ product_variants - Product catalog")
    
    logger.info("\n📋 FEATURES READY:")
    logger.info("  ✅ Automatic bill numbering")
    logger.info("  ✅ Tax and discount calculations")
    logger.info("  ✅ Status workflow management")
    logger.info("  ✅ Transport details tracking")
    logger.info("  ✅ Audit trail (created/updated)")
    
    logger.info("\n🚀 NEXT STEPS:")
    logger.info("  1. Create SQLAlchemy models")
    logger.info("  2. Create Pydantic schemas")
    logger.info("  3. Implement business logic")
    logger.info("  4. Create API endpoints")
    logger.info("  5. Add sample data for testing")


if __name__ == "__main__":
    logger.info("🚀 Starting Sales Tables Migration...")
    logger.info("=" * 60)
    
    success = create_sales_tables()
    
    if success:
        if verify_tables():
            show_integration_summary()
        else:
            logger.error("❌ Table verification failed")
    else:
        logger.error("❌ Sales tables creation failed")
