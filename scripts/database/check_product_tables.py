#!/usr/bin/env python3
"""Check if product management tables exist"""
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:rnrinfo@localhost:5432/garments_erp')
    cur = conn.cursor()
    
    # Check if product management tables exist
    product_tables = [
        'product_sizes',
        'product_sleeve_types', 
        'product_designs',
        'products',
        'product_variants',
        'product_stock_ledger'
    ]
    
    for table in product_tables:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table,))
        
        exists = cur.fetchone()[0]
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"{table}: {status}")
        
        if exists:
            # Count records
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  Records: {count}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
