#!/usr/bin/env python3
"""Check database enum values"""
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:rnrinfo@localhost:5432/garments_erp')
    cur = conn.cursor()
    
    # Check if the enum type exists
    cur.execute("""
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (
            SELECT oid 
            FROM pg_type 
            WHERE typname = 'purchasetype'
        )
        ORDER BY enumsortorder;
    """)
    
    rows = cur.fetchall()
    if rows:
        print("PurchaseType enum values in database:")
        for row in rows:
            print(f"  '{row[0]}'")
    else:
        print("No PurchaseType enum found in database")
    
    # Also check the actual table structure
    cur.execute("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'purchases' AND column_name = 'purchase_type';
    """)
    
    type_info = cur.fetchall()
    if type_info:
        print(f"\nColumn definition: {type_info[0]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
