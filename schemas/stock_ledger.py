from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class StockLedgerBase(BaseModel):
    raw_material_id: str = Field(..., description="Raw Material ID reference")
    size_id: str = Field(..., description="Size ID reference")
    supplier_id: Optional[int] = Field(None, description="Supplier ID reference (NULL for some transactions)")
    transaction_date: date = Field(..., description="Transaction date")
    transaction_type: str = Field(..., description="Type of transaction")
    reference_table: Optional[str] = Field(None, max_length=100, description="Source table for this entry")
    reference_id: Optional[int] = Field(None, description="Primary key from source table")
    qty_in: Decimal = Field(Decimal("0.00"), ge=0, description="Inward quantity")
    qty_out: Decimal = Field(Decimal("0.00"), ge=0, description="Outward quantity") 
    rate: Decimal = Field(Decimal("0.00"), ge=0, description="Rate for this transaction")


class StockLedgerCreate(StockLedgerBase):
    pass


class StockLedgerUpdate(BaseModel):
    raw_material_id: Optional[str] = None
    size_id: Optional[str] = None
    supplier_id: Optional[int] = None
    transaction_date: Optional[date] = None
    transaction_type: Optional[str] = None
    reference_table: Optional[str] = None
    reference_id: Optional[int] = None
    qty_in: Optional[Decimal] = None
    qty_out: Optional[Decimal] = None
    rate: Optional[Decimal] = None


class StockLedgerResponse(StockLedgerBase):
    model_config = ConfigDict(from_attributes=True)
    
    ledger_id: int = Field(..., description="Unique ledger entry ID")
    amount: Decimal = Field(..., description="Computed amount: (QtyIn - QtyOut) * Rate")
    net_quantity: Decimal = Field(..., description="Net quantity: QtyIn - QtyOut")
    created_by: str = Field(..., description="User who created this entry")
    created_at: datetime = Field(..., description="Entry creation timestamp")
    
    # Related data (optional, loaded with joins)
    raw_material: Optional[dict] = None
    size: Optional[dict] = None
    supplier: Optional[dict] = None


class StockLedgerSummary(BaseModel):
    """Summary of stock for a particular raw material"""
    raw_material_id: str
    size_id: str
    raw_material_name: Optional[str] = None
    total_qty_in: Decimal = Field(Decimal("0.00"), description="Total inward quantity")
    total_qty_out: Decimal = Field(Decimal("0.00"), description="Total outward quantity") 
    current_stock: Decimal = Field(Decimal("0.00"), description="Current stock balance")
    last_transaction_date: Optional[date] = None
    avg_rate: Optional[Decimal] = None


class StockMovementFilter(BaseModel):
    """Filter criteria for stock ledger queries"""
    raw_material_id: Optional[str] = None
    supplier_id: Optional[int] = None
    transaction_type: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    reference_table: Optional[str] = None
    reference_id: Optional[int] = None