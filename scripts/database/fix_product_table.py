#!/usr/bin/env python3
"""
Fix Product Table - Remove Foreign Key Constraint
Removes the foreign key constraint on category_id in the products table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from database import DATABASE_URL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_product_category_constraint():
    """Remove foreign key constraint on products.category_id"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        logger.info("🔧 Fixing products table foreign key constraint...")
        
        # First, check if the constraint exists
        cur.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'products' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%category%';
        """)
        
        constraints = cur.fetchall()
        
        if constraints:
            for constraint in constraints:
                constraint_name = constraint[0]
                logger.info(f"🗑️ Dropping constraint: {constraint_name}")
                
                cur.execute(f"ALTER TABLE products DROP CONSTRAINT {constraint_name};")
                logger.info(f"✅ Dropped constraint: {constraint_name}")
        else:
            logger.info("ℹ️ No foreign key constraints found on category_id")
        
        # Also modify the column to be longer and ensure it's nullable
        cur.execute("""
            ALTER TABLE products 
            ALTER COLUMN category_id TYPE VARCHAR(100),
            ALTER COLUMN category_id DROP NOT NULL;
        """)
        logger.info("✅ Updated category_id column definition")
        
        conn.commit()
        logger.info("✅ Products table fixed successfully!")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing products table: {e}")
        return False


def verify_fix():
    """Verify that the fix was applied correctly"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check column definition
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'products' AND column_name = 'category_id';
        """)
        
        column_info = cur.fetchone()
        if column_info:
            logger.info(f"✅ Column definition: {column_info}")
        
        # Check for any remaining foreign key constraints
        cur.execute("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'products' AND constraint_type = 'FOREIGN KEY';
        """)
        
        constraints = cur.fetchall()
        logger.info(f"📋 Remaining foreign key constraints: {len(constraints)}")
        for constraint in constraints:
            logger.info(f"  - {constraint[0]}: {constraint[1]}")
        
        # Test a simple query
        cur.execute("SELECT COUNT(*) FROM products;")
        count = cur.fetchone()[0]
        logger.info(f"✅ Products table accessible, {count} records found")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying fix: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting products table fix...")
    
    if fix_product_category_constraint():
        logger.info("✅ Fix applied successfully")
        
        if verify_fix():
            logger.info("✅ Verification passed")
            logger.info("🎉 Products table is now ready!")
        else:
            logger.error("❌ Verification failed")
            sys.exit(1)
    else:
        logger.error("❌ Fix failed")
        sys.exit(1)
