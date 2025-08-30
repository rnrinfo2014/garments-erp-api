from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import enum


# Enums for validation
class StockMovementType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"


class DesignCategory(str, enum.Enum):
    PLAIN = "plain"
    PATTERN = "pattern"
    PRINT = "print"
    TEXTURE = "texture"


# Base schemas for Product Size
class ProductSizeBase(BaseModel):
    size_value: str = Field(..., description="Size value (e.g., 36, 38, 40)")
    size_display: Optional[str] = Field(None, description="Display name for size")
    size_code: Optional[str] = Field(None, description="Size code for internal use")
    sort_order: Optional[int] = Field(None, description="Sort order for sizes")
    is_active: Optional[bool] = Field(True, description="Size status")


class ProductSizeCreate(ProductSizeBase):
    pass


class ProductSizeUpdate(BaseModel):
    size_value: Optional[str] = Field(None, description="Size value")
    size_display: Optional[str] = Field(None, description="Display name")
    size_code: Optional[str] = Field(None, description="Size code")
    sort_order: Optional[int] = Field(None, description="Sort order")
    is_active: Optional[bool] = Field(None, description="Size status")


class ProductSize(ProductSizeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# Base schemas for Product Sleeve Type
class ProductSleeveTypeBase(BaseModel):
    sleeve_type: str = Field(..., description="Sleeve type (e.g., Full Sleeve, Half Sleeve)")
    sleeve_code: Optional[str] = Field(None, description="Sleeve code")
    description: Optional[str] = Field(None, description="Sleeve description")
    is_active: Optional[bool] = Field(True, description="Sleeve type status")


class ProductSleeveTypeCreate(ProductSleeveTypeBase):
    pass


class ProductSleeveTypeUpdate(BaseModel):
    sleeve_type: Optional[str] = Field(None, description="Sleeve type")
    sleeve_code: Optional[str] = Field(None, description="Sleeve code")
    description: Optional[str] = Field(None, description="Description")
    is_active: Optional[bool] = Field(None, description="Status")


class ProductSleeveType(ProductSleeveTypeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# Base schemas for Product Design
class ProductDesignBase(BaseModel):
    design_name: str = Field(..., description="Design name (e.g., Plain, Checked)")
    design_code: Optional[str] = Field(None, description="Design code")
    design_category: Optional[DesignCategory] = Field(None, description="Design category")
    description: Optional[str] = Field(None, description="Design description")
    is_active: Optional[bool] = Field(True, description="Design status")


class ProductDesignCreate(ProductDesignBase):
    pass


class ProductDesignUpdate(BaseModel):
    design_name: Optional[str] = Field(None, description="Design name")
    design_code: Optional[str] = Field(None, description="Design code")
    design_category: Optional[DesignCategory] = Field(None, description="Design category")
    description: Optional[str] = Field(None, description="Description")
    is_active: Optional[bool] = Field(None, description="Status")


class ProductDesign(ProductDesignBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# Base schemas for Product
class ProductBase(BaseModel):
    product_name: str = Field(..., description="Product name (e.g., smart_plus)")
    product_code: Optional[str] = Field(None, description="Product code")
    category_id: Optional[str] = Field(None, description="Category ID")
    description: Optional[str] = Field(None, description="Product description")
    # Three different price points
    price_a: Optional[Decimal] = Field(None, description="Price A")
    price_b: Optional[Decimal] = Field(None, description="Price B")
    price_c: Optional[Decimal] = Field(None, description="Price C")
    base_price: Optional[Decimal] = Field(None, description="Base price (for compatibility)")
    is_active: Optional[bool] = Field(True, description="Product status")


class ProductCreate(ProductBase):
    # Additional fields for variant creation
    size_ids: Optional[List[int]] = Field(None, description="List of size IDs to create variants")
    sleeve_type_ids: Optional[List[int]] = Field(None, description="List of sleeve type IDs")
    design_ids: Optional[List[int]] = Field(None, description="List of design IDs")
    create_all_variants: Optional[bool] = Field(False, description="Create all possible variants")


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, description="Product name")
    product_code: Optional[str] = Field(None, description="Product code")
    category_id: Optional[str] = Field(None, description="Category ID")
    description: Optional[str] = Field(None, description="Description")
    # Three different price points
    price_a: Optional[Decimal] = Field(None, description="Price A")
    price_b: Optional[Decimal] = Field(None, description="Price B")
    price_c: Optional[Decimal] = Field(None, description="Price C")
    base_price: Optional[Decimal] = Field(None, description="Base price (for compatibility)")
    is_active: Optional[bool] = Field(None, description="Status")


class Product(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# Base schemas for Product Variant
class ProductVariantBase(BaseModel):
    product_id: int = Field(..., description="Product ID")
    size_id: int = Field(..., description="Size ID")
    sleeve_type_id: int = Field(..., description="Sleeve type ID")
    design_id: int = Field(..., description="Design ID")
    variant_code: Optional[str] = Field(None, description="Variant code")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    price: Optional[Decimal] = Field(None, description="Variant price")
    cost_price: Optional[Decimal] = Field(None, description="Cost price")
    is_active: Optional[bool] = Field(True, description="Variant status")


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantBulkCreate(BaseModel):
    product_id: int = Field(..., description="Product ID")
    variants: List[dict] = Field(..., description="List of variant data")
    
    @field_validator('variants')
    @classmethod
    def validate_variants(cls, v):
        for variant in v:
            required_fields = ['size_id', 'sleeve_type_id', 'design_id']
            if not all(field in variant for field in required_fields):
                raise ValueError(f"Each variant must have: {', '.join(required_fields)}")
        return v


class ProductVariantUpdate(BaseModel):
    variant_code: Optional[str] = Field(None, description="Variant code")
    sku: Optional[str] = Field(None, description="SKU")
    price: Optional[Decimal] = Field(None, description="Price")
    cost_price: Optional[Decimal] = Field(None, description="Cost price")
    is_active: Optional[bool] = Field(None, description="Status")


class ProductVariant(ProductVariantBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    variant_name: Optional[str] = Field(None, description="Generated variant name")
    stock_balance: Optional[Decimal] = Field(None, description="Current stock balance")
    created_at: datetime
    updated_at: datetime


# Base schemas for Product Stock Ledger
class ProductStockLedgerBase(BaseModel):
    variant_id: int = Field(..., description="Product variant ID")
    movement_type: StockMovementType = Field(..., description="Stock movement type")
    quantity: Decimal = Field(..., description="Quantity moved")
    unit_price: Optional[Decimal] = Field(None, description="Unit price")
    reference_type: Optional[str] = Field(None, description="Reference document type")
    reference_id: Optional[int] = Field(None, description="Reference document ID")
    reference_number: Optional[str] = Field(None, description="Reference number")
    notes: Optional[str] = Field(None, description="Additional notes")


class ProductStockLedgerCreate(ProductStockLedgerBase):
    pass


class ProductStockLedgerUpdate(BaseModel):
    notes: Optional[str] = Field(None, description="Update notes")


class ProductStockLedger(ProductStockLedgerBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    balance_after: Decimal = Field(..., description="Stock balance after this movement")
    transaction_date: datetime
    created_at: datetime
    
    # Include related data
    variant: Optional['ProductVariant'] = None


# Stock management schemas
class StockMovementRequest(BaseModel):
    variant_id: int = Field(..., description="Product variant ID")
    movement_type: StockMovementType = Field(..., description="Movement type")
    quantity: Decimal = Field(..., description="Quantity to move")
    unit_price: Optional[Decimal] = Field(None, description="Unit price")
    reference_type: Optional[str] = Field(None, description="Reference type")
    reference_id: Optional[int] = Field(None, description="Reference ID")
    reference_number: Optional[str] = Field(None, description="Reference number")
    notes: Optional[str] = Field(None, description="Notes")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class BulkStockMovementRequest(BaseModel):
    movements: List[StockMovementRequest] = Field(..., description="List of stock movements")
    
    @field_validator('movements')
    @classmethod
    def validate_movements(cls, v):
        if not v:
            raise ValueError("At least one movement is required")
        return v


class StockBalanceResponse(BaseModel):
    variant_id: int
    current_balance: Decimal
    variant_name: Optional[str] = None
    product_name: Optional[str] = None
    size_value: Optional[str] = None
    sleeve_type: Optional[str] = None
    design_name: Optional[str] = None


class StockSummaryResponse(BaseModel):
    total_variants: int
    total_stock_value: Decimal
    low_stock_variants: int
    out_of_stock_variants: int
    variants_summary: List[StockBalanceResponse]


# Dashboard and reporting schemas
class ProductPerformanceReport(BaseModel):
    product_id: int
    product_name: str
    total_variants: int
    total_stock: Decimal
    total_value: Decimal
    avg_price: Optional[Decimal] = None
    last_movement_date: Optional[datetime] = None


class VariantPerformanceReport(BaseModel):
    variant_id: int
    variant_name: str
    product_name: str
    current_stock: Decimal
    total_in: Decimal
    total_out: Decimal
    stock_value: Decimal
    last_movement_date: Optional[datetime] = None


# Search and filter schemas
class ProductSearchFilter(BaseModel):
    search: Optional[str] = Field(None, description="Search in product name, code")
    category_id: Optional[str] = Field(None, description="Filter by category")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    has_stock: Optional[bool] = Field(None, description="Filter products with stock")


class VariantSearchFilter(BaseModel):
    search: Optional[str] = Field(None, description="Search in variant name, code, SKU")
    product_id: Optional[int] = Field(None, description="Filter by product")
    size_id: Optional[int] = Field(None, description="Filter by size")
    sleeve_type_id: Optional[int] = Field(None, description="Filter by sleeve type")
    design_id: Optional[int] = Field(None, description="Filter by design")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    min_stock: Optional[Decimal] = Field(None, description="Minimum stock balance")
    max_stock: Optional[Decimal] = Field(None, description="Maximum stock balance")


# Response schemas for lists
class ProductListResponse(BaseModel):
    products: List[Product]
    total: int
    page: int
    per_page: int


class VariantListResponse(BaseModel):
    variants: List[ProductVariant]
    total: int
    page: int
    per_page: int


class StockLedgerListResponse(BaseModel):
    entries: List[ProductStockLedger]
    total: int
    page: int
    per_page: int
