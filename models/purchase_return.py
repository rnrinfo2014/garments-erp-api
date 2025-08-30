from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from decimal import Decimal
from database import Base
import enum


class PurchaseReturnStatus(enum.Enum):
    DRAFT = "Draft"
    POSTED = "Posted"
    CANCELLED = "Cancelled"


class ReturnReason(enum.Enum):
    DEFECTIVE = "Defective"
    EXCESS_QUANTITY = "Excess Quantity"
    WRONG_ITEM = "Wrong Item"
    QUALITY_ISSUE = "Quality Issue"
    DAMAGED = "Damaged"
    EXPIRED = "Expired"
    OTHER = "Other"


class PurchaseReturn(Base):
    """
    Purchase Return Model - Returns to suppliers
    Automatically creates reverse transactions in Stock Ledger & Account Ledger
    """
    __tablename__ = "purchase_returns"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    return_number = Column(String(50), nullable=False, unique=True, index=True)
    return_date = Column(Date, nullable=False, index=True)
    
    # Supplier Information
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Reference to Original Purchase
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False, index=True)
    purchase_number = Column(String(50), nullable=True)
    
    # Return Details
    return_reason = Column(SQLEnum(ReturnReason), nullable=False)
    status = Column(SQLEnum(PurchaseReturnStatus), nullable=False, default=PurchaseReturnStatus.DRAFT)
    
    # Supplier Credit Note Details
    supplier_credit_note_number = Column(String(100), nullable=True)
    supplier_credit_note_date = Column(Date, nullable=True)
    
    # Financial Totals
    sub_total = Column(Numeric(15, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    transport_charges = Column(Numeric(15, 2), default=0.00, nullable=False)
    other_charges = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # Refund Information
    refund_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    refund_mode = Column(String(20), nullable=True)  # 'CASH', 'BANK', 'ADJUST_PAYABLE'
    refund_reference = Column(String(100), nullable=True)  # Transaction ID, etc.
    refund_date = Column(Date, nullable=True)
    
    # Additional Details
    transport_details = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    
    # Ledger Integration Fields
    ledger_batch_id = Column(Integer, ForeignKey("transaction_batches.id"), nullable=True)
    is_ledger_posted = Column(Boolean, default=False, nullable=False)
    is_stock_updated = Column(Boolean, default=False, nullable=False)
    
    # Quality Control
    quality_check_done = Column(Boolean, default=False, nullable=False)
    quality_approved_by = Column(String(50), nullable=True)
    quality_approved_at = Column(DateTime, nullable=True)
    
    # Approval Workflow
    approval_required = Column(Boolean, default=True, nullable=False)
    approved_by = Column(String(50), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Audit Fields
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=True)
    posted_by = Column(String(50), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier")
    purchase = relationship("Purchase")
    items = relationship("PurchaseReturnItem", back_populates="purchase_return", cascade="all, delete-orphan")
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
    def pending_refund_amount(self):
        """Calculate pending refund amount"""
        total = self.total_amount or Decimal('0.00')
        refunded = self.refund_amount or Decimal('0.00')
        return total - refunded
    
    @property
    def is_fully_refunded(self):
        """Check if return is fully refunded"""
        return self.pending_refund_amount <= Decimal('0.00')
    
    def __repr__(self):
        return f"<PurchaseReturn(id={self.id}, return_number='{self.return_number}', status='{self.status}')>"


class PurchaseReturnItem(Base):
    """
    Purchase Return Item Model - Individual items in a return
    Automatically updates Stock Ledger with negative quantities
    """
    __tablename__ = "purchase_return_items"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    return_id = Column(Integer, ForeignKey("purchase_returns.id"), nullable=False, index=True)
    
    # Reference to Original Purchase Item
    purchase_item_id = Column(Integer, ForeignKey("purchase_items.id"), nullable=False, index=True)
    
    # Material Information
    material_id = Column(String(50), ForeignKey("raw_material_master.id"), nullable=False, index=True)
    size_id = Column(String(50), ForeignKey("size_master.id"), nullable=False, index=True)
    
    # Item Details
    supplier_material_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Quantity and Unit
    return_quantity = Column(Numeric(15, 3), nullable=False)
    unit_id = Column(String(50), ForeignKey("unit_master.id"), nullable=False)
    
    # Pricing (from original purchase)
    rate = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)  # return_quantity * rate
    
    # Return Specific Details
    return_reason = Column(SQLEnum(ReturnReason), nullable=False)
    condition_on_return = Column(String(100), nullable=True)  # 'Good', 'Damaged', 'Defective'
    
    # Stock Ledger Integration
    stock_ledger_id = Column(Integer, ForeignKey("stock_ledger.ledger_id"), nullable=True)
    is_stock_updated = Column(Boolean, default=False, nullable=False)
    
    # Batch/Lot Information (from original purchase)
    batch_number = Column(String(50), nullable=True)
    expiry_date = Column(Date, nullable=True)
    
    # Quality Control
    quality_check_status = Column(String(20), default="Pending")  # 'Pending', 'Approved', 'Rejected'
    quality_notes = Column(Text, nullable=True)
    
    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    purchase_return = relationship("PurchaseReturn", back_populates="items")
    purchase_item = relationship("PurchaseItem")
    material = relationship("RawMaterialMaster")
    size = relationship("SizeMaster")
    unit = relationship("UnitMaster")
    stock_ledger = relationship("StockLedger")
    
    @property
    def calculated_total(self):
        """Calculate total: return_quantity * rate"""
        qty = self.return_quantity or Decimal('0.00')
        rate = self.rate or Decimal('0.00')
        return qty * rate
    
    def __repr__(self):
        return f"<PurchaseReturnItem(id={self.id}, return_id={self.return_id}, material_id='{self.material_id}')>"


class PurchaseReturnApproval(Base):
    """
    Purchase Return Approval Workflow
    Tracks approval history for returns
    """
    __tablename__ = "purchase_return_approvals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    return_id = Column(Integer, ForeignKey("purchase_returns.id"), nullable=False, index=True)
    
    # Approval Details
    approver_id = Column(String(50), nullable=False)
    approver_name = Column(String(100), nullable=False)
    approval_level = Column(Integer, nullable=False)  # 1, 2, 3 (multi-level approval)
    
    # Approval Status
    status = Column(String(20), nullable=False)  # 'Approved', 'Rejected', 'Pending'
    approval_date = Column(DateTime, nullable=True)
    
    # Comments
    comments = Column(Text, nullable=True)
    
    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    purchase_return = relationship("PurchaseReturn")
    
    def __repr__(self):
        return f"<PurchaseReturnApproval(id={self.id}, return_id={self.return_id}, status='{self.status}')>"
