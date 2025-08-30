from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from decimal import Decimal
import logging

from database import get_db
from models.user import User
from models.suppliers import Supplier, SupplierType
from models.state import State
from models.agents import Agent
from models.accounts import AccountsMaster
from schemas.suppliers import (
    SupplierCreate, 
    SupplierUpdate, 
    SupplierResponse, 
    SupplierWithDetailsResponse
)
from dependencies import get_current_user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def generate_supplier_account_code(db: Session) -> str:
    """Generate unique account code for supplier automatically under Supplier Payables (2106)"""
    base_code = "2106"
    
    # Get the last supplier account code to determine next sequence
    last_account = db.query(AccountsMaster).filter(
        AccountsMaster.account_code.like(f"{base_code}%")
    ).order_by(AccountsMaster.account_code.desc()).first()
    
    if last_account:
        # Extract number part and increment
        try:
            account_code = str(last_account.account_code)
            last_number = int(account_code[4:])  # Skip "2106" prefix
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    # Generate new code with zero padding (3 digits for supplier accounts)
    new_code = f"{base_code}{next_number:03d}"
    
    # Ensure uniqueness (in case of race conditions)
    while db.query(AccountsMaster).filter(AccountsMaster.account_code == new_code).first():
        next_number += 1
        new_code = f"{base_code}{next_number:03d}"
    
    return new_code


def create_supplier_account(db: Session, supplier_name: str, account_code: str):
    """Create associated payable account for the supplier"""
    try:
        # Create account in chart of accounts - Supplier is a payable account
        supplier_account = AccountsMaster(
            account_code=account_code,
            account_name=f"Supplier - {supplier_name}",
            account_type="Liability",
            parent_account_code="2106",  # Parent: Supplier Payables
            is_active=True,
            opening_balance=Decimal('0.00'),
            current_balance=Decimal('0.00'),
            description=f"Supplier payable account for {supplier_name}"
        )
        
        db.add(supplier_account)
        db.commit()
        db.refresh(supplier_account)
        
        logger.info(f"Created payable account {account_code} for supplier {supplier_name}")
        return supplier_account
        
    except Exception as e:
        logger.error(f"Failed to create payable account for supplier {supplier_name}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create associated payable account: {str(e)}"
        )


@router.post("/", response_model=SupplierWithDetailsResponse, status_code=201)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new supplier with automatic account generation"""
    
    # Validate state if provided
    if supplier.state_id:
        state = db.query(State).filter(State.id == supplier.state_id).first()
        if not state:
            raise HTTPException(status_code=400, detail="State not found")
    
    # Validate agent if provided
    if supplier.agent_id:
        agent = db.query(Agent).filter(Agent.id == supplier.agent_id).first()
        if not agent:
            raise HTTPException(status_code=400, detail="Agent not found")
    
    # Check for duplicate GST number if provided
    if supplier.gst_number:
        existing_gst = db.query(Supplier).filter(Supplier.gst_number == supplier.gst_number).first()
        if existing_gst:
            raise HTTPException(status_code=400, detail="GST number already exists")
    
    try:
        # Generate unique account code for supplier
        account_code = generate_supplier_account_code(db)
        
        # Create supplier
        db_supplier = Supplier(
            supplier_name=supplier.supplier_name,
            supplier_type=SupplierType(supplier.supplier_type.value),
            gst_number=supplier.gst_number,
            contact_person=supplier.contact_person,
            phone=supplier.phone,
            email=supplier.email,
            address=supplier.address,
            city=supplier.city,
            pincode=supplier.pincode,
            state_id=supplier.state_id,
            agent_id=supplier.agent_id,
            supplier_acc_code=account_code,
            status=supplier.status
        )
        
        db.add(db_supplier)
        db.flush()  # Flush to get the ID
        
        # Create associated account in chart of accounts
        create_supplier_account(db, supplier.supplier_name, account_code)
        
        db.commit()
        db.refresh(db_supplier)
        
        # Load relationships for response
        db_supplier_with_relations = db.query(Supplier).options(
            joinedload(Supplier.state),
            joinedload(Supplier.agent)
        ).filter(Supplier.id == db_supplier.id).first()
        
        if not db_supplier_with_relations:
            raise HTTPException(status_code=500, detail="Failed to load created supplier")
        
        # Format response with additional details
        response_data = SupplierWithDetailsResponse.from_orm(db_supplier_with_relations)
        if db_supplier_with_relations.state:
            response_data.state_name = db_supplier_with_relations.state.name
            response_data.state_code = db_supplier_with_relations.state.code
            response_data.gst_code = db_supplier_with_relations.state.gst_code
        if db_supplier_with_relations.agent:
            response_data.agent_name = db_supplier_with_relations.agent.agent_name
            response_data.agent_acc_code = db_supplier_with_relations.agent.agent_acc_code
            
        logger.info(f"Created supplier: {supplier.supplier_name} with account code: {account_code}")
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to create supplier {supplier.supplier_name}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create supplier: {str(e)}")


@router.get("/", response_model=List[SupplierWithDetailsResponse])
def get_suppliers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    supplier_type: Optional[str] = Query(None, description="Filter by supplier type"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all suppliers with pagination and optional filters"""
    query = db.query(Supplier).options(joinedload(Supplier.state), joinedload(Supplier.agent))
    
    if supplier_type:
        query = query.filter(Supplier.supplier_type == supplier_type)
    
    if status_filter:
        query = query.filter(Supplier.status == status_filter)
    
    suppliers = query.offset(skip).limit(limit).all()
    
    # Format response with state and agent information
    result = []
    for supplier in suppliers:
        supplier_data = SupplierWithDetailsResponse.from_orm(supplier)
        # Additional fields from relationships
        if supplier.state:
            supplier_data.state_name = supplier.state.name
            supplier_data.state_code = supplier.state.code
            supplier_data.gst_code = supplier.state.gst_code
        if supplier.agent:
            supplier_data.agent_name = supplier.agent.agent_name
            supplier_data.agent_acc_code = supplier.agent.agent_acc_code
        result.append(supplier_data)
    
    return result


@router.get("/{supplier_id}", response_model=SupplierWithDetailsResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific supplier by ID"""
    supplier = db.query(Supplier).options(
        joinedload(Supplier.state),
        joinedload(Supplier.agent)
    ).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Format response with additional details
    response_data = SupplierWithDetailsResponse.from_orm(supplier)
    if supplier.state:
        response_data.state_name = supplier.state.name
        response_data.state_code = supplier.state.code
        response_data.gst_code = supplier.state.gst_code
    if supplier.agent:
        response_data.agent_name = supplier.agent.agent_name
        response_data.agent_acc_code = supplier.agent.agent_acc_code
        
    return response_data


@router.put("/{supplier_id}", response_model=SupplierWithDetailsResponse)
def update_supplier(
    supplier_id: int,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a supplier"""
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Validate state if provided
    if supplier_update.state_id:
        state = db.query(State).filter(State.id == supplier_update.state_id).first()
        if not state:
            raise HTTPException(status_code=400, detail="State not found")
    
    # Validate agent if provided
    if supplier_update.agent_id:
        agent = db.query(Agent).filter(Agent.id == supplier_update.agent_id).first()
        if not agent:
            raise HTTPException(status_code=400, detail="Agent not found")
    
    # Check for duplicate GST number if being updated
    if supplier_update.gst_number and supplier_update.gst_number != db_supplier.gst_number:
        existing_gst = db.query(Supplier).filter(
            Supplier.gst_number == supplier_update.gst_number,
            Supplier.id != supplier_id
        ).first()
        if existing_gst:
            raise HTTPException(status_code=400, detail="GST number already exists")
    
    # Update supplier fields
    update_data = supplier_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_supplier, field):
            if field == "supplier_type" and value:
                setattr(db_supplier, field, SupplierType(value.value))
            else:
                setattr(db_supplier, field, value)
    
    try:
        db.commit()
        db.refresh(db_supplier)
        
        # Load relationships for response
        db_supplier_updated = db.query(Supplier).options(
            joinedload(Supplier.state),
            joinedload(Supplier.agent)
        ).filter(Supplier.id == supplier_id).first()
        
        if not db_supplier_updated:
            raise HTTPException(status_code=500, detail="Failed to load updated supplier")
        
        # Format response
        response_data = SupplierWithDetailsResponse.from_orm(db_supplier_updated)
        if db_supplier_updated.state:
            response_data.state_name = db_supplier_updated.state.name
            response_data.state_code = db_supplier_updated.state.code
            response_data.gst_code = db_supplier_updated.state.gst_code
        if db_supplier_updated.agent:
            response_data.agent_name = db_supplier_updated.agent.agent_name
            response_data.agent_acc_code = db_supplier_updated.agent.agent_acc_code
            
        logger.info(f"Updated supplier: {db_supplier_updated.supplier_name}")
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to update supplier {supplier_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update supplier: {str(e)}")


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a supplier (sets status to Inactive)"""
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    try:
        # Soft delete by changing status
        setattr(db_supplier, 'status', 'Inactive')
        db.commit()
        
        logger.info(f"Deleted (deactivated) supplier: {db_supplier.supplier_name}")
        
    except Exception as e:
        logger.error(f"Failed to delete supplier {supplier_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete supplier: {str(e)}")


@router.get("/by-gst/{gst_number}", response_model=SupplierWithDetailsResponse)
def get_supplier_by_gst(
    gst_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get supplier by GST number"""
    supplier = db.query(Supplier).options(
        joinedload(Supplier.state),
        joinedload(Supplier.agent)
    ).filter(Supplier.gst_number == gst_number).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Format response
    response_data = SupplierWithDetailsResponse.from_orm(supplier)
    if supplier.state:
        response_data.state_name = supplier.state.name
        response_data.state_code = supplier.state.code
        response_data.gst_code = supplier.state.gst_code
    if supplier.agent:
        response_data.agent_name = supplier.agent.agent_name
        response_data.agent_acc_code = supplier.agent.agent_acc_code
        
    return response_data
