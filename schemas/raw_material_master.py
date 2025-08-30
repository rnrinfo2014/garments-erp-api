from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class RawMaterialMasterBase(BaseModel):
    material_name: str = Field(..., max_length=100, description="Material name")
    material_code: str = Field(..., max_length=50, description="Material code")
    category_id: str = Field(..., description="Category ID")
    size_id: str = Field(..., description="Size ID")
    unit_id: str = Field(..., description="Unit ID")
    standard_rate: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Standard rate per unit")
    minimum_stock: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Minimum stock level")
    maximum_stock: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Maximum stock level")
    reorder_level: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Reorder level")
    description: Optional[str] = Field(None, description="Material description")
    is_active: Optional[bool] = Field(True, description="Active status")

class RawMaterialMasterCreate(RawMaterialMasterBase):
    pass

class RawMaterialMasterUpdate(BaseModel):
    material_name: Optional[str] = Field(None, max_length=100)
    material_code: Optional[str] = Field(None, max_length=50)
    category_id: Optional[str] = None
    size_id: Optional[str] = None
    unit_id: Optional[str] = None
    standard_rate: Optional[Decimal] = Field(None, ge=0)
    minimum_stock: Optional[Decimal] = Field(None, ge=0)
    maximum_stock: Optional[Decimal] = Field(None, ge=0)
    reorder_level: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class RawMaterialMasterResponse(RawMaterialMasterBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RawMaterialMasterWithDetailsResponse(BaseModel):
    id: str
    material_name: str
    material_code: str
    category_id: str
    size_id: str
    unit_id: str
    standard_rate: Decimal
    minimum_stock: Decimal
    maximum_stock: Decimal
    reorder_level: Decimal
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Related details
    category_name: Optional[str] = None
    size_name: Optional[str] = None
    unit_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class RawMaterialMasterListResponse(BaseModel):
    message: str
    data: list[RawMaterialMasterWithDetailsResponse]

class RawMaterialMasterSingleResponse(BaseModel):
    message: str
    data: RawMaterialMasterWithDetailsResponse
