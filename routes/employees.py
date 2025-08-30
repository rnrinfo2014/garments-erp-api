from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
from dependencies import get_current_active_user, require_admin
from models.employees import Employee
from models.employee_category import EmployeeCategory
from models.accounts import AccountsMaster
from models.user import User
from schemas.employees import (
    EmployeeCreate, 
    EmployeeUpdate, 
    EmployeeResponse,
    EmployeeWithCategoryResponse
)
from decimal import Decimal

router = APIRouter()


def generate_employee_id(db: Session) -> str:
    """Generate a unique employee database ID in format EMP001, EMP002, etc."""
    # Find the highest existing employee ID
    latest_employee = db.query(Employee)\
        .filter(Employee.id.like("EMP%"))\
        .order_by(Employee.id.desc())\
        .first()
    
    if latest_employee:
        try:
            employee_id = str(latest_employee.id)
            last_number = int(employee_id[3:])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1
    
    return f"EMP{new_number:03d}"


def generate_employee_number(db: Session) -> str:
    """Generate a unique employee number in format EMP-001, EMP-002, etc."""
    # Find the highest existing employee number
    latest_employee = db.query(Employee)\
        .filter(Employee.employee_id.like("EMP-%"))\
        .order_by(Employee.employee_id.desc())\
        .first()
    
    if latest_employee:
        try:
            employee_number = str(latest_employee.employee_id)
            last_number = int(employee_number[4:])  # Get "001" from "EMP-001"
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1
    
    return f"EMP-{new_number:03d}"


def generate_employee_account_code(db: Session, employee_name: str) -> str:
    """Generate a unique account code for employee payable account."""
    base_code = "2108"  # Employee payables base code
    
    # Find the next available account code
    counter = 1
    while True:
        acc_code = f"{base_code}{counter:03d}"
        existing = db.query(AccountsMaster).filter(AccountsMaster.account_code == acc_code).first()
        if not existing:
            return acc_code
        counter += 1


def create_employee_account(db: Session, employee_name: str, employee_id: str) -> str:
    """Create a payable account for the employee."""
    acc_code = generate_employee_account_code(db, employee_name)
    
    # Create the account record
    account = AccountsMaster(
        account_code=acc_code,
        account_name=f"Employee - {employee_name}",
        account_type="Liability",
        parent_account_code="2108",  # Employee Payables parent
        is_active=True,
        opening_balance=Decimal('0.00'),
        current_balance=Decimal('0.00'),
        description=f"Payable account for employee {employee_name} (ID: {employee_id})"
    )
    
    db.add(account)
    db.flush()  # Ensure the account is created
    return acc_code


@router.get("/", response_model=List[EmployeeWithCategoryResponse])
def get_employees(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all employees with pagination and optional filtering. Requires authentication."""
    query = db.query(Employee).options(joinedload(Employee.category))
    
    if status:
        query = query.filter(Employee.status == status)
    
    if category_id:
        query = query.filter(Employee.category_id == category_id)
    
    employees = query.offset(skip).limit(limit).all()
    
    # Transform to include category details
    result = []
    for employee in employees:
        employee_dict = {
            "id": employee.id,
            "employee_id": employee.employee_id,
            "name": employee.name,
            "category_id": employee.category_id,
            "join_date": employee.join_date,
            "phone": employee.phone,
            "address": employee.address,
            "status": employee.status,
            "photo_url": employee.photo_url,
            "acc_code": employee.acc_code,
            "created_at": employee.created_at,
            "updated_at": employee.updated_at,
            "category_name": employee.category.name if employee.category else None,
            "salary_structure": employee.category.salary_structure if employee.category else None,
            "base_rate": employee.base_rate
        }
        result.append(employee_dict)
    
    return result


@router.get("/{employee_id}", response_model=EmployeeWithCategoryResponse)
def get_employee(
    employee_id: str, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Get a specific employee by ID with category details. Requires authentication."""
    employee = db.query(Employee).options(joinedload(Employee.category)).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "id": employee.id,
        "employee_id": employee.employee_id,
        "name": employee.name,
        "category_id": employee.category_id,
        "join_date": employee.join_date,
        "phone": employee.phone,
        "address": employee.address,
        "status": employee.status,
        "photo_url": employee.photo_url,
        "acc_code": employee.acc_code,
        "created_at": employee.created_at,
        "updated_at": employee.updated_at,
        "category_name": employee.category.name if employee.category else None,
        "salary_structure": employee.category.salary_structure if employee.category else None,
        "base_rate": employee.base_rate
    }


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate, 
    current_user: User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    """Create a new employee with auto-generated IDs and automatic payable account creation. Requires admin privileges."""
    
    # Validate that category exists
    category = db.query(EmployeeCategory).filter(EmployeeCategory.id == employee_data.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Employee category not found")
    
    try:
        # Generate unique employee IDs
        employee_id = generate_employee_id(db)  # EMP001, EMP002, etc.
        employee_number = generate_employee_number(db)  # EMP-001, EMP-002, etc.
        
        # Create associated payable account first
        acc_code = create_employee_account(db, employee_data.name, employee_number)
        
        # Create employee record with generated IDs and account code
        db_employee = Employee(
            id=employee_id,
            employee_id=employee_number,
            acc_code=acc_code,
            **employee_data.model_dump()
        )
        
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        
        return db_employee
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create employee: {str(e)}")


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: str, 
    employee_data: EmployeeUpdate, 
    current_user: User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    """Update an employee. Requires admin privileges."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_data = employee_data.model_dump(exclude_unset=True)
    
    # Check if new employee_id already exists (if employee_id is being updated)
    if 'employee_id' in update_data:
        existing_employee_id = db.query(Employee).filter(
            Employee.employee_id == update_data['employee_id'],
            Employee.id != employee_id
        ).first()
        if existing_employee_id:
            raise HTTPException(status_code=400, detail="Employee ID number already exists")
    
    # Validate that new category exists (if category_id is being updated)
    if 'category_id' in update_data:
        category = db.query(EmployeeCategory).filter(EmployeeCategory.id == update_data['category_id']).first()
        if not category:
            raise HTTPException(status_code=400, detail="Employee category not found")
    
    # Update only provided fields
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    # If name is updated, also update the associated account name
    if 'name' in update_data and getattr(employee, 'acc_code', None):
        account = db.query(AccountsMaster).filter(AccountsMaster.account_code == getattr(employee, 'acc_code')).first()
        if account:
            setattr(account, 'account_name', f"Employee - {getattr(employee, 'name')}")
    
    try:
        db.commit()
        db.refresh(employee)
        return employee
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update employee: {str(e)}")


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: str, 
    current_user: User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    """Delete an employee (soft delete by setting status to Inactive) and deactivate associated account. Requires admin privileges."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Soft delete - set status to Inactive
    setattr(employee, 'status', 'Inactive')
    
    # Also deactivate the associated account
    if getattr(employee, 'acc_code', None):
        account = db.query(AccountsMaster).filter(AccountsMaster.account_code == getattr(employee, 'acc_code')).first()
        if account:
            setattr(account, 'is_active', False)
    
    try:
        db.commit()
        return {"message": "Employee deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to deactivate employee: {str(e)}")


@router.get("/status/{status_filter}", response_model=List[EmployeeWithCategoryResponse])
def get_employees_by_status(
    status_filter: str, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get employees filtered by status with category details. Requires authentication."""
    employees = db.query(Employee).options(joinedload(Employee.category)).filter(Employee.status == status_filter).all()
    
    result = []
    for employee in employees:
        employee_dict = {
            "id": employee.id,
            "employee_id": employee.employee_id,
            "name": employee.name,
            "category_id": employee.category_id,
            "join_date": employee.join_date,
            "phone": employee.phone,
            "address": employee.address,
            "status": employee.status,
            "photo_url": employee.photo_url,
            "acc_code": employee.acc_code,
            "created_at": employee.created_at,
            "updated_at": employee.updated_at,
            "category_name": employee.category.name if employee.category else None,
            "salary_structure": employee.category.salary_structure if employee.category else None,
            "base_rate": employee.base_rate
        }
        result.append(employee_dict)
    
    return result


@router.get("/category/{category_id}", response_model=List[EmployeeResponse])
def get_employees_by_category(
    category_id: str, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get employees filtered by category. Requires authentication."""
    # Validate that category exists
    category = db.query(EmployeeCategory).filter(EmployeeCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Employee category not found")
    
    employees = db.query(Employee).filter(Employee.category_id == category_id).all()
    return employees


@router.get("/employee-number/{employee_number}", response_model=EmployeeWithCategoryResponse)
def get_employee_by_number(
    employee_number: str, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Get employee by employee number with category details. Requires authentication."""
    employee = db.query(Employee).options(joinedload(Employee.category)).filter(Employee.employee_id == employee_number).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "id": employee.id,
        "employee_id": employee.employee_id,
        "name": employee.name,
        "category_id": employee.category_id,
        "join_date": employee.join_date,
        "phone": employee.phone,
        "address": employee.address,
        "status": employee.status,
        "photo_url": employee.photo_url,
        "acc_code": employee.acc_code,
        "created_at": employee.created_at,
        "updated_at": employee.updated_at,
        "category_name": employee.category.name if employee.category else None,
        "salary_structure": employee.category.salary_structure if employee.category else None,
        "base_rate": employee.base_rate
    }


@router.get("/public/count")
def get_employees_count(
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get total count of employees with optional filtering."""
    query = db.query(Employee)
    
    if status:
        query = query.filter(Employee.status == status)
    
    if category_id:
        query = query.filter(Employee.category_id == category_id)
    
    count = query.count()
    return {"count": count}


@router.get("/account/{employee_id}")
def get_employee_account(employee_id: str, db: Session = Depends(get_db)):
    """Get the associated account details for an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if not getattr(employee, 'acc_code', None):
        raise HTTPException(status_code=404, detail="No account associated with this employee")
    
    account = db.query(AccountsMaster).filter(AccountsMaster.account_code == getattr(employee, 'acc_code')).first()
    if not account:
        raise HTTPException(status_code=404, detail="Associated account not found")
    
    return {
        "employee_id": employee.id,
        "employee_name": employee.name,
        "employee_number": employee.employee_id,
        "account_code": account.account_code,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "current_balance": account.current_balance,
        "is_active": account.is_active
    }
