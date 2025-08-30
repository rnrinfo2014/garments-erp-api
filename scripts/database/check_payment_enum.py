#!/usr/bin/env python3
"""Check database enum values for payment mode"""
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:rnrinfo@localhost:5432/garments_erp')
    cur = conn.cursor()
    
    # Check PaymentMode enum
    cur.execute("""
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (
            SELECT oid 
            FROM pg_type 
            WHERE typname = 'paymentmodeenum'
        )
        ORDER BY enumsortorder;
    """)
    
    rows = cur.fetchall()
    if rows:
        print("PaymentModeEnum enum values in database:")
        for row in rows:
            print(f"  '{row[0]}'")
    else:
        print("No PaymentModeEnum found, checking other payment-related enums...")
        
        # Check for any payment-related enums
        cur.execute("""
            SELECT typname 
            FROM pg_type 
            WHERE typname LIKE '%payment%' OR typname LIKE '%mode%'
        """)
        
        types = cur.fetchall()
        for type_name in types:
            print(f"Found enum type: {type_name[0]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
