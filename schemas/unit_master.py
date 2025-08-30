from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UnitMasterBase(BaseModel):
    unit_name: str = Field(..., max_length=100, description="Unit name")
    unit_code: str = Field(..., max_length=20, description="Unit code")
    description: Optional[str] = Field(None, description="Unit description")
    is_active: Optional[bool] = Field(True, description="Active status")

class UnitMasterCreate(UnitMasterBase):
    pass

class UnitMasterUpdate(BaseModel):
    unit_name: Optional[str] = Field(None, max_length=100)
    unit_code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class UnitMasterResponse(UnitMasterBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UnitMasterListResponse(BaseModel):
    message: str
    data: list[UnitMasterResponse]

class UnitMasterSingleResponse(BaseModel):
    message: str
    data: UnitMasterResponse
