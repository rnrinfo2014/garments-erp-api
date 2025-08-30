from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class VendorStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class VendorMasterBase(BaseModel):
    id: str = Field(..., max_length=50, description="Unique vendor ID")
    name: str = Field(..., max_length=100, description="Vendor name")
    company_name: str = Field(..., max_length=150, description="Company name")
    address: str = Field(..., description="Vendor address")
    phone: str = Field(..., max_length=15, description="Phone number")
    gst: Optional[str] = Field(None, max_length=15, description="GST number (optional)")
    services: str = Field(..., description="Services provided")
    status: VendorStatus = Field(VendorStatus.ACTIVE, description="Vendor status")


class VendorMasterCreate(VendorMasterBase):
    pass


class VendorMasterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=150)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=15)
    gst: Optional[str] = Field(None, max_length=15)
    services: Optional[str] = None
    status: Optional[VendorStatus] = None


class VendorMasterResponse(VendorMasterBase):
    acc_code: str = Field(..., description="Associated account code")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
