from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EmployeeStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class EmployeeBase(BaseModel):
    name: str = Field(..., max_length=100, description="Employee name")
    category_id: str = Field(..., max_length=50, description="Employee category ID")
    join_date: datetime = Field(..., description="Date of joining")
    phone: str = Field(..., max_length=15, description="Phone number")
    address: str = Field(..., description="Employee address")
    base_rate: float = Field(..., ge=0, description="Employee base salary/rate")
    status: EmployeeStatus = Field(EmployeeStatus.ACTIVE, description="Employee status")
    photo_url: Optional[str] = Field(None, max_length=255, description="Photo URL (optional)")


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    category_id: Optional[str] = Field(None, max_length=50)
    join_date: Optional[datetime] = None
    phone: Optional[str] = Field(None, max_length=15)
    address: Optional[str] = None
    base_rate: Optional[float] = Field(None, ge=0, description="Employee base salary/rate")
    status: Optional[EmployeeStatus] = None
    photo_url: Optional[str] = Field(None, max_length=255)


class EmployeeResponse(BaseModel):
    id: str = Field(..., description="Auto-generated unique employee ID")
    employee_id: str = Field(..., description="Auto-generated employee ID number")
    name: str = Field(..., max_length=100, description="Employee name")
    category_id: str = Field(..., max_length=50, description="Employee category ID")
    join_date: datetime = Field(..., description="Date of joining")
    phone: str = Field(..., max_length=15, description="Phone number")
    address: str = Field(..., description="Employee address")
    base_rate: float = Field(..., ge=0, description="Employee base salary/rate")
    status: EmployeeStatus = Field(..., description="Employee status")
    photo_url: Optional[str] = Field(None, max_length=255, description="Photo URL (optional)")
    acc_code: str = Field(..., description="Associated account code")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeWithCategoryResponse(EmployeeResponse):
    category_name: Optional[str] = Field(None, description="Category name")
    salary_structure: Optional[str] = Field(None, description="Salary structure")
    base_rate: Optional[float] = Field(None, description="Base rate")

    class Config:
        from_attributes = True
