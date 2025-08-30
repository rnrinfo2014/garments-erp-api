#!/usr/bin/env python3
"""
Database migration script to add state_id column to company_details table
"""
import asyncio
from sqlalchemy import text
from database import engine


async def check_column_exists():
    """Check if state_id column exists in company_details table"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'company_details' 
            AND column_name = 'state_id'
        """))
        return result.fetchone() is not None


async def add_state_id_column():
    """Add state_id column to company_details table"""
    try:
        with engine.connect() as conn:
            # Add the state_id column as nullable integer with foreign key
            conn.execute(text("""
                ALTER TABLE company_details 
                ADD COLUMN state_id INTEGER
            """))
            
            # Add foreign key constraint
            conn.execute(text("""
                ALTER TABLE company_details 
                ADD CONSTRAINT fk_company_state 
                FOREIGN KEY (state_id) REFERENCES states(id)
            """))
            
            conn.commit()
            print("✅ Successfully added state_id column to company_details table")
            return True
            
    except Exception as e:
        print(f"❌ Error adding state_id column: {e}")
        return False


async def main():
    """Main migration function"""
    print("🔍 Checking database schema...")
    
    # Check if column already exists
    column_exists = await check_column_exists()
    
    if column_exists:
        print("✅ state_id column already exists in company_details table")
        return
    
    print("➕ Adding state_id column to company_details table...")
    success = await add_state_id_column()
    
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")


if __name__ == "__main__":
    asyncio.run(main())
