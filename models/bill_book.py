from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from models.user import Base


class BillBookStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"


class TaxType(str, enum.Enum):
    """Tax handling types for bill books"""
    INCLUDE_TAX = "INCLUDE_TAX"      # Tax is included in item rate, need to separate it
    EXCLUDE_TAX = "EXCLUDE_TAX"      # Tax is added on top of item rate
    WITHOUT_TAX = "WITHOUT_TAX"      # No tax calculations needed


class BillBook(Base):
    __tablename__ = "bill_books"
    
    id = Column(Integer, primary_key=True, index=True)
    book_name = Column(String(100), nullable=False)
    book_code = Column(String(20), nullable=False, unique=True)
    prefix = Column(String(20), nullable=False)  # Prefix for sales bill numbers
    
    # Tax type - determines how tax is handled in sales
    tax_type = Column(SQLEnum(TaxType), nullable=False, default=TaxType.INCLUDE_TAX)
    
    # Bill number tracking
    last_bill_no = Column(Integer, default=0)
    starting_number = Column(Integer, default=1)  # Starting number for bill sequence
    
    # Status
    status = Column(SQLEnum(BillBookStatus), default=BillBookStatus.ACTIVE)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sales = relationship("Sales", back_populates="bill_book")
