from pydantic import BaseModel, Field, field_validator, validator, model_validator
from typing import Optional
from datetime import datetime
from enum import Enum
from .state import StateResponse
from .agents import AgentResponse


class CustomerTypeEnum(str, Enum):
    REGISTERED = "Registered"
    UNREGISTERED = "Unregistered"


class CustomerBase(BaseModel):
    customer_name: str = Field(..., max_length=100, description="Customer name")
    customer_type: CustomerTypeEnum = Field(CustomerTypeEnum.UNREGISTERED, description="Customer registration type")
    
    # GST Details
    gst_number: Optional[str] = Field(None, max_length=15, description="GST number (mandatory if registered)")
    
    # Contact Details
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person name")
    phone: Optional[str] = Field(None, max_length=15, description="Phone number")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    
    # Address Details
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, max_length=100, description="City name")
    pincode: Optional[str] = Field(None, max_length=10, description="PIN code")
    
    # Foreign Keys
    state_id: Optional[int] = Field(None, description="State ID")
    agent_id: Optional[int] = Field(None, description="Agent ID")
    
    # Status
    status: str = Field("Active", max_length=20, description="Customer status")

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['Active', 'Inactive', 'Suspended']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, +, -, and spaces')
        return v

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email address')
        return v

    @validator('gst_number')
    def validate_gst_format(cls, v):
        if v:
            # GST format validation (15 characters)
            # Format: 2 digits (state) + 10 alphanumeric (PAN+entity) + 1 digit + 1 alphanumeric + 1 alphanumeric
            if len(v) != 15:
                raise ValueError('GST number must be 15 characters long')
            if not v[:2].isdigit():
                raise ValueError('First 2 characters must be state code (digits)')
            if not v[2:12].isalnum():
                raise ValueError('Characters 3-12 must be alphanumeric (PAN + entity code)')
            if not v[12].isdigit():
                raise ValueError('13th character must be a digit')
            if not v[13:15].isalnum():
                raise ValueError('Last 2 characters must be alphanumeric')
        return v

    @model_validator(mode='after')
    def validate_gst_requirement(cls, model):
        customer_type = model.customer_type
        gst_number = model.gst_number
        
        if customer_type == CustomerTypeEnum.REGISTERED and not gst_number:
            raise ValueError('GST number is mandatory for registered customers')
        
        if customer_type == CustomerTypeEnum.UNREGISTERED and gst_number:
            raise ValueError('GST number should not be provided for unregistered customers')
            
        return model


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, max_length=100)
    customer_type: Optional[CustomerTypeEnum] = None
    gst_number: Optional[str] = Field(None, max_length=15)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    state_id: Optional[int] = None
    agent_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=20)

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['Active', 'Inactive', 'Suspended']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, +, -, and spaces')
        return v

    @field_validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email address')
        return v

    @field_validator('gst_number')
    def validate_gst_format(cls, v):
        if v:
            # GST format validation (15 characters)
            # Format: 2 digits (state) + 10 alphanumeric (PAN+entity) + 1 digit + 1 alphanumeric + 1 alphanumeric
            if len(v) != 15:
                raise ValueError('GST number must be 15 characters long')
            if not v[:2].isdigit():
                raise ValueError('First 2 characters must be state code (digits)')
            if not v[2:12].isalnum():
                raise ValueError('Characters 3-12 must be alphanumeric (PAN + entity code)')
            if not v[12].isdigit():
                raise ValueError('13th character must be a digit')
            if not v[13:15].isalnum():
                raise ValueError('Last 2 characters must be alphanumeric')
        return v


class CustomerResponse(CustomerBase):
    id: int
    customer_acc_code: str
    created_at: datetime
    updated_at: datetime
    
    # Include related data
    state: Optional[StateResponse] = None
    agent: Optional[AgentResponse] = None

    class Config:
        from_attributes = True


class CustomerWithDetailsResponse(CustomerResponse):
    state_name: Optional[str] = None
    state_code: Optional[str] = None
    gst_code: Optional[str] = None
    agent_name: Optional[str] = None
    agent_acc_code: Optional[str] = None
