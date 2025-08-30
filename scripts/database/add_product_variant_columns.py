#!/usr/bin/env python3
"""
Add Missing Columns to Product Variants
Add hsn_code, unit_type, and mrp columns to product_variants table
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_missing_columns():
    """Add missing columns to product_variants table"""
    try:
        logger.info("🔧 Adding Missing Columns to Product Variants")
        logger.info("=" * 60)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Check if columns already exist
                logger.info("Checking existing columns...")
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'product_variants' 
                    AND column_name IN ('hsn_code', 'unit_type', 'mrp')
                """))
                
                existing_columns = [row[0] for row in result]
                logger.info(f"Found existing columns: {existing_columns}")
                
                # Add hsn_code column
                if 'hsn_code' not in existing_columns:
                    logger.info("Adding hsn_code column...")
                    conn.execute(text("""
                        ALTER TABLE product_variants 
                        ADD COLUMN hsn_code VARCHAR(20) NULL
                    """))
                    logger.info("✅ hsn_code column added")
                else:
                    logger.info("✅ hsn_code column already exists")
                
                # Add unit_type column
                if 'unit_type' not in existing_columns:
                    logger.info("Adding unit_type column...")
                    conn.execute(text("""
                        ALTER TABLE product_variants 
                        ADD COLUMN unit_type VARCHAR(50) NOT NULL DEFAULT 'PCS'
                    """))
                    logger.info("✅ unit_type column added")
                else:
                    logger.info("✅ unit_type column already exists")
                
                # Add mrp column
                if 'mrp' not in existing_columns:
                    logger.info("Adding mrp column...")
                    conn.execute(text("""
                        ALTER TABLE product_variants 
                        ADD COLUMN mrp NUMERIC(10,2) NULL
                    """))
                    logger.info("✅ mrp column added")
                else:
                    logger.info("✅ mrp column already exists")
                
                # Update existing records with default values
                logger.info("Updating existing records with default values...")
                
                # Set HSN codes based on product type (example values)
                conn.execute(text("""
                    UPDATE product_variants 
                    SET hsn_code = '6205' 
                    WHERE hsn_code IS NULL
                """))
                
                # Set unit_type to PCS for all records
                conn.execute(text("""
                    UPDATE product_variants 
                    SET unit_type = 'PCS' 
                    WHERE unit_type IS NULL OR unit_type = ''
                """))
                
                # Set MRP as price + 20% margin where price exists
                conn.execute(text("""
                    UPDATE product_variants 
                    SET mrp = price * 1.20 
                    WHERE mrp IS NULL AND price IS NOT NULL
                """))
                
                # Set default MRP for variants without price
                conn.execute(text("""
                    UPDATE product_variants 
                    SET mrp = 200.00 
                    WHERE mrp IS NULL
                """))
                
                trans.commit()
                logger.info("✅ All columns added and updated successfully!")
                
                # Show updated table structure
                logger.info("\n📋 Updated Product Variants Table Structure:")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'product_variants' 
                    AND column_name IN ('hsn_code', 'unit_type', 'mrp', 'price', 'variant_name')
                    ORDER BY column_name
                """))
                
                for row in result:
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {row[3]}" if row[3] else ""
                    logger.info(f"  {row[0]}: {row[1]} ({nullable}){default}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Error adding columns: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False


def verify_columns():
    """Verify that all columns were added correctly"""
    try:
        logger.info("\n🔍 Verifying Column Addition")
        logger.info("=" * 50)
        
        with engine.connect() as conn:
            # Check column existence
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'product_variants' 
                AND column_name IN ('hsn_code', 'unit_type', 'mrp')
                ORDER BY column_name
            """))
            
            columns = list(result)
            
            if len(columns) == 3:
                logger.info("✅ All required columns found:")
                for row in columns:
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    logger.info(f"  {row[0]}: {row[1]} ({nullable})")
                
                # Check data
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_variants,
                        COUNT(hsn_code) as with_hsn,
                        COUNT(unit_type) as with_unit_type,
                        COUNT(mrp) as with_mrp
                    FROM product_variants
                """))
                
                row = result.fetchone()
                if row:
                    logger.info(f"\n📊 Data verification:")
                    logger.info(f"  Total variants: {row[0]}")
                    logger.info(f"  With HSN code: {row[1]}")
                    logger.info(f"  With unit type: {row[2]}")
                    logger.info(f"  With MRP: {row[3]}")
                
                return True
            else:
                logger.error(f"❌ Expected 3 columns, found {len(columns)}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Error verifying columns: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting Product Variants Column Migration...")
    logger.info("=" * 60)
    
    success = add_missing_columns()
    
    if success:
        if verify_columns():
            logger.info("\n" + "="*60)
            logger.info("🎉 PRODUCT VARIANTS MIGRATION COMPLETE!")
            logger.info("="*60)
            logger.info("✅ All required columns added successfully")
            logger.info("✅ Existing data updated with defaults")
            logger.info("✅ Sales API can now access product variants")
            logger.info("\n🚀 Ready to test Sales API again!")
        else:
            logger.error("❌ Column verification failed")
    else:
        logger.error("❌ Column migration failed")
