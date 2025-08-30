#!/usr/bin/env python3
"""Check paymentmode enum values"""
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:rnrinfo@localhost:5432/garments_erp')
    cur = conn.cursor()
    
    # Check paymentmode enum
    cur.execute("""
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (
            SELECT oid 
            FROM pg_type 
            WHERE typname = 'paymentmode'
        )
        ORDER BY enumsortorder;
    """)
    
    rows = cur.fetchall()
    if rows:
        print("paymentmode enum values in database:")
        for row in rows:
            print(f"  '{row[0]}'")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
