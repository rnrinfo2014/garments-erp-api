from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User, UserRole, UserStatus
from auth import verify_token, verify_password
from schemas.user import TokenData

# Security schemes
security = HTTPBearer()
security_basic = HTTPBasic()

def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    username = payload.get("sub")
    if username is None:
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

def get_current_user_basic(
    credentials: HTTPBasicCredentials = Depends(security_basic),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user using Basic Authentication (username/password)."""
    # Find user by username
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Verify password
    if not verify_password(credentials.password, str(user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Check if user is active
    if user.status.value != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return user

def get_current_active_user_basic(current_user: User = Depends(get_current_user_basic)) -> User:
    """Get current active user using Basic Authentication."""
    return current_user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    return current_user

def require_role(required_role: UserRole):
    """Dependency to require specific user role (Token-based auth)."""
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

def require_role_basic(required_role: UserRole):
    """Dependency to require specific user role (Basic auth)."""
    def role_checker(current_user: User = Depends(get_current_active_user_basic)):
        if current_user.role.value == UserRole.SUPERADMIN.value:
            return current_user  # Superadmin can access everything
        
        if current_user.role.value != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Common role dependencies (Token-based)
require_admin = require_role(UserRole.ADMIN)
require_superadmin = require_role(UserRole.SUPERADMIN)

# Common role dependencies (Basic auth)
require_admin_basic = require_role_basic(UserRole.ADMIN)
require_superadmin_basic = require_role_basic(UserRole.SUPERADMIN)
