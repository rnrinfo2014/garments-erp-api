#!/usr/bin/env python3
"""
Quick script to check bill_books table status
"""

from database import engine
from sqlalchemy import text

try:
    print("Checking bill_books table status...")
    
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'bill_books'
        """))
        table_exists = result.fetchone()
        
        if table_exists:
            print("✅ bill_books table EXISTS")
            
            # Check table structure
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'bill_books' 
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Table structure:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
                
            # Check if table has data
            result = conn.execute(text("SELECT COUNT(*) FROM bill_books"))
            count = result.scalar()
            print(f"\n📊 Records in table: {count}")
            
        else:
            print("❌ bill_books table does NOT exist")
            print("You need to create the table first!")
            
except Exception as e:
    print(f"❌ Error checking database: {e}")
    print("Make sure your database connection is working")
