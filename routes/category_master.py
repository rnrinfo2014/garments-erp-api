from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from database import get_db
from models.category_master import CategoryMaster
from schemas.category_master import (
    CategoryMasterCreate,
    CategoryMasterUpdate,
    CategoryMasterResponse,
    CategoryMasterListResponse,
    CategoryMasterSingleResponse
)
from dependencies import get_current_active_user, require_admin
from models.user import User

router = APIRouter()

def generate_category_id(db: Session) -> str:
    """Generate unique category ID in format CAT001, CAT002, etc."""
    last_category = db.query(CategoryMaster).order_by(CategoryMaster.id.desc()).first()
    
    if not last_category:
        return "CAT001"
    
    try:
        # Access the actual string value from the SQLAlchemy model
        category_id_str = str(last_category.id)
        last_number = int(category_id_str[3:])  # Remove "CAT" prefix
        new_number = last_number + 1
        return f"CAT{new_number:03d}"
    except (ValueError, IndexError):
        return f"CAT{db.query(CategoryMaster).count() + 1:03d}"

@router.get("/", response_model=CategoryMasterListResponse)
def get_categories(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all categories with optional filtering"""
    query = db.query(CategoryMaster)
    
    if is_active is not None:
        query = query.filter(CategoryMaster.is_active == is_active)
    
    categories = query.offset(skip).limit(limit).all()
    
    return {
        "message": "Categories retrieved successfully",
        "data": categories
    }

@router.get("/search/{search_term}", response_model=CategoryMasterListResponse)
def search_categories(
    search_term: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search categories by name or description"""
    categories = db.query(CategoryMaster).filter(
        or_(
            CategoryMaster.category_name.ilike(f"%{search_term}%"),
            CategoryMaster.description.ilike(f"%{search_term}%")
        )
    ).all()
    
    return {
        "message": f"Search results for '{search_term}'",
        "data": categories
    }

@router.get("/{category_id}", response_model=CategoryMasterSingleResponse)
def get_category(
    category_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get category by ID"""
    category = db.query(CategoryMaster).filter(CategoryMaster.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return {
        "message": "Category retrieved successfully",
        "data": category
    }

@router.post("/", response_model=CategoryMasterSingleResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryMasterCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new category (Admin only)"""
    
    # Check if category name already exists
    existing_category = db.query(CategoryMaster).filter(
        CategoryMaster.category_name == category.category_name
    ).first()
    
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists"
        )
    
    # Generate unique ID
    new_id = generate_category_id(db)
    
    # Create new category
    db_category = CategoryMaster(
        id=new_id,
        **category.model_dump()
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return {
        "message": "Category created successfully",
        "data": db_category
    }

@router.put("/{category_id}", response_model=CategoryMasterSingleResponse)
def update_category(
    category_id: str,
    category_update: CategoryMasterUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update category (Admin only)"""
    
    db_category = db.query(CategoryMaster).filter(CategoryMaster.id == category_id).first()
    
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if new name conflicts with existing category
    if category_update.category_name and category_update.category_name != db_category.category_name:
        existing_category = db.query(CategoryMaster).filter(
            CategoryMaster.category_name == category_update.category_name
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name already exists"
            )
    
    # Update fields
    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    
    return {
        "message": "Category updated successfully",
        "data": db_category
    }

@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate category (Admin only)"""
    
    db_category = db.query(CategoryMaster).filter(CategoryMaster.id == category_id).first()
    
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Soft delete by setting is_active to False
    setattr(db_category, 'is_active', False)
    db.commit()
    
    return {
        "message": "Category deactivated successfully"
    }
