# Complete API Guide - Easy Understanding

## 📁 Project Structure Explained

```
backend/
├── main.py                 # API server starting point
├── database.py            # Database connection settings
├── auth.py               # Login and authentication logic
├── dependencies.py       # Common functions used everywhere
├── requirements.txt      # List of Python packages needed
├── seed.py              # Creates initial data in database
├── migrate_employees.py  # Creates employee tables
│
├── models/              # Database table definitions
│   ├── user.py         # User table structure
│   ├── company.py      # Company table structure
│   ├── vendors.py      # Vendor table structure
│   ├── employees.py    # Employee table structure
│   └── employee_category.py # Employee category table structure
│
├── schemas/             # Data validation rules
│   ├── user.py         # User data validation
│   ├── vendors.py      # Vendor data validation
│   ├── employees.py    # Employee data validation
│   └── employee_category.py # Category data validation
│
└── routes/              # API endpoint handlers
    ├── __init__.py     # Combines all routes
    ├── user.py         # Login/user endpoints
    ├── vendors.py      # Vendor CRUD endpoints
    ├── employees.py    # Employee CRUD endpoints
    └── employee_category.py # Category CRUD endpoints
```

---

## 🔄 Complete API Workflow Explanation

### Step 1: Server Startup Process
```python
# main.py - This is where everything starts
from fastapi import FastAPI

app = FastAPI(title="Garments ERP API")

# When server starts:
1. Database connection is established (database.py)
2. All routes are loaded (routes/__init__.py)
3. Initial data is created if needed (seed.py)
4. Server starts listening on port 8000
```

### Step 2: User Authentication Flow
```
1. User sends login request → routes/user.py
2. Checks username/password → auth.py
3. Creates JWT token if valid
4. Returns token to user
5. User includes token in all future requests
```

### Step 3: API Request Flow (Example: Create Employee)
```
Frontend Request → FastAPI → Route Handler → Database → Response

Detailed Flow:
1. Frontend: POST /api/employees/ with employee data
2. FastAPI receives request
3. Routes to routes/employees.py → create_employee()
4. Validates data using schemas/employees.py
5. Generates account code automatically
6. Saves to database using models/employees.py
7. Creates payable account in accounts table
8. Returns success response with employee data
```

---

## 📊 Database Tables and Relationships

### Employee Category Table
```sql
CREATE TABLE employee_category (
    id VARCHAR(50) PRIMARY KEY,           -- CAT001, CAT002, etc. (AUTO-GENERATED)
    name VARCHAR(100) NOT NULL UNIQUE,   -- "Management", "Production"
    salary_structure VARCHAR(20),         -- "Monthly", "Daily", "Piece-rate"
    base_rate DECIMAL(10,2),             -- Base salary amount
    description TEXT,                     -- Optional description
    is_active BOOLEAN DEFAULT TRUE,       -- Active/Inactive status
    created_at TIMESTAMP,                -- When created
    updated_at TIMESTAMP                 -- When last updated
);
```

### Employee Table
```sql
CREATE TABLE employees (
    id VARCHAR(50) PRIMARY KEY,           -- EMP001, EMP002, etc.
    employee_id VARCHAR(50) UNIQUE,       -- EMP-001, EMP-002, etc.
    name VARCHAR(100) NOT NULL,           -- Employee name
    category_id VARCHAR(50),              -- Links to employee_category.id
    join_date DATETIME NOT NULL,          -- When employee joined
    phone VARCHAR(15) NOT NULL,           -- Phone number
    address TEXT NOT NULL,                -- Full address
    status VARCHAR(10) DEFAULT 'Active',  -- "Active" or "Inactive"
    photo_url VARCHAR(255),               -- Optional photo URL
    acc_code VARCHAR(20) UNIQUE,          -- Account code (2108001, 2108002)
    created_at TIMESTAMP,                -- When created
    updated_at TIMESTAMP,                -- When last updated
    
    FOREIGN KEY (category_id) REFERENCES employee_category(id)
);
```

---

## 🔧 Code Flow Explanation

### 1. Model Files (Database Structure)

**models/employees.py** - Defines how employee data is stored
```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from database import Base

class Employee(Base):
    __tablename__ = "employees"  # Table name in database
    
    id = Column(String(50), primary_key=True)     # Unique ID
    employee_id = Column(String(50), unique=True)  # Display ID
    name = Column(String(100), nullable=False)     # Required field
    category_id = Column(String(50), ForeignKey("employee_category.id"))
    acc_code = Column(String(20), unique=True)     # Account code
    
    # Relationship - gets category data when needed
    category = relationship("EmployeeCategory", back_populates="employees")
```

### 2. Schema Files (Data Validation)

**schemas/employees.py** - Validates incoming data
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmployeeCreate(BaseModel):
    name: str                    # Required
    category_id: str            # Required  
    join_date: str              # Required (date format)
    phone: str                  # Required
    address: str                # Required
    status: Optional[str] = "Active"  # Optional, defaults to "Active"
    photo_url: Optional[str] = None   # Optional

class EmployeeResponse(BaseModel):
    id: str                     # Auto-generated
    employee_id: str            # Auto-generated  
    acc_code: str              # Auto-generated
    name: str
    # ... all other fields
    category: dict             # Category information included
```

### 3. Route Files (API Endpoints)

**routes/employees.py** - Handles API requests
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db, get_admin_user

router = APIRouter()

@router.post("/employees/")  # POST /api/employees/
async def create_employee(
    employee_data: EmployeeCreate,           # Data from request
    db: Session = Depends(get_db),           # Database connection
    current_user = Depends(get_admin_user)   # Must be admin
):
    try:
        # Step 1: Generate unique account code
        acc_code = generate_employee_account_code(db, employee_data.name)
        
        # Step 2: Create employee record
        new_employee = Employee(
            id=generate_unique_id(),
            employee_id=generate_employee_id(db),
            acc_code=acc_code,
            **employee_data.dict()  # All the form data
        )
        
        # Step 3: Save to database
        db.add(new_employee)
        db.flush()  # Get the ID
        
        # Step 4: Create payable account automatically
        create_employee_account(db, new_employee.name, new_employee.employee_id)
        
        # Step 5: Save everything
        db.commit()
        
        # Step 6: Return success response
        return {
            "message": "Employee created successfully",
            "data": format_employee_response(new_employee)
        }
        
    except Exception as e:
        db.rollback()  # Undo changes if error
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🔐 Authentication System

### How Login Works
```python
# routes/user.py
@router.post("/login")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    # Step 1: Find user in database
    user = db.query(User).filter(User.username == login_data.username).first()
    
    # Step 2: Check if user exists and password is correct
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Step 3: Create JWT token
    token = create_access_token(data={"sub": user.username, "role": user.role})
    
    # Step 4: Return token
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }
```

### How Authentication is Checked
```python
# dependencies.py
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Find user in database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

---

## 💰 Automatic Account Creation System

### How Account Codes are Generated
```python
def generate_employee_account_code(db: Session, employee_name: str) -> str:
    # Find the highest existing account code
    latest_account = db.query(AccountsMaster)\
        .filter(AccountsMaster.account_code.like("2108%"))\
        .order_by(AccountsMaster.account_code.desc())\
        .first()
    
    if latest_account:
        # Extract number and increment: 2108001 → 2108002
        last_number = int(latest_account.account_code[4:])
        new_number = last_number + 1
    else:
        # First employee account: 2108001
        new_number = 1
    
    return f"2108{new_number:03d}"  # Format: 2108001, 2108002, etc.

def create_employee_account(db: Session, employee_name: str, employee_id: str):
    # Create payable account for this employee
    account = AccountsMaster(
        account_code=acc_code,           # 2108001
        account_name=f"{employee_name} - Employee Payable",  # "John Doe - Employee Payable"
        account_type="Liability",        # It's money we owe to employee
        parent_account_code="2108",      # Under Employee Payables
        is_active=True,
        opening_balance=Decimal('0.00'), # Starts with zero balance
        current_balance=Decimal('0.00')
    )
    db.add(account)
```

---

## 🌐 API Request/Response Examples

### Creating an Employee (Complete Flow)

**1. Frontend Request:**
```javascript
const response = await fetch('http://localhost:8000/api/employees/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
    },
    body: JSON.stringify({
        name: 'John Doe',
        category_id: 'CAT001',
        join_date: '2024-01-15',
        phone: '9876543210',
        address: '123 Main Street, Mumbai',
        status: 'Active'
    })
});
```

**2. Backend Processing:**
```
1. FastAPI receives request
2. Validates JWT token → gets current user
3. Checks if user is admin
4. Validates request data using EmployeeCreate schema
5. Generates account code: 2108001
6. Generates employee ID: EMP-001
7. Creates Employee record in database
8. Creates Account record in accounts table
9. Returns response
```

**3. API Response:**
```json
{
    "message": "Employee created successfully",
    "data": {
        "id": "EMP001",
        "employee_id": "EMP-001",
        "name": "John Doe",
        "category_id": "CAT001",
        "join_date": "2024-01-15T00:00:00",
        "phone": "9876543210",
        "address": "123 Main Street, Mumbai",
        "status": "Active",
        "photo_url": null,
        "acc_code": "2108001",
        "created_at": "2024-08-22T10:30:00",
        "updated_at": "2024-08-22T10:30:00",
        "category": {
            "id": "CAT001",
            "name": "Management",
            "salary_structure": "Monthly",
            "base_rate": 50000.00
        }
    }
}
```

---

## 🗃️ Database Account Structure

### Account Code System
```
Account Codes Pattern:
- 1000-1999: Assets (things we own)
- 2000-2999: Liabilities (things we owe)
- 3000-3999: Equity (owner's money)
- 4000-4999: Revenue (money coming in)
- 5000-5999: Expenses (money going out)

Specific Payable Accounts:
- 2106xxx: Supplier Payables (money we owe to suppliers)
- 2107xxx: Vendor Payables (money we owe to vendors)  
- 2108xxx: Employee Payables (money we owe to employees)

Example:
2108001 = "John Doe - Employee Payable"
2108002 = "Jane Smith - Employee Payable"
```

---

## 🚀 How to Use This API

### Step 1: Start the Server
```bash
cd backend
python main.py
```
Server starts at: http://localhost:8000

### Step 2: Login to Get Token
```javascript
const loginResponse = await fetch('http://localhost:8000/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'superadmin',
        password: 'admin123'
    })
});
const { access_token } = await loginResponse.json();
```

### Step 3: Use Token for API Calls
```javascript
const response = await fetch('http://localhost:8000/api/employees/', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
});
const employees = await response.json();
```

---

## 🔍 Testing the API

### 1. Swagger UI (Automatic Documentation)
- Go to: http://localhost:8000/docs
- Click "Authorize" button
- Enter: `Bearer your_jwt_token_here`
- Test any endpoint directly

### 2. Using Postman
- Import OpenAPI spec from: http://localhost:8000/openapi.json
- Set Authorization to Bearer Token
- Test all endpoints

### 3. Using curl (Command Line)
```bash
# Login
curl -X POST "http://localhost:8000/api/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"superadmin","password":"admin123"}'

# Get employees
curl -X GET "http://localhost:8000/api/employees/" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🐛 Common Issues and Solutions

### Issue 1: "401 Unauthorized"
**Problem:** Token missing or invalid
**Solution:** 
1. Login first to get token
2. Include token in Authorization header
3. Check token hasn't expired

### Issue 2: "403 Forbidden" 
**Problem:** Need admin access
**Solution:** Login with admin account (superadmin/admin123)

### Issue 3: "422 Validation Error"
**Problem:** Request data doesn't match schema
**Solution:** Check required fields and data types

### Issue 4: "500 Internal Server Error"
**Problem:** Server error (database, code bug)
**Solution:** Check server logs, verify database connection

---

## 📝 Summary

This API system works in layers:

1. **Frontend** sends HTTP requests
2. **FastAPI** receives and routes requests  
3. **Authentication** validates user tokens
4. **Schemas** validate request data
5. **Routes** handle business logic
6. **Models** interact with database
7. **Database** stores/retrieves data
8. **Response** sent back to frontend

The automatic account creation ensures every employee gets a payable account for salary transactions, following proper accounting principles.

**Key Files to Remember:**
- `main.py` - Server startup
- `routes/employees.py` - Employee API logic
- `models/employees.py` - Database structure
- `schemas/employees.py` - Data validation
- `auth.py` - Login system

The server is running and ready for your frontend development! 🚀
