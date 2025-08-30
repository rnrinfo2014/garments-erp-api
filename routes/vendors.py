from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from dependencies import get_current_active_user, require_admin
from models.vendors import VendorMaster
from models.accounts import AccountsMaster
from models.user import User
from schemas.vendors import VendorMasterCreate, VendorMasterUpdate, VendorMasterResponse
from decimal import Decimal

router = APIRouter()


def generate_vendor_account_code(db: Session, vendor_name: str) -> str:
    """Generate a unique account code for vendor payable account."""
    base_code = "2107"  # Vendor payables base code
    
    # Find the next available account code
    counter = 1
    while True:
        acc_code = f"{base_code}{counter:03d}"
        existing = db.query(AccountsMaster).filter(AccountsMaster.account_code == acc_code).first()
        if not existing:
            return acc_code
        counter += 1


def create_vendor_account(db: Session, vendor_name: str, company_name: str) -> str:
    """Create a payable account for the vendor."""
    acc_code = generate_vendor_account_code(db, vendor_name)
    
    # Create the account record
    account = AccountsMaster(
        account_code=acc_code,
        account_name=f"Vendor - {vendor_name}",
        account_type="Liability",
        parent_account_code="2107",  # Vendor Payables parent
        is_active=True,
        opening_balance=Decimal('0.00'),
        current_balance=Decimal('0.00'),
        description=f"Payable account for vendor {company_name}"
    )
    
    db.add(account)
    db.flush()  # Ensure the account is created
    return acc_code


@router.get("/", response_model=List[VendorMasterResponse])
def get_vendors(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all vendors with optional filtering by status. Requires authentication."""
    query = db.query(VendorMaster)
    
    if status:
        query = query.filter(VendorMaster.status == status)
    
    vendors = query.offset(skip).limit(limit).all()
    return vendors


@router.get("/{vendor_id}", response_model=VendorMasterResponse)
def get_vendor(vendor_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get a specific vendor by ID. Requires authentication."""
    vendor = db.query(VendorMaster).filter(VendorMaster.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.post("/", response_model=VendorMasterResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(vendor_data: VendorMasterCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Create a new vendor and automatically create associated payable account. Requires admin privileges."""
    
    # Check if vendor ID already exists
    existing_vendor = db.query(VendorMaster).filter(VendorMaster.id == vendor_data.id).first()
    if existing_vendor:
        raise HTTPException(status_code=400, detail="Vendor ID already exists")
    
    try:
        # Create associated payable account first
        acc_code = create_vendor_account(db, vendor_data.name, vendor_data.company_name)
        
        # Create vendor record with account code
        vendor_dict = vendor_data.model_dump()
        vendor_dict['acc_code'] = acc_code  # Add the generated account code
        db_vendor = VendorMaster(**vendor_dict)
        
        db.add(db_vendor)
        db.commit()
        db.refresh(db_vendor)
        
        return db_vendor
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create vendor account: {str(e)}")


@router.put("/{vendor_id}", response_model=VendorMasterResponse)
def update_vendor(vendor_id: str, vendor_data: VendorMasterUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Update a vendor. Requires admin privileges."""
    vendor = db.query(VendorMaster).filter(VendorMaster.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Update only provided fields
    update_data = vendor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)
    
    # If name is updated, also update the associated account name
    if 'name' in update_data and getattr(vendor, 'acc_code', None):
        account = db.query(AccountsMaster).filter(AccountsMaster.account_code == getattr(vendor, 'acc_code')).first()
        if account:
            setattr(account, 'account_name', f"Vendor - {getattr(vendor, 'name')}")
    
    try:
        db.commit()
        db.refresh(vendor)
        return vendor
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update vendor: {str(e)}")


@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: str, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Delete a vendor (soft delete by setting status to Inactive). Requires admin privileges."""
    vendor = db.query(VendorMaster).filter(VendorMaster.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Soft delete - set status to Inactive
    setattr(vendor, 'status', 'Inactive')
    
    # Also deactivate the associated account
    if getattr(vendor, 'acc_code', None):
        account = db.query(AccountsMaster).filter(AccountsMaster.account_code == getattr(vendor, 'acc_code')).first()
        if account:
            setattr(account, 'is_active', False)
    
    try:
        db.commit()
        return {"message": "Vendor deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to deactivate vendor: {str(e)}")


@router.get("/status/{status_filter}", response_model=List[VendorMasterResponse])
def get_vendors_by_status(status_filter: str, db: Session = Depends(get_db)):
    """Get vendors filtered by status."""
    vendors = db.query(VendorMaster).filter(VendorMaster.status == status_filter).all()
    return vendors


@router.get("/account/{vendor_id}")
def get_vendor_account(vendor_id: str, db: Session = Depends(get_db)):
    """Get the associated account details for a vendor."""
    vendor = db.query(VendorMaster).filter(VendorMaster.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if not getattr(vendor, 'acc_code', None):
        raise HTTPException(status_code=404, detail="No account associated with this vendor")
    
    account = db.query(AccountsMaster).filter(AccountsMaster.account_code == getattr(vendor, 'acc_code')).first()
    if not account:
        raise HTTPException(status_code=404, detail="Associated account not found")
    
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "account_code": account.account_code,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "current_balance": account.current_balance,
        "is_active": account.is_active
    }
