from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.user import UserRole, UserStatus

# Request schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")
    confirm_password: str = Field(..., min_length=6, description="Confirm new password")

class LogoutResponse(BaseModel):
    message: str
    logged_out_at: datetime

# Response schemas
class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
