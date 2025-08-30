from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models.user import Base

class State(Base):
    __tablename__ = 'states'
    
    id = Column(Integer, primary_key=True, index=True)  # Keep original column name
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)  # State abbreviation (e.g., "MH", "DL")
    gst_code = Column(String(2), nullable=False, unique=True)  # GST state code (e.g., "27", "07")
    
    # Relationships  
    companies = relationship("CompanyDetails", back_populates="state")
    agents = relationship("Agent", back_populates="state")
    customers = relationship("Customer", back_populates="state")
    suppliers = relationship("Supplier", back_populates="state")
    # Note: All relationships removed to avoid circular import issues
    # Access related models via explicit queries
    
    def __str__(self):
        return f"{self.name} ({self.code})"
