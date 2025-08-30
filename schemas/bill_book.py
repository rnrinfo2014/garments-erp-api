from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class BillBookStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"


class TaxType(str, Enum):
    """Tax handling types for bill books"""
    INCLUDE_TAX = "INCLUDE_TAX"      # Tax is included in item rate, need to separate it
    EXCLUDE_TAX = "EXCLUDE_TAX"      # Tax is added on top of item rate
    WITHOUT_TAX = "WITHOUT_TAX"      # No tax calculations needed


class BillBookBase(BaseModel):
    book_name: str = Field(..., description="Name of the bill book")
    book_code: str = Field(..., description="Unique code for the bill book")
    prefix: str = Field(..., description="Prefix for sales bill numbers")
    tax_type: TaxType = Field(TaxType.INCLUDE_TAX, description="How tax is handled for this bill book")
    starting_number: int = Field(1, description="Starting number for bill sequence")
    status: Optional[BillBookStatus] = Field(BillBookStatus.ACTIVE, description="Status of the bill book")


class BillBookCreate(BillBookBase):
    """Schema for creating a new bill book"""
    pass


class BillBookUpdate(BaseModel):
    """Schema for updating an existing bill book"""
    book_name: Optional[str] = Field(None, description="Name of the bill book")
    book_code: Optional[str] = Field(None, description="Unique code for the bill book")
    prefix: Optional[str] = Field(None, description="Prefix for sales bill numbers")
    tax_type: Optional[TaxType] = Field(None, description="How tax is handled for this bill book")
    starting_number: Optional[int] = Field(None, description="Starting number for bill sequence")
    status: Optional[BillBookStatus] = Field(None, description="Status of the bill book")


class BillBook(BillBookBase):
    """Schema for bill book responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    last_bill_no: int
    created_at: datetime
    updated_at: datetime


class BillBookListResponse(BaseModel):
    """Schema for paginated bill book list response"""
    model_config = ConfigDict(from_attributes=True)
    
    bill_books: list[BillBook]
    total: int
    page: int
    per_page: int
