#!/usr/bin/env python3
"""
Fix Product Variant Names
Update product variants with proper names for sales integration
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


def fix_variant_names():
    """Fix null variant names in product_variants table"""
    try:
        logger.info("🔧 Fixing Product Variant Names")
        logger.info("=" * 50)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Check current state
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_variants,
                        COUNT(variant_name) as with_names,
                        COUNT(*) - COUNT(variant_name) as without_names
                    FROM product_variants
                """))
                
                row = result.fetchone()
                logger.info(f"Current state: {row[0]} total, {row[1]} with names, {row[2]} without names")
                
                if row[2] > 0:  # If there are variants without names
                    logger.info("Updating variants without names...")
                    
                    # Update variants to have generated names
                    conn.execute(text("""
                        UPDATE product_variants 
                        SET variant_name = CONCAT('Product Variant ', id)
                        WHERE variant_name IS NULL OR variant_name = ''
                    """))
                    
                    # Update some specific ones with better names if they have product relationships
                    conn.execute(text("""
                        UPDATE product_variants 
                        SET variant_name = CONCAT(
                            COALESCE((SELECT product_name FROM products WHERE id = product_variants.product_id), 'Product'),
                            ' - Variant ', 
                            product_variants.id
                        )
                        WHERE variant_name LIKE 'Product Variant %'
                    """))
                
                trans.commit()
                
                # Check final state
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_variants,
                        COUNT(variant_name) as with_names,
                        COUNT(*) - COUNT(variant_name) as without_names
                    FROM product_variants
                """))
                
                row = result.fetchone()
                logger.info(f"Final state: {row[0]} total, {row[1]} with names, {row[2]} without names")
                
                # Show some examples
                logger.info("\nExample variant names:")
                result = conn.execute(text("""
                    SELECT id, variant_name, variant_code 
                    FROM product_variants 
                    WHERE variant_name IS NOT NULL 
                    LIMIT 5
                """))
                
                for row in result:
                    logger.info(f"  ID {row[0]}: {row[1]} ({row[2]})")
                
                logger.info("✅ Product variant names fixed successfully!")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Error fixing variant names: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting Product Variant Names Fix...")
    logger.info("=" * 60)
    
    success = fix_variant_names()
    
    if success:
        logger.info("\n🎉 Variant names fixed! Ready to create sales data.")
    else:
        logger.error("\n❌ Failed to fix variant names.")
