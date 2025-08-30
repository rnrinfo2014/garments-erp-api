from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from dependencies import get_db, get_current_user
from models.accounts import AccountsMaster
from schemas.accounts import AccountsMasterCreate, AccountsMasterUpdate, AccountsMasterResponse
from models.user import User

router = APIRouter()


@router.get("/", response_model=List[AccountsMasterResponse])
async def get_accounts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accounts with pagination"""
    accounts = db.query(AccountsMaster).offset(skip).limit(limit).all()
    return accounts


@router.get("/{account_code}", response_model=AccountsMasterResponse)
async def get_account(
    account_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific account by account code"""
    account = db.query(AccountsMaster).filter(AccountsMaster.account_code == account_code).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/code/{account_code}", response_model=AccountsMasterResponse)
async def get_account_by_code(
    account_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific account by account code"""
    account = db.query(AccountsMaster).filter(AccountsMaster.account_code == account_code).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/", response_model=AccountsMasterResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountsMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new account"""
    # Check if account code already exists
    existing_account = db.query(AccountsMaster).filter(AccountsMaster.account_code == account.account_code).first()
    if existing_account:
        raise HTTPException(status_code=400, detail="Account code already exists")
    
    # Validate account type
    valid_account_types = ["Asset", "Liability", "Equity", "Income", "Expense"]
    if account.account_type not in valid_account_types:
        raise HTTPException(status_code=400, detail=f"Invalid account type. Must be one of: {', '.join(valid_account_types)}")
    
    # If parent account code is provided, validate it exists
    if account.parent_account_code:
        parent_account = db.query(AccountsMaster).filter(AccountsMaster.account_code == account.parent_account_code).first()
        if not parent_account:
            raise HTTPException(status_code=400, detail="Parent account code does not exist")
    
    db_account = AccountsMaster(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.put("/{account_code}", response_model=AccountsMasterResponse)
async def update_account(
    account_code: str,
    account_update: AccountsMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing account"""
    account = db.query(AccountsMaster).filter(AccountsMaster.account_code == account_code).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Validate account type if provided
    if account_update.account_type:
        valid_account_types = ["Asset", "Liability", "Equity", "Income", "Expense"]
        if account_update.account_type not in valid_account_types:
            raise HTTPException(status_code=400, detail=f"Invalid account type. Must be one of: {', '.join(valid_account_types)}")
    
    # If parent account code is provided, validate it exists
    if account_update.parent_account_code:
        parent_account = db.query(AccountsMaster).filter(AccountsMaster.account_code == account_update.parent_account_code).first()
        if not parent_account:
            raise HTTPException(status_code=400, detail="Parent account code does not exist")
    
    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_code}")
async def delete_account(
    account_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an account (soft delete by setting is_active to False)"""
    account = db.query(AccountsMaster).filter(AccountsMaster.account_code == account_code).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Soft delete by setting is_active to False
    setattr(account, 'is_active', False)
    db.commit()
    return {"message": "Account deactivated successfully"}


@router.get("/type/{account_type}", response_model=List[AccountsMasterResponse])
async def get_accounts_by_type(
    account_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accounts by account type"""
    valid_account_types = ["Asset", "Liability", "Equity", "Income", "Expense"]
    if account_type not in valid_account_types:
        raise HTTPException(status_code=400, detail=f"Invalid account type. Must be one of: {', '.join(valid_account_types)}")
    
    accounts = db.query(AccountsMaster).filter(
        AccountsMaster.account_type == account_type,
        AccountsMaster.is_active == True
    ).all()
    return accounts


@router.get("/active/all", response_model=List[AccountsMasterResponse])
async def get_active_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active accounts"""
    accounts = db.query(AccountsMaster).filter(AccountsMaster.is_active == True).all()
    return accounts


@router.get("/public/count")
async def get_accounts_count(db: Session = Depends(get_db)):
    """Public endpoint to get total accounts count (no auth required)"""
    count = db.query(AccountsMaster).count()
    return {"total_accounts": count, "active_accounts": db.query(AccountsMaster).filter(AccountsMaster.is_active == True).count()}
