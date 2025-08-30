#!/usr/bin/env python3
from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Check what tables exist
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"))
        tables = [row[0] for row in result]
        print("Existing tables:")
        for table in tables:
            print(f"  - {table}")
        
        # Check if suppliers table exists and has the right structure
        if 'suppliers' in tables:
            print("\nSuppliers table structure:")
            result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'suppliers' ORDER BY ordinal_position;"))
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
        
        # Check stock_ledger table structure if exists
        if 'stock_ledger' in tables:
            print("\nStock ledger table structure:")
            result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'stock_ledger' ORDER BY ordinal_position;"))
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
            
            # Check foreign key constraints
            print("\nStock ledger foreign key constraints:")
            result = conn.execute(text("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name='stock_ledger';
            """))
            for row in result:
                print(f"  - {row[1]} -> {row[2]}.{row[3]}")
                
except Exception as e:
    print(f"Error: {e}")
