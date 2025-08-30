#!/usr/bin/env python3
"""
Add three price fields (price_a, price_b, price_c) to the products table
Run this script to migrate existing products table with the new price structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_price_columns():
    """Add three price columns to products table"""
    try:
        with engine.connect() as connection:
            # Add the three new price columns
            logger.info("Adding price_a column to products table...")
            connection.execute(text("""
                ALTER TABLE products 
                ADD COLUMN price_a NUMERIC(10,2)
            """))
            
            logger.info("Adding price_b column to products table...")
            connection.execute(text("""
                ALTER TABLE products 
                ADD COLUMN price_b NUMERIC(10,2)
            """))
            
            logger.info("Adding price_c column to products table...")
            connection.execute(text("""
                ALTER TABLE products 
                ADD COLUMN price_c NUMERIC(10,2)
            """))
            
            # Commit the changes
            connection.commit()
            logger.info("Successfully added three price columns to products table")
            
            # Optional: Copy existing base_price to price_a for existing records
            logger.info("Copying existing base_price to price_a for existing records...")
            connection.execute(text("""
                UPDATE products 
                SET price_a = base_price 
                WHERE base_price IS NOT NULL AND price_a IS NULL
            """))
            
            connection.commit()
            logger.info("Successfully copied base_price to price_a for existing products")
            
    except Exception as e:
        logger.error(f"Error adding price columns: {str(e)}")
        raise e

def check_columns():
    """Check if the new columns were added successfully"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND column_name IN ('price_a', 'price_b', 'price_c')
                ORDER BY column_name
            """))
            
            columns = result.fetchall()
            logger.info("New price columns in products table:")
            for column in columns:
                logger.info(f"  {column[0]}: {column[1]}")
                
            if len(columns) == 3:
                logger.info("✅ All three price columns added successfully!")
                return True
            else:
                logger.error(f"❌ Expected 3 columns, found {len(columns)}")
                return False
                
    except Exception as e:
        logger.error(f"Error checking columns: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting products table price columns migration...")
    
    try:
        # Add the new price columns
        add_price_columns()
        
        # Verify the columns were added
        if check_columns():
            logger.info("🎉 Products table price columns migration completed successfully!")
        else:
            logger.error("❌ Migration verification failed")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        sys.exit(1)
