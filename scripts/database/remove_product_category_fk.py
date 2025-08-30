#!/usr/bin/env python3
"""
Remove foreign key constraint from products.category_id
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres:rnrinfo@localhost:5432/garments_erp"

def remove_foreign_key_constraint():
    """Remove foreign key constraint from products.category_id"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if the foreign key constraint exists
        cur.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'products' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%category%'
        """)
        
        constraints = cur.fetchall()
        
        if constraints:
            for constraint in constraints:
                constraint_name = constraint[0]
                logger.info(f"🔄 Dropping foreign key constraint: {constraint_name}")
                
                # Drop the foreign key constraint
                cur.execute(f"ALTER TABLE products DROP CONSTRAINT {constraint_name}")
                logger.info(f"✅ Dropped foreign key constraint: {constraint_name}")
        else:
            logger.info("ℹ️ No foreign key constraints found on products.category_id")
        
        # Commit the changes
        conn.commit()
        logger.info("✅ Foreign key constraint removal completed successfully!")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error removing foreign key constraint: {e}")
        return False

def verify_constraint_removal():
    """Verify that the constraint has been removed"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check remaining constraints
        cur.execute("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'products'
        """)
        
        constraints = cur.fetchall()
        
        logger.info("📋 Current constraints on products table:")
        for constraint_name, constraint_type in constraints:
            logger.info(f"  - {constraint_name}: {constraint_type}")
        
        # Check if category_id column still exists
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'products' AND column_name = 'category_id'
        """)
        
        column_info = cur.fetchall()
        if column_info:
            col_name, data_type, is_nullable = column_info[0]
            logger.info(f"✅ Column {col_name}: {data_type} {'NULL' if is_nullable == 'YES' else 'NOT NULL'}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying constraint removal: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("🚀 Starting foreign key constraint removal...")
    
    # Remove foreign key constraint
    if not remove_foreign_key_constraint():
        logger.error("❌ Migration failed!")
        sys.exit(1)
    
    # Verify changes
    if not verify_constraint_removal():
        logger.error("❌ Verification failed!")
        sys.exit(1)
    
    logger.info("🎉 Migration completed successfully!")
    logger.info("ℹ️ Products.category_id is now a simple string field without foreign key constraint")

if __name__ == "__main__":
    main()
