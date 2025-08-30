#!/usr/bin/env python3
"""
Database constraint fix script
"""

from sqlalchemy import text
from database import engine, SessionLocal
import os

def check_and_fix_constraints():
    """Check and fix database constraints"""
    print("=== Database Constraint Check ===")
    
    db = SessionLocal()
    
    try:
        # Check if the foreign key constraint exists
        print("1. Checking existing constraints...")
        
        result = db.execute(text("""
            SELECT conname, contype 
            FROM pg_constraint 
            WHERE conname LIKE '%stock_ledger%supplier%'
        """))
        
        constraints = result.fetchall()
        print(f"Found {len(constraints)} stock_ledger supplier constraints:")
        for constraint in constraints:
            print(f"  - {constraint[0]} (type: {constraint[1]})")
        
        # If foreign key constraint exists, drop it
        if constraints:
            print("\n2. Dropping foreign key constraint...")
            try:
                db.execute(text("ALTER TABLE stock_ledger DROP CONSTRAINT IF EXISTS stock_ledger_supplier_id_fkey"))
                db.commit()
                print("✓ Foreign key constraint dropped successfully!")
            except Exception as e:
                print(f"✗ Failed to drop constraint: {e}")
                db.rollback()
        else:
            print("✓ No problematic constraints found!")
        
        # Check if suppliers exist
        print("\n3. Checking suppliers table...")
        result = db.execute(text("SELECT id, supplier_name FROM suppliers LIMIT 5"))
        suppliers = result.fetchall()
        print(f"Found {len(suppliers)} suppliers:")
        for supplier in suppliers:
            print(f"  - ID {supplier[0]}: {supplier[1]}")
            
        # Check if raw materials exist
        print("\n4. Checking raw materials...")
        result = db.execute(text("SELECT id, raw_material_name FROM raw_material_master LIMIT 5"))
        materials = result.fetchall()
        print(f"Found {len(materials)} raw materials:")
        for material in materials:
            print(f"  - ID {material[0]}: {material[1]}")
            
        # Check if sizes exist
        print("\n5. Checking sizes...")
        result = db.execute(text("SELECT id, size_name FROM size_master LIMIT 5"))
        sizes = result.fetchall()
        print(f"Found {len(sizes)} sizes:")
        for size in sizes:
            print(f"  - ID {size[0]}: {size[1]}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

def create_test_data():
    """Create some test data if missing"""
    print("\n=== Creating Test Data ===")
    
    db = SessionLocal()
    
    try:
        # Check if we need to create test raw materials
        result = db.execute(text("SELECT COUNT(*) FROM raw_material_master WHERE id IN ('RM001', 'RM002')"))
        count = result.scalar() or 0
        
        if count < 2:
            print("Creating test raw materials...")
            db.execute(text("""
                INSERT INTO raw_material_master (id, raw_material_name, description, unit_id, category_id, created_by)
                VALUES 
                ('RM001', 'Test Material 1', 'Test material for opening stock', 'KG', 'CAT001', 'system'),
                ('RM002', 'Test Material 2', 'Another test material', 'MTR', 'CAT001', 'system')
                ON CONFLICT (id) DO NOTHING
            """))
        
        # Check if we need to create test sizes
        result = db.execute(text("SELECT COUNT(*) FROM size_master WHERE id IN ('SIZ001', 'SIZ002')"))
        count = result.scalar() or 0
        
        if count < 2:
            print("Creating test sizes...")
            db.execute(text("""
                INSERT INTO size_master (id, size_name, description, created_by)
                VALUES 
                ('SIZ001', 'Small', 'Small size', 'system'),
                ('SIZ002', 'Medium', 'Medium size', 'system')
                ON CONFLICT (id) DO NOTHING
            """))
        
        # Check if we need to create test suppliers
        result = db.execute(text("SELECT COUNT(*) FROM suppliers WHERE id IN (1, 2)"))
        count = result.scalar() or 0
        
        if count < 2:
            print("Creating test suppliers...")
            db.execute(text("""
                INSERT INTO suppliers (id, supplier_name, supplier_type, created_by)
                VALUES 
                (1, 'Test Supplier 1', 'UNREGISTERED', 'system'),
                (2, 'Test Supplier 2', 'REGISTERED', 'system')
                ON CONFLICT (id) DO NOTHING
            """))
        
        db.commit()
        print("✓ Test data created successfully!")
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_constraints()
    create_test_data()
    print("\n=== Database fix complete! ===")
