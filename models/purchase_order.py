from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from decimal import Decimal
from database import Base

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    po_number = Column(String(50), nullable=False, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    po_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(20), default="Draft", nullable=False)  # Draft, Pending, Approved, Received, Cancelled
    transport_details = Column(Text, nullable=True)
    
    # Financial fields
    sub_total = Column(Numeric(15, 2), default=0.00)
    tax_amount = Column(Numeric(15, 2), default=0.00)
    discount_amount = Column(Numeric(15, 2), default=0.00)
    total_amount = Column(Numeric(15, 2), default=0.00)
    
    remarks = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    
    @property
    def calculated_sub_total(self):
        """Calculate sub total from items"""
        return sum(item.total_amount for item in self.items) if self.items else Decimal('0.00')
    
    @property
    def calculated_total(self):
        """Calculate final total: sub_total + tax - discount"""
        sub = self.calculated_sub_total
        tax = self.tax_amount or Decimal('0.00')
        discount = self.discount_amount or Decimal('0.00')
        return sub + tax - discount
    
    def __repr__(self):
        return f"<PurchaseOrder(id={self.id}, po_number='{self.po_number}', status='{self.status}')>"


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    material_id = Column(String(50), ForeignKey("raw_material_master.id"), nullable=False)
    supplier_material_name = Column(String(200), nullable=True)  # Supplier's product name
    description = Column(Text, nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_id = Column(String(50), ForeignKey("unit_master.id"), nullable=False)  # Link to unit master
    rate = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)  # qty * rate
    
    # Tracking fields
    received_qty = Column(Numeric(15, 3), default=0.000)
    pending_qty = Column(Numeric(15, 3), nullable=False)  # quantity - received_qty
    item_status = Column(String(20), default="Pending")  # Pending, Partial, Received, Cancelled
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    material = relationship("RawMaterialMaster")
    unit = relationship("UnitMaster")
    
    def __repr__(self):
        return f"<PurchaseOrderItem(id={self.id}, po_id={self.po_id}, material_id='{self.material_id}')>"
