#!/usr/bin/env python
"""
Standalone migration script for Material Master System
Creates and seeds CategoryMaster, SizeMaster, UnitMaster, and RawMaterialMaster tables
"""

import sys
import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Text, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_material_master_tables():
    """Create material master tables"""
    
    metadata = MetaData()
    
    # Category Master table
    category_master = Table(
        'category_master',
        metadata,
        Column('id', String(50), primary_key=True),
        Column('category_name', String(100), nullable=False, unique=True),
        Column('description', Text),
        Column('is_active', Boolean, default=True, nullable=False),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), server_default=func.now()),
        extend_existing=True
    )
    
    # Size Master table
    size_master = Table(
        'size_master',
        metadata,
        Column('id', String(50), primary_key=True),
        Column('size_name', String(100), nullable=False, unique=True),
        Column('size_code', String(20), nullable=False, unique=True),
        Column('description', Text),
        Column('is_active', Boolean, default=True, nullable=False),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), server_default=func.now()),
        extend_existing=True
    )
    
    # Unit Master table
    unit_master = Table(
        'unit_master',
        metadata,
        Column('id', String(50), primary_key=True),
        Column('unit_name', String(100), nullable=False, unique=True),
        Column('unit_code', String(20), nullable=False, unique=True),
        Column('description', Text),
        Column('is_active', Boolean, default=True, nullable=False),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), server_default=func.now()),
        extend_existing=True
    )
    
    # Raw Material Master table
    raw_material_master = Table(
        'raw_material_master',
        metadata,
        Column('id', String(50), primary_key=True),
        Column('material_name', String(100), nullable=False),
        Column('material_code', String(50), nullable=False, unique=True),
        Column('category_id', String(50), ForeignKey('category_master.id'), nullable=False),
        Column('size_id', String(50), ForeignKey('size_master.id'), nullable=False),
        Column('unit_id', String(50), ForeignKey('unit_master.id'), nullable=False),
        Column('standard_rate', Numeric(15, 2), default=0.00),
        Column('minimum_stock', Numeric(15, 2), default=0.00),
        Column('maximum_stock', Numeric(15, 2), default=0.00),
        Column('reorder_level', Numeric(15, 2), default=0.00),
        Column('description', Text),
        Column('is_active', Boolean, default=True, nullable=False),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), server_default=func.now()),
        extend_existing=True
    )
    
    # Create tables
    metadata.create_all(engine)
    print("✅ All material master tables created successfully")
    
    return metadata

def seed_material_master_data():
    """Seed initial data for all material masters"""
    
    db = SessionLocal()
    try:
        # Check if data already exists
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM category_master")).fetchone()
            existing_categories = result[0] if result else 0
            
            result = conn.execute(text("SELECT COUNT(*) FROM size_master")).fetchone()
            existing_sizes = result[0] if result else 0
            
            result = conn.execute(text("SELECT COUNT(*) FROM unit_master")).fetchone()
            existing_units = result[0] if result else 0
            
            result = conn.execute(text("SELECT COUNT(*) FROM raw_material_master")).fetchone()
            existing_materials = result[0] if result else 0
        
        if existing_categories > 0 or existing_sizes > 0 or existing_units > 0 or existing_materials > 0:
            print(f"📊 Tables already have data:")
            print(f"   - Categories: {existing_categories}")
            print(f"   - Sizes: {existing_sizes}")
            print(f"   - Units: {existing_units}")
            print(f"   - Raw Materials: {existing_materials}")
            return
        
        # Seed Category Master
        with engine.connect() as conn:
            categories = [
                ("CAT001", "Fabric", "All types of fabrics"),
                ("CAT002", "Thread", "Sewing and embroidery threads"),
                ("CAT003", "Button", "All types of buttons"),
                ("CAT004", "Zipper", "All types of zippers"),
                ("CAT005", "Packing Material", "Packaging and shipping materials"),
                ("CAT006", "Lining", "Garment lining materials"),
                ("CAT007", "Trim", "Decorative trims and accessories"),
            ]
            
            for cat_id, name, desc in categories:
                conn.execute(text("""
                    INSERT INTO category_master (id, category_name, description, is_active) 
                    VALUES (:id, :name, :desc, :active)
                """), {"id": cat_id, "name": name, "desc": desc, "active": True})
            
            conn.commit()
            print(f"✅ Created {len(categories)} categories")
        
        # Seed Size Master
        with engine.connect() as conn:
            sizes = [
                ("SIZ001", "35 inch", "35IN", "35 inch width"),
                ("SIZ002", "44 inch", "44IN", "44 inch width"),
                ("SIZ003", "58 inch", "58IN", "58 inch width"),
                ("SIZ004", "Free Size", "FREE", "One size fits all"),
                ("SIZ005", "Small", "S", "Small size"),
                ("SIZ006", "Medium", "M", "Medium size"),
                ("SIZ007", "Large", "L", "Large size"),
                ("SIZ008", "Extra Large", "XL", "Extra Large size"),
            ]
            
            for size_id, name, code, desc in sizes:
                conn.execute(text("""
                    INSERT INTO size_master (id, size_name, size_code, description, is_active) 
                    VALUES (:id, :name, :code, :desc, :active)
                """), {"id": size_id, "name": name, "code": code, "desc": desc, "active": True})
            
            conn.commit()
            print(f"✅ Created {len(sizes)} sizes")
        
        # Seed Unit Master
        with engine.connect() as conn:
            units = [
                ("UNT001", "Meter", "MTR", "Length measurement in meters"),
                ("UNT002", "Kilogram", "KG", "Weight measurement in kilograms"),
                ("UNT003", "Piece", "PCS", "Individual pieces/count"),
                ("UNT004", "Roll", "ROLL", "Fabric rolls"),
                ("UNT005", "Yard", "YRD", "Length measurement in yards"),
                ("UNT006", "Spool", "SPOOL", "Thread spools"),
                ("UNT007", "Box", "BOX", "Packaging boxes"),
                ("UNT008", "Gram", "GM", "Weight measurement in grams"),
            ]
            
            for unit_id, name, code, desc in units:
                conn.execute(text("""
                    INSERT INTO unit_master (id, unit_name, unit_code, description, is_active) 
                    VALUES (:id, :name, :code, :desc, :active)
                """), {"id": unit_id, "name": name, "code": code, "desc": desc, "active": True})
            
            conn.commit()
            print(f"✅ Created {len(units)} units")
        
        # Seed Raw Material Master
        with engine.connect() as conn:
            raw_materials = [
                ("RM001", "Smart Plus Slub", "SPS001", "CAT001", "SIZ002", "UNT001", 
                 180.00, 50.00, 500.00, 100.00, "Premium slub cotton fabric"),
                ("RM002", "Smart Plus Check", "SPC001", "CAT001", "SIZ002", "UNT001", 
                 200.00, 30.00, 300.00, 75.00, "Premium check pattern cotton fabric"),
                ("RM003", "Smart Plus Plain", "SPP001", "CAT001", "SIZ002", "UNT001", 
                 160.00, 75.00, 750.00, 150.00, "Premium plain cotton fabric"),
                ("RM004", "Cotton Thread - White", "CTW001", "CAT002", "SIZ004", "UNT006", 
                 25.00, 100.00, 1000.00, 200.00, "White cotton sewing thread"),
                ("RM005", "Plastic Button - Navy", "PBN001", "CAT003", "SIZ005", "UNT003", 
                 1.50, 500.00, 5000.00, 1000.00, "Navy blue plastic shirt buttons"),
                ("RM006", "Metal Zipper - Black", "MZB001", "CAT004", "SIZ006", "UNT003", 
                 15.00, 100.00, 1000.00, 250.00, "Black metal zipper for jackets"),
                ("RM007", "Poly Bag - Clear", "PBC001", "CAT005", "SIZ006", "UNT003", 
                 0.75, 1000.00, 10000.00, 2000.00, "Clear polybags for garment packaging"),
            ]
            
            for (rm_id, name, code, cat_id, size_id, unit_id, 
                 std_rate, min_stock, max_stock, reorder, desc) in raw_materials:
                conn.execute(text("""
                    INSERT INTO raw_material_master 
                    (id, material_name, material_code, category_id, size_id, unit_id,
                     standard_rate, minimum_stock, maximum_stock, reorder_level, 
                     description, is_active) 
                    VALUES (:id, :name, :code, :cat_id, :size_id, :unit_id,
                            :std_rate, :min_stock, :max_stock, :reorder, :desc, :active)
                """), {
                    "id": rm_id, "name": name, "code": code, "cat_id": cat_id,
                    "size_id": size_id, "unit_id": unit_id, "std_rate": std_rate,
                    "min_stock": min_stock, "max_stock": max_stock, "reorder": reorder,
                    "desc": desc, "active": True
                })
            
            conn.commit()
            print(f"✅ Created {len(raw_materials)} raw materials")
        
        print("\n🎉 Material Master System Migration completed successfully!")
        
        # Display summary
        print("\n📋 Created Data Summary:")
        print("=" * 50)
        print("CATEGORIES: Fabric, Thread, Button, Zipper, Packing Material, Lining, Trim")
        print("SIZES: 35-58 inch widths, Free Size, S/M/L/XL")
        print("UNITS: Meter, Kilogram, Piece, Roll, Yard, Spool, Box, Gram")
        print("RAW MATERIALS: Smart Plus fabrics, Cotton Thread, Buttons, Zippers, Poly Bags")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise
    
    finally:
        db.close()

def main():
    """Main migration function"""
    print("🚀 Starting Material Master System Migration...")
    
    # Create tables
    create_material_master_tables()
    
    # Seed data
    seed_material_master_data()
    
    print("✅ Migration completed! Ready for API testing.")
    print("📍 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
