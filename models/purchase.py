from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from decimal import Decimal
from database import Base
import enum


class PurchaseStatus(enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"  
    CANCELLED = "CANCELLED"


class PurchaseType(enum.Enum):
    CASH = "CASH"
    CREDIT = "CREDIT"
    ADVANCE = "ADVANCE"


class Purchase(Base):
    """
    Purchase Entry Model - Actual receipt/invoice from suppliers
    Links to Purchase Orders and automatically updates Stock Ledger & Account Ledger
    """
    __tablename__ = "purchases"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_number = Column(String(50), nullable=False, unique=True, index=True)
    purchase_date = Column(Date, nullable=False, index=True)
    
    # Supplier Information
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier_invoice_number = Column(String(100), nullable=True)  # Supplier's invoice number
    supplier_invoice_date = Column(Date, nullable=True)
    
    # Reference to Purchase Order (optional)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    po_number = Column(String(50), nullable=True)
    
    # Purchase Type and Status
    purchase_type = Column(SQLEnum(PurchaseType), nullable=False, default=PurchaseType.CREDIT)
    status = Column(SQLEnum(PurchaseStatus), nullable=False, default=PurchaseStatus.DRAFT)
    
    # Financial Totals
    sub_total = Column(Numeric(15, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    transport_charges = Column(Numeric(15, 2), default=0.00, nullable=False)
    other_charges = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # Payment Information (for cash purchases)
    amount_paid = Column(Numeric(15, 2), default=0.00, nullable=False)
    payment_mode = Column(String(20), nullable=True)  # 'CASH', 'BANK', 'CHEQUE'
    payment_reference = Column(String(100), nullable=True)  # Cheque number, transaction ID, etc.
    
    # Additional Details
    transport_details = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    
    # Ledger Integration Fields
    ledger_batch_id = Column(Integer, ForeignKey("transaction_batches.id"), nullable=True)
    is_ledger_posted = Column(Boolean, default=False, nullable=False)
    is_stock_updated = Column(Boolean, default=False, nullable=False)
    
    # Audit Fields
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=True)
    posted_by = Column(String(50), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchases")
    purchase_order = relationship("PurchaseOrder")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    ledger_batch = relationship("TransactionBatch")
    
    @property
    def calculated_sub_total(self):
        """Calculate sub total from items"""
        return sum(item.total_amount for item in self.items) if self.items else Decimal('0.00')
    
    @property
    def calculated_total(self):
        """Calculate final total: sub_total + tax + transport + other - discount"""
        sub = self.calculated_sub_total
        tax = self.tax_amount or Decimal('0.00')
        transport = self.transport_charges or Decimal('0.00')
        other = self.other_charges or Decimal('0.00')
        discount = self.discount_amount or Decimal('0.00')
        return sub + tax + transport + other - discount
    
    @property
    def balance_amount(self):
        """Calculate balance amount: total - amount_paid"""
        total = self.total_amount or Decimal('0.00')
        paid = self.amount_paid or Decimal('0.00')
        return total - paid
    
    @property
    def is_fully_paid(self):
        """Check if purchase is fully paid"""
        return self.balance_amount <= Decimal('0.00')
    
    def __repr__(self):
        return f"<Purchase(id={self.id}, purchase_number='{self.purchase_number}', status='{self.status}')>"


class PurchaseItem(Base):
    """
    Purchase Item Model - Individual items in a purchase entry
    Automatically updates Stock Ledger when posted
    """
    __tablename__ = "purchase_items"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False, index=True)
    
    # Material Information
    material_id = Column(String(50), ForeignKey("raw_material_master.id"), nullable=False, index=True)
    size_id = Column(String(50), ForeignKey("size_master.id"), nullable=False, index=True)
    
    # Item Details
    supplier_material_name = Column(String(200), nullable=True)  # Supplier's product name
    description = Column(Text, nullable=True)
    
    # Quantity and Unit
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_id = Column(String(50), ForeignKey("unit_master.id"), nullable=False)
    
    # Pricing
    rate = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)  # quantity * rate
    
    # Purchase Order Reference (optional)
    po_item_id = Column(Integer, ForeignKey("purchase_order_items.id"), nullable=True)
    
    # Stock Ledger Integration
    stock_ledger_id = Column(Integer, ForeignKey("stock_ledger.ledger_id"), nullable=True)
    is_stock_updated = Column(Boolean, default=False, nullable=False)
    
    # Quality and Inspection
    quality_status = Column(String(20), default="Accepted")  # 'Accepted', 'Rejected', 'Pending'
    rejected_qty = Column(Numeric(15, 3), default=0.000)
    accepted_qty = Column(Numeric(15, 3), nullable=False)  # quantity - rejected_qty
    
    # Batch/Lot Information
    batch_number = Column(String(50), nullable=True)
    expiry_date = Column(Date, nullable=True)
    
    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    purchase = relationship("Purchase", back_populates="items")
    material = relationship("RawMaterialMaster")
    size = relationship("SizeMaster")
    unit = relationship("UnitMaster")
    po_item = relationship("PurchaseOrderItem")
    stock_ledger = relationship("StockLedger")
    
    @property
    def calculated_total(self):
        """Calculate total: quantity * rate"""
        qty = self.quantity or Decimal('0.00')
        rate = self.rate or Decimal('0.00')
        return qty * rate
    
    @property
    def net_accepted_amount(self):
        """Calculate amount for accepted quantity"""
        accepted_qty = self.accepted_qty or Decimal('0.00')
        rate = self.rate or Decimal('0.00')
        return accepted_qty * rate
    
    def __repr__(self):
        return f"<PurchaseItem(id={self.id}, purchase_id={self.purchase_id}, material_id='{self.material_id}')>"
