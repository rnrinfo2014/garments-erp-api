from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class PurchaseReturnStatusEnum(str, Enum):
    DRAFT = "Draft"
    POSTED = "Posted"
    CANCELLED = "Cancelled"


class ReturnReasonEnum(str, Enum):
    DEFECTIVE = "Defective"
    EXCESS_QUANTITY = "Excess Quantity"
    WRONG_ITEM = "Wrong Item"
    QUALITY_ISSUE = "Quality Issue"
    DAMAGED = "Damaged"
    EXPIRED = "Expired"
    OTHER = "Other"


class RefundModeEnum(str, Enum):
    CASH = "CASH"
    BANK = "BANK"
    ADJUST_PAYABLE = "ADJUST_PAYABLE"


class QualityCheckStatusEnum(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class ConditionEnum(str, Enum):
    GOOD = "Good"
    DAMAGED = "Damaged"
    DEFECTIVE = "Defective"


# Purchase Return Item Schemas
class PurchaseReturnItemBase(BaseModel):
    purchase_item_id: int = Field(..., description="Original purchase item ID")
    material_id: str = Field(..., description="Raw material ID")
    size_id: str = Field(..., description="Size ID")
    supplier_material_name: Optional[str] = None
    description: Optional[str] = None
    return_quantity: Decimal = Field(..., ge=0.001, description="Quantity to return")
    unit_id: str = Field(..., description="Unit of measurement")
    rate: Decimal = Field(..., ge=0.01, description="Rate per unit (from original purchase)")
    return_reason: ReturnReasonEnum = Field(..., description="Reason for return")
    condition_on_return: Optional[ConditionEnum] = ConditionEnum.GOOD
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    quality_notes: Optional[str] = None

    @validator('return_quantity')
    def validate_return_quantity(cls, v):
        if v <= 0:
            raise ValueError('Return quantity must be greater than 0')
        return v


class PurchaseReturnItemCreate(PurchaseReturnItemBase):
    pass


class PurchaseReturnItemUpdate(BaseModel):
    return_quantity: Optional[Decimal] = Field(None, ge=0.001)
    return_reason: Optional[ReturnReasonEnum] = None
    condition_on_return: Optional[ConditionEnum] = None
    quality_notes: Optional[str] = None


class PurchaseReturnItemResponse(PurchaseReturnItemBase):
    id: int
    return_id: int
    total_amount: Decimal
    is_stock_updated: bool
    stock_ledger_id: Optional[int]
    quality_check_status: QualityCheckStatusEnum
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    calculated_total: Decimal
    
    class Config:
        from_attributes = True


# Purchase Return Schemas
class PurchaseReturnBase(BaseModel):
    return_date: date = Field(..., description="Return date")
    supplier_id: int = Field(..., description="Supplier ID")
    purchase_id: int = Field(..., description="Original purchase ID")
    return_reason: ReturnReasonEnum = Field(..., description="Main reason for return")
    supplier_credit_note_number: Optional[str] = None
    supplier_credit_note_date: Optional[date] = None
    tax_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    transport_charges: Decimal = Field(default=Decimal('0.00'), ge=0)
    other_charges: Decimal = Field(default=Decimal('0.00'), ge=0)
    refund_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    refund_mode: Optional[RefundModeEnum] = None
    refund_reference: Optional[str] = None
    refund_date: Optional[date] = None
    transport_details: Optional[str] = None
    remarks: Optional[str] = None
    approval_required: bool = Field(default=True)

    @validator('refund_amount', always=True)
    def validate_refund_details(cls, v, values):
        refund_mode = values.get('refund_mode')
        
        if v > 0 and not refund_mode:
            raise ValueError('Refund mode is required when refund amount is specified')
        
        return v


class PurchaseReturnCreate(PurchaseReturnBase):
    items: List[PurchaseReturnItemCreate] = Field(..., description="Return items")
    created_by: str = Field(..., description="User who created the return")

    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('At least one item is required for return')
        return v


class PurchaseReturnUpdate(BaseModel):
    supplier_credit_note_number: Optional[str] = None
    supplier_credit_note_date: Optional[date] = None
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    transport_charges: Optional[Decimal] = Field(None, ge=0)
    other_charges: Optional[Decimal] = Field(None, ge=0)
    refund_amount: Optional[Decimal] = Field(None, ge=0)
    refund_mode: Optional[RefundModeEnum] = None
    refund_reference: Optional[str] = None
    refund_date: Optional[date] = None
    transport_details: Optional[str] = None
    remarks: Optional[str] = None
    updated_by: str = Field(..., description="User who updated the return")


class PurchaseReturnResponse(PurchaseReturnBase):
    id: int
    return_number: str
    purchase_number: Optional[str]
    status: PurchaseReturnStatusEnum
    sub_total: Decimal
    total_amount: Decimal
    ledger_batch_id: Optional[int]
    is_ledger_posted: bool
    is_stock_updated: bool
    quality_check_done: bool
    quality_approved_by: Optional[str]
    quality_approved_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_by: str
    updated_by: Optional[str]
    posted_by: Optional[str]
    posted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    calculated_sub_total: Decimal
    calculated_total: Decimal
    pending_refund_amount: Decimal
    is_fully_refunded: bool
    
    # Related items
    items: List[PurchaseReturnItemResponse] = []
    
    class Config:
        from_attributes = True


class PurchaseReturnListResponse(BaseModel):
    id: int
    return_number: str
    return_date: date
    supplier_id: int
    purchase_id: int
    purchase_number: Optional[str]
    return_reason: ReturnReasonEnum
    status: PurchaseReturnStatusEnum
    total_amount: Decimal
    pending_refund_amount: Decimal
    is_ledger_posted: bool
    is_stock_updated: bool
    quality_check_done: bool
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Purchase Return Operations
class PurchaseReturnPostRequest(BaseModel):
    return_id: int
    post_to_ledger: bool = Field(default=True, description="Create reverse ledger transactions")
    post_to_stock: bool = Field(default=True, description="Update stock ledger with returns")
    posted_by: str = Field(..., description="User posting the return")


class PurchaseReturnApprovalRequest(BaseModel):
    return_id: int
    approved: bool = Field(..., description="True for approval, False for rejection")
    comments: Optional[str] = None
    approver_id: str = Field(..., description="Approver user ID")
    approver_name: str = Field(..., description="Approver name")


class QualityCheckRequest(BaseModel):
    return_id: int
    approved: bool = Field(..., description="Quality check result")
    notes: Optional[str] = None
    checked_by: str = Field(..., description="Quality checker user ID")


# Bulk Operations
class BulkPurchaseReturnCreate(BaseModel):
    returns: List[PurchaseReturnCreate] = Field(..., description="List of returns to create")
    created_by: str = Field(..., description="User creating bulk returns")

    @validator('returns')
    def validate_returns(cls, v):
        if not v:
            raise ValueError('At least one return is required')
        return v


# Reports and Summary
class PurchaseReturnSummaryResponse(BaseModel):
    total_returns: int
    total_amount: Decimal
    total_refunded: Decimal
    pending_refund: Decimal
    draft_count: int
    posted_count: int
    pending_approval_count: int
    quality_pending_count: int


class SupplierReturnSummary(BaseModel):
    supplier_id: int
    supplier_name: str
    total_returns: int
    total_return_amount: Decimal
    pending_refund: Decimal
    last_return_date: Optional[date]
    most_common_reason: Optional[ReturnReasonEnum]


class ReturnReasonAnalysis(BaseModel):
    reason: ReturnReasonEnum
    count: int
    total_amount: Decimal
    percentage: float


# Integration with Original Purchase
class PurchaseItemReturnEligibility(BaseModel):
    purchase_item_id: int
    material_id: str
    material_name: str
    purchased_quantity: Decimal
    already_returned_quantity: Decimal
    eligible_for_return_quantity: Decimal
    rate: Decimal
    batch_number: Optional[str]
    expiry_date: Optional[date]
    days_since_purchase: int
    is_returnable: bool
    return_restrictions: List[str] = []


class CreateReturnFromPurchaseRequest(BaseModel):
    purchase_id: int
    return_date: date
    return_reason: ReturnReasonEnum
    return_items: List[dict] = Field(..., description="Items to return with quantities")
    supplier_credit_note_number: Optional[str] = None
    supplier_credit_note_date: Optional[date] = None
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "purchase_id": 1,
                "return_date": "2025-08-26",
                "return_reason": "Defective",
                "supplier_credit_note_number": "CN-001",
                "supplier_credit_note_date": "2025-08-26",
                "return_items": [
                    {
                        "purchase_item_id": 1,
                        "return_quantity": 10,
                        "return_reason": "Defective",
                        "condition_on_return": "Damaged"
                    }
                ],
                "created_by": "user123"
            }
        }


# Refund Processing
class ProcessRefundRequest(BaseModel):
    return_id: int
    refund_amount: Decimal = Field(..., gt=0, description="Amount to refund")
    refund_mode: RefundModeEnum = Field(..., description="Refund method")
    refund_reference: Optional[str] = None
    refund_date: date = Field(..., description="Refund processing date")
    processed_by: str = Field(..., description="User processing the refund")
    notes: Optional[str] = None
