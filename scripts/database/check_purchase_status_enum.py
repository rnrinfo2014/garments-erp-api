#!/usr/bin/env python3
"""Check database enum values for purchase status"""
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:rnrinfo@localhost:5432/garments_erp')
    cur = conn.cursor()
    
    # Check PurchaseStatus enum
    cur.execute("""
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (
            SELECT oid 
            FROM pg_type 
            WHERE typname = 'purchasestatus'
        )
        ORDER BY enumsortorder;
    """)
    
    rows = cur.fetchall()
    if rows:
        print("PurchaseStatus enum values in database:")
        for row in rows:
            print(f"  '{row[0]}'")
    else:
        print("No PurchaseStatus enum found in database")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
