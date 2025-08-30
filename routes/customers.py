from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from decimal import Decimal
import logging

from database import get_db
from models.user import User
from models.customers import Customer, CustomerType
from models.state import State
from models.agents import Agent
from models.accounts import AccountsMaster
from schemas.customers import (
    CustomerCreate, 
    CustomerUpdate, 
    CustomerResponse, 
    CustomerWithDetailsResponse
)
from dependencies import get_current_user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def generate_customer_account_code(db: Session) -> str:
    """Generate unique account code for customer automatically under Customer Receivables (1301)"""
    base_code = "1301"
    
    # Get the last customer account code to determine next sequence
    last_account = db.query(AccountsMaster).filter(
        AccountsMaster.account_code.like(f"{base_code}%")
    ).order_by(AccountsMaster.account_code.desc()).first()
    
    if last_account:
        # Extract number part and increment
        try:
            account_code = str(last_account.account_code)
            last_number = int(account_code[4:])  # Skip "1301" prefix
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    # Generate new code with zero padding (3 digits for customer accounts)
    new_code = f"{base_code}{next_number:03d}"
    
    # Ensure uniqueness (in case of race conditions)
    while db.query(AccountsMaster).filter(AccountsMaster.account_code == new_code).first():
        next_number += 1
        new_code = f"{base_code}{next_number:03d}"
    
    return new_code


def create_customer_account(db: Session, customer_name: str, account_code: str):
    """Create associated receivable account for the customer"""
    try:
        # Create account in chart of accounts - Customer is a receivable account
        customer_account = AccountsMaster(
            account_code=account_code,
            account_name=f"Customer - {customer_name}",
            account_type="Asset",
            parent_account_code="1301",  # Parent: Customer Receivables
            is_active=True,
            opening_balance=Decimal('0.00'),
            current_balance=Decimal('0.00'),
            description=f"Customer receivable account for {customer_name}"
        )
        
        db.add(customer_account)
        db.commit()
        db.refresh(customer_account)
        
        logger.info(f"Created receivable account {account_code} for customer {customer_name}")
        return customer_account
        
    except Exception as e:
        logger.error(f"Failed to create receivable account for customer {customer_name}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create associated receivable account: {str(e)}"
        )


@router.post("/", response_model=CustomerWithDetailsResponse, status_code=201)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new customer with automatic account generation"""
    
    # Validate state if provided
    if customer.state_id:
        state = db.query(State).filter(State.id == customer.state_id).first()
        if not state:
            raise HTTPException(status_code=400, detail="State not found")
    
    # Validate agent if provided
    if customer.agent_id:
        agent = db.query(Agent).filter(Agent.id == customer.agent_id).first()
        if not agent:
            raise HTTPException(status_code=400, detail="Agent not found")
    
    # Check for duplicate GST number if provided
    if customer.gst_number:
        existing_gst = db.query(Customer).filter(Customer.gst_number == customer.gst_number).first()
        if existing_gst:
            raise HTTPException(status_code=400, detail="GST number already exists")
    
    try:
        # Generate unique account code for customer
        account_code = generate_customer_account_code(db)
        
        # Create customer
        db_customer = Customer(
            customer_name=customer.customer_name,
            customer_type=CustomerType(customer.customer_type.value),
            gst_number=customer.gst_number,
            contact_person=customer.contact_person,
            phone=customer.phone,
            email=customer.email,
            address=customer.address,
            city=customer.city,
            pincode=customer.pincode,
            state_id=customer.state_id,
            agent_id=customer.agent_id,
            customer_acc_code=account_code,
            status=customer.status
        )
        
        db.add(db_customer)
        db.flush()  # Flush to get the ID
        
        # Create associated account in chart of accounts
        create_customer_account(db, customer.customer_name, account_code)
        
        db.commit()
        db.refresh(db_customer)
        
        # Load relationships for response
        db_customer_with_relations = db.query(Customer).options(
            joinedload(Customer.state),
            joinedload(Customer.agent)
        ).filter(Customer.id == db_customer.id).first()
        
        if not db_customer_with_relations:
            raise HTTPException(status_code=500, detail="Failed to load created customer")
        
        # Format response with additional details
        response_data = CustomerWithDetailsResponse.from_orm(db_customer_with_relations)
        if db_customer_with_relations.state:
            response_data.state_name = db_customer_with_relations.state.name
            response_data.state_code = db_customer_with_relations.state.code
            response_data.gst_code = db_customer_with_relations.state.gst_code
        if db_customer_with_relations.agent:
            response_data.agent_name = db_customer_with_relations.agent.agent_name
            response_data.agent_acc_code = db_customer_with_relations.agent.agent_acc_code
            
        logger.info(f"Created customer: {customer.customer_name} with account code: {account_code}")
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to create customer {customer.customer_name}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")


@router.get("/", response_model=List[CustomerWithDetailsResponse])
def get_customers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    customer_type: Optional[str] = Query(None, description="Filter by customer type"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all customers with pagination and optional filters"""
    query = db.query(Customer).options(joinedload(Customer.state), joinedload(Customer.agent))
    
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)
    
    if status_filter:
        query = query.filter(Customer.status == status_filter)
    
    customers = query.offset(skip).limit(limit).all()
    
    # Format response with state and agent information
    result = []
    for customer in customers:
        customer_data = CustomerWithDetailsResponse.from_orm(customer)
        # Additional fields from relationships
        if customer.state:
            customer_data.state_name = customer.state.name
            customer_data.state_code = customer.state.code
            customer_data.gst_code = customer.state.gst_code
        if customer.agent:
            customer_data.agent_name = customer.agent.agent_name
            customer_data.agent_acc_code = customer.agent.agent_acc_code
        result.append(customer_data)
    
    return result


@router.get("/{customer_id}", response_model=CustomerWithDetailsResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific customer by ID"""
    customer = db.query(Customer).options(
        joinedload(Customer.state),
        joinedload(Customer.agent)
    ).filter(Customer.id == customer_id).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Format response with additional details
    response_data = CustomerWithDetailsResponse.from_orm(customer)
    if customer.state:
        response_data.state_name = customer.state.name
        response_data.state_code = customer.state.code
        response_data.gst_code = customer.state.gst_code
    if customer.agent:
        response_data.agent_name = customer.agent.agent_name
        response_data.agent_acc_code = customer.agent.agent_acc_code
        
    return response_data


@router.put("/{customer_id}", response_model=CustomerWithDetailsResponse)
def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a customer"""
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Validate state if provided
    if customer_update.state_id:
        state = db.query(State).filter(State.id == customer_update.state_id).first()
        if not state:
            raise HTTPException(status_code=400, detail="State not found")
    
    # Validate agent if provided
    if customer_update.agent_id:
        agent = db.query(Agent).filter(Agent.id == customer_update.agent_id).first()
        if not agent:
            raise HTTPException(status_code=400, detail="Agent not found")
    
    # Check for duplicate GST number if being updated
    if customer_update.gst_number and customer_update.gst_number != db_customer.gst_number:
        existing_gst = db.query(Customer).filter(
            Customer.gst_number == customer_update.gst_number,
            Customer.id != customer_id
        ).first()
        if existing_gst:
            raise HTTPException(status_code=400, detail="GST number already exists")
    
    # Update customer fields
    update_data = customer_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_customer, field):
            if field == "customer_type" and value:
                setattr(db_customer, field, CustomerType(value.value))
            else:
                setattr(db_customer, field, value)
    
    try:
        db.commit()
        db.refresh(db_customer)
        
        # Load relationships for response
        db_customer_updated = db.query(Customer).options(
            joinedload(Customer.state),
            joinedload(Customer.agent)
        ).filter(Customer.id == customer_id).first()
        
        if not db_customer_updated:
            raise HTTPException(status_code=500, detail="Failed to load updated customer")
        
        # Format response
        response_data = CustomerWithDetailsResponse.from_orm(db_customer_updated)
        if db_customer_updated.state:
            response_data.state_name = db_customer_updated.state.name
            response_data.state_code = db_customer_updated.state.code
            response_data.gst_code = db_customer_updated.state.gst_code
        if db_customer_updated.agent:
            response_data.agent_name = db_customer_updated.agent.agent_name
            response_data.agent_acc_code = db_customer_updated.agent.agent_acc_code
            
        logger.info(f"Updated customer: {db_customer_updated.customer_name}")
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to update customer {customer_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(e)}")


@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a customer (sets status to Inactive)"""
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")   
    
    try:
        # Soft delete by changing status
        setattr(db_customer, 'status', 'Inactive')
        db.commit()
        
        logger.info(f"Deleted (deactivated) customer: {db_customer.customer_name}")
        
    except Exception as e:
        logger.error(f"Failed to delete customer {customer_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete customer: {str(e)}")


@router.get("/by-gst/{gst_number}", response_model=CustomerWithDetailsResponse)
def get_customer_by_gst(
    gst_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer by GST number"""
    customer = db.query(Customer).options(
        joinedload(Customer.state),
        joinedload(Customer.agent)
    ).filter(Customer.gst_number == gst_number).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Format response
    response_data = CustomerWithDetailsResponse.from_orm(customer)
    if customer.state:
        response_data.state_name = customer.state.name
        response_data.state_code = customer.state.code
        response_data.gst_code = customer.state.gst_code
    if customer.agent:
        response_data.agent_name = customer.agent.agent_name
        response_data.agent_acc_code = customer.agent.agent_acc_code
        
    return response_data
