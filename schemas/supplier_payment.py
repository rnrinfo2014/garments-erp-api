from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class PaymentStatusEnum(str, Enum):
    DRAFT = "Draft"
    POSTED = "Posted"
    CANCELLED = "Cancelled"


class PaymentModeEnum(str, Enum):
    CASH = "Cash"
    BANK_TRANSFER = "Bank Transfer"
    CHEQUE = "Cheque"
    DEMAND_DRAFT = "Demand Draft"
    ONLINE_TRANSFER = "Online Transfer"
    UPI = "UPI"
    RTGS = "RTGS"
    NEFT = "NEFT"
    CREDIT_CARD = "Credit Card"


class PaymentTypeEnum(str, Enum):
    ADVANCE = "Advance"
    AGAINST_BILL = "Against Bill"
    ON_ACCOUNT = "On Account"


class TDSSectionEnum(str, Enum):
    SECTION_194C = "194C"  # Payments to contractors
    SECTION_194J = "194J"  # Professional fees
    SECTION_194I = "194I"  # Rent payments
    SECTION_194H = "194H"  # Commission/Brokerage
    SECTION_194A = "194A"  # Interest payments
    SECTION_195 = "195"    # Non-resident payments


# Supplier Payment Bill Schemas
class SupplierPaymentBillBase(BaseModel):
    purchase_id: int = Field(..., description="Purchase bill ID")
    bill_amount: Decimal = Field(..., ge=0.01, description="Original bill amount")
    outstanding_amount: Decimal = Field(..., ge=0, description="Outstanding amount before payment")
    paid_amount: Decimal = Field(..., ge=0, description="Amount to pay in this transaction")
    discount_allowed: Decimal = Field(default=Decimal('0.00'), ge=0, description="Discount allowed on this bill")
    adjustment_amount: Decimal = Field(default=Decimal('0.00'), description="Adjustment amount (+ve or -ve)")
    remarks: Optional[str] = None

    @validator('paid_amount')
    def validate_paid_amount(cls, v, values):
        outstanding = values.get('outstanding_amount', Decimal('0'))
        if v > outstanding:
            raise ValueError('Paid amount cannot exceed outstanding amount')
        return v


class SupplierPaymentBillCreate(SupplierPaymentBillBase):
    pass


class SupplierPaymentBillUpdate(BaseModel):
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    discount_allowed: Optional[Decimal] = Field(None, ge=0)
    adjustment_amount: Optional[Decimal] = None
    remarks: Optional[str] = None


class SupplierPaymentBillResponse(SupplierPaymentBillBase):
    id: int
    payment_id: int
    purchase_number: Optional[str]
    bill_date: Optional[date]
    previous_payments: Decimal
    balance_amount: Decimal
    is_fully_paid: bool
    payment_percentage: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# TDS Entry Schemas
class TDSEntryBase(BaseModel):
    tds_section: TDSSectionEnum = Field(..., description="TDS section")
    tds_rate: Decimal = Field(..., ge=0, le=30, description="TDS rate percentage")
    gross_amount: Decimal = Field(..., ge=0.01, description="Gross amount on which TDS calculated")
    certificate_number: Optional[str] = None
    certificate_date: Optional[date] = None
    challan_number: Optional[str] = None
    challan_date: Optional[date] = None


class TDSEntryCreate(TDSEntryBase):
    pass


class TDSEntryResponse(TDSEntryBase):
    id: int
    financial_year: str
    quarter: str
    payment_id: int
    supplier_id: int
    tds_amount: Decimal
    is_certificate_issued: bool
    is_deposited: bool
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Supplier Payment Schemas
class SupplierPaymentBase(BaseModel):
    payment_date: date = Field(..., description="Payment date")
    supplier_id: int = Field(..., description="Supplier ID")
    payment_type: PaymentTypeEnum = PaymentTypeEnum.AGAINST_BILL
    payment_mode: PaymentModeEnum = Field(..., description="Payment method")
    gross_amount: Decimal = Field(..., ge=0.01, description="Total gross amount")
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="Discount given")
    tds_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="TDS deducted")
    other_deductions: Decimal = Field(default=Decimal('0.00'), ge=0, description="Other deductions")
    
    # Payment mode specific fields
    bank_account_id: Optional[str] = Field(None, description="Our bank account code")
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    transaction_reference: Optional[str] = None
    
    # TDS details
    tds_rate: Decimal = Field(default=Decimal('0.00'), ge=0, le=30)
    tds_section: Optional[TDSSectionEnum] = None
    
    # Additional fields
    narration: Optional[str] = None
    remarks: Optional[str] = None

    @validator('cheque_date')
    def validate_cheque_details(cls, v, values):
        payment_mode = values.get('payment_mode')
        cheque_number = values.get('cheque_number')
        
        if payment_mode == PaymentModeEnum.CHEQUE:
            if not cheque_number:
                raise ValueError('Cheque number is required for cheque payments')
            if not v:
                raise ValueError('Cheque date is required for cheque payments')
        
        return v

    @validator('transaction_reference')
    def validate_transaction_reference(cls, v, values):
        payment_mode = values.get('payment_mode')
        
        if payment_mode in [PaymentModeEnum.UPI, PaymentModeEnum.ONLINE_TRANSFER, PaymentModeEnum.RTGS, PaymentModeEnum.NEFT]:
            if not v:
                raise ValueError(f'Transaction reference is required for {payment_mode.value} payments')
        
        return v

    @validator('tds_section')
    def validate_tds_section(cls, v, values):
        tds_amount = values.get('tds_amount', Decimal('0'))
        
        if tds_amount > 0 and not v:
            raise ValueError('TDS section is required when TDS amount is specified')
        
        return v


class SupplierPaymentCreate(SupplierPaymentBase):
    bills: List[SupplierPaymentBillCreate] = Field(..., description="Bills to pay")
    created_by: str = Field(..., description="User who created the payment")

    @validator('bills')
    def validate_bills(cls, v, values):
        if not v and values.get('payment_type') == PaymentTypeEnum.AGAINST_BILL:
            raise ValueError('At least one bill is required for bill payments')
        
        # Calculate total paid amount from bills
        total_bill_amount = sum(bill.paid_amount for bill in v)
        net_amount = values.get('gross_amount', Decimal('0')) - values.get('discount_amount', Decimal('0')) - values.get('tds_amount', Decimal('0')) - values.get('other_deductions', Decimal('0'))
        
        if abs(total_bill_amount - net_amount) > Decimal('0.01'):  # Allow small rounding differences
            raise ValueError('Total bill payments must match net payment amount')
        
        return v


class SupplierPaymentUpdate(BaseModel):
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tds_amount: Optional[Decimal] = Field(None, ge=0)
    other_deductions: Optional[Decimal] = Field(None, ge=0)
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    transaction_reference: Optional[str] = None
    tds_rate: Optional[Decimal] = Field(None, ge=0, le=30)
    tds_section: Optional[TDSSectionEnum] = None
    narration: Optional[str] = None
    remarks: Optional[str] = None
    updated_by: str = Field(..., description="User who updated the payment")


class SupplierPaymentResponse(SupplierPaymentBase):
    id: int
    payment_number: str
    status: PaymentStatusEnum
    net_amount: Decimal
    ledger_batch_id: Optional[int]
    is_ledger_posted: bool
    is_reconciled: bool
    reconciled_date: Optional[date]
    reconciled_by: Optional[str]
    created_by: str
    updated_by: Optional[str]
    posted_by: Optional[str]
    posted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    calculated_net_amount: Decimal
    total_bill_amount: Decimal
    payment_method_display: str
    
    # Related data
    bills: List[SupplierPaymentBillResponse] = []
    
    class Config:
        from_attributes = True


class SupplierPaymentListResponse(BaseModel):
    id: int
    payment_number: str
    payment_date: date
    supplier_id: int
    payment_type: PaymentTypeEnum
    payment_mode: PaymentModeEnum
    gross_amount: Decimal
    net_amount: Decimal
    status: PaymentStatusEnum
    is_ledger_posted: bool
    is_reconciled: bool
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Supplier Ledger Schemas
class SupplierLedgerResponse(BaseModel):
    id: int
    supplier_id: int
    transaction_date: date
    transaction_type: str
    reference_type: Optional[str]
    reference_id: Optional[int]
    reference_number: Optional[str]
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal
    balance_type: str
    description: str
    is_reconciled: bool
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Payment Operations
class PaymentPostRequest(BaseModel):
    payment_id: int
    post_to_ledger: bool = Field(default=True, description="Create ledger transactions")
    posted_by: str = Field(..., description="User posting the payment")


class PaymentReconciliationRequest(BaseModel):
    payment_id: int
    reconciled: bool = Field(..., description="Mark as reconciled or unreconciled")
    reconciled_by: str = Field(..., description="User performing reconciliation")
    reconciliation_date: date = Field(..., description="Reconciliation date")


# Bulk Operations
class BulkSupplierPaymentCreate(BaseModel):
    payments: List[SupplierPaymentCreate] = Field(..., description="List of payments to create")
    created_by: str = Field(..., description="User creating bulk payments")

    @validator('payments')
    def validate_payments(cls, v):
        if not v:
            raise ValueError('At least one payment is required')
        return v


# Reports and Analytics
class SupplierPaymentSummaryResponse(BaseModel):
    total_payments: int
    total_amount: Decimal
    total_tds: Decimal
    cash_payments: Decimal
    bank_payments: Decimal
    pending_reconciliation: int
    draft_payments: int
    posted_payments: int


class SupplierOutstandingResponse(BaseModel):
    supplier_id: int
    supplier_name: str
    total_purchases: Decimal
    total_payments: Decimal
    outstanding_amount: Decimal
    overdue_amount: Decimal
    days_outstanding: int
    last_payment_date: Optional[date]


class TDSSummaryResponse(BaseModel):
    financial_year: str
    quarter: str
    total_tds: Decimal
    total_suppliers: int
    certificates_issued: int
    certificates_pending: int
    deposited_amount: Decimal
    pending_deposit: Decimal


# Outstanding Bills for Payment
class OutstandingBillResponse(BaseModel):
    purchase_id: int
    purchase_number: str
    purchase_date: date
    bill_amount: Decimal
    payments_made: Decimal
    outstanding_amount: Decimal
    days_outstanding: int
    supplier_invoice_number: Optional[str]
    is_overdue: bool


class GetOutstandingBillsRequest(BaseModel):
    supplier_id: int
    as_of_date: Optional[date] = None
    include_advance_adjustable: bool = Field(default=False, description="Include advance payments for adjustment")


# Payment against specific bills
class PayAgainstBillsRequest(BaseModel):
    supplier_id: int
    payment_date: date
    payment_mode: PaymentModeEnum
    selected_bills: List[dict] = Field(..., description="Bills with payment amounts")
    bank_account_id: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    transaction_reference: Optional[str] = None
    tds_rate: Decimal = Field(default=Decimal('0.00'), ge=0, le=30)
    tds_section: Optional[TDSSectionEnum] = None
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "supplier_id": 1,
                "payment_date": "2025-08-26",
                "payment_mode": "Bank Transfer",
                "selected_bills": [
                    {
                        "purchase_id": 1,
                        "outstanding_amount": 10000.00,
                        "paying_amount": 9500.00,
                        "discount_allowed": 500.00
                    },
                    {
                        "purchase_id": 2,
                        "outstanding_amount": 5000.00,
                        "paying_amount": 5000.00,
                        "discount_allowed": 0.00
                    }
                ],
                "bank_account_id": "BANK001",
                "transaction_reference": "TXN123456789",
                "tds_rate": 2.00,
                "tds_section": "194C",
                "created_by": "user123"
            }
        }
