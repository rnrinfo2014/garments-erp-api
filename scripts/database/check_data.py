#!/usr/bin/env python3
from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Check if supplier with ID 1 exists
        result = conn.execute(text("SELECT id, supplier_name FROM suppliers WHERE id = 1;"))
        supplier = result.fetchone()
        
        if supplier:
            print(f"Supplier ID 1 exists: {supplier[1]}")
        else:
            print("Supplier ID 1 does NOT exist")
            
        # Show all suppliers
        result = conn.execute(text("SELECT id, supplier_name FROM suppliers ORDER BY id;"))
        suppliers = result.fetchall()
        print(f"\nAll suppliers ({len(suppliers)} total):")
        for supplier in suppliers:
            print(f"  ID {supplier[0]}: {supplier[1]}")
            
        # Check raw materials
        result = conn.execute(text("SELECT id FROM raw_material_master WHERE id = 'COTTON001';"))
        material = result.fetchone()
        if material:
            print(f"\nRaw material COTTON001 exists")
        else:
            print(f"\nRaw material COTTON001 does NOT exist")
            
        # Check sizes  
        result = conn.execute(text("SELECT id FROM size_master WHERE id = 'MEDIUM';"))
        size = result.fetchone()
        if size:
            print(f"Size MEDIUM exists")
        else:
            print(f"Size MEDIUM does NOT exist")
                
except Exception as e:
    print(f"Error: {e}")
