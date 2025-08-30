from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class PurchaseStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class PurchaseTypeEnum(str, Enum):
    CASH = "CASH"
    CREDIT = "CREDIT"
    ADVANCE = "ADVANCE"


class QualityStatusEnum(str, Enum):
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    PENDING = "Pending"


class PaymentModeEnum(str, Enum):
    CASH = "CASH"
    BANK = "BANK"
    CHEQUE = "CHEQUE"


# Purchase Item Schemas
class PurchaseItemBase(BaseModel):
    material_id: str = Field(..., description="Raw material ID")
    size_id: str = Field(..., description="Size ID")
    supplier_material_name: Optional[str] = Field(None, description="Supplier's product name")
    description: Optional[str] = None
    quantity: Decimal = Field(..., ge=0.001, description="Quantity received")
    unit_id: str = Field(..., description="Unit of measurement")
    rate: Decimal = Field(..., ge=0.01, description="Rate per unit")
    po_item_id: Optional[int] = Field(None, description="Purchase order item reference")
    quality_status: QualityStatusEnum = QualityStatusEnum.ACCEPTED
    rejected_qty: Decimal = Field(default=Decimal('0.000'), ge=0)
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None

    @validator('rejected_qty')
    def validate_rejected_qty(cls, v, values):
        quantity = values.get('quantity', Decimal('0'))
        if v > quantity:
            raise ValueError('Rejected quantity cannot be greater than total quantity')
        return v

    @root_validator(skip_on_failure=True)
    def validate_quality_and_rejected_qty(cls, values):
        quality_status = values.get('quality_status')
        rejected_qty = values.get('rejected_qty', Decimal('0'))
        
        if quality_status == QualityStatusEnum.REJECTED and rejected_qty <= 0:
            raise ValueError('Rejected quantity must be greater than 0 when quality status is Rejected')
        
        if quality_status == QualityStatusEnum.ACCEPTED and rejected_qty > 0:
            values['quality_status'] = QualityStatusEnum.PENDING
        
        return values


class PurchaseItemCreate(PurchaseItemBase):
    pass


class PurchaseItemUpdate(BaseModel):
    supplier_material_name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, ge=0.001)
    rate: Optional[Decimal] = Field(None, ge=0.01)
    quality_status: Optional[QualityStatusEnum] = None
    rejected_qty: Optional[Decimal] = Field(None, ge=0)
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None


class PurchaseItemResponse(PurchaseItemBase):
    id: int
    purchase_id: int
    total_amount: Decimal
    accepted_qty: Decimal
    is_stock_updated: bool
    stock_ledger_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    calculated_total: Decimal
    net_accepted_amount: Decimal
    
    class Config:
        from_attributes = True


# Purchase Schemas
class PurchaseBase(BaseModel):
    purchase_date: date = Field(..., description="Purchase date")
    supplier_id: int = Field(..., description="Supplier ID")
    supplier_invoice_number: Optional[str] = Field(None, description="Supplier's invoice number")
    supplier_invoice_date: Optional[date] = None
    po_id: Optional[int] = Field(None, description="Reference purchase order ID")
    po_number: Optional[str] = None
    purchase_type: PurchaseTypeEnum = PurchaseTypeEnum.CREDIT
    tax_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    transport_charges: Decimal = Field(default=Decimal('0.00'), ge=0)
    other_charges: Decimal = Field(default=Decimal('0.00'), ge=0)
    amount_paid: Decimal = Field(default=Decimal('0.00'), ge=0)
    payment_mode: Optional[PaymentModeEnum] = None
    payment_reference: Optional[str] = None
    transport_details: Optional[str] = None
    remarks: Optional[str] = None

    @root_validator(skip_on_failure=True)
    def validate_payment_details(cls, values):
        purchase_type = values.get('purchase_type')
        amount_paid = values.get('amount_paid', Decimal('0'))
        payment_mode = values.get('payment_mode')
        
        if purchase_type == PurchaseTypeEnum.CASH and amount_paid <= 0:
            raise ValueError('Amount paid must be greater than 0 for cash purchases')
        
        if amount_paid > 0 and not payment_mode:
            raise ValueError('Payment mode is required when amount paid is specified')
        
        return values


class PurchaseCreate(PurchaseBase):
    items: List[PurchaseItemCreate] = Field(..., min_items=1, description="Purchase items")
    created_by: str = Field(..., description="User who created the purchase")

    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('At least one item is required')
        return v


class PurchaseUpdate(BaseModel):
    supplier_invoice_number: Optional[str] = None
    supplier_invoice_date: Optional[date] = None
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    transport_charges: Optional[Decimal] = Field(None, ge=0)
    other_charges: Optional[Decimal] = Field(None, ge=0)
    amount_paid: Optional[Decimal] = Field(None, ge=0)
    payment_mode: Optional[PaymentModeEnum] = None
    payment_reference: Optional[str] = None
    transport_details: Optional[str] = None
    remarks: Optional[str] = None
    updated_by: str = Field(..., description="User who updated the purchase")


class PurchaseResponse(PurchaseBase):
    id: int
    purchase_number: str
    status: PurchaseStatusEnum
    sub_total: Decimal
    total_amount: Decimal
    ledger_batch_id: Optional[int]
    is_ledger_posted: bool
    is_stock_updated: bool
    created_by: str
    updated_by: Optional[str]
    posted_by: Optional[str]
    posted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    calculated_sub_total: Decimal
    calculated_total: Decimal
    balance_amount: Decimal
    is_fully_paid: bool
    
    # Related items
    items: List[PurchaseItemResponse] = []
    
    class Config:
        from_attributes = True


class PurchaseListResponse(BaseModel):
    id: int
    purchase_number: str
    purchase_date: date
    supplier_id: int
    supplier_invoice_number: Optional[str]
    status: PurchaseStatusEnum
    purchase_type: PurchaseTypeEnum
    total_amount: Decimal
    balance_amount: Decimal
    is_ledger_posted: bool
    is_stock_updated: bool
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Bulk Purchase Operations
class BulkPurchaseCreate(BaseModel):
    purchases: List[PurchaseCreate] = Field(..., min_items=1)
    created_by: str = Field(..., description="User creating bulk purchases")

    @validator('purchases')
    def validate_purchases(cls, v):
        if not v:
            raise ValueError('At least one purchase is required')
        return v


# Purchase Posting Schema
class PurchasePostRequest(BaseModel):
    purchase_id: int
    post_to_ledger: bool = Field(default=True, description="Create ledger transactions")
    post_to_stock: bool = Field(default=True, description="Update stock ledger")
    posted_by: str = Field(..., description="User posting the purchase")


# Purchase Reports
class PurchaseSummaryResponse(BaseModel):
    total_purchases: int
    total_amount: Decimal
    total_paid: Decimal
    total_pending: Decimal
    draft_count: int
    posted_count: int


class SupplierPurchaseSummary(BaseModel):
    supplier_id: int
    supplier_name: str
    total_purchases: int
    total_amount: Decimal
    total_paid: Decimal
    pending_amount: Decimal
    last_purchase_date: Optional[date]


# Purchase Integration Schemas
class PurchaseFromPORequest(BaseModel):
    po_id: int
    purchase_date: date
    supplier_invoice_number: Optional[str] = None
    supplier_invoice_date: Optional[date] = None
    received_items: List[dict] = Field(..., description="Items received with quantities")
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "po_id": 1,
                "purchase_date": "2025-08-26",
                "supplier_invoice_number": "INV-001",
                "supplier_invoice_date": "2025-08-25",
                "received_items": [
                    {
                        "po_item_id": 1,
                        "received_quantity": 100,
                        "rate": 25.50,
                        "quality_status": "Accepted",
                        "batch_number": "BATCH001"
                    }
                ],
                "created_by": "user123"
            }
        }
