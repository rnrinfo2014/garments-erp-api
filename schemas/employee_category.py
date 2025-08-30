from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SalaryStructure(str, Enum):
    MONTHLY = "Monthly"
    DAILY = "Daily"
    PIECE_RATE = "Piece-rate"


class EmployeeCategoryBase(BaseModel):
    name: str = Field(..., max_length=100, description="Category name")
    salary_structure: SalaryStructure = Field(..., description="Salary structure type")


class EmployeeCategoryCreate(EmployeeCategoryBase):
    description: Optional[str] = Field(None, description="Optional category description")
    is_active: Optional[bool] = Field(True, description="Whether the category is active")


class EmployeeCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    salary_structure: Optional[SalaryStructure] = None
    description: Optional[str] = Field(None, description="Category description")
    is_active: Optional[bool] = Field(None, description="Whether the category is active")


class EmployeeCategoryResponse(BaseModel):
    id: str = Field(..., description="Auto-generated unique category ID")
    name: str = Field(..., max_length=100, description="Category name")
    salary_structure: SalaryStructure = Field(..., description="Salary structure type")
    description: Optional[str] = Field(None, description="Category description")
    is_active: bool = Field(..., description="Whether the category is active")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
