from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class AccountsMasterBase(BaseModel):
    account_code: str = Field(..., max_length=20, description="Unique account code")
    account_name: str = Field(..., max_length=100, description="Account name")
    account_type: str = Field(..., max_length=50, description="Account type (Asset, Liability, Equity, Income, Expense)")
    parent_account_code: Optional[str] = Field(None, max_length=20, description="Parent account code for hierarchical structure")
    is_active: bool = Field(True, description="Whether the account is active")
    opening_balance: Decimal = Field(Decimal('0.00'), description="Opening balance")
    current_balance: Decimal = Field(Decimal('0.00'), description="Current balance")
    description: Optional[str] = Field(None, max_length=255, description="Account description")


class AccountsMasterCreate(AccountsMasterBase):
    pass


class AccountsMasterUpdate(BaseModel):
    account_name: Optional[str] = Field(None, max_length=100)
    account_type: Optional[str] = Field(None, max_length=50)
    parent_account_code: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    opening_balance: Optional[Decimal] = None
    current_balance: Optional[Decimal] = None
    description: Optional[str] = Field(None, max_length=255)


class AccountsMasterResponse(AccountsMasterBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
