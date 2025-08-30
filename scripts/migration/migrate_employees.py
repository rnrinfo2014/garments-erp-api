"""
Migration script to add employee categories and employees tables
"""

from database import engine, Base
from models.employee_category import EmployeeCategory
from models.employees import Employee
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal

def create_employee_tables():
    """Create employee category and employees tables."""
    print("Creating employee category and employees tables...")
    
    # Import all models to ensure they are registered
    from models import employee_category, employees
    
    # Create the tables
    Base.metadata.create_all(bind=engine)
    print("Employee tables created successfully!")

def seed_employee_categories():
    """Seed some initial employee categories."""
    print("Seeding employee categories...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Ensure the Employee Payables parent account exists
        from models.accounts import AccountsMaster
        employee_payables_account = session.query(AccountsMaster).filter(AccountsMaster.account_code == "2108").first()
        if not employee_payables_account:
            employee_payables = AccountsMaster(
                account_code="2108",
                account_name="Employee Payables",
                account_type="Liability",
                parent_account_code="2100",
                is_active=True,
                opening_balance=Decimal('0.00'),
                current_balance=Decimal('0.00'),
                description="Parent account for employee payable accounts"
            )
            session.add(employee_payables)
            session.commit()
            print("Created Employee Payables parent account (2108)")
        
        # Check if categories already exist
        if session.query(EmployeeCategory).first():
            print("Employee categories already exist, skipping seed...")
            return
        
        # Sample employee categories
        categories = [
            {
                "id": "MGMT001",
                "name": "Management",
                "salary_structure": "Monthly",
                "base_rate": 50000.0
            },
            {
                "id": "PROD001", 
                "name": "Production Worker",
                "salary_structure": "Daily",
                "base_rate": 500.0
            },
            {
                "id": "TAIL001",
                "name": "Tailor",
                "salary_structure": "Piece-rate",
                "base_rate": 25.0
            },
            {
                "id": "SUPV001",
                "name": "Supervisor",
                "salary_structure": "Monthly",
                "base_rate": 30000.0
            },
            {
                "id": "HLPR001",
                "name": "Helper",
                "salary_structure": "Daily",
                "base_rate": 300.0
            }
        ]
        
        for cat_data in categories:
            category = EmployeeCategory(**cat_data)
            session.add(category)
        
        session.commit()
        print(f"Seeded {len(categories)} employee categories successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding employee categories: {e}")
    finally:
        session.close()

def seed_sample_employees():
    """Seed some sample employees with automatic account creation."""
    print("Seeding sample employees...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Check if employees already exist
        if session.query(Employee).first():
            print("Employees already exist, skipping seed...")
            return
        
        # Get category IDs (they should exist from seed_employee_categories)
        categories = session.query(EmployeeCategory).all()
        if not categories:
            print("No employee categories found. Please run seed_employee_categories first.")
            return
        
        # Import account generation functions
        from routes.employees import generate_employee_account_code, create_employee_account
        
        # Sample employees with new structure
        employees_data = [
            {
                "id": "EMP001",
                "employee_id": "EMP-001",
                "name": "Rajesh Kumar",
                "category_id": categories[0].id,
                "join_date": datetime(2024, 1, 15),
                "phone": "9876543210",
                "address": "123 Main Street, Mumbai, Maharashtra",
                "status": "Active"
            },
            {
                "id": "EMP002",
                "employee_id": "EMP-002",
                "name": "Priya Sharma",
                "category_id": categories[1].id if len(categories) > 1 else categories[0].id,
                "join_date": datetime(2024, 2, 1),
                "phone": "9876543211", 
                "address": "456 Worker Colony, Mumbai, Maharashtra",
                "status": "Active"
            },
            {
                "id": "EMP003",
                "employee_id": "EMP-003",
                "name": "Amit Patel",
                "category_id": categories[2].id if len(categories) > 2 else categories[0].id,
                "join_date": datetime(2024, 1, 20),
                "phone": "9876543212",
                "address": "789 Industrial Area, Mumbai, Maharashtra",
                "status": "Active"
            },
            {
                "id": "EMP004",
                "employee_id": "EMP-004",
                "name": "Sunita Devi",
                "category_id": categories[3].id if len(categories) > 3 else categories[0].id,
                "join_date": datetime(2024, 1, 10),
                "phone": "9876543213",
                "address": "321 Supervisor Quarters, Mumbai, Maharashtra", 
                "status": "Active"
            },
            {
                "id": "EMP005",
                "employee_id": "EMP-005",
                "name": "Ravi Singh",
                "category_id": categories[4].id if len(categories) > 4 else categories[0].id,
                "join_date": datetime(2024, 3, 1),
                "phone": "9876543214",
                "address": "654 Helper Housing, Mumbai, Maharashtra",
                "status": "Active"
            }
        ]
        
        # Create employees with automatic account creation
        for emp_data in employees_data:
            # Generate account code for this employee
            acc_code = generate_employee_account_code(session, emp_data["name"])
            emp_data["acc_code"] = acc_code
            
            # Create the employee
            employee = Employee(**emp_data)
            session.add(employee)
            session.flush()  # Get the employee ID
            
            # Create the payable account using the data we have
            create_employee_account(session, emp_data["name"], emp_data["employee_id"])
            print(f"Created employee {emp_data['name']} with account {acc_code}")
        
        session.commit()
        print(f"Seeded {len(employees_data)} sample employees with accounts successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding employees: {e}")
        raise
    finally:
        session.close()

def migrate_employees():
    """Run the complete employee migration."""
    print("=== Employee Migration Started ===")
    
    try:
        create_employee_tables()
        seed_employee_categories()
        seed_sample_employees()
        print("=== Employee Migration Completed Successfully ===")
        
    except Exception as e:
        print(f"=== Employee Migration Failed: {e} ===")
        raise

if __name__ == "__main__":
    migrate_employees()
