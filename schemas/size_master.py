from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SizeMasterBase(BaseModel):
    size_name: str = Field(..., max_length=100, description="Size name")
    size_code: str = Field(..., max_length=20, description="Size code")
    description: Optional[str] = Field(None, description="Size description")
    is_active: Optional[bool] = Field(True, description="Active status")

class SizeMasterCreate(SizeMasterBase):
    pass

class SizeMasterUpdate(BaseModel):
    size_name: Optional[str] = Field(None, max_length=100)
    size_code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SizeMasterResponse(SizeMasterBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SizeMasterListResponse(BaseModel):
    message: str
    data: list[SizeMasterResponse]

class SizeMasterSingleResponse(BaseModel):
    message: str
    data: SizeMasterResponse
