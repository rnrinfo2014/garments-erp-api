from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CategoryMasterBase(BaseModel):
    category_name: str = Field(..., max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: Optional[bool] = Field(True, description="Active status")

class CategoryMasterCreate(CategoryMasterBase):
    pass

class CategoryMasterUpdate(BaseModel):
    category_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryMasterResponse(CategoryMasterBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CategoryMasterListResponse(BaseModel):
    message: str
    data: list[CategoryMasterResponse]

class CategoryMasterSingleResponse(BaseModel):
    message: str
    data: CategoryMasterResponse
