from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class RawMaterialMaster(Base):
    __tablename__ = "raw_material_master"
    
    id = Column(String(50), primary_key=True, index=True)
    material_name = Column(String(100), nullable=False)
    material_code = Column(String(50), nullable=False, unique=True)
    category_id = Column(String(50), ForeignKey("category_master.id"), nullable=False)
    size_id = Column(String(50), ForeignKey("size_master.id"), nullable=False)
    unit_id = Column(String(50), ForeignKey("unit_master.id"), nullable=False)
    standard_rate = Column(Numeric(15, 2), default=0.00)
    minimum_stock = Column(Numeric(15, 2), default=0.00)
    maximum_stock = Column(Numeric(15, 2), default=0.00)
    reorder_level = Column(Numeric(15, 2), default=0.00)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("CategoryMaster", back_populates="raw_materials")
    size = relationship("SizeMaster", back_populates="raw_materials") 
    unit = relationship("UnitMaster", back_populates="raw_materials")
    # stock_ledger_entries = relationship("StockLedger", back_populates="raw_material")  # Temporarily disabled
