from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from database import get_db
from models.unit_master import UnitMaster
from schemas.unit_master import (
    UnitMasterCreate,
    UnitMasterUpdate,
    UnitMasterResponse,
    UnitMasterListResponse,
    UnitMasterSingleResponse
)
from dependencies import get_current_active_user, require_admin
from models.user import User

router = APIRouter()

def generate_unit_id(db: Session) -> str:
    """Generate unique unit ID in format UNT001, UNT002, etc."""
    last_unit = db.query(UnitMaster).order_by(UnitMaster.id.desc()).first()
    
    if not last_unit:
        return "UNT001"
    
    try:
        last_number = int(str(last_unit.id)[3:])  # Remove "UNT" prefix
        new_number = last_number + 1
        return f"UNT{new_number:03d}"
    except (ValueError, IndexError):
        return f"UNT{db.query(UnitMaster).count() + 1:03d}"

@router.get("/", response_model=UnitMasterListResponse)
def get_units(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all units with optional filtering"""
    query = db.query(UnitMaster)
    
    if is_active is not None:
        query = query.filter(UnitMaster.is_active == is_active)
    
    units = query.offset(skip).limit(limit).all()
    
    return {
        "message": "Units retrieved successfully",
        "data": units
    }

@router.get("/search/{search_term}", response_model=UnitMasterListResponse)
def search_units(
    search_term: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search units by name, code or description"""
    units = db.query(UnitMaster).filter(
        or_(
            UnitMaster.unit_name.ilike(f"%{search_term}%"),
            UnitMaster.unit_code.ilike(f"%{search_term}%"),
            UnitMaster.description.ilike(f"%{search_term}%")
        )
    ).all()
    
    return {
        "message": f"Search results for '{search_term}'",
        "data": units
    }

@router.get("/{unit_id}", response_model=UnitMasterSingleResponse)
def get_unit(
    unit_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get unit by ID"""
    unit = db.query(UnitMaster).filter(UnitMaster.id == unit_id).first()
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    return {
        "message": "Unit retrieved successfully",
        "data": unit
    }

@router.post("/", response_model=UnitMasterSingleResponse, status_code=status.HTTP_201_CREATED)
def create_unit(
    unit: UnitMasterCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new unit (Admin only)"""
    
    # Check if unit name or code already exists
    existing_unit = db.query(UnitMaster).filter(
        or_(
            UnitMaster.unit_name == unit.unit_name,
            UnitMaster.unit_code == unit.unit_code
        )
    ).first()
    
    if existing_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit name or code already exists"
        )
    
    # Generate unique ID
    new_id = generate_unit_id(db)
    
    # Create new unit
    db_unit = UnitMaster(
        id=new_id,
        **unit.model_dump()
    )
    
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    
    return {
        "message": "Unit created successfully",
        "data": db_unit
    }

@router.put("/{unit_id}", response_model=UnitMasterSingleResponse)
def update_unit(
    unit_id: str,
    unit_update: UnitMasterUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update unit (Admin only)"""
    
    db_unit = db.query(UnitMaster).filter(UnitMaster.id == unit_id).first()
    
    if not db_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    # Check if new name or code conflicts with existing unit
    if unit_update.unit_name or unit_update.unit_code:
        conditions = []
        if unit_update.unit_name:
            conditions.append(UnitMaster.unit_name == unit_update.unit_name)
        if unit_update.unit_code:
            conditions.append(UnitMaster.unit_code == unit_update.unit_code)
            
        existing_unit = db.query(UnitMaster).filter(
            UnitMaster.id != unit_id,
            or_(*conditions)
        ).first()
        
        if existing_unit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unit name or code already exists"
            )
    
    # Update fields
    update_data = unit_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_unit, field, value)
    
    db.commit()
    db.refresh(db_unit)
    
    return {
        "message": "Unit updated successfully",
        "data": db_unit
    }

@router.delete("/{unit_id}")
def delete_unit(
    unit_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate unit (Admin only)"""
    
    db_unit = db.query(UnitMaster).filter(UnitMaster.id == unit_id).first()
    
    if not db_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    # Soft delete by setting is_active to False
    setattr(db_unit, 'is_active', False)
    db.commit()
    
    return {
        "message": "Unit deactivated successfully"
    }
