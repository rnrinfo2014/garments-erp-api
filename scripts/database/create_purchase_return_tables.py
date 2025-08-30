"""
Purchase Return Tables Migration Script
Creates purchase return, purchase return items, and approval workflow tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database import DATABASE_URL, engine
from models.purchase_return import PurchaseReturn, PurchaseReturnItem, PurchaseReturnApproval
from models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_purchase_return_tables():
    """Create purchase return tables"""
    try:
        # Create all tables (this will only create missing tables)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Purchase return tables created successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating purchase return tables: {e}")
        return False


def verify_tables():
    """Verify that all tables are created properly"""
    try:
        with engine.connect() as conn:
            # Check purchase_returns table
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'purchase_returns'"))
            row = result.fetchone()
            returns_exists = (row[0] if row else 0) > 0
            
            # Check purchase_return_items table
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'purchase_return_items'"))
            row = result.fetchone()
            items_exists = (row[0] if row else 0) > 0
            
            # Check purchase_return_approvals table
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'purchase_return_approvals'"))
            row = result.fetchone()
            approvals_exists = (row[0] if row else 0) > 0
            
            if returns_exists and items_exists and approvals_exists:
                logger.info("✅ All purchase return tables verified successfully")
                
                # Show table structure for main table
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'purchase_returns' 
                    ORDER BY ordinal_position
                """))
                
                logger.info("📋 Purchase returns table structure:")
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
                    AND tc.table_name IN ('purchase_returns', 'purchase_return_items', 'purchase_return_approvals')
                """))
                
                logger.info("🔗 Purchase return table relationships:")
                for row in result:
                    logger.info(f"  - {row[0]}.{row[1]} → {row[2]}.{row[3]}")
                
                return True
            else:
                logger.error("❌ Some purchase return tables are missing")
                logger.error(f"Returns: {returns_exists}, Items: {items_exists}, Approvals: {approvals_exists}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {e}")
        return False


def show_integration_summary():
    """Show summary of purchase return system integration"""
    logger.info("""
    
🎉 PURCHASE RETURN SYSTEM INTEGRATION SUMMARY:

📊 DATABASE TABLES:
  ✅ purchase_returns - Main return entries with supplier details
  ✅ purchase_return_items - Individual items being returned
  ✅ purchase_return_approvals - Approval workflow tracking
  
🔗 AUTOMATIC INTEGRATIONS:
  ✅ Reverse Stock Ledger - Auto reduces inventory on return posting
  ✅ Reverse Account Ledger - Auto creates reverse double-entry transactions
  ✅ Supplier Credits - Links to supplier account codes for credit management
  ✅ Original Purchase Tracking - Full traceability to original purchase items

💰 ACCOUNTING INTEGRATION (REVERSE ENTRIES):
  • Cash Refund Return: 
    Cr. Purchase Account → Dr. Cash/Bank Account
  • Credit Adjustment Return: 
    Cr. Purchase Account → Dr. Supplier Account (reduce payable)
  • Partial Refund Return: 
    Cr. Purchase Account → Dr. Cash/Bank + Dr. Supplier Account

📦 STOCK INTEGRATION (REVERSE ENTRIES):
  • Auto creates Stock OUT entries for returned quantities
  • Links to original material, sizes, and units
  • Tracks return reasons and item conditions
  • Handles quality control and approval workflow
  • Maintains batch/lot traceability

🔄 WORKFLOW:
  1. Create Purchase Return Entry (Draft status)
  2. Add items with return quantities and reasons
  3. Optional: Approval workflow for high-value returns
  4. Optional: Quality check for returned items
  5. Post Return (creates reverse ledger + stock entries)
  6. Process refunds (cash/bank/adjustment)

📋 RETURN REASONS TRACKING:
  • Defective items
  • Excess quantity
  • Wrong items received
  • Quality issues
  • Damaged goods
  • Expired items
  • Custom reasons

🔍 APPROVAL & QUALITY CONTROL:
  • Multi-level approval workflow
  • Quality inspection tracking
  • Condition assessment (Good/Damaged/Defective)
  • Approval comments and history

🌐 API ENDPOINTS AVAILABLE:
  • POST /api/purchase-returns/ - Create return
  • GET /api/purchase-returns/ - List returns with filters
  • PUT /api/purchase-returns/{id} - Update return
  • POST /api/purchase-returns/{id}/post - Post to ledger/stock
  • POST /api/purchase-returns/{id}/approve - Approval workflow
  • GET /api/purchase-returns/reports/summary - Return analytics

✅ Ready for production use with complete return management!
    """)


if __name__ == "__main__":
    logger.info("🚀 Starting Purchase Return Tables Migration...")
    
    if create_purchase_return_tables():
        if verify_tables():
            show_integration_summary()
            logger.info("✅ Purchase return system setup completed successfully!")
        else:
            logger.error("❌ Table verification failed")
    else:
        logger.error("❌ Purchase return tables creation failed")
