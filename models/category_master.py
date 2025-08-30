from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class CategoryMaster(Base):
    __tablename__ = "category_master"
    
    id = Column(String(50), primary_key=True, index=True)
    category_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship with RawMaterialMaster
    raw_materials = relationship("RawMaterialMaster", back_populates="category")
