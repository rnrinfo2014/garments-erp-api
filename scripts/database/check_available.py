#!/usr/bin/env python3
from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Show available raw materials
        result = conn.execute(text("SELECT id, material_name FROM raw_material_master ORDER BY id LIMIT 5;"))
        materials = result.fetchall()
        print("Available raw materials:")
        for material in materials:
            print(f"  ID: {material[0]}, Name: {material[1]}")
            
        # Show available sizes
        result = conn.execute(text("SELECT id, size_name FROM size_master ORDER BY id LIMIT 5;"))  
        sizes = result.fetchall()
        print("\nAvailable sizes:")
        for size in sizes:
            print(f"  ID: {size[0]}, Name: {size[1]}")
                
except Exception as e:
    print(f"Error: {e}")
