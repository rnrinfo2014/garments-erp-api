"""
Migration script to update employee category table with new fields
"""

from database import engine, Base
from models.employee_category import EmployeeCategory
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

def update_employee_category_table():
    """Update employee category table with new fields."""
    print("Updating employee category table...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Add new columns if they don't exist
        try:
            session.execute(text("ALTER TABLE employee_category ADD COLUMN description TEXT"))
            print("Added description column")
        except Exception as e:
            print(f"Description column might already exist: {e}")
        
        try:
            session.execute(text("ALTER TABLE employee_category ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
            print("Added is_active column")
        except Exception as e:
            print(f"is_active column might already exist: {e}")
        
        session.commit()
        
        # Update existing records to set is_active = TRUE if NULL
        session.execute(text("UPDATE employee_category SET is_active = TRUE WHERE is_active IS NULL"))
        session.commit()
        
        print("Employee category table updated successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error updating employee category table: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    update_employee_category_table()
