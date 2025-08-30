from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from .state import StateResponse


class AgentBase(BaseModel):
    agent_name: str = Field(..., max_length=100, description="Agent name")
    address: Optional[str] = Field(None, max_length=255, description="Agent address")
    state_id: Optional[int] = Field(None, description="State ID from states table")
    city: Optional[str] = Field(None, max_length=100, description="City name")
    phone: Optional[str] = Field(None, max_length=15, description="Phone number")
    status: str = Field("Active", max_length=20, description="Agent status")

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


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    agent_name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    state_id: Optional[int] = None
    city: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
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


class AgentResponse(AgentBase):
    id: int
    agent_acc_code: str
    created_at: datetime
    updated_at: datetime
    
    # Include state information if available
    state: Optional[StateResponse] = None

    class Config:
        from_attributes = True


class AgentWithStateResponse(AgentResponse):
    state_name: Optional[str] = None
    state_code: Optional[str] = None
    gst_code: Optional[str] = None
