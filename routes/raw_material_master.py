from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional, cast
from database import get_db
from models.raw_material_master import RawMaterialMaster
from models.category_master import CategoryMaster
from models.size_master import SizeMaster
from models.unit_master import UnitMaster
from schemas.raw_material_master import (
    RawMaterialMasterCreate,
    RawMaterialMasterUpdate,
    RawMaterialMasterWithDetailsResponse,
    RawMaterialMasterListResponse,
    RawMaterialMasterSingleResponse
)
from dependencies import get_current_active_user, require_admin
from models.user import User

router = APIRouter()

def generate_raw_material_id(db: Session) -> str:
    """Generate unique raw material ID in format RM001, RM002, etc."""
    last_material = db.query(RawMaterialMaster).order_by(RawMaterialMaster.id.desc()).first()
    
    if not last_material:
        return "RM001"
    
    try:
        last_number = int(str(last_material.id)[2:])  # Remove "RM" prefix
        new_number = last_number + 1
        return f"RM{new_number:03d}"
    except (ValueError, IndexError):
        return f"RM{db.query(RawMaterialMaster).count() + 1:03d}"

@router.get("/", response_model=RawMaterialMasterListResponse)
def get_raw_materials(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all raw materials with optional filtering"""
    query = db.query(RawMaterialMaster).options(
        joinedload(RawMaterialMaster.category),
        joinedload(RawMaterialMaster.size),
        joinedload(RawMaterialMaster.unit)
    )
    
    if category_id:
        query = query.filter(RawMaterialMaster.category_id == category_id)
        
    if is_active is not None:
        query = query.filter(RawMaterialMaster.is_active == is_active)
    
    materials = query.offset(skip).limit(limit).all()
    
    # Transform to include related details
    result = []
    for material in materials:
        material_dict = {
            "id": material.id,
            "material_name": material.material_name,
            "material_code": material.material_code,
            "category_id": material.category_id,
            "size_id": material.size_id,
            "unit_id": material.unit_id,
            "standard_rate": material.standard_rate,
            "minimum_stock": material.minimum_stock,
            "maximum_stock": material.maximum_stock,
            "reorder_level": material.reorder_level,
            "description": material.description,
            "is_active": material.is_active,
            "created_at": material.created_at,
            "updated_at": material.updated_at,
            "category_name": material.category.category_name if material.category else None,
            "size_name": material.size.size_name if material.size else None,
            "unit_name": material.unit.unit_name if material.unit else None
        }
        result.append(material_dict)
    
    return {
        "message": "Raw materials retrieved successfully",
        "data": result
    }

@router.get("/search/{search_term}", response_model=RawMaterialMasterListResponse)
def search_raw_materials(
    search_term: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search raw materials by name, code or description"""
    materials = db.query(RawMaterialMaster).options(
        joinedload(RawMaterialMaster.category),
        joinedload(RawMaterialMaster.size),
        joinedload(RawMaterialMaster.unit)
    ).filter(
        or_(
            RawMaterialMaster.material_name.ilike(f"%{search_term}%"),
            RawMaterialMaster.material_code.ilike(f"%{search_term}%"),
            RawMaterialMaster.description.ilike(f"%{search_term}%")
        )
    ).all()
    
    # Transform to include related details
    result = []
    for material in materials:
        material_dict = {
            "id": material.id,
            "material_name": material.material_name,
            "material_code": material.material_code,
            "category_id": material.category_id,
            "size_id": material.size_id,
            "unit_id": material.unit_id,
            "standard_rate": material.standard_rate,
            "minimum_stock": material.minimum_stock,
            "maximum_stock": material.maximum_stock,
            "reorder_level": material.reorder_level,
            "description": material.description,
            "is_active": material.is_active,
            "created_at": material.created_at,
            "updated_at": material.updated_at,
            "category_name": material.category.category_name if material.category else None,
            "size_name": material.size.size_name if material.size else None,
            "unit_name": material.unit.unit_name if material.unit else None
        }
        result.append(material_dict)
    
    return {
        "message": f"Search results for '{search_term}'",
        "data": result
    }

@router.get("/category/{category_id}", response_model=RawMaterialMasterListResponse)
def get_raw_materials_by_category(
    category_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get raw materials by category"""
    materials = db.query(RawMaterialMaster).options(
        joinedload(RawMaterialMaster.category),
        joinedload(RawMaterialMaster.size),
        joinedload(RawMaterialMaster.unit)
    ).filter(RawMaterialMaster.category_id == category_id).all()
    
    # Transform to include related details
    result = []
    for material in materials:
        material_dict = {
            "id": material.id,
            "material_name": material.material_name,
            "material_code": material.material_code,
            "category_id": material.category_id,
            "size_id": material.size_id,
            "unit_id": material.unit_id,
            "standard_rate": material.standard_rate,
            "minimum_stock": material.minimum_stock,
            "maximum_stock": material.maximum_stock,
            "reorder_level": material.reorder_level,
            "description": material.description,
            "is_active": material.is_active,
            "created_at": material.created_at,
            "updated_at": material.updated_at,
            "category_name": material.category.category_name if material.category else None,
            "size_name": material.size.size_name if material.size else None,
            "unit_name": material.unit.unit_name if material.unit else None
        }
        result.append(material_dict)
    
    return {
        "message": f"Raw materials in category retrieved successfully",
        "data": result
    }

@router.get("/{material_id}", response_model=RawMaterialMasterSingleResponse)
def get_raw_material(
    material_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get raw material by ID"""
    material = db.query(RawMaterialMaster).options(
        joinedload(RawMaterialMaster.category),
        joinedload(RawMaterialMaster.size),
        joinedload(RawMaterialMaster.unit)
    ).filter(RawMaterialMaster.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found"
        )
    
    material_dict = {
        "id": material.id,
        "material_name": material.material_name,
        "material_code": material.material_code,
        "category_id": material.category_id,
        "size_id": material.size_id,
        "unit_id": material.unit_id,
        "standard_rate": material.standard_rate,
        "minimum_stock": material.minimum_stock,
        "maximum_stock": material.maximum_stock,
        "reorder_level": material.reorder_level,
        "description": material.description,
        "is_active": material.is_active,
        "created_at": material.created_at,
        "updated_at": material.updated_at,
        "category_name": material.category.category_name if material.category else None,
        "size_name": material.size.size_name if material.size else None,
        "unit_name": material.unit.unit_name if material.unit else None
    }
    
    return {
        "message": "Raw material retrieved successfully",
        "data": material_dict
    }

@router.post("/", response_model=RawMaterialMasterSingleResponse, status_code=status.HTTP_201_CREATED)
def create_raw_material(
    material: RawMaterialMasterCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new raw material (Admin only)"""
    
    # Validate that category, size, and unit exist
    category = db.query(CategoryMaster).filter(CategoryMaster.id == material.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )
    
    size = db.query(SizeMaster).filter(SizeMaster.id == material.size_id).first()
    if not size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Size not found"
        )
        
    unit = db.query(UnitMaster).filter(UnitMaster.id == material.unit_id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit not found"
        )
    
    # Check if material code already exists
    existing_material = db.query(RawMaterialMaster).filter(
        RawMaterialMaster.material_code == material.material_code
    ).first()
    
    if existing_material:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material code already exists"
        )
    
    # Generate unique ID
    new_id = generate_raw_material_id(db)
    
    # Create new raw material
    db_material = RawMaterialMaster(
        id=new_id,
        **material.model_dump()
    )
    
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    
    # Load relationships for response
    db_material = db.query(RawMaterialMaster).options(
        joinedload(RawMaterialMaster.category),
        joinedload(RawMaterialMaster.size),
        joinedload(RawMaterialMaster.unit)
    ).filter(RawMaterialMaster.id == new_id).first()
    
    if not db_material:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading created material"
        )
    
    # Cast for type checking
    db_material = cast(RawMaterialMaster, db_material)
    
    material_dict = {
        "id": db_material.id,
        "material_name": db_material.material_name,
        "material_code": db_material.material_code,
        "category_id": db_material.category_id,
        "size_id": db_material.size_id,
        "unit_id": db_material.unit_id,
        "standard_rate": db_material.standard_rate,
        "minimum_stock": db_material.minimum_stock,
        "maximum_stock": db_material.maximum_stock,
        "reorder_level": db_material.reorder_level,
        "description": db_material.description,
        "is_active": db_material.is_active,
        "created_at": db_material.created_at,
        "updated_at": db_material.updated_at,
        "category_name": db_material.category.category_name if db_material.category else None,
        "size_name": db_material.size.size_name if db_material.size else None,
        "unit_name": db_material.unit.unit_name if db_material.unit else None
    }
    
    return {
        "message": "Raw material created successfully",
        "data": material_dict
    }

@router.put("/{material_id}", response_model=RawMaterialMasterSingleResponse)
def update_raw_material(
    material_id: str,
    material_update: RawMaterialMasterUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update raw material (Admin only)"""
    
    db_material = db.query(RawMaterialMaster).filter(RawMaterialMaster.id == material_id).first()
    
    if not db_material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found"
        )
    
    # Validate relationships if they are being updated
    if material_update.category_id:
        category = db.query(CategoryMaster).filter(CategoryMaster.id == material_update.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )
    
    if material_update.size_id:
        size = db.query(SizeMaster).filter(SizeMaster.id == material_update.size_id).first()
        if not size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Size not found"
            )
            
    if material_update.unit_id:
        unit = db.query(UnitMaster).filter(UnitMaster.id == material_update.unit_id).first()
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unit not found"
            )
    
    # Check if new material code conflicts with existing material
    if material_update.material_code and material_update.material_code != db_material.material_code:
        existing_material = db.query(RawMaterialMaster).filter(
            RawMaterialMaster.material_code == material_update.material_code
        ).first()
        
        if existing_material:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Material code already exists"
            )
    
    # Update fields
    update_data = material_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_material, field, value)
    
    db.commit()
    db.refresh(db_material)
    
    # Load relationships for response
    db_material = db.query(RawMaterialMaster).options(
        joinedload(RawMaterialMaster.category),
        joinedload(RawMaterialMaster.size),
        joinedload(RawMaterialMaster.unit)
    ).filter(RawMaterialMaster.id == material_id).first()
    
    if not db_material:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading updated material"
        )
    
    # Cast for type checking
    db_material = cast(RawMaterialMaster, db_material)
    
    material_dict = {
        "id": db_material.id,
        "material_name": db_material.material_name,
        "material_code": db_material.material_code,
        "category_id": db_material.category_id,
        "size_id": db_material.size_id,
        "unit_id": db_material.unit_id,
        "standard_rate": db_material.standard_rate,
        "minimum_stock": db_material.minimum_stock,
        "maximum_stock": db_material.maximum_stock,
        "reorder_level": db_material.reorder_level,
        "description": db_material.description,
        "is_active": db_material.is_active,
        "created_at": db_material.created_at,
        "updated_at": db_material.updated_at,
        "category_name": db_material.category.category_name if db_material.category else None,
        "size_name": db_material.size.size_name if db_material.size else None,
        "unit_name": db_material.unit.unit_name if db_material.unit else None
    }
    
    return {
        "message": "Raw material updated successfully",
        "data": material_dict
    }

@router.delete("/{material_id}")
def delete_raw_material(
    material_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate raw material (Admin only)"""
    
    db_material = db.query(RawMaterialMaster).filter(RawMaterialMaster.id == material_id).first()
    
    if not db_material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found"
        )
    
    # Soft delete by setting is_active to False
    setattr(db_material, 'is_active', False)
    db.commit()
    
    return {
        "message": "Raw material deactivated successfully"
    }
