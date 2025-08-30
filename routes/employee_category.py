from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from dependencies import get_current_active_user, require_admin
from models.employee_category import EmployeeCategory
from models.user import User
from schemas.employee_category import (
    EmployeeCategoryCreate, 
    EmployeeCategoryUpdate, 
    EmployeeCategoryResponse
)

router = APIRouter()


def generate_category_id(db: Session) -> str:
    """Generate a unique category ID in format CAT001, CAT002, etc."""
    # Find the highest existing category ID
    latest_category = db.query(EmployeeCategory)\
        .filter(EmployeeCategory.id.like("CAT%"))\
        .order_by(EmployeeCategory.id.desc())\
        .first()
    
    if latest_category:
        # Extract number and increment: CAT001 → CAT002
        try:
            category_id = str(latest_category.id)  # Convert to string first
            last_number = int(category_id[3:])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        # First category: CAT001
        new_number = 1
    
    return f"CAT{new_number:03d}"


@router.get("/", response_model=List[EmployeeCategoryResponse])
def get_employee_categories(
    skip: int = 0, 
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all employee categories with pagination. Requires authentication."""
    categories = db.query(EmployeeCategory).offset(skip).limit(limit).all()
    return categories


@router.get("/{category_id}", response_model=EmployeeCategoryResponse)
def get_employee_category(
    category_id: str, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Get a specific employee category by ID. Requires authentication."""
    category = db.query(EmployeeCategory).filter(EmployeeCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Employee category not found")
    return category


@router.post("/", response_model=EmployeeCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_employee_category(
    category_data: EmployeeCategoryCreate, 
    current_user: User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    """Create a new employee category with auto-generated ID. Requires admin privileges."""
    
    # Check if category name already exists
    existing_name = db.query(EmployeeCategory).filter(EmployeeCategory.name == category_data.name).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Employee category name already exists")
    
    try:
        # Generate unique category ID
        category_id = generate_category_id(db)
        
        # Create category with generated ID
        db_category = EmployeeCategory(
            id=category_id,
            **category_data.model_dump()
        )
        
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create employee category: {str(e)}")


@router.put("/{category_id}", response_model=EmployeeCategoryResponse)
def update_employee_category(
    category_id: str, 
    category_data: EmployeeCategoryUpdate, 
    current_user: User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    """Update an employee category. Requires admin privileges."""
    category = db.query(EmployeeCategory).filter(EmployeeCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Employee category not found")
    
    # Check if new name already exists (if name is being updated)
    update_data = category_data.model_dump(exclude_unset=True)
    if 'name' in update_data:
        existing_name = db.query(EmployeeCategory).filter(
            EmployeeCategory.name == update_data['name'],
            EmployeeCategory.id != category_id
        ).first()
        if existing_name:
            raise HTTPException(status_code=400, detail="Employee category name already exists")
    
    # Update only provided fields
    for field, value in update_data.items():
        setattr(category, field, value)
    
    try:
        db.commit()
        db.refresh(category)
        return category
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update employee category: {str(e)}")


@router.delete("/{category_id}")
def delete_employee_category(
    category_id: str, 
    current_user: User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    """Delete an employee category. Requires admin privileges."""
    category = db.query(EmployeeCategory).filter(EmployeeCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Employee category not found")
    
    # Check if category is being used by any employees
    from models.employees import Employee
    employees_using_category = db.query(Employee).filter(Employee.category_id == category_id).first()
    if employees_using_category:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category that is being used by employees"
        )
    
    try:
        db.delete(category)
        db.commit()
        return {"message": "Employee category deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete employee category: {str(e)}")


@router.get("/salary-structure/{structure}", response_model=List[EmployeeCategoryResponse])
def get_categories_by_salary_structure(
    structure: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get employee categories filtered by salary structure. Requires authentication."""
    categories = db.query(EmployeeCategory).filter(EmployeeCategory.salary_structure == structure).all()
    return categories


@router.get("/public/count")
def get_employee_categories_count(db: Session = Depends(get_db)):
    """Get total count of employee categories."""
    count = db.query(EmployeeCategory).count()
    return {"count": count}
