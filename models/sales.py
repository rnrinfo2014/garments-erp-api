"""
Sales Management Models
SQLAlchemy models for sales and sales_items tables
"""

from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, Enum as SQLEnum, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base
import enum
from datetime import datetime, date
from typing import List, Optional


class SalesStatus(enum.Enum):
    """Sales status enumeration"""
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Sales(Base):
    """
    Sales/Invoice Model
    Represents a complete sales transaction with multiple line items
    """
    __tablename__ = "sales"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Bill book and customer info
    bill_book_id = Column(Integer, ForeignKey("bill_books.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    
    # Bill details
    bill_number = Column(String(50), nullable=False, unique=True, index=True)
    bill_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    
    # Summary fields (calculated from items)
    item_count = Column(Integer, default=0)
    total_qty = Column(Numeric(15, 3), default=0.000)
    gross_amount = Column(Numeric(15, 2), default=0.00)
    discount_amount = Column(Numeric(15, 2), default=0.00)
    tax_amount = Column(Numeric(15, 2), default=0.00)
    additional_charges = Column(Numeric(15, 2), default=0.00)
    total_amount = Column(Numeric(15, 2), default=0.00)
    
    # Transport details
    transport_details = Column(Text, nullable=True)
    llr_no = Column(String(100), nullable=True)
    llr_date = Column(Date, nullable=True)
    
    # Status and audit
    status = Column(SQLEnum(SalesStatus), default=SalesStatus.DRAFT, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=True)

    # Relationships
    bill_book = relationship("BillBook", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    agent = relationship("Agent", back_populates="sales")
    items = relationship("SalesItem", back_populates="sales", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sales(id={self.id}, bill_number='{self.bill_number}', customer_id={self.customer_id}, total_amount={self.total_amount})>"

    @property
    def is_editable(self) -> bool:
        """Check if sales record can be edited"""
        return self.status in [SalesStatus.DRAFT, SalesStatus.CONFIRMED]
    
    @property
    def is_cancellable(self) -> bool:
        """Check if sales record can be cancelled"""
        return self.status in [SalesStatus.DRAFT, SalesStatus.CONFIRMED, SalesStatus.DISPATCHED]
    
    @property
    def can_dispatch(self) -> bool:
        """Check if sales record can be dispatched"""
        return self.status == SalesStatus.CONFIRMED
    
    @property
    def can_deliver(self) -> bool:
        """Check if sales record can be marked as delivered"""
        return self.status == SalesStatus.DISPATCHED

    def calculate_totals(self):
        """Calculate and update summary totals from items"""
        if not self.items:
            self.item_count = 0
            self.total_qty = 0.000
            self.gross_amount = 0.00
            self.discount_amount = 0.00
            self.tax_amount = 0.00
            self.total_amount = self.additional_charges or 0.00
            return

        self.item_count = len(self.items)
        self.total_qty = sum(item.quantity for item in self.items)
        
        # Calculate gross amount (before discount and tax)
        self.gross_amount = sum(item.quantity * item.sale_rate for item in self.items)
        
        # Calculate total discount
        self.discount_amount = sum(item.discount_amount for item in self.items)
        
        # Calculate total tax
        self.tax_amount = sum(item.tax_amount for item in self.items)
        
        # Calculate final total
        self.total_amount = (
            self.gross_amount - 
            self.discount_amount + 
            self.tax_amount + 
            (self.additional_charges or 0.00)
        )


class SalesItem(Base):
    """
    Sales Item Model
    Represents individual line items in a sales transaction
    """
    __tablename__ = "sales_items"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    sales_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False, index=True)
    
    # Product details (captured at time of sale)
    product_name = Column(String(200), nullable=False)
    hsn_code = Column(String(20), nullable=True)
    unit_type = Column(String(50), nullable=False)
    
    # Quantity and pricing
    quantity = Column(Numeric(15, 3), nullable=False)
    mrp = Column(Numeric(15, 2), nullable=False)
    sale_rate = Column(Numeric(15, 2), nullable=False)
    
    # Tax calculations
    tax_percentage = Column(Numeric(5, 2), default=0.00)
    tax_amount = Column(Numeric(15, 2), default=0.00)
    
    # Discount calculations
    discount_percentage = Column(Numeric(5, 2), default=0.00)
    discount_amount = Column(Numeric(15, 2), default=0.00)
    
    # Total amount for this item
    total_amount = Column(Numeric(15, 2), nullable=False)
    
    # Audit
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    sales = relationship("Sales", back_populates="items")
    variant = relationship("ProductVariant", back_populates="sales_items")

    def __repr__(self):
        return f"<SalesItem(id={self.id}, sales_id={self.sales_id}, product='{self.product_name}', qty={self.quantity}, total={self.total_amount})>"

    @property
    def line_total_before_discount(self) -> float:
        """Calculate line total before discount"""
        return float(self.quantity * self.sale_rate)
    
    @property
    def line_total_after_discount(self) -> float:
        """Calculate line total after discount but before tax"""
        return self.line_total_before_discount - float(self.discount_amount or 0)
    
    @property
    def effective_rate_after_discount(self) -> float:
        """Calculate effective rate per unit after discount"""
        if self.quantity == 0:
            return 0.0
        return self.line_total_after_discount / float(self.quantity)

    def calculate_amounts(self):
        """Calculate discount, tax and total amounts"""
        # Calculate base amount
        base_amount = float(self.quantity * self.sale_rate)
        
        # Calculate discount amount
        if self.discount_percentage and self.discount_percentage > 0:
            self.discount_amount = round(base_amount * float(self.discount_percentage) / 100, 2)
        else:
            self.discount_amount = 0.00
        
        # Amount after discount
        amount_after_discount = base_amount - float(self.discount_amount)
        
        # Calculate tax amount
        if self.tax_percentage and self.tax_percentage > 0:
            self.tax_amount = round(amount_after_discount * float(self.tax_percentage) / 100, 2)
        else:
            self.tax_amount = 0.00
        
        # Calculate total amount
        self.total_amount = round(amount_after_discount + float(self.tax_amount), 2)

    def validate_amounts(self) -> bool:
        """Validate that calculated amounts are correct"""
        base_amount = float(self.quantity * self.sale_rate)
        expected_discount = round(base_amount * float(self.discount_percentage or 0) / 100, 2)
        amount_after_discount = base_amount - expected_discount
        expected_tax = round(amount_after_discount * float(self.tax_percentage or 0) / 100, 2)
        expected_total = round(amount_after_discount + expected_tax, 2)
        
        return (
            abs(float(self.discount_amount or 0) - expected_discount) < 0.01 and
            abs(float(self.tax_amount or 0) - expected_tax) < 0.01 and
            abs(float(self.total_amount) - expected_total) < 0.01
        )


# Add reverse relationships to existing models (these should be added to respective model files)
"""
Add these relationships to existing models:

# In models/bill_book.py - BillBook class:
sales = relationship("Sales", back_populates="bill_book")

# In models/customer.py - Customer class:  
sales = relationship("Sales", back_populates="customer")

# In models/agent.py - Agent class:
sales = relationship("Sales", back_populates="agent")

# In models/product_variant.py - ProductVariant class:
sales_items = relationship("SalesItem", back_populates="variant")
"""
