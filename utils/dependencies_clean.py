from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User, UserRole, UserStatus
from auth import verify_token
from schemas.user import TokenData

# Security schemes - Only JWT Bearer token
security = HTTPBearer()

def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user using JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if user.status.value != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active"
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user."""
    if current_user.status.value != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user

def require_role(required_role: UserRole):
    """Dependency to require specific user role."""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role.value == UserRole.SUPERADMIN.value:
            return current_user  # Superadmin can access everything
        
        if current_user.role.value != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Common role dependencies
require_admin = require_role(UserRole.ADMIN)
require_superadmin = require_role(UserRole.SUPERADMIN)
