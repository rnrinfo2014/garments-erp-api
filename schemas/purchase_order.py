from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# Purchase Order Item Schemas
class PurchaseOrderItemBase(BaseModel):
    material_id: str = Field(..., description="Raw Material ID reference")
    supplier_material_name: Optional[str] = Field(None, max_length=200, description="Supplier's product name")
    description: Optional[str] = Field(None, description="Item description")
    quantity: Decimal = Field(..., gt=0, description="Quantity to order")
    unit_id: str = Field(..., description="Unit of measurement ID")
    rate: Decimal = Field(..., ge=0, description="Rate per unit")

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    @validator('quantity', 'rate')
    def validate_decimals(cls, v):
        if v is not None and v < 0:
            raise ValueError('Value must be non-negative')
        return v

class PurchaseOrderItemUpdate(BaseModel):
    material_id: Optional[str] = None
    supplier_material_name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_id: Optional[str] = None
    rate: Optional[Decimal] = None
    received_qty: Optional[Decimal] = None
    item_status: Optional[str] = None

class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    po_id: int
    total_amount: Decimal
    received_qty: Decimal
    pending_qty: Decimal
    item_status: str
    created_at: datetime
    updated_at: datetime
    
    # Related data (will be populated via relationships)
    material: Optional[dict] = None
    unit: Optional[dict] = None

# Purchase Order Main Schemas
class PurchaseOrderBase(BaseModel):
    po_number: str = Field(..., max_length=50, description="Purchase Order Number")
    supplier_id: int = Field(..., description="Supplier ID reference")
    po_date: date = Field(..., description="Purchase Order Date")
    due_date: Optional[date] = Field(None, description="Expected delivery date")
    transport_details: Optional[str] = Field(None, description="Shipping/Transport details")
    tax_amount: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Tax amount")
    discount_amount: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Discount amount")
    remarks: Optional[str] = Field(None, description="Additional remarks")

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1, description="Purchase order items")
    
    @validator('items')
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one item is required')
        return v

class PurchaseOrderUpdate(BaseModel):
    po_number: Optional[str] = None
    supplier_id: Optional[int] = None
    po_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    transport_details: Optional[str] = None
    tax_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    remarks: Optional[str] = None

class PurchaseOrderResponse(PurchaseOrderBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: str
    sub_total: Decimal
    total_amount: Decimal
    created_by: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Calculated properties
    calculated_sub_total: Optional[Decimal] = None
    calculated_total: Optional[Decimal] = None
    
    # Related data
    items: List[PurchaseOrderItemResponse] = []
    supplier: Optional[dict] = None

class PurchaseOrderSummary(BaseModel):
    """Summary view of purchase orders"""
    id: int
    po_number: str
    supplier_id: int
    supplier_name: Optional[str] = None
    po_date: date
    due_date: Optional[date] = None
    status: str
    total_amount: Decimal
    items_count: int
    created_at: datetime

# Status update schema
class PurchaseOrderStatusUpdate(BaseModel):
    status: str = Field(..., description="New status")
    remarks: Optional[str] = Field(None, description="Status change remarks")

# Filtering schema
class PurchaseOrderFilter(BaseModel):
    supplier_id: Optional[int] = None
    status: Optional[str] = None
    po_date_from: Optional[date] = None
    po_date_to: Optional[date] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
