"""
Migration Script: Add Supplier Payment System Tables
Created: 2025-01-25
Purpose: Create comprehensive supplier payment management system with automatic accounting integration

Tables Created:
1. supplier_payments - Main payment entries
2. supplier_payment_bills - Links payments to specific purchase bills
3. supplier_ledger - Running balance ledger for suppliers
4. tds_entries - Tax deduction at source tracking

Features:
- Payment against multiple bills
- TDS calculation and tracking
- Payment mode validation
- Automatic ledger integration
- Partial payment support
- Reconciliation tracking
"""

import sys
sys.path.append('.')

from database import get_db, engine, Base
from models.supplier_payment import SupplierPayment, SupplierPaymentBill, SupplierLedger, TDSEntry
from models.accounts import AccountsMaster
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from datetime import datetime


def check_table_exists(table_name: str) -> bool:
    """Check if table exists in database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_required_accounts(db: Session):
    """Create required accounts for payment processing"""
    
    required_accounts = [
        {
            'account_code': 'CASH_IN_HAND',
            'account_name': 'Cash in Hand',
            'account_type': 'Asset',
            'parent_account_code': 'CURRENT_ASSETS',
            'is_active': True,
            'opening_balance': 0.00
        },
        {
            'account_code': 'BANK_ACCOUNT',
            'account_name': 'Bank Account',
            'account_type': 'Asset',
            'parent_account_code': 'CURRENT_ASSETS',
            'is_active': True,
            'opening_balance': 0.00
        },
        {
            'account_code': 'UPI_ACCOUNT',
            'account_name': 'UPI Payments',
            'account_type': 'Asset',
            'parent_account_code': 'CURRENT_ASSETS',
            'is_active': True,
            'opening_balance': 0.00
        },
        {
            'account_code': 'CREDIT_CARD_ACCOUNT',
            'account_name': 'Credit Card Payments',
            'account_type': 'Liability',
            'parent_account_code': 'CURRENT_LIABILITIES',
            'is_active': True,
            'opening_balance': 0.00
        },
        {
            'account_code': 'TDS_PAYABLE',
            'account_name': 'TDS Payable',
            'account_type': 'Liability',
            'parent_account_code': 'CURRENT_LIABILITIES',
            'is_active': True,
            'opening_balance': 0.00
        },
        {
            'account_code': 'OTHER_DEDUCTIONS',
            'account_name': 'Other Deductions',
            'account_type': 'Expense',
            'parent_account_code': 'INDIRECT_EXPENSES',
            'is_active': True,
            'opening_balance': 0.00
        }
    ]
    
    print("Creating required payment accounts...")
    
    for account_data in required_accounts:
        existing = db.query(AccountsMaster).filter(
            AccountsMaster.account_code == account_data['account_code']
        ).first()
        
        if not existing:
            account = AccountsMaster(
                account_code=account_data['account_code'],
                account_name=account_data['account_name'],
                account_type=account_data['account_type'],
                parent_account_code=account_data['parent_account_code'],
                is_active=account_data['is_active'],
                opening_balance=account_data['opening_balance'],
                created_at=datetime.now().replace(tzinfo=None),
                updated_at=datetime.now().replace(tzinfo=None)
            )
            db.add(account)
            print(f"✓ Created account: {account_data['account_name']}")
        else:
            print(f"✓ Account already exists: {account_data['account_name']}")
    
    try:
        db.commit()
        print("✓ All payment accounts created successfully")
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating accounts: {str(e)}")
        raise


def create_payment_tables():
    """Create all supplier payment related tables"""
    
    print("Starting supplier payment system migration...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine, tables=[
            SupplierPayment.__table__,
            SupplierPaymentBill.__table__,
            SupplierLedger.__table__,
            TDSEntry.__table__
        ])
        
        print("✓ Payment system tables created successfully")
        
        # Create indexes for better performance
        with engine.connect() as connection:
            # Indexes for supplier_payments
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_payments_supplier_id 
                ON supplier_payments(supplier_id);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_payments_payment_date 
                ON supplier_payments(payment_date);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_payments_status 
                ON supplier_payments(status);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_payments_payment_number 
                ON supplier_payments(payment_number);
            """))
            
            # Indexes for supplier_payment_bills
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_payment_bills_payment_id 
                ON supplier_payment_bills(payment_id);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_payment_bills_purchase_id 
                ON supplier_payment_bills(purchase_id);
            """))
            
            # Indexes for supplier_ledger
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_ledger_supplier_id 
                ON supplier_ledger(supplier_id);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_ledger_transaction_date 
                ON supplier_ledger(transaction_date);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supplier_ledger_reference 
                ON supplier_ledger(reference_type, reference_id);
            """))
            
            # Indexes for tds_entries
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tds_entries_payment_id 
                ON tds_entries(payment_id);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tds_entries_supplier_id 
                ON tds_entries(supplier_id);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tds_entries_financial_year 
                ON tds_entries(financial_year, quarter);
            """))
            
            connection.commit()
            
        print("✓ Database indexes created successfully")
        
    except Exception as e:
        print(f"✗ Error creating payment tables: {str(e)}")
        raise


def verify_migration():
    """Verify that all tables were created successfully"""
    
    print("\nVerifying migration...")
    
    tables_to_check = [
        'supplier_payments',
        'supplier_payment_bills', 
        'supplier_ledger',
        'tds_entries'
    ]
    
    missing_tables = []
    
    for table_name in tables_to_check:
        if check_table_exists(table_name):
            print(f"✓ Table '{table_name}' created successfully")
        else:
            missing_tables.append(table_name)
            print(f"✗ Table '{table_name}' not found")
    
    if missing_tables:
        raise Exception(f"Migration incomplete. Missing tables: {missing_tables}")
    
    # Verify foreign key constraints
    print("\nVerifying foreign key constraints...")
    
    with engine.connect() as connection:
        # Check supplier_payments -> suppliers foreign key
        result = connection.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY' 
            AND table_name = 'supplier_payments'
            AND constraint_name LIKE '%supplier_id%'
        """))
        
        row = result.fetchone()
        if row and row[0] > 0:
            print("✓ Supplier payments -> suppliers foreign key constraint exists")
        else:
            print("⚠ Warning: supplier_payments -> suppliers foreign key constraint not found")
        
        # Check supplier_payment_bills -> purchases foreign key
        result = connection.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY' 
            AND table_name = 'supplier_payment_bills'
            AND constraint_name LIKE '%purchase_id%'
        """))
        
        row = result.fetchone()
        if row and row[0] > 0:
            print("✓ Payment bills -> purchases foreign key constraint exists")
        else:
            print("⚠ Warning: supplier_payment_bills -> purchases foreign key constraint not found")
    
    print("✓ Migration verification completed")


def add_sample_data():
    """Add sample data for testing (optional)"""
    
    print("\nWould you like to add sample payment data for testing? (y/n): ", end="")
    choice = input().lower().strip()
    
    if choice == 'y':
        db = next(get_db())
        try:
            # Check if we have suppliers and purchases to work with
            from models.suppliers import Supplier
            from models.purchase import Purchase
            
            supplier_count = db.query(Supplier).count()
            purchase_count = db.query(Purchase).filter(Purchase.status == "Posted").count()
            
            if supplier_count == 0 or purchase_count == 0:
                print("⚠ Warning: No suppliers or posted purchases found. Skipping sample data creation.")
                return
            
            print(f"Found {supplier_count} suppliers and {purchase_count} posted purchases")
            print("Sample data creation would require more detailed setup. Skipping for now.")
            print("You can create payments through the API endpoints once the system is running.")
            
        except Exception as e:
            print(f"Error checking for sample data prerequisites: {str(e)}")
        finally:
            db.close()
    else:
        print("Skipping sample data creation")


def main():
    """Main migration function"""
    
    print("=" * 60)
    print("SUPPLIER PAYMENT SYSTEM MIGRATION")
    print("=" * 60)
    
    try:
        # Step 1: Create payment system tables
        create_payment_tables()
        
        # Step 2: Create required accounts
        db = next(get_db())
        try:
            create_required_accounts(db)
        finally:
            db.close()
        
        # Step 3: Verify migration
        verify_migration()
        
        # Step 4: Optional sample data
        add_sample_data()
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSupplier Payment System Features:")
        print("✓ Payment against multiple purchase bills")
        print("✓ Multiple payment modes (Cash, Bank, UPI, etc.)")
        print("✓ TDS calculation and tracking")
        print("✓ Automatic ledger integration")
        print("✓ Payment reconciliation")
        print("✓ Supplier ledger with running balance")
        print("✓ Comprehensive reporting")
        
        print("\nAPI Endpoints Available:")
        print("• POST /supplier-payments/ - Create payment")
        print("• GET /supplier-payments/outstanding-bills/{supplier_id} - Get outstanding bills")
        print("• POST /supplier-payments/pay-against-bills - Pay specific bills")
        print("• GET /supplier-payments/reports/summary - Payment summary")
        print("• GET /supplier-payments/supplier-ledger/{supplier_id} - Supplier ledger")
        
        print("\nNext Steps:")
        print("1. Update main.py to include supplier payment routes")
        print("2. Test API endpoints with sample data")
        print("3. Configure TDS sections as per tax regulations")
        print("4. Set up bank account mappings")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure database is running and accessible")
        print("2. Check if supplier and purchase tables exist")
        print("3. Verify database user has create table permissions")
        print("4. Check database connection settings")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
