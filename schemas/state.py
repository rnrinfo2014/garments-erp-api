from pydantic import BaseModel, Field
from typing import Optional

# Request schemas
class StateCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=10)
    gst_code: str = Field(..., max_length=2)

class StateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=10)
    gst_code: Optional[str] = Field(None, max_length=2)

# Response schema
class StateResponse(BaseModel):
    id: int
    name: str
    code: str
    gst_code: str

    class Config:
        from_attributes = True
