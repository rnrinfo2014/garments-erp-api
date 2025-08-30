"""
Sales Management Schemas
Pydantic schemas for request/response models
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class SalesStatusSchema(str, Enum):
    """Sales status enumeration for API"""
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# Base schemas for common fields
class SalesItemBase(BaseModel):
    """Base schema for sales item"""
    variant_id: int = Field(..., description="Product variant ID")
    quantity: Decimal = Field(..., gt=0, description="Quantity to sell")
    sale_rate: Decimal = Field(..., ge=0, description="Sale rate per unit")
    discount_percentage: Optional[Decimal] = Field(0, ge=0, le=100, description="Discount percentage")
    tax_percentage: Optional[Decimal] = Field(0, ge=0, le=100, description="Tax percentage")

    @validator('quantity', 'sale_rate')
    def validate_decimal_places(cls, v):
        """Validate decimal places"""
        if v is not None:
            # Quantity: max 3 decimal places
            # Sale rate: max 2 decimal places  
            return round(v, 3 if 'quantity' in str(v) else 2)
        return v


class SalesBase(BaseModel):
    """Base schema for sales"""
    bill_book_id: int = Field(..., description="Bill book ID for bill number generation")
    customer_id: int = Field(..., description="Customer ID")
    agent_id: Optional[int] = Field(None, description="Sales agent ID")
    bill_date: date = Field(..., description="Bill date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    additional_charges: Optional[Decimal] = Field(0, ge=0, description="Additional charges")
    transport_details: Optional[str] = Field(None, max_length=500, description="Transport details")
    llr_no: Optional[str] = Field(None, max_length=100, description="LLR number")
    llr_date: Optional[date] = Field(None, description="LLR date")

    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Validate due date is not before bill date"""
        if v and 'bill_date' in values and v < values['bill_date']:
            raise ValueError('Due date cannot be before bill date')
        return v


# Request schemas
class SalesItemCreate(SalesItemBase):
    """Schema for creating sales item"""
    pass

    class Config:
        schema_extra = {
            "example": {
                "variant_id": 1,
                "quantity": 5.000,
                "sale_rate": 150.00,
                "discount_percentage": 10.0,
                "tax_percentage": 18.0
            }
        }


class SalesCreate(SalesBase):
    """Schema for creating sales"""
    items: List[SalesItemCreate] = Field(..., min_items=1, description="Sales items")

    @validator('items')
    def validate_items_not_empty(cls, v):
        """Validate items list is not empty"""
        if not v:
            raise ValueError('Sales must have at least one item')
        return v

    class Config:
        schema_extra = {
            "example": {
                "bill_book_id": 1,
                "customer_id": 1,
                "agent_id": 1,
                "bill_date": "2025-08-30",
                "due_date": "2025-09-30",
                "additional_charges": 50.00,
                "transport_details": "By road via ABC Transport",
                "llr_no": "LLR001",
                "llr_date": "2025-08-30",
                "items": [
                    {
                        "variant_id": 1,
                        "quantity": 5.000,
                        "sale_rate": 150.00,
                        "discount_percentage": 10.0,
                        "tax_percentage": 18.0
                    }
                ]
            }
        }


class SalesItemUpdate(BaseModel):
    """Schema for updating sales item"""
    variant_id: Optional[int] = Field(None, description="Product variant ID")
    quantity: Optional[Decimal] = Field(None, gt=0, description="Quantity to sell")
    sale_rate: Optional[Decimal] = Field(None, ge=0, description="Sale rate per unit")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Discount percentage")
    tax_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Tax percentage")

    class Config:
        schema_extra = {
            "example": {
                "quantity": 7.000,
                "sale_rate": 140.00,
                "discount_percentage": 15.0
            }
        }


class SalesUpdate(BaseModel):
    """Schema for updating sales"""
    customer_id: Optional[int] = Field(None, description="Customer ID")
    agent_id: Optional[int] = Field(None, description="Sales agent ID")
    bill_date: Optional[date] = Field(None, description="Bill date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    additional_charges: Optional[Decimal] = Field(None, ge=0, description="Additional charges")
    transport_details: Optional[str] = Field(None, max_length=500, description="Transport details")
    llr_no: Optional[str] = Field(None, max_length=100, description="LLR number")
    llr_date: Optional[date] = Field(None, description="LLR date")

    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Validate due date is not before bill date"""
        if v and 'bill_date' in values and v < values['bill_date']:
            raise ValueError('Due date cannot be before bill date')
        return v

    class Config:
        schema_extra = {
            "example": {
                "due_date": "2025-10-15",
                "additional_charges": 75.00,
                "transport_details": "Updated transport details"
            }
        }


class SalesStatusUpdate(BaseModel):
    """Schema for updating sales status"""
    status: SalesStatusSchema = Field(..., description="New status")
    updated_by: str = Field(..., max_length=50, description="User updating the status")

    class Config:
        schema_extra = {
            "example": {
                "status": "CONFIRMED",
                "updated_by": "admin"
            }
        }


# Response schemas
class SalesItemResponse(SalesItemBase):
    """Schema for sales item response"""
    id: int
    sales_id: int
    product_name: str
    hsn_code: Optional[str]
    unit_type: str
    mrp: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "sales_id": 1,
                "variant_id": 1,
                "product_name": "Cotton Shirt - Blue - XL",
                "hsn_code": "6205",
                "unit_type": "PCS",
                "quantity": 5.000,
                "mrp": 200.00,
                "sale_rate": 150.00,
                "discount_percentage": 10.0,
                "discount_amount": 75.00,
                "tax_percentage": 18.0,
                "tax_amount": 121.50,
                "total_amount": 796.50,
                "created_at": "2025-08-30T10:30:00Z",
                "updated_at": "2025-08-30T10:30:00Z"
            }
        }


class SalesResponse(SalesBase):
    """Schema for sales response"""
    id: int
    bill_number: str
    item_count: int
    total_qty: Decimal
    gross_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: SalesStatusSchema
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str]
    items: List[SalesItemResponse] = []

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "bill_book_id": 1,
                "customer_id": 1,
                "agent_id": 1,
                "bill_number": "TI-001",
                "bill_date": "2025-08-30",
                "due_date": "2025-09-30",
                "item_count": 1,
                "total_qty": 5.000,
                "gross_amount": 750.00,
                "discount_amount": 75.00,
                "tax_amount": 121.50,
                "additional_charges": 50.00,
                "total_amount": 846.50,
                "transport_details": "By road via ABC Transport",
                "llr_no": "LLR001",
                "llr_date": "2025-08-30",
                "status": "DRAFT",
                "created_at": "2025-08-30T10:30:00Z",
                "updated_at": "2025-08-30T10:30:00Z",
                "created_by": "admin",
                "updated_by": None,
                "items": []
            }
        }


class SalesListResponse(BaseModel):
    """Schema for sales list response (without items)"""
    id: int
    bill_number: str
    customer_id: int
    agent_id: Optional[int]
    bill_date: date
    due_date: Optional[date]
    item_count: int
    total_qty: Decimal
    total_amount: Decimal
    status: SalesStatusSchema
    created_at: datetime

    class Config:
        from_attributes = True


class SalesSummary(BaseModel):
    """Schema for sales summary statistics"""
    total_sales: int
    total_amount: Decimal
    status_breakdown: Dict[str, int]
    date_range: Dict[str, date]

    class Config:
        schema_extra = {
            "example": {
                "total_sales": 150,
                "total_amount": 125000.00,
                "status_breakdown": {
                    "DRAFT": 25,
                    "CONFIRMED": 100,
                    "DISPATCHED": 20,
                    "DELIVERED": 5
                },
                "date_range": {
                    "from_date": "2025-08-01",
                    "to_date": "2025-08-30"
                }
            }
        }


# Filters and pagination
class SalesFilter(BaseModel):
    """Schema for sales filtering"""
    customer_id: Optional[int] = Field(None, description="Filter by customer")
    agent_id: Optional[int] = Field(None, description="Filter by agent")
    bill_book_id: Optional[int] = Field(None, description="Filter by bill book")
    status: Optional[SalesStatusSchema] = Field(None, description="Filter by status")
    from_date: Optional[date] = Field(None, description="Filter from date")
    to_date: Optional[date] = Field(None, description="Filter to date")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum amount")
    bill_number: Optional[str] = Field(None, description="Search by bill number")

    @validator('to_date')
    def validate_date_range(cls, v, values):
        """Validate date range"""
        if v and 'from_date' in values and values['from_date'] and v < values['from_date']:
            raise ValueError('To date cannot be before from date')
        return v

    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        """Validate amount range"""
        if v and 'min_amount' in values and values['min_amount'] and v < values['min_amount']:
            raise ValueError('Max amount cannot be less than min amount')
        return v

    class Config:
        schema_extra = {
            "example": {
                "customer_id": 1,
                "status": "CONFIRMED",
                "from_date": "2025-08-01",
                "to_date": "2025-08-30",
                "min_amount": 1000.00
            }
        }


class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.limit

    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "limit": 20
            }
        }


class PaginatedSalesResponse(BaseModel):
    """Schema for paginated sales response"""
    items: List[SalesListResponse]
    total: int
    page: int
    limit: int
    pages: int

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 1,
                "limit": 20,
                "pages": 8
            }
        }


# Bulk operations
class BulkStatusUpdate(BaseModel):
    """Schema for bulk status update"""
    sales_ids: List[int] = Field(..., min_items=1, description="List of sales IDs")
    status: SalesStatusSchema = Field(..., description="New status")
    updated_by: str = Field(..., max_length=50, description="User updating the status")

    class Config:
        schema_extra = {
            "example": {
                "sales_ids": [1, 2, 3],
                "status": "CONFIRMED",
                "updated_by": "admin"
            }
        }


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response"""
    success_count: int
    failed_count: int
    failed_ids: List[int]
    errors: List[str]

    class Config:
        schema_extra = {
            "example": {
                "success_count": 2,
                "failed_count": 1,
                "failed_ids": [3],
                "errors": ["Sales ID 3: Cannot change status from DELIVERED to CONFIRMED"]
            }
        }
