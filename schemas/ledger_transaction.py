from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from enum import Enum


class VoucherType(str, Enum):
    JOURNAL = "JV"
    PAYMENT = "PV"
    RECEIPT = "RV"
    SALES = "SV"
    PURCHASE = "PurchaseV"


class ReferenceType(str, Enum):
    PURCHASE_ORDER = "PURCHASE_ORDER"
    SALE = "SALE"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"
    JOURNAL = "JOURNAL"
    OPENING_BALANCE = "OPENING_BALANCE"
    CLOSING_BALANCE = "CLOSING_BALANCE"
    ADJUSTMENT = "ADJUSTMENT"


class PartyType(str, Enum):
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"
    VENDOR = "VENDOR"
    EMPLOYEE = "EMPLOYEE"
    AGENT = "AGENT"


class TransactionCategory(str, Enum):
    SALES = "SALES"
    PURCHASE = "PURCHASE"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"
    ADJUSTMENT = "ADJUSTMENT"
    OPENING = "OPENING"
    CLOSING = "CLOSING"


# Ledger Transaction Schemas
class LedgerTransactionBase(BaseModel):
    transaction_number: str = Field(..., max_length=50, description="Unique transaction number")
    transaction_date: datetime = Field(..., description="Transaction date")
    account_code: str = Field(..., max_length=20, description="Reference to AccountsMaster")
    description: str = Field(..., max_length=500, description="Transaction description")
    reference_type: Optional[ReferenceType] = Field(None, description="Type of source document")
    reference_id: Optional[str] = Field(None, max_length=50, description="Source document ID")
    debit_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="Debit amount")
    credit_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="Credit amount")
    voucher_type: VoucherType = Field(..., description="Type of voucher")
    voucher_number: Optional[str] = Field(None, max_length=50, description="Voucher number")
    party_type: Optional[PartyType] = Field(None, description="Type of party involved")
    party_id: Optional[str] = Field(None, max_length=50, description="Party ID")
    party_name: Optional[str] = Field(None, max_length=200, description="Party name")
    is_reconciled: bool = Field(default=False, description="Reconciliation status")
    reconciled_date: Optional[datetime] = Field(None, description="Date of reconciliation")
    is_active: bool = Field(default=True, description="Active status")
    is_posted: bool = Field(default=True, description="Posted status")
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator('debit_amount', 'credit_amount')
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError('Amounts cannot be negative')
        return v

    @validator('credit_amount')
    def validate_debit_credit_exclusive(cls, v, values):
        if 'debit_amount' in values:
            debit = values['debit_amount']
            if debit > 0 and v > 0:
                raise ValueError('Either debit_amount or credit_amount should be greater than 0, not both')
            if debit == 0 and v == 0:
                raise ValueError('Either debit_amount or credit_amount must be greater than 0')
        return v


class LedgerTransactionCreate(LedgerTransactionBase):
    created_by: str = Field(..., max_length=50, description="Created by user")


class LedgerTransactionUpdate(BaseModel):
    transaction_date: Optional[datetime] = None
    account_code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    reference_type: Optional[ReferenceType] = None
    reference_id: Optional[str] = Field(None, max_length=50)
    debit_amount: Optional[Decimal] = Field(None, ge=0)
    credit_amount: Optional[Decimal] = Field(None, ge=0)
    voucher_type: Optional[VoucherType] = None
    voucher_number: Optional[str] = Field(None, max_length=50)
    party_type: Optional[PartyType] = None
    party_id: Optional[str] = Field(None, max_length=50)
    party_name: Optional[str] = Field(None, max_length=200)
    is_reconciled: Optional[bool] = None
    reconciled_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_posted: Optional[bool] = None
    notes: Optional[str] = None
    updated_by: Optional[str] = Field(None, max_length=50)


class LedgerTransactionResponse(LedgerTransactionBase):
    id: int
    transaction_amount: Decimal = Field(..., description="Transaction amount (debit or credit)")
    transaction_type: str = Field(..., description="DEBIT or CREDIT")
    balance_effect: Decimal = Field(..., description="Net effect on account balance")
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Transaction Batch Schemas
class TransactionBatchBase(BaseModel):
    batch_number: str = Field(..., max_length=50, description="Unique batch number")
    batch_date: datetime = Field(..., description="Batch date")
    description: str = Field(..., max_length=500, description="Batch description")
    reference_type: Optional[ReferenceType] = Field(None, description="Source of batch")
    reference_id: Optional[str] = Field(None, max_length=50, description="Reference ID")
    total_debit: Decimal = Field(default=Decimal('0.00'), ge=0)
    total_credit: Decimal = Field(default=Decimal('0.00'), ge=0)
    is_balanced: bool = Field(default=False, description="Double-entry balance status")
    is_posted: bool = Field(default=False, description="Posted status")
    is_active: bool = Field(default=True, description="Active status")
    notes: Optional[str] = Field(None, description="Additional notes")


class TransactionBatchCreate(TransactionBatchBase):
    created_by: str = Field(..., max_length=50, description="Created by user")


class TransactionBatchUpdate(BaseModel):
    batch_date: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=500)
    reference_type: Optional[ReferenceType] = None
    reference_id: Optional[str] = Field(None, max_length=50)
    total_debit: Optional[Decimal] = Field(None, ge=0)
    total_credit: Optional[Decimal] = Field(None, ge=0)
    is_balanced: Optional[bool] = None
    is_posted: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    updated_by: Optional[str] = Field(None, max_length=50)


class TransactionBatchResponse(TransactionBatchBase):
    id: int
    is_valid_double_entry: bool = Field(..., description="Whether batch maintains double-entry balance")
    balance_difference: Decimal = Field(..., description="Difference between debit and credit")
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Transaction Template Schemas
class TransactionTemplateBase(BaseModel):
    template_name: str = Field(..., max_length=100, description="Template name")
    template_code: str = Field(..., max_length=20, description="Unique template code")
    description: str = Field(..., max_length=500, description="Template description")
    category: TransactionCategory = Field(..., description="Template category")
    transaction_type: VoucherType = Field(..., description="Transaction type")
    default_debit_account: Optional[str] = Field(None, max_length=20, description="Default debit account")
    default_credit_account: Optional[str] = Field(None, max_length=20, description="Default credit account")
    is_active: bool = Field(default=True, description="Active status")


class TransactionTemplateCreate(TransactionTemplateBase):
    created_by: str = Field(..., max_length=50, description="Created by user")


class TransactionTemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[TransactionCategory] = None
    transaction_type: Optional[VoucherType] = None
    default_debit_account: Optional[str] = Field(None, max_length=20)
    default_credit_account: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class TransactionTemplateResponse(TransactionTemplateBase):
    id: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional Schemas for Reporting and Analytics
class AccountBalanceResponse(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    total_debits: Decimal = Field(...)
    total_credits: Decimal = Field(...)
    net_balance: Decimal = Field(...)
    transaction_count: int
    last_transaction_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class LedgerSummaryResponse(BaseModel):
    account_code: str
    account_name: str
    opening_balance: Decimal = Field(...)
    total_debits: Decimal = Field(...)
    total_credits: Decimal = Field(...)
    closing_balance: Decimal = Field(...)
    period_from: datetime
    period_to: datetime

    class Config:
        from_attributes = True


# Bulk Transaction Schema
class BulkTransactionCreate(BaseModel):
    batch_number: str = Field(..., max_length=50)
    batch_date: datetime
    batch_description: str = Field(..., max_length=500)
    transactions: List[LedgerTransactionCreate] = Field(..., description="At least 2 transactions required for double-entry")
    created_by: str = Field(..., max_length=50)

    @validator('transactions')
    def validate_double_entry(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 transactions required for double-entry bookkeeping')
        
        total_debit = sum(t.debit_amount for t in v)
        total_credit = sum(t.credit_amount for t in v)
        
        if total_debit != total_credit:
            raise ValueError(f'Total debits ({total_debit}) must equal total credits ({total_credit})')
        
        return v
