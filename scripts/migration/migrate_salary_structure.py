"""
Migration script to restructure salary management:
- Remove base_rate from employee_category table
- Add base_rate to employees table
"""

from database import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

def migrate_salary_structure():
    """Migrate salary structure from categories to individual employees."""
    print("Migrating salary structure...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Step 1: Add base_rate column to employees table
        try:
            session.execute(text("ALTER TABLE employees ADD COLUMN base_rate FLOAT"))
            print("Added base_rate column to employees table")
        except Exception as e:
            print(f"base_rate column might already exist in employees table: {e}")
        
        # Step 2: Migrate existing data - copy category base_rate to employees
        print("Migrating existing salary data...")
        migrate_query = text("""
            UPDATE employees 
            SET base_rate = (
                SELECT ec.base_rate 
                FROM employee_category ec 
                WHERE ec.id = employees.category_id
            )
            WHERE employees.base_rate IS NULL
        """)
        session.execute(migrate_query)
        print("Updated employee records with base_rate from categories")
        
        # Step 3: Set default base_rate for any employees that still don't have one
        default_rate_query = text("""
            UPDATE employees 
            SET base_rate = 25000.0 
            WHERE base_rate IS NULL
        """)
        session.execute(default_rate_query)
        print("Set default base_rate for any employees without salary")
        
        session.commit()
        
        # Step 4: Make base_rate NOT NULL in employees table
        try:
            session.execute(text("ALTER TABLE employees ALTER COLUMN base_rate SET NOT NULL"))
            print("Made base_rate NOT NULL in employees table")
        except Exception as e:
            print(f"Could not set NOT NULL constraint: {e}")
        
        # Step 5: Remove base_rate column from employee_category table
        try:
            session.execute(text("ALTER TABLE employee_category DROP COLUMN base_rate"))
            print("Removed base_rate column from employee_category table")
        except Exception as e:
            print(f"Could not remove base_rate from employee_category: {e}")
        
        session.commit()
        print("Salary structure migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error migrating salary structure: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_salary_structure()
