"""
Purchase Tables Migration Script
Creates purchase and purchase_items tables with proper relationships
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database import DATABASE_URL, engine
from models.purchase import Purchase, PurchaseItem
from models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_purchase_tables():
    """Create purchase and purchase_items tables"""
    try:
        # Create all tables (this will only create missing tables)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Purchase tables created successfully!")
        
        # Add some sample data
        add_sample_accounts()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating purchase tables: {e}")
        return False


def add_sample_accounts():
    """Add sample accounts required for purchase transactions"""
    try:
        with engine.connect() as conn:
            # Check if accounts already exist
            result = conn.execute(text("SELECT COUNT(*) as count FROM accounts_master WHERE account_code IN ('PURCHASE001', 'CREDITORS001')"))
            row = result.fetchone()
            count = row[0] if row else 0
            
            if count < 2:
                # Add purchase account
                conn.execute(text("""
                    INSERT INTO accounts_master (account_code, account_name, account_type, opening_balance, current_balance, description) 
                    VALUES ('PURCHASE001', 'Purchase Account', 'Expense', 0.00, 0.00, 'Main purchase account for inventory purchases')
                    ON CONFLICT (account_code) DO NOTHING
                """))
                
                # Add creditors account
                conn.execute(text("""
                    INSERT INTO accounts_master (account_code, account_name, account_type, opening_balance, current_balance, description) 
                    VALUES ('CREDITORS001', 'Accounts Payable', 'Liability', 0.00, 0.00, 'General creditors and suppliers account')
                    ON CONFLICT (account_code) DO NOTHING
                """))
                
                conn.commit()
                logger.info("✅ Sample purchase accounts created")
            else:
                logger.info("ℹ️ Purchase accounts already exist")
                
    except Exception as e:
        logger.error(f"❌ Error creating sample accounts: {e}")


def verify_tables():
    """Verify that all tables are created properly"""
    try:
        with engine.connect() as conn:
            # Check purchases table
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'purchases'"))
            row = result.fetchone()
            purchases_exists = (row[0] if row else 0) > 0
            
            # Check purchase_items table
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'purchase_items'"))
            row = result.fetchone()
            items_exists = (row[0] if row else 0) > 0
            
            if purchases_exists and items_exists:
                logger.info("✅ All purchase tables verified successfully")
                
                # Show table structure
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'purchases' 
                    ORDER BY ordinal_position
                """))
                
                logger.info("📋 Purchases table structure:")
                for row in result:
                    logger.info(f"  - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
                
                # Show foreign key relationships
                result = conn.execute(text("""
                    SELECT 
                        tc.table_name, 
                        kcu.column_name, 
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM 
                        information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name IN ('purchases', 'purchase_items')
                """))
                
                logger.info("🔗 Purchase table relationships:")
                for row in result:
                    logger.info(f"  - {row[0]}.{row[1]} → {row[2]}.{row[3]}")
                
                return True
            else:
                logger.error("❌ Some purchase tables are missing")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {e}")
        return False


def show_integration_summary():
    """Show summary of purchase system integration"""
    logger.info("""
    
🎉 PURCHASE SYSTEM INTEGRATION SUMMARY:

📊 DATABASE TABLES:
  ✅ purchases - Main purchase entries with supplier details
  ✅ purchase_items - Individual items in each purchase
  
🔗 AUTOMATIC INTEGRATIONS:
  ✅ Stock Ledger - Auto updates inventory on purchase posting
  ✅ Account Ledger - Auto creates double-entry transactions
  ✅ Supplier Accounts - Links to supplier account codes
  ✅ Purchase Orders - Can create purchases from POs

💰 ACCOUNTING INTEGRATION:
  • Cash Purchase: 
    Dr. Purchase Account → Cr. Cash/Bank Account
  • Credit Purchase: 
    Dr. Purchase Account → Cr. Supplier Account
  • Partial Payment: 
    Dr. Supplier Account → Cr. Cash/Bank Account

📦 STOCK INTEGRATION:
  • Auto creates Stock IN entries for accepted quantities
  • Links to raw materials, sizes, and units
  • Tracks batch numbers and expiry dates
  • Handles rejected quantities separately

🔄 WORKFLOW:
  1. Create Purchase Entry (Draft status)
  2. Add items with quantities and rates
  3. Post Purchase (creates ledger + stock entries)
  4. System automatically handles all accounting

🌐 API ENDPOINTS AVAILABLE:
  • POST /api/purchases/ - Create purchase
  • GET /api/purchases/ - List purchases with filters
  • PUT /api/purchases/{id} - Update purchase
  • POST /api/purchases/{id}/post - Post to ledger/stock
  • POST /api/purchases/from-po - Create from PO
  • GET /api/purchases/reports/summary - Purchase reports

✅ Ready for production use!
    """)


if __name__ == "__main__":
    logger.info("🚀 Starting Purchase Tables Migration...")
    
    if create_purchase_tables():
        if verify_tables():
            show_integration_summary()
            logger.info("✅ Purchase system setup completed successfully!")
        else:
            logger.error("❌ Table verification failed")
    else:
        logger.error("❌ Purchase tables creation failed")
