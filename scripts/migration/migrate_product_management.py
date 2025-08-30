"""
Migration script for Product Management System
Creates tables and populates with sample data for garment manufacturing
"""

from sqlalchemy.orm import Session
from decimal import Decimal
import logging

from database import SessionLocal, engine
from models.product_management import (
    ProductSize, ProductSleeveType, ProductDesign, 
    Product, ProductVariant, ProductStockLedger,
    DesignCategory
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_sizes(db: Session):
    """Create sample product sizes."""
    sizes = [
        {'size_value': '36', 'size_display': '36', 'size_code': 'SZ36', 'sort_order': 1},
        {'size_value': '38', 'size_display': '38', 'size_code': 'SZ38', 'sort_order': 2},
        {'size_value': '40', 'size_display': '40', 'size_code': 'SZ40', 'sort_order': 3},
        {'size_value': '42', 'size_display': '42', 'size_code': 'SZ42', 'sort_order': 4},
        {'size_value': '44', 'size_display': '44', 'size_code': 'SZ44', 'sort_order': 5},
        {'size_value': '46', 'size_display': '46', 'size_code': 'SZ46', 'sort_order': 6},
        {'size_value': 'S', 'size_display': 'Small', 'size_code': 'SZS', 'sort_order': 10},
        {'size_value': 'M', 'size_display': 'Medium', 'size_code': 'SZM', 'sort_order': 11},
        {'size_value': 'L', 'size_display': 'Large', 'size_code': 'SZL', 'sort_order': 12},
        {'size_value': 'XL', 'size_display': 'Extra Large', 'size_code': 'SZXL', 'sort_order': 13},
        {'size_value': 'XXL', 'size_display': 'Double Extra Large', 'size_code': 'SZXXL', 'sort_order': 14},
    ]
    
    created_sizes = []
    for size_data in sizes:
        # Check if size already exists
        existing = db.query(ProductSize).filter(ProductSize.size_value == size_data['size_value']).first()
        if not existing:
            size = ProductSize(**size_data)
            db.add(size)
            created_sizes.append(size)
    
    db.commit()
    logger.info(f"Created {len(created_sizes)} product sizes")
    return db.query(ProductSize).all()


def create_sample_sleeve_types(db: Session):
    """Create sample sleeve types."""
    sleeve_types = [
        {
            'sleeve_type': 'Full Sleeve',
            'sleeve_code': 'FS',
            'description': 'Full length sleeves'
        },
        {
            'sleeve_type': 'Half Sleeve',
            'sleeve_code': 'HS',
            'description': 'Half length sleeves'
        },
        {
            'sleeve_type': 'Sleeveless',
            'sleeve_code': 'SL',
            'description': 'No sleeves'
        },
        {
            'sleeve_type': 'Quarter Sleeve',
            'sleeve_code': 'QS',
            'description': 'Quarter length sleeves'
        },
        {
            'sleeve_type': 'Three Quarter Sleeve',
            'sleeve_code': 'TQS',
            'description': 'Three quarter length sleeves'
        }
    ]
    
    created_sleeves = []
    for sleeve_data in sleeve_types:
        # Check if sleeve type already exists
        existing = db.query(ProductSleeveType).filter(
            ProductSleeveType.sleeve_type == sleeve_data['sleeve_type']
        ).first()
        if not existing:
            sleeve = ProductSleeveType(**sleeve_data)
            db.add(sleeve)
            created_sleeves.append(sleeve)
    
    db.commit()
    logger.info(f"Created {len(created_sleeves)} sleeve types")
    return db.query(ProductSleeveType).all()


def create_sample_designs(db: Session):
    """Create sample product designs."""
    designs = [
        {
            'design_name': 'Plain',
            'design_code': 'PLN',
            'design_category': DesignCategory.PLAIN,
            'description': 'Simple plain design without patterns'
        },
        {
            'design_name': 'Checked',
            'design_code': 'CHK',
            'design_category': DesignCategory.PATTERN,
            'description': 'Checkered pattern design'
        },
        {
            'design_name': 'Kaaki',
            'design_code': 'KAK',
            'design_category': DesignCategory.TEXTURE,
            'description': 'Khaki textured design'
        },
        {
            'design_name': 'Linen',
            'design_code': 'LIN',
            'design_category': DesignCategory.TEXTURE,
            'description': 'Linen texture finish'
        },
        {
            'design_name': 'Print',
            'design_code': 'PRT',
            'design_category': DesignCategory.PRINT,
            'description': 'Various print designs'
        },
        {
            'design_name': 'Striped',
            'design_code': 'STR',
            'design_category': DesignCategory.PATTERN,
            'description': 'Striped pattern design'
        },
        {
            'design_name': 'Dotted',
            'design_code': 'DOT',
            'design_category': DesignCategory.PATTERN,
            'description': 'Polka dot pattern'
        },
        {
            'design_name': 'Floral Print',
            'design_code': 'FLR',
            'design_category': DesignCategory.PRINT,
            'description': 'Floral pattern prints'
        },
        {
            'design_name': 'Geometric',
            'design_code': 'GEO',
            'design_category': DesignCategory.PATTERN,
            'description': 'Geometric pattern design'
        },
        {
            'design_name': 'Abstract',
            'design_code': 'ABS',
            'design_category': DesignCategory.PRINT,
            'description': 'Abstract art prints'
        }
    ]
    
    created_designs = []
    for design_data in designs:
        # Check if design already exists
        existing = db.query(ProductDesign).filter(
            ProductDesign.design_name == design_data['design_name']
        ).first()
        if not existing:
            design = ProductDesign(**design_data)
            db.add(design)
            created_designs.append(design)
    
    db.commit()
    logger.info(f"Created {len(created_designs)} product designs")
    return db.query(ProductDesign).all()


def create_sample_products(db: Session):
    """Create sample products."""
    products = [
        {
            'product_name': 'smart_plus',
            'product_code': 'PRDSMTPL',
            'description': 'Smart Plus collection shirts',
            'base_price': Decimal('1200.00')
        },
        {
            'product_name': 'premium_cotton',
            'product_code': 'PRDPRMCT',
            'description': 'Premium cotton shirts',
            'base_price': Decimal('1500.00')
        },
        {
            'product_name': 'classic_formal',
            'product_code': 'PRDCLFML',
            'description': 'Classic formal wear',
            'base_price': Decimal('1800.00')
        },
        {
            'product_name': 'casual_wear',
            'product_code': 'PRDCSWR',
            'description': 'Casual everyday wear',
            'base_price': Decimal('900.00')
        },
        {
            'product_name': 'business_line',
            'product_code': 'PRDBSLN',
            'description': 'Business professional line',
            'base_price': Decimal('2000.00')
        }
    ]
    
    created_products = []
    for product_data in products:
        # Check if product already exists
        existing = db.query(Product).filter(
            Product.product_name == product_data['product_name']
        ).first()
        if not existing:
            product = Product(**product_data)
            db.add(product)
            created_products.append(product)
    
    db.commit()
    logger.info(f"Created {len(created_products)} products")
    return db.query(Product).all()


def create_sample_variants(db: Session, products, sizes, sleeve_types, designs):
    """Create sample product variants for all combinations."""
    created_variants = []
    
    for product in products:
        logger.info(f"Creating variants for product: {product.product_name}")
        
        # Create variants for specific size/sleeve/design combinations
        # For demo purposes, create variants for first few items of each category
        demo_sizes = sizes[:6]  # First 6 sizes (36-46)
        demo_sleeves = sleeve_types[:2]  # Full Sleeve and Half Sleeve
        demo_designs = designs[:5]  # First 5 designs
        
        for size in demo_sizes:
            for sleeve in demo_sleeves:
                for design in demo_designs:
                    # Check if variant already exists
                    existing = db.query(ProductVariant).filter(
                        ProductVariant.product_id == product.id,
                        ProductVariant.size_id == size.id,
                        ProductVariant.sleeve_type_id == sleeve.id,
                        ProductVariant.design_id == design.id
                    ).first()
                    
                    if not existing:
                        # Generate variant code and SKU
                        variant_code = f"{product.product_code}-{size.size_code}-{sleeve.sleeve_code}-{design.design_code}"
                        sku = f"{product.product_name.upper()}-{size.size_value}-{sleeve.sleeve_type.upper()}-{design.design_name.upper()}"
                        sku = sku.replace(' ', '').replace('_', '')[:50]
                        
                        # Set price with some variation
                        price_multiplier = Decimal('1.0')
                        if sleeve.sleeve_type == 'Full Sleeve':
                            price_multiplier += Decimal('0.1')
                        if design.design_category in ['print', 'pattern']:
                            price_multiplier += Decimal('0.15')
                        
                        variant = ProductVariant(
                            product_id=product.id,
                            size_id=size.id,
                            sleeve_type_id=sleeve.id,
                            design_id=design.id,
                            variant_code=variant_code,
                            sku=sku,
                            price=product.base_price * price_multiplier,
                            cost_price=product.base_price * Decimal('0.7'),  # 70% of selling price
                            stock_balance=Decimal('0')  # Start with zero stock
                        )
                        
                        db.add(variant)
                        created_variants.append(variant)
    
    db.commit()
    logger.info(f"Created {len(created_variants)} product variants")
    return created_variants


def create_sample_stock_entries(db: Session, variants):
    """Create sample stock entries for some variants."""
    from models.product_management import StockMovementType
    import random
    
    created_entries = []
    
    # Add initial stock for random variants (about 30% of all variants)
    sample_variants = random.sample(variants, min(len(variants) // 3, 100))
    
    for variant in sample_variants:
        # Create initial stock entry
        initial_qty = Decimal(str(random.randint(10, 100)))
        
        stock_entry = ProductStockLedger(
            variant_id=variant.id,
            movement_type=StockMovementType.IN,
            quantity=initial_qty,
            unit_price=variant.cost_price,
            balance_after=initial_qty,
            reference_type='Initial Stock',
            reference_number=f'INIT-{variant.id}',
            notes='Initial stock entry for variant'
        )
        
        # Update variant balance
        variant.stock_balance = initial_qty
        
        db.add(stock_entry)
        created_entries.append(stock_entry)
        
        # Sometimes add a few more stock movements
        if random.random() < 0.3:  # 30% chance
            # Add some outward movement
            out_qty = Decimal(str(random.randint(1, min(int(initial_qty), 20))))
            new_balance = initial_qty - out_qty
            
            out_entry = ProductStockLedger(
                variant_id=variant.id,
                movement_type=StockMovementType.OUT,
                quantity=out_qty,
                unit_price=variant.price,
                balance_after=new_balance,
                reference_type='Sale',
                reference_number=f'SALE-{variant.id}-001',
                notes='Sample sale transaction'
            )
            
            variant.stock_balance = new_balance
            db.add(out_entry)
            created_entries.append(out_entry)
    
    db.commit()
    logger.info(f"Created {len(created_entries)} sample stock entries")
    return created_entries


def run_migration():
    """Run the complete product management migration."""
    try:
        logger.info("Starting Product Management System migration...")
        
        # First, create all tables
        logger.info("Creating database tables...")
        from models.user import Base  # Import Base
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        db = SessionLocal()
        
        # Create sample data
        logger.info("Creating sample sizes...")
        sizes = create_sample_sizes(db)
        
        logger.info("Creating sample sleeve types...")
        sleeve_types = create_sample_sleeve_types(db)
        
        logger.info("Creating sample designs...")
        designs = create_sample_designs(db)
        
        logger.info("Creating sample products...")
        products = create_sample_products(db)
        
        logger.info("Creating product variants...")
        variants = create_sample_variants(db, products, sizes, sleeve_types, designs)
        
        logger.info("Creating sample stock entries...")
        stock_entries = create_sample_stock_entries(db, variants)
        
        # Print summary
        logger.info("Migration completed successfully!")
        logger.info("="*50)
        logger.info("MIGRATION SUMMARY:")
        logger.info(f"Product Sizes: {len(sizes)}")
        logger.info(f"Sleeve Types: {len(sleeve_types)}")
        logger.info(f"Designs: {len(designs)}")
        logger.info(f"Products: {len(products)}")
        logger.info(f"Variants: {len(variants)}")
        logger.info(f"Stock Entries: {len(stock_entries)}")
        logger.info("="*50)
        
        # Show some examples
        logger.info("\nSample Product Variants Created:")
        sample_variants = db.query(ProductVariant).limit(10).all()
        for variant in sample_variants:
            logger.info(f"- {variant.variant_code} | {variant.sku} | Stock: {variant.stock_balance} | Price: ₹{variant.price}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


def verify_migration():
    """Verify the migration was successful."""
    try:
        db = SessionLocal()
        
        # Check counts
        size_count = db.query(ProductSize).count()
        sleeve_count = db.query(ProductSleeveType).count()
        design_count = db.query(ProductDesign).count()
        product_count = db.query(Product).count()
        variant_count = db.query(ProductVariant).count()
        stock_count = db.query(ProductStockLedger).count()
        
        logger.info("Migration Verification:")
        logger.info(f"Sizes: {size_count}")
        logger.info(f"Sleeve Types: {sleeve_count}")
        logger.info(f"Designs: {design_count}")
        logger.info(f"Products: {product_count}")
        logger.info(f"Variants: {variant_count}")
        logger.info(f"Stock Entries: {stock_count}")
        
        # Check specific example
        smart_plus = db.query(Product).filter(Product.product_name == 'smart_plus').first()
        if smart_plus:
            variant_count = db.query(ProductVariant).filter(ProductVariant.product_id == smart_plus.id).count()
            logger.info(f"Smart Plus variants: {variant_count}")
            
            # Show some variants
            variants = db.query(ProductVariant).filter(ProductVariant.product_id == smart_plus.id).limit(5).all()
            logger.info("Sample Smart Plus Variants:")
            for variant in variants:
                logger.info(f"  - Size {variant.size.size_value if variant.size else 'N/A'} | "
                          f"{variant.sleeve_type.sleeve_type if variant.sleeve_type else 'N/A'} | "
                          f"{variant.design.design_name if variant.design else 'N/A'} | "
                          f"Stock: {variant.stock_balance}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        run_migration()
        verify_migration()
        logger.info("Product Management System setup completed successfully!")
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        exit(1)
