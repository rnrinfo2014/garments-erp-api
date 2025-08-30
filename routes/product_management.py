from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from decimal import Decimal
import logging

from dependencies import get_db
from models.product_management import (
    ProductSize, ProductSleeveType, ProductDesign, Product, 
    ProductVariant, ProductStockLedger, StockMovementType
)
from schemas.product_management import (
    # Size schemas
    ProductSize as ProductSizeSchema,
    ProductSizeCreate,
    ProductSizeUpdate,
    # Sleeve type schemas
    ProductSleeveType as ProductSleeveTypeSchema,
    ProductSleeveTypeCreate,
    ProductSleeveTypeUpdate,
    # Design schemas
    ProductDesign as ProductDesignSchema,
    ProductDesignCreate,
    ProductDesignUpdate,
    # Product schemas
    Product as ProductSchema,
    ProductCreate,
    ProductUpdate,
    # Variant schemas
    ProductVariant as ProductVariantSchema,
    ProductVariantCreate,
    ProductVariantBulkCreate,
    ProductVariantUpdate,
    # Stock schemas
    ProductStockLedger as ProductStockLedgerSchema,
    StockMovementRequest,
    BulkStockMovementRequest,
    StockBalanceResponse,
    StockSummaryResponse,
    # Filter and response schemas
    ProductSearchFilter,
    VariantSearchFilter,
    ProductListResponse,
    VariantListResponse,
    StockLedgerListResponse,
    ProductPerformanceReport,
    VariantPerformanceReport
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

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

# ================================
# PRODUCT SIZE ROUTES
# ================================

@router.post("/sizes/", response_model=ProductSizeSchema)
def create_product_size(
    size_data: ProductSizeCreate,
    db: Session = Depends(get_db)
):
    """Create a new product size."""
    try:
        # Check if size already exists
        existing_size = db.query(ProductSize).filter(
            ProductSize.size_value == size_data.size_value
        ).first()
        
        if existing_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Size '{size_data.size_value}' already exists"
            )
        
        # Generate size code if not provided
        size_code = size_data.size_code
        if not size_code:
            size_code = f"SZ{size_data.size_value.replace(' ', '').upper()}"
        
        db_size = ProductSize(
            size_value=size_data.size_value,
            size_display=size_data.size_display or size_data.size_value,
            size_code=size_code,
            sort_order=size_data.sort_order,
            is_active=size_data.is_active
        )
        
        db.add(db_size)
        db.commit()
        db.refresh(db_size)
        
        logger.info(f"Created product size: {db_size.size_value}")
        return db_size
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product size: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product size: {str(e)}"
        )


@router.get("/sizes/", response_model=List[ProductSizeSchema])
def list_product_sizes(
    active_only: bool = Query(True, description="Filter active sizes only"),
    db: Session = Depends(get_db)
):
    """List all product sizes."""
    try:
        query = db.query(ProductSize)
        
        if active_only:
            query = query.filter(ProductSize.is_active == True)
        
        sizes = query.order_by(ProductSize.sort_order.asc().nulls_last(), ProductSize.size_value).all()
        return sizes
        
    except Exception as e:
        logger.error(f"Error listing product sizes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list product sizes: {str(e)}"
        )


@router.get("/sizes/{size_id}", response_model=ProductSizeSchema)
def get_product_size(size_id: int, db: Session = Depends(get_db)):
    """Get a specific product size."""
    size = db.query(ProductSize).filter(ProductSize.id == size_id).first()
    if not size:
        raise HTTPException(status_code=404, detail="Product size not found")
    return size


@router.put("/sizes/{size_id}", response_model=ProductSizeSchema)
def update_product_size(
    size_id: int,
    size_update: ProductSizeUpdate,
    db: Session = Depends(get_db)
):
    """Update a product size."""
    try:
        db_size = db.query(ProductSize).filter(ProductSize.id == size_id).first()
        if not db_size:
            raise HTTPException(status_code=404, detail="Product size not found")
        
        # Update fields
        update_data = size_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_size, field, value)
        
        db.commit()
        db.refresh(db_size)
        
        logger.info(f"Updated product size: {db_size.size_value}")
        return db_size
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product size: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product size: {str(e)}"
        )


# ================================
# PRODUCT SLEEVE TYPE ROUTES
# ================================

@router.post("/sleeve-types/", response_model=ProductSleeveTypeSchema)
def create_sleeve_type(
    sleeve_data: ProductSleeveTypeCreate,
    db: Session = Depends(get_db)
):
    """Create a new sleeve type."""
    try:
        # Check if sleeve type already exists
        existing = db.query(ProductSleeveType).filter(
            ProductSleeveType.sleeve_type == sleeve_data.sleeve_type
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sleeve type '{sleeve_data.sleeve_type}' already exists"
            )
        
        # Generate sleeve code if not provided
        sleeve_code = sleeve_data.sleeve_code
        if not sleeve_code:
            sleeve_code = f"SL{sleeve_data.sleeve_type.replace(' ', '').upper()[:3]}"
        
        db_sleeve = ProductSleeveType(
            sleeve_type=sleeve_data.sleeve_type,
            sleeve_code=sleeve_code,
            description=sleeve_data.description,
            is_active=sleeve_data.is_active
        )
        
        db.add(db_sleeve)
        db.commit()
        db.refresh(db_sleeve)
        
        logger.info(f"Created sleeve type: {db_sleeve.sleeve_type}")
        return db_sleeve
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sleeve type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sleeve type: {str(e)}"
        )


@router.get("/sleeve-types/", response_model=List[ProductSleeveTypeSchema])
def list_sleeve_types(
    active_only: bool = Query(True, description="Filter active sleeve types only"),
    db: Session = Depends(get_db)
):
    """List all sleeve types."""
    try:
        query = db.query(ProductSleeveType)
        
        if active_only:
            query = query.filter(ProductSleeveType.is_active == True)
        
        sleeve_types = query.order_by(ProductSleeveType.sleeve_type).all()
        return sleeve_types
        
    except Exception as e:
        logger.error(f"Error listing sleeve types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sleeve types: {str(e)}"
        )


@router.get("/sleeve-types/{sleeve_id}", response_model=ProductSleeveTypeSchema)
def get_sleeve_type(sleeve_id: int, db: Session = Depends(get_db)):
    """Get a specific sleeve type."""
    sleeve = db.query(ProductSleeveType).filter(ProductSleeveType.id == sleeve_id).first()
    if not sleeve:
        raise HTTPException(status_code=404, detail="Sleeve type not found")
    return sleeve


@router.put("/sleeve-types/{sleeve_id}", response_model=ProductSleeveTypeSchema)
def update_sleeve_type(
    sleeve_id: int,
    sleeve_update: ProductSleeveTypeUpdate,
    db: Session = Depends(get_db)
):
    """Update a sleeve type."""
    try:
        db_sleeve = db.query(ProductSleeveType).filter(ProductSleeveType.id == sleeve_id).first()
        if not db_sleeve:
            raise HTTPException(status_code=404, detail="Sleeve type not found")
        
        # Update fields
        update_data = sleeve_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_sleeve, field, value)
        
        db.commit()
        db.refresh(db_sleeve)
        
        logger.info(f"Updated sleeve type: {db_sleeve.sleeve_type}")
        return db_sleeve
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating sleeve type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sleeve type: {str(e)}"
        )


# ================================
# PRODUCT DESIGN ROUTES
# ================================

@router.post("/designs/", response_model=ProductDesignSchema)
def create_product_design(
    design_data: ProductDesignCreate,
    db: Session = Depends(get_db)
):
    """Create a new product design."""
    try:
        # Check if design already exists
        existing = db.query(ProductDesign).filter(
            ProductDesign.design_name == design_data.design_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Design '{design_data.design_name}' already exists"
            )
        
        # Generate design code if not provided
        design_code = design_data.design_code
        if not design_code:
            design_code = f"DS{design_data.design_name.replace(' ', '').upper()[:3]}"
        
        db_design = ProductDesign(
            design_name=design_data.design_name,
            design_code=design_code,
            design_category=design_data.design_category,
            description=design_data.description,
            is_active=design_data.is_active
        )
        
        db.add(db_design)
        db.commit()
        db.refresh(db_design)
        
        logger.info(f"Created product design: {db_design.design_name}")
        return db_design
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product design: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product design: {str(e)}"
        )


@router.get("/designs/", response_model=List[ProductDesignSchema])
def list_product_designs(
    active_only: bool = Query(True, description="Filter active designs only"),
    category: Optional[str] = Query(None, description="Filter by design category"),
    db: Session = Depends(get_db)
):
    """List all product designs."""
    try:
        query = db.query(ProductDesign)
        
        if active_only:
            query = query.filter(ProductDesign.is_active == True)
        
        if category:
            query = query.filter(ProductDesign.design_category == category)
        
        designs = query.order_by(ProductDesign.design_name).all()
        return designs
        
    except Exception as e:
        logger.error(f"Error listing product designs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list product designs: {str(e)}"
        )


@router.get("/designs/{design_id}", response_model=ProductDesignSchema)
def get_product_design(design_id: int, db: Session = Depends(get_db)):
    """Get a specific product design."""
    design = db.query(ProductDesign).filter(ProductDesign.id == design_id).first()
    if not design:
        raise HTTPException(status_code=404, detail="Product design not found")
    return design


@router.put("/designs/{design_id}", response_model=ProductDesignSchema)
def update_product_design(
    design_id: int,
    design_update: ProductDesignUpdate,
    db: Session = Depends(get_db)
):
    """Update a product design."""
    try:
        db_design = db.query(ProductDesign).filter(ProductDesign.id == design_id).first()
        if not db_design:
            raise HTTPException(status_code=404, detail="Product design not found")
        
        # Update fields
        update_data = design_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_design, field, value)
        
        db.commit()
        db.refresh(db_design)
        
        logger.info(f"Updated product design: {db_design.design_name}")
        return db_design
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product design: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product design: {str(e)}"
        )


# ================================
# PRODUCT ROUTES
# ================================

@router.post("/products/", response_model=ProductSchema)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product with optional variant generation."""
    try:
        # Check if product already exists
        existing = db.query(Product).filter(
            Product.product_name == product_data.product_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product_data.product_name}' already exists"
            )
        
        # Generate product code if not provided
        product_code = product_data.product_code
        if not product_code:
            product_code = f"PRD{product_data.product_name.replace(' ', '').upper()[:5]}"
        
        # Create product
        db_product = Product(
            product_name=product_data.product_name,
            product_code=product_code,
            category_id=product_data.category_id,
            description=product_data.description,
            # Three price points
            price_a=product_data.price_a,
            price_b=product_data.price_b,
            price_c=product_data.price_c,
            base_price=product_data.base_price,  # Keep for compatibility
            is_active=product_data.is_active
        )
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        # Create variants if requested
        if product_data.create_all_variants and product_data.size_ids and product_data.sleeve_type_ids and product_data.design_ids:
            create_product_variants(db_product.id, product_data.size_ids, product_data.sleeve_type_ids, product_data.design_ids, db)
        
        logger.info(f"Created product: {db_product.product_name}")
        return db_product
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )


def create_product_variants(product_id: int, size_ids: List[int], sleeve_type_ids: List[int], design_ids: List[int], db: Session):
    """Helper function to create all combinations of product variants."""
    try:
        for size_id in size_ids:
            for sleeve_type_id in sleeve_type_ids:
                for design_id in design_ids:
                    # Check if variant already exists
                    existing = db.query(ProductVariant).filter(
                        and_(
                            ProductVariant.product_id == product_id,
                            ProductVariant.size_id == size_id,
                            ProductVariant.sleeve_type_id == sleeve_type_id,
                            ProductVariant.design_id == design_id
                        )
                    ).first()
                    
                    if not existing:
                        # Get related data for naming
                        size = db.query(ProductSize).filter(ProductSize.id == size_id).first()
                        sleeve = db.query(ProductSleeveType).filter(ProductSleeveType.id == sleeve_type_id).first()
                        design = db.query(ProductDesign).filter(ProductDesign.id == design_id).first()
                        product = db.query(Product).filter(Product.id == product_id).first()
                        
                        if size and sleeve and design and product:
                            # Generate variant code and SKU
                            variant_code = f"{product.product_code}-{size.size_code}-{sleeve.sleeve_code}-{design.design_code}"
                            sku = generate_short_sku(
                                product.product_name, 
                                size.size_value, 
                                sleeve.sleeve_type, 
                                design.design_name
                            )
                            
                            variant = ProductVariant(
                                product_id=product_id,
                                size_id=size_id,
                                sleeve_type_id=sleeve_type_id,
                                design_id=design_id,
                                variant_code=variant_code,
                                sku=sku,
                                price=product.base_price
                            )
                            
                            db.add(variant)
        
        db.commit()
        logger.info(f"Created variants for product {product_id}")
        
    except Exception as e:
        logger.error(f"Error creating product variants: {str(e)}")
        raise e


@router.get("/products/", response_model=ProductListResponse)
def list_products(
    search: Optional[str] = Query(None, description="Search in product name or code"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    has_stock: Optional[bool] = Query(None, description="Filter products with stock"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List products with filtering and pagination."""
    try:
        query = db.query(Product)
        
        # Apply filters
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Product.product_name.ilike(search_filter),
                    Product.product_code.ilike(search_filter)
                )
            )
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        # Temporarily disable the has_stock filter to avoid join issues
        # if has_stock:
        #     # Join with variants and check stock
        #     query = query.join(ProductVariant).filter(ProductVariant.stock_balance > 0)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        products = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return ProductListResponse(
            products=products,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list products: {str(e)}"
        )


@router.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, include_variants: bool = Query(False), db: Session = Depends(get_db)):
    """Get a specific product with optional variants."""
    query = db.query(Product)
    
    if include_variants:
        query = query.options(joinedload(Product.variants))
    
    product = query.filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.put("/products/{product_id}", response_model=ProductSchema)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product."""
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update fields
        update_data = product_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        db.commit()
        db.refresh(db_product)
        
        logger.info(f"Updated product: {db_product.product_name}")
        return db_product
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


# ================================
# PRODUCT VARIANT ROUTES
# ================================

@router.post("/variants/", response_model=ProductVariantSchema)
def create_variant(
    variant_data: ProductVariantCreate,
    db: Session = Depends(get_db)
):
    """Create a single product variant."""
    try:
        # Check if variant already exists
        existing = db.query(ProductVariant).filter(
            and_(
                ProductVariant.product_id == variant_data.product_id,
                ProductVariant.size_id == variant_data.size_id,
                ProductVariant.sleeve_type_id == variant_data.sleeve_type_id,
                ProductVariant.design_id == variant_data.design_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Variant with this combination already exists"
            )
        
        # Get related data for naming
        product = db.query(Product).filter(Product.id == variant_data.product_id).first()
        size = db.query(ProductSize).filter(ProductSize.id == variant_data.size_id).first()
        sleeve = db.query(ProductSleeveType).filter(ProductSleeveType.id == variant_data.sleeve_type_id).first()
        design = db.query(ProductDesign).filter(ProductDesign.id == variant_data.design_id).first()
        
        if not all([product, size, sleeve, design]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product, size, sleeve type, or design ID"
            )
        
        # Generate codes if not provided
        variant_code = variant_data.variant_code
        if not variant_code:
            variant_code = f"{product.product_code}-{size.size_code}-{sleeve.sleeve_code}-{design.design_code}"
        
        sku = variant_data.sku
        if not sku:
            sku = generate_short_sku(
                product.product_name, 
                size.size_value, 
                sleeve.sleeve_type, 
                design.design_name
            )
        
        db_variant = ProductVariant(
            product_id=variant_data.product_id,
            size_id=variant_data.size_id,
            sleeve_type_id=variant_data.sleeve_type_id,
            design_id=variant_data.design_id,
            variant_code=variant_code,
            sku=sku,
            price=variant_data.price or product.base_price,
            cost_price=variant_data.cost_price,
            is_active=variant_data.is_active
        )
        
        db.add(db_variant)
        db.commit()
        db.refresh(db_variant)
        
        logger.info(f"Created product variant: {variant_code}")
        return db_variant
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product variant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product variant: {str(e)}"
        )


@router.post("/variants/bulk", response_model=List[ProductVariantSchema])
def create_variants_bulk(
    bulk_data: ProductVariantBulkCreate,
    db: Session = Depends(get_db)
):
    """Create multiple product variants in bulk."""
    try:
        created_variants = []
        
        for variant_info in bulk_data.variants:
            variant_data = ProductVariantCreate(
                product_id=bulk_data.product_id,
                **variant_info
            )
            
            # Check if variant already exists
            existing = db.query(ProductVariant).filter(
                and_(
                    ProductVariant.product_id == variant_data.product_id,
                    ProductVariant.size_id == variant_data.size_id,
                    ProductVariant.sleeve_type_id == variant_data.sleeve_type_id,
                    ProductVariant.design_id == variant_data.design_id
                )
            ).first()
            
            if not existing:
                # Create variant using the same logic as single variant creation
                try:
                    variant = create_variant(variant_data, db)
                    created_variants.append(variant)
                except Exception as e:
                    logger.warning(f"Skipped variant creation: {str(e)}")
                    continue
        
        logger.info(f"Created {len(created_variants)} variants in bulk")
        return created_variants
        
    except Exception as e:
        logger.error(f"Error creating variants in bulk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create variants in bulk: {str(e)}"
        )


@router.get("/variants/", response_model=VariantListResponse)
def list_variants(
    search: Optional[str] = Query(None, description="Search in variant name, code, SKU"),
    product_id: Optional[int] = Query(None, description="Filter by product"),
    size_id: Optional[int] = Query(None, description="Filter by size"),
    sleeve_type_id: Optional[int] = Query(None, description="Filter by sleeve type"),
    design_id: Optional[int] = Query(None, description="Filter by design"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    min_stock: Optional[Decimal] = Query(None, description="Minimum stock balance"),
    max_stock: Optional[Decimal] = Query(None, description="Maximum stock balance"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List product variants with filtering and pagination."""
    try:
        query = db.query(ProductVariant).options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.size),
            joinedload(ProductVariant.sleeve_type),
            joinedload(ProductVariant.design)
        )
        
        # Apply filters
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    ProductVariant.variant_code.ilike(search_filter),
                    ProductVariant.sku.ilike(search_filter),
                    ProductVariant.variant_name.ilike(search_filter)
                )
            )
        
        if product_id:
            query = query.filter(ProductVariant.product_id == product_id)
        
        if size_id:
            query = query.filter(ProductVariant.size_id == size_id)
        
        if sleeve_type_id:
            query = query.filter(ProductVariant.sleeve_type_id == sleeve_type_id)
        
        if design_id:
            query = query.filter(ProductVariant.design_id == design_id)
        
        if is_active is not None:
            query = query.filter(ProductVariant.is_active == is_active)
        
        if min_stock is not None:
            query = query.filter(ProductVariant.stock_balance >= min_stock)
        
        if max_stock is not None:
            query = query.filter(ProductVariant.stock_balance <= max_stock)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        variants = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return VariantListResponse(
            variants=variants,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing variants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list variants: {str(e)}"
        )


@router.get("/variants/{variant_id}", response_model=ProductVariantSchema)
def get_variant(variant_id: int, db: Session = Depends(get_db)):
    """Get a specific product variant."""
    variant = db.query(ProductVariant).options(
        joinedload(ProductVariant.product),
        joinedload(ProductVariant.size),
        joinedload(ProductVariant.sleeve_type),
        joinedload(ProductVariant.design)
    ).filter(ProductVariant.id == variant_id).first()
    
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found")
    
    return variant


@router.put("/variants/{variant_id}", response_model=ProductVariantSchema)
def update_variant(
    variant_id: int,
    variant_update: ProductVariantUpdate,
    db: Session = Depends(get_db)
):
    """Update a product variant."""
    try:
        db_variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not db_variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        
        # Update fields
        update_data = variant_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_variant, field, value)
        
        db.commit()
        db.refresh(db_variant)
        
        logger.info(f"Updated product variant: {db_variant.variant_code}")
        return db_variant
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product variant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product variant: {str(e)}"
        )


# ================================
# STOCK MANAGEMENT ROUTES
# ================================

@router.post("/stock/movement", response_model=ProductStockLedgerSchema)
def create_stock_movement(
    movement_data: StockMovementRequest,
    db: Session = Depends(get_db)
):
    """Create a single stock movement."""
    try:
        # Validate variant exists
        variant = db.query(ProductVariant).filter(ProductVariant.id == movement_data.variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        
        # Calculate quantity based on movement type
        quantity = movement_data.quantity
        if movement_data.movement_type == StockMovementType.OUT:
            quantity = -quantity
        
        # Get current balance
        current_balance = variant.stock_balance or Decimal('0')
        new_balance = current_balance + quantity
        
        # Validate stock doesn't go negative
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Current: {current_balance}, Requested: {abs(quantity)}"
            )
        
        # Create stock ledger entry
        stock_entry = ProductStockLedger(
            variant_id=movement_data.variant_id,
            movement_type=movement_data.movement_type,
            quantity=movement_data.quantity,
            unit_price=movement_data.unit_price,
            balance_after=new_balance,
            reference_type=movement_data.reference_type,
            reference_id=movement_data.reference_id,
            reference_number=movement_data.reference_number,
            notes=movement_data.notes
        )
        
        # Update variant balance
        variant.stock_balance = new_balance
        
        db.add(stock_entry)
        db.commit()
        db.refresh(stock_entry)
        
        logger.info(f"Stock movement created for variant {movement_data.variant_id}: {movement_data.movement_type} {movement_data.quantity}")
        return stock_entry
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating stock movement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create stock movement: {str(e)}"
        )


@router.post("/stock/movements/bulk", response_model=List[ProductStockLedgerSchema])
def create_bulk_stock_movements(
    bulk_movements: BulkStockMovementRequest,
    db: Session = Depends(get_db)
):
    """Create multiple stock movements in bulk."""
    try:
        created_entries = []
        
        for movement_data in bulk_movements.movements:
            try:
                entry = create_stock_movement(movement_data, db)
                created_entries.append(entry)
            except Exception as e:
                logger.warning(f"Skipped movement for variant {movement_data.variant_id}: {str(e)}")
                continue
        
        logger.info(f"Created {len(created_entries)} stock movements in bulk")
        return created_entries
        
    except Exception as e:
        logger.error(f"Error creating bulk stock movements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk stock movements: {str(e)}"
        )


@router.get("/stock/balance/{variant_id}", response_model=StockBalanceResponse)
def get_stock_balance(variant_id: int, db: Session = Depends(get_db)):
    """Get current stock balance for a variant."""
    try:
        variant = db.query(ProductVariant).options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.size),
            joinedload(ProductVariant.sleeve_type),
            joinedload(ProductVariant.design)
        ).filter(ProductVariant.id == variant_id).first()
        
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        
        return StockBalanceResponse(
            variant_id=variant.id,
            current_balance=variant.stock_balance or Decimal('0'),
            variant_name=variant.variant_name,
            product_name=variant.product.product_name if variant.product else None,
            size_value=variant.size.size_value if variant.size else None,
            sleeve_type=variant.sleeve_type.sleeve_type if variant.sleeve_type else None,
            design_name=variant.design.design_name if variant.design else None
        )
        
    except Exception as e:
        logger.error(f"Error getting stock balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stock balance: {str(e)}"
        )


@router.get("/stock/summary", response_model=StockSummaryResponse)
def get_stock_summary(
    product_id: Optional[int] = Query(None, description="Filter by product"),
    low_stock_threshold: Decimal = Query(Decimal('10'), description="Low stock threshold"),
    db: Session = Depends(get_db)
):
    """Get stock summary with low stock alerts."""
    try:
        query = db.query(ProductVariant).options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.size),
            joinedload(ProductVariant.sleeve_type),
            joinedload(ProductVariant.design)
        )
        
        if product_id:
            query = query.filter(ProductVariant.product_id == product_id)
        
        variants = query.filter(ProductVariant.is_active == True).all()
        
        total_variants = len(variants)
        total_stock_value = Decimal('0')
        low_stock_variants = 0
        out_of_stock_variants = 0
        variants_summary = []
        
        for variant in variants:
            balance = variant.stock_balance or Decimal('0')
            
            if balance == 0:
                out_of_stock_variants += 1
            elif balance <= low_stock_threshold:
                low_stock_variants += 1
            
            # Calculate stock value
            if variant.cost_price and balance > 0:
                total_stock_value += variant.cost_price * balance
            
            variants_summary.append(StockBalanceResponse(
                variant_id=variant.id,
                current_balance=balance,
                variant_name=variant.variant_name,
                product_name=variant.product.product_name if variant.product else None,
                size_value=variant.size.size_value if variant.size else None,
                sleeve_type=variant.sleeve_type.sleeve_type if variant.sleeve_type else None,
                design_name=variant.design.design_name if variant.design else None
            ))
        
        return StockSummaryResponse(
            total_variants=total_variants,
            total_stock_value=total_stock_value,
            low_stock_variants=low_stock_variants,
            out_of_stock_variants=out_of_stock_variants,
            variants_summary=variants_summary
        )
        
    except Exception as e:
        logger.error(f"Error getting stock summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stock summary: {str(e)}"
        )


@router.get("/stock/ledger/{variant_id}", response_model=StockLedgerListResponse)
def get_stock_ledger(
    variant_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get stock ledger entries for a variant."""
    try:
        query = db.query(ProductStockLedger).filter(
            ProductStockLedger.variant_id == variant_id
        ).order_by(desc(ProductStockLedger.transaction_date))
        
        total = query.count()
        entries = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return StockLedgerListResponse(
            entries=entries,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error getting stock ledger: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stock ledger: {str(e)}"
        )
