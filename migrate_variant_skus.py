"""
Migration script to update existing variant SKUs to new shorter format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal
from models.product_management import ProductVariant, Product, ProductSize, ProductSleeveType, ProductDesign
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_short_sku(product_name: str, size_value: str, sleeve_type: str, design_name: str) -> str:
    """Generate a short, meaningful SKU from product components."""
    # Shorten product name - take first 3 consonants or significant letters
    product_short = ""
    consonants = "BCDFGHJKLMNPQRSTVWXYZ"
    for char in product_name.upper().replace(' ', '').replace('_', ''):
        if char in consonants:
            product_short += char
        elif char.isalpha() and len(product_short) == 0:  # Include first vowel if no consonants yet
            product_short += char
        if len(product_short) >= 3:
            break
    
    # If we don't have enough characters, take first 3 chars
    if len(product_short) < 3:
        product_short = product_name.upper().replace(' ', '').replace('_', '')[:3]
    
    # Shorten size (already short usually)
    size_short = size_value.replace(' ', '')[:2]
    
    # Shorten sleeve type
    sleeve_mapping = {
        'FULL': 'F',
        'HALF': 'H', 
        'SLEEVELESS': 'S',
        'QUARTER': 'Q',
        '3/4': 'T',
        'THREE': 'T'
    }
    
    sleeve_short = sleeve_type.upper().replace(' ', '').replace('SLEEVE', '')
    for key, value in sleeve_mapping.items():
        if key in sleeve_short:
            sleeve_short = value
            break
    else:
        sleeve_short = sleeve_short[:2]
    
    # Shorten design name
    design_mapping = {
        'PLAIN': 'PLN',
        'CHECK': 'CHK',
        'CHECKED': 'CHK',
        'STRIPE': 'STR',
        'STRIPED': 'STR',
        'PRINT': 'PRT',
        'PATTERN': 'PTN'
    }
    
    design_short = design_name.upper().replace(' ', '')
    for key, value in design_mapping.items():
        if key in design_short:
            design_short = value
            break
    else:
        design_short = design_short[:3]
    
    # Combine all parts
    sku = f"{product_short}{size_short}{sleeve_short}{design_short}"
    return sku[:20]  # Limit to 20 characters max

def update_variant_skus():
    """Update all existing variant SKUs to new shorter format."""
    db = SessionLocal()
    
    try:
        # Get all variants with their related data
        variants = db.query(ProductVariant).all()
        
        if not variants:
            logger.info("No variants found to update")
            return
        
        updated_count = 0
        skipped_count = 0
        
        logger.info(f"Found {len(variants)} variants to process")
        
        for variant in variants:
            try:
                # Get related data
                product = db.query(Product).filter(Product.id == variant.product_id).first()
                size = db.query(ProductSize).filter(ProductSize.id == variant.size_id).first()
                sleeve = db.query(ProductSleeveType).filter(ProductSleeveType.id == variant.sleeve_type_id).first()
                design = db.query(ProductDesign).filter(ProductDesign.id == variant.design_id).first()
                
                if not all([product, size, sleeve, design]):
                    logger.warning(f"Skipping variant {variant.id}: Missing related data")
                    skipped_count += 1
                    continue
                
                # Generate new SKU
                old_sku = variant.sku
                new_sku = generate_short_sku(
                    product.product_name,
                    size.size_value,
                    sleeve.sleeve_type,
                    design.design_name
                )
                
                # Check if SKU actually changed
                if old_sku == new_sku:
                    logger.debug(f"Variant {variant.id}: SKU unchanged ({new_sku})")
                    continue
                
                # Check for duplicate SKUs and make unique
                base_sku = new_sku
                counter = 1
                while db.query(ProductVariant).filter(
                    ProductVariant.sku == new_sku,
                    ProductVariant.id != variant.id
                ).first():
                    new_sku = f"{base_sku}{counter}"
                    counter += 1
                    if len(new_sku) > 20:  # Prevent SKUs from getting too long
                        new_sku = f"{base_sku[:17]}{counter}"
                
                # Update the variant
                variant.sku = new_sku
                
                # Commit each change individually to avoid bulk constraint violations
                db.commit()
                
                logger.info(f"Variant {variant.id}: Updated SKU from '{old_sku}' to '{new_sku}'")
                updated_count += 1
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error updating variant {variant.id}: {str(e)}")
                skipped_count += 1
                continue
        
        logger.info(f"Migration completed: {updated_count} variants updated, {skipped_count} skipped")
        
        # Show some examples of updated SKUs
        logger.info("\nExample updated SKUs:")
        sample_variants = db.query(ProductVariant).limit(5).all()
        for variant in sample_variants:
            logger.info(f"  Variant {variant.id}: {variant.sku}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {str(e)}")
        raise
    
    finally:
        db.close()

def preview_sku_changes():
    """Preview what the SKU changes would look like without committing."""
    db = SessionLocal()
    
    try:
        variants = db.query(ProductVariant).limit(10).all()  # Preview first 10
        
        logger.info("Preview of SKU changes (first 10 variants):")
        logger.info("=" * 80)
        
        for variant in variants:
            # Get related data
            product = db.query(Product).filter(Product.id == variant.product_id).first()
            size = db.query(ProductSize).filter(ProductSize.id == variant.size_id).first()
            sleeve = db.query(ProductSleeveType).filter(ProductSleeveType.id == variant.sleeve_type_id).first()
            design = db.query(ProductDesign).filter(ProductDesign.id == variant.design_id).first()
            
            if all([product, size, sleeve, design]):
                old_sku = variant.sku or "NULL"
                new_sku = generate_short_sku(
                    product.product_name,
                    size.size_value,
                    sleeve.sleeve_type,
                    design.design_name
                )
                
                logger.info(f"Variant {variant.id}:")
                logger.info(f"  Product: {product.product_name}")
                logger.info(f"  Size: {size.size_value}")
                logger.info(f"  Sleeve: {sleeve.sleeve_type}")
                logger.info(f"  Design: {design.design_name}")
                logger.info(f"  Old SKU: {old_sku} ({len(old_sku)} chars)")
                logger.info(f"  New SKU: {new_sku} ({len(new_sku)} chars)")
                logger.info(f"  Savings: {len(old_sku) - len(new_sku)} characters")
                logger.info("-" * 50)
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update variant SKUs to new shorter format")
    parser.add_argument("--preview", action="store_true", help="Preview changes without committing")
    parser.add_argument("--execute", action="store_true", help="Execute the migration")
    
    args = parser.parse_args()
    
    if args.preview:
        logger.info("Previewing SKU changes...")
        preview_sku_changes()
    elif args.execute:
        logger.info("Starting SKU migration...")
        confirmation = input("Are you sure you want to update all variant SKUs? This cannot be easily undone. (yes/no): ")
        if confirmation.lower() == 'yes':
            update_variant_skus()
        else:
            logger.info("Migration cancelled")
    else:
        logger.info("Usage:")
        logger.info("  python migrate_variant_skus.py --preview   # Preview changes")
        logger.info("  python migrate_variant_skus.py --execute   # Execute migration")
