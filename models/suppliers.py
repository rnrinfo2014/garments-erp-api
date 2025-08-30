from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.user import Base
import enum


class SupplierType(enum.Enum):
    REGISTERED = "Registered"
    UNREGISTERED = "Unregistered"


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(100), nullable=False, index=True)
    supplier_type = Column(SQLEnum(SupplierType), nullable=False, default=SupplierType.UNREGISTERED)
    
    # GST Details (mandatory if registered)
    gst_number = Column(String(15), nullable=True, unique=True, index=True)
    
    # Contact Details
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Address Details
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Foreign Keys
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    
    # Account Details (auto-generated)
    supplier_acc_code = Column(String(20), nullable=False, unique=True, index=True)
    
    # Status and Timestamps
    status = Column(String(20), default="Active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    state = relationship("State", back_populates="suppliers")
    agent = relationship("Agent", back_populates="suppliers")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")
    # stock_ledger_entries = relationship("StockLedger", back_populates="supplier")  # Temporarily disabled

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.supplier_name}', type='{self.supplier_type}')>"
