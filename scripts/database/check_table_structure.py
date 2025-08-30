#!/usr/bin/env python3
"""
Check table structure for debugging foreign key issues
"""

from database import SessionLocal
from sqlalchemy import text

def check_table_structure():
    session = SessionLocal()
    try:
        # Check ledger_transactions table structure
        print("=== ledger_transactions table columns ===")
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'ledger_transactions' 
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"{row[0]} - {row[1]} - {row[2]}")
            
        print("\n=== accounts_master table columns ===")
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'accounts_master' 
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"{row[0]} - {row[1]} - {row[2]}")
            
        # Check if the tables exist
        print("\n=== Table existence check ===")
        result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('ledger_transactions', 'accounts_master', 'sales', 'sale_items', 'sale_payments')
            AND table_schema = 'public'
        """))
        
        existing_tables = [row[0] for row in result]
        print(f"Existing tables: {existing_tables}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_table_structure()
