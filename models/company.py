from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from models.user import Base

class CompanyDetails(Base):
    __tablename__ = 'company_details'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    contact = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    gst = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    logo = Column(String(500), nullable=True)  # URL or file path to logo
    state_id = Column(Integer, ForeignKey('states.id'), nullable=True)
    
    # Relationship
    state = relationship("State", back_populates="companies")
