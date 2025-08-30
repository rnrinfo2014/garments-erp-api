from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.user import Base
import enum


# Enums for the product management system
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


class ProductSize(Base):
    __tablename__ = "product_sizes"
    
    id = Column(Integer, primary_key=True, index=True)
    size_value = Column(String(50), nullable=False)  # 36, 38, 40, 42, 46, S, M, L, XL
    size_display = Column(String(100), nullable=True)  # Display name
    size_code = Column(String(20), nullable=False, unique=True)  # SZ36, SZ38, SZS, SZM
    sort_order = Column(Integer, nullable=True)  # For sorting sizes
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    variants = relationship("ProductVariant", back_populates="size")


class ProductSleeveType(Base):
    __tablename__ = "product_sleeve_types"
    
    id = Column(Integer, primary_key=True, index=True)
    sleeve_type = Column(String(100), nullable=False)  # Full Sleeve, Half Sleeve, Sleeveless
    sleeve_code = Column(String(20), nullable=False, unique=True)  # FS, HS, SL
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    variants = relationship("ProductVariant", back_populates="sleeve_type")


class ProductDesign(Base):
    __tablename__ = "product_designs"
    
    id = Column(Integer, primary_key=True, index=True)
    design_name = Column(String(100), nullable=False)  # Plain, Checked, Kaaki, Linen, Print
    design_code = Column(String(30), nullable=False, unique=True)  # PLN, CHK, KAK, LIN, PRT
    design_category = Column(SQLEnum(DesignCategory), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    variants = relationship("ProductVariant", back_populates="design")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(200), nullable=False)  # smart_plus, premium_cotton
    product_code = Column(String(50), nullable=False, unique=True)  # PRDSMTPL, PRDPRMCT
    category_id = Column(String(50), nullable=True)  # Simple string field, no foreign key
    description = Column(Text, nullable=True)
    # Three different price points
    price_a = Column(Numeric(10, 2), nullable=True)  # Price A
    price_b = Column(Numeric(10, 2), nullable=True)  # Price B
    price_c = Column(Numeric(10, 2), nullable=True)  # Price C
    base_price = Column(Numeric(10, 2), nullable=True)  # Base price for the product (kept for compatibility)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size_id = Column(Integer, ForeignKey("product_sizes.id"), nullable=False)
    sleeve_type_id = Column(Integer, ForeignKey("product_sleeve_types.id"), nullable=False)
    design_id = Column(Integer, ForeignKey("product_designs.id"), nullable=False)
    
    # Automatically generated fields
    variant_name = Column(String(300), nullable=True)  # Auto-generated: "Smart Plus - 36 - Full Sleeve - Plain"
    variant_code = Column(String(100), nullable=False, unique=True)  # PRDSMTPL-SZ36-FS-PLN
    sku = Column(String(100), nullable=True, unique=True)  # Stock Keeping Unit
    
    # Product details for sales
    hsn_code = Column(String(20), nullable=True)  # HSN code for tax purposes
    unit_type = Column(String(50), nullable=False, default="PCS")  # Unit type (PCS, KG, MTR, etc.)
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=True)  # Selling price for this variant
    cost_price = Column(Numeric(10, 2), nullable=True)  # Cost price
    mrp = Column(Numeric(10, 2), nullable=True)  # Maximum Retail Price
    
    # Stock tracking
    stock_balance = Column(Numeric(10, 2), default=0, nullable=False)  # Current stock balance
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    size = relationship("ProductSize", back_populates="variants")
    sleeve_type = relationship("ProductSleeveType", back_populates="variants")
    design = relationship("ProductDesign", back_populates="variants")
    stock_ledger_entries = relationship("ProductStockLedger", back_populates="variant", cascade="all, delete-orphan")
    sales_items = relationship("SalesItem", back_populates="variant")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-generate variant_name on creation if not provided
        if not self.variant_name:
            self._generate_variant_name()
    
    def _generate_variant_name(self):
        """Generate variant name from related objects."""
        # This will be populated after the relationships are loaded
        pass


class ProductStockLedger(Base):
    __tablename__ = "product_stock_ledger"
    
    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    
    # Transaction details
    movement_type = Column(SQLEnum(StockMovementType), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)  # Positive for IN, negative for OUT
    unit_price = Column(Numeric(10, 2), nullable=True)  # Price per unit
    balance_after = Column(Numeric(10, 2), nullable=False)  # Stock balance after this transaction
    
    # Reference information
    reference_type = Column(String(50), nullable=True)  # Purchase, Sale, Transfer, Adjustment
    reference_id = Column(Integer, nullable=True)  # ID of the reference document
    reference_number = Column(String(100), nullable=True)  # Reference document number
    
    # Additional info
    notes = Column(Text, nullable=True)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    variant = relationship("ProductVariant", back_populates="stock_ledger_entries")
