"""
Sales System Removal Script
Safely removes all sales-related components from the ERP system
"""

from sqlalchemy import text
from database import SessionLocal, engine
import os
import shutil
from pathlib import Path

def backup_files():
    """Create backup of sales-related files before deletion"""
    backup_dir = Path("sales_backup_" + str(datetime.now().strftime("%Y%m%d_%H%M%S")))
    backup_dir.mkdir(exist_ok=True)
    
    sales_files = [
        # Models
        "models/sales.py",
        "models/sales_bills.py", 
        "models/income_receipts.py",
        
        # Schemas
        "schemas/sales.py",
        "schemas/sales_bills.py",
        "schemas/income_receipts.py",
        
        # Routes
        "routes/sales.py",
        "routes/sales_bills.py",
        "routes/income_receipts.py",
        "routes/sales_bills_backup.py",
        "routes/sales_bills_fixed.py",
        
        # Scripts
        "create_sales_tables.py",
        "create_income_receipt_tables.py",
        "migrate_sales.py",
        "migrate_sales_tables.py",
        
        # Tests
        "test_sales_api.py",
        "test_sales_bills_playwright.py"
    ]
    
    for file_path in sales_files:
        if os.path.exists(file_path):
            dest_path = backup_dir / file_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_path)
            print(f"Backed up: {file_path}")
    
    return backup_dir

def remove_database_tables():
    """Remove all sales-related database tables"""
    db = SessionLocal()
    
    try:
        # Tables to drop (in order to handle foreign key dependencies)
        tables_to_drop = [
            # Income receipt system tables
            "receipt_bill_allocations",
            "receipt_templates", 
            "income_receipts",
            
            # Sales bill system tables
            "sales_bill_items",
            "sales_bill_payments", 
            "sales_bills",
            
            # Legacy sales tables
            "sale_items",
            "sale_payments",
            "sales",
            
            # Backup tables
            "sale_items_backup_20250827_092241",
            "sale_payments_backup_20250827_092242",
            "sales_backup_20250827_092242"
        ]
        
        print("🗑️  Removing sales-related database tables...")
        
        for table in tables_to_drop:
            try:
                # Check if table exists
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = '{table}'
                    )
                """)).fetchone()
                
                if result[0]:  # Table exists
                    db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    print(f"  ✅ Dropped table: {table}")
                else:
                    print(f"  ℹ️  Table not found: {table}")
                    
            except Exception as e:
                print(f"  ❌ Error dropping table {table}: {e}")
        
        # Remove enum types if they exist
        enum_types = [
            "salesbillstatus",
            "salesbillpaymentstatus", 
            "salesbilltype",
            "taxtype"
        ]
        
        for enum_type in enum_types:
            try:
                db.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
                print(f"  ✅ Dropped enum type: {enum_type}")
            except Exception as e:
                print(f"  ℹ️  Enum type {enum_type} not found or couldn't be dropped")
        
        db.commit()
        print("✅ Database cleanup completed successfully")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Database cleanup failed: {e}")
        raise
    finally:
        db.close()

def remove_sales_files():
    """Remove sales-related Python files"""
    files_to_remove = [
        # Models
        "models/sales.py",
        "models/sales_bills.py", 
        "models/income_receipts.py",
        
        # Schemas
        "schemas/sales.py",
        "schemas/sales_bills.py",
        "schemas/income_receipts.py",
        
        # Routes
        "routes/sales.py",
        "routes/sales_bills.py",
        "routes/income_receipts.py",
        "routes/sales_bills_backup.py",
        "routes/sales_bills_fixed.py",
        
        # Scripts
        "create_sales_tables.py",
        "create_income_receipt_tables.py",
        "migrate_sales.py",
        "migrate_sales_tables.py",
        
        # Tests
        "test_sales_api.py",
        "test_sales_bills_playwright.py"
    ]
    
    print("🗑️  Removing sales-related Python files...")
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"  ✅ Removed file: {file_path}")
        else:
            print(f"  ℹ️  File not found: {file_path}")

def update_route_imports():
    """Remove sales route imports from main route file"""
    routes_init_path = "routes/__init__.py"
    
    if os.path.exists(routes_init_path):
        with open(routes_init_path, 'r') as f:
            content = f.read()
        
        # Remove sales-related imports and route inclusions
        lines_to_remove = [
            "from .sales import router as sales_router",
            "from .sales_bills import router as sales_bills_router", 
            "from .income_receipts import router as income_receipts_router",
            "api_router.include_router(sales_router, prefix=\"/api\", tags=[\"sales\"])",
            "api_router.include_router(sales_bills_router, prefix=\"/api\", tags=[\"sales-bills\"])",
            "api_router.include_router(income_receipts_router, prefix=\"/api\", tags=[\"income-receipts\"])"
        ]
        
        updated_content = content
        for line in lines_to_remove:
            updated_content = updated_content.replace(line + "\n", "")
            updated_content = updated_content.replace(line, "")
        
        with open(routes_init_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ Updated routes/__init__.py")

def clean_documentation():
    """Remove sales-related documentation"""
    docs_to_remove = [
        "SALES_API_GUIDE.md",
        "INCOME_RECEIPT_SYSTEM_GUIDE.md"
    ]
    
    for doc in docs_to_remove:
        if os.path.exists(doc):
            os.remove(doc)
            print(f"  ✅ Removed documentation: {doc}")

if __name__ == "__main__":
    import datetime
    
    print("🚨 SALES SYSTEM REMOVAL SCRIPT")
    print("=" * 50)
    print("This will remove ALL sales-related components:")
    print("• Database tables")
    print("• Python files (models, schemas, routes)")
    print("• Documentation")
    print("• Route imports")
    print("=" * 50)
    
    confirm = input("Are you sure you want to proceed? Type 'YES' to confirm: ")
    
    if confirm != "YES":
        print("❌ Operation cancelled")
        exit(1)
    
    try:
        # Step 1: Backup files
        print("\n📦 Creating backup...")
        backup_dir = backup_files()
        print(f"✅ Backup created in: {backup_dir}")
        
        # Step 2: Remove database tables
        print("\n🗃️  Cleaning database...")
        remove_database_tables()
        
        # Step 3: Remove Python files
        print("\n📁 Removing files...")
        remove_sales_files()
        
        # Step 4: Update route imports
        print("\n🔧 Updating imports...")
        update_route_imports()
        
        # Step 5: Clean documentation
        print("\n📚 Cleaning documentation...")
        clean_documentation()
        
        print("\n" + "=" * 50)
        print("✅ SALES SYSTEM REMOVAL COMPLETED SUCCESSFULLY")
        print("=" * 50)
        print(f"📦 Backup available in: {backup_dir}")
        print("🔄 Please restart your API server")
        
    except Exception as e:
        print(f"\n❌ REMOVAL FAILED: {e}")
        print("Check the backup and manual cleanup may be required")
