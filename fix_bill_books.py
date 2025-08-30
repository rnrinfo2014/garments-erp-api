#!/usr/bin/env python3
"""
Manual fix for bill_books table schema
"""

from database import engine
from sqlalchemy import text

try:
    print("🔧 Fixing bill_books table schema...")
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        
        try:
            # Check if tax_type column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'bill_books' AND column_name = 'tax_type'
            """))
            
            if not result.fetchone():
                print("Adding tax_type column...")
                # Add the tax_type column directly (enum type already exists)
                conn.execute(text("""
                    ALTER TABLE bill_books 
                    ADD COLUMN tax_type taxtype DEFAULT 'INCLUDE_TAX'
                """))
            else:
                print("tax_type column already exists")
            
            # Update existing records based on old boolean columns
            print("Updating existing records...")
            conn.execute(text("""
                UPDATE bill_books
                SET tax_type = CASE
                    WHEN with_tax = true AND without_tax = false THEN 'INCLUDE_TAX'::taxtype
                    WHEN with_tax = false AND without_tax = true THEN 'WITHOUT_TAX'::taxtype
                    ELSE 'INCLUDE_TAX'::taxtype
                END
                WHERE tax_type IS NULL OR tax_type = 'INCLUDE_TAX'::taxtype
            """))
            
            # Check if starting_number column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'bill_books' AND column_name = 'starting_number'
            """))
            
            if not result.fetchone():
                print("Adding starting_number column...")
                conn.execute(text("""
                    ALTER TABLE bill_books 
                    ADD COLUMN starting_number INTEGER DEFAULT 1
                """))
            else:
                print("starting_number column already exists")
            
            # Update starting_number for existing records
            conn.execute(text("""
                UPDATE bill_books 
                SET starting_number = 1 
                WHERE starting_number IS NULL
            """))
            
            # Commit the transaction
            trans.commit()
            print("✅ Schema update completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error during schema update: {e}")
            raise
            
except Exception as e:
    print(f"❌ Connection error: {e}")
