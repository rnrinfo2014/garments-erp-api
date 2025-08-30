from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.user import Base
import enum


class CustomerType(enum.Enum):
    REGISTERED = "Registered"
    UNREGISTERED = "Unregistered"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False, index=True)
    customer_type = Column(SQLEnum(CustomerType), nullable=False, default=CustomerType.UNREGISTERED)
    
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
    customer_acc_code = Column(String(20), nullable=False, unique=True, index=True)
    
    # Status and Timestamps
    status = Column(String(20), default="Active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    state = relationship("State", back_populates="customers")
    agent = relationship("Agent", back_populates="customers")
    sales = relationship("Sales", back_populates="customer")

    @property
    def name(self):
        """Alias for customer_name to match sales route expectations"""
        return self.customer_name
    
    @property
    def code(self):
        """Alias for customer_acc_code to match sales route expectations"""
        return self.customer_acc_code

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.customer_name}', type='{self.customer_type}')>"
