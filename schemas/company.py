from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from .state import StateResponse

# Request schemas
class CompanyDetailsCreate(BaseModel):
    name: str = Field(..., max_length=255)
    address: Optional[str] = None
    contact: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    gst: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    logo: Optional[str] = Field(None, max_length=500)
    state_id: Optional[int] = None

class CompanyDetailsUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    contact: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    gst: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    logo: Optional[str] = Field(None, max_length=500)
    state_id: Optional[int] = None

# Response schema
class CompanyDetailsResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    contact: Optional[str]
    email: Optional[str]
    gst: Optional[str]
    website: Optional[str]
    logo: Optional[str]
    state_id: Optional[int]
    state: Optional[StateResponse]

    class Config:
        from_attributes = True
