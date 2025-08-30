#!/usr/bin/env python3

import database
from sqlalchemy import text

def check_tables():
    """Check what tables exist in the database"""
    try:
        db = database.SessionLocal()
        
        # Check all tables
        result = db.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        )).fetchall()
        
        print("All tables in database:")
        for row in result:
            print(f"  - {row[0]}")
        
        # Check for accounts table specifically
        accounts_tables = [row[0] for row in result if 'account' in row[0].lower()]
        print(f"\nAccount-related tables: {accounts_tables}")
        
        # Check accounts_master table structure if it exists
        if 'accounts_master' in [row[0] for row in result]:
            print("\naccounts_master table structure:")
            columns = db.execute(text(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'accounts_master' ORDER BY ordinal_position;"
            )).fetchall()
            
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        else:
            print("\naccounts_master table does not exist!")
        
        db.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tables()
