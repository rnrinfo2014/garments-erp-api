from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enum import Enum


class VendorStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class VendorMaster(Base):
    __tablename__ = "vendor_master"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    company_name = Column(String(150), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(15), nullable=False)
    gst = Column(String(15), nullable=True)  # Optional field, no validation
    services = Column(Text, nullable=False)
    acc_code = Column(String(20), nullable=False, unique=True, index=True)  # Reference to accounts table
    status = Column(String(10), nullable=False, default=VendorStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Note: Relationship to AccountsMaster removed to avoid circular import issues
    # Use explicit queries to get account details when needed

    def __repr__(self):
        return f"<VendorMaster(id={self.id}, name={self.name}, company={self.company_name})>"
