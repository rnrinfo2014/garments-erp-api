from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class UnitMaster(Base):
    __tablename__ = "unit_master"
    
    id = Column(String(50), primary_key=True, index=True)
    unit_name = Column(String(100), nullable=False, unique=True)
    unit_code = Column(String(20), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    raw_materials = relationship("RawMaterialMaster", back_populates="unit")
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="unit")
