from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from database import get_db
from models.size_master import SizeMaster
from schemas.size_master import (
    SizeMasterCreate,
    SizeMasterUpdate,
    SizeMasterResponse,
    SizeMasterListResponse,
    SizeMasterSingleResponse
)
from dependencies import get_current_active_user, require_admin
from models.user import User

router = APIRouter()

def generate_size_id(db: Session) -> str:
    """Generate unique size ID in format SIZ001, SIZ002, etc."""
    last_size = db.query(SizeMaster).order_by(SizeMaster.id.desc()).first()
    
    if not last_size:
        return "SIZ001"
    
    try:
        # Access the actual string value from the SQLAlchemy model
        size_id_str = str(last_size.id)
        last_number = int(size_id_str[3:])  # Remove "SIZ" prefix
        new_number = last_number + 1
        return f"SIZ{new_number:03d}"
    except (ValueError, IndexError):
        return f"SIZ{db.query(SizeMaster).count() + 1:03d}"

@router.get("/", response_model=SizeMasterListResponse)
def get_sizes(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all sizes with optional filtering"""
    query = db.query(SizeMaster)
    
    if is_active is not None:
        query = query.filter(SizeMaster.is_active == is_active)
    
    sizes = query.offset(skip).limit(limit).all()
    
    return {
        "message": "Sizes retrieved successfully",
        "data": sizes
    }

@router.get("/search/{search_term}", response_model=SizeMasterListResponse)
def search_sizes(
    search_term: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search sizes by name, code or description"""
    sizes = db.query(SizeMaster).filter(
        or_(
            SizeMaster.size_name.ilike(f"%{search_term}%"),
            SizeMaster.size_code.ilike(f"%{search_term}%"),
            SizeMaster.description.ilike(f"%{search_term}%")
        )
    ).all()
    
    return {
        "message": f"Search results for '{search_term}'",
        "data": sizes
    }

@router.get("/{size_id}", response_model=SizeMasterSingleResponse)
def get_size(
    size_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get size by ID"""
    size = db.query(SizeMaster).filter(SizeMaster.id == size_id).first()
    
    if not size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Size not found"
        )
    
    return {
        "message": "Size retrieved successfully",
        "data": size
    }

@router.post("/", response_model=SizeMasterSingleResponse, status_code=status.HTTP_201_CREATED)
def create_size(
    size: SizeMasterCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new size (Admin only)"""
    
    # Check if size name or code already exists
    existing_size = db.query(SizeMaster).filter(
        or_(
            SizeMaster.size_name == size.size_name,
            SizeMaster.size_code == size.size_code
        )
    ).first()
    
    if existing_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Size name or code already exists"
        )
    
    # Generate unique ID
    new_id = generate_size_id(db)
    
    # Create new size
    db_size = SizeMaster(
        id=new_id,
        **size.model_dump()
    )
    
    db.add(db_size)
    db.commit()
    db.refresh(db_size)
    
    return {
        "message": "Size created successfully",
        "data": db_size
    }

@router.put("/{size_id}", response_model=SizeMasterSingleResponse)
def update_size(
    size_id: str,
    size_update: SizeMasterUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update size (Admin only)"""
    
    db_size = db.query(SizeMaster).filter(SizeMaster.id == size_id).first()
    
    if not db_size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Size not found"
        )
    
    # Check if new name or code conflicts with existing size
    if (size_update.size_name or size_update.size_code):
        filter_conditions = []
        if size_update.size_name:
            filter_conditions.append(SizeMaster.size_name == size_update.size_name)
        if size_update.size_code:
            filter_conditions.append(SizeMaster.size_code == size_update.size_code)
        
        if filter_conditions:
            existing_size = db.query(SizeMaster).filter(
                SizeMaster.id != size_id,
                or_(*filter_conditions)
            ).first()
            
            if existing_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Size name or code already exists"
                )
    
    # Update fields
    update_data = size_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_size, field, value)
    
    db.commit()
    db.refresh(db_size)
    
    return {
        "message": "Size updated successfully",
        "data": db_size
    }

@router.delete("/{size_id}")
def delete_size(
    size_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate size (Admin only)"""
    
    db_size = db.query(SizeMaster).filter(SizeMaster.id == size_id).first()
    
    if not db_size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Size not found"
        )
    
    # Soft delete by setting is_active to False
    setattr(db_size, 'is_active', False)
    db.commit()
    
    return {
        "message": "Size deactivated successfully"
    }
