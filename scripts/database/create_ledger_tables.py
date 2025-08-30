"""
Database Migration Script for Ledger Transaction Tables
Run this script to create the ledger transaction tables in your database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database import DATABASE_URL, Base
from models.ledger_transaction import LedgerTransaction, TransactionBatch, TransactionTemplate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_ledger_transaction_tables():
    """Create ledger transaction tables"""
    try:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL is not configured")
            
        engine = create_engine(DATABASE_URL)
        
        logger.info("Creating ledger transaction tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        logger.info("✅ Ledger transaction tables created successfully!")
        
        # Create some sample accounts if they don't exist
        with engine.connect() as conn:
            # Check if sample accounts exist
            result = conn.execute(text("SELECT COUNT(*) FROM accounts_master"))
            account_count = result.scalar()
            
            if account_count == 0:
                logger.info("Creating sample accounts...")
                
                sample_accounts = [
                    ("CASH001", "Cash in Hand", "Asset", None, True, 0.00, 0.00, "Cash account for daily transactions"),
                    ("BANK001", "Bank Account - Current", "Asset", None, True, 0.00, 0.00, "Main bank account"),
                    ("SALES001", "Sales Revenue", "Income", None, True, 0.00, 0.00, "Sales income account"),
                    ("PURCHASE001", "Purchase Account", "Expense", None, True, 0.00, 0.00, "Purchase expense account"),
                    ("CREDITORS001", "Accounts Payable", "Liability", None, True, 0.00, 0.00, "Supplier creditors"),
                    ("DEBTORS001", "Accounts Receivable", "Asset", None, True, 0.00, 0.00, "Customer debtors"),
                    ("TAX001", "GST Output", "Liability", None, True, 0.00, 0.00, "GST output tax account"),
                    ("TAX002", "GST Input", "Asset", None, True, 0.00, 0.00, "GST input tax account"),
                    ("EQUITY001", "Owner's Equity", "Equity", None, True, 0.00, 0.00, "Owner's equity account"),
                    ("DISCOUNT001", "Discount Given", "Expense", None, True, 0.00, 0.00, "Discount given to customers")
                ]
                
                for account_code, account_name, account_type, parent_code, is_active, opening_balance, current_balance, description in sample_accounts:
                    conn.execute(text("""
                        INSERT INTO accounts_master 
                        (account_code, account_name, account_type, parent_account_code, is_active, 
                         opening_balance, current_balance, description, created_at, updated_at)
                        VALUES (:account_code, :account_name, :account_type, :parent_code, :is_active,
                                :opening_balance, :current_balance, :description, NOW(), NOW())
                    """), {
                        "account_code": account_code,
                        "account_name": account_name,
                        "account_type": account_type,
                        "parent_code": parent_code,
                        "is_active": is_active,
                        "opening_balance": opening_balance,
                        "current_balance": current_balance,
                        "description": description
                    })
                
                conn.commit()
                logger.info("✅ Sample accounts created successfully!")
            
            # Create sample transaction templates
            logger.info("Creating sample transaction templates...")
            
            sample_templates = [
                ("CASH_SALE", "Cash Sale Template", "Cash sale transaction", "SALES", "SV", "CASH001", "SALES001"),
                ("CASH_PURCHASE", "Cash Purchase Template", "Cash purchase transaction", "PURCHASE", "PurchaseV", "PURCHASE001", "CASH001"),
                ("BANK_PAYMENT", "Bank Payment Template", "Bank payment transaction", "PAYMENT", "PV", "CREDITORS001", "BANK001"),
                ("BANK_RECEIPT", "Bank Receipt Template", "Bank receipt transaction", "RECEIPT", "RV", "BANK001", "DEBTORS001"),
                ("OPENING_BALANCE", "Opening Balance Template", "Opening balance entry", "OPENING", "JV", None, None)
            ]
            
            for template_code, template_name, description, category, transaction_type, debit_acc, credit_acc in sample_templates:
                try:
                    conn.execute(text("""
                        INSERT INTO transaction_templates 
                        (template_code, template_name, description, category, transaction_type, 
                         default_debit_account, default_credit_account, is_active, created_by, created_at, updated_at)
                        VALUES (:template_code, :template_name, :description, :category, :transaction_type,
                                :debit_acc, :credit_acc, TRUE, 'SYSTEM', NOW(), NOW())
                    """), {
                        "template_code": template_code,
                        "template_name": template_name,
                        "description": description,
                        "category": category,
                        "transaction_type": transaction_type,
                        "debit_acc": debit_acc,
                        "credit_acc": credit_acc
                    })
                except Exception as e:
                    # Template might already exist
                    logger.info(f"Template {template_code} already exists or error: {e}")
            
            conn.commit()
            logger.info("✅ Sample transaction templates created successfully!")
            
        logger.info("\n🎉 Database migration completed successfully!")
        logger.info("\nYou can now use the following API endpoints:")
        logger.info("- POST /api/ledger-transactions/ - Create new transaction")
        logger.info("- GET /api/ledger-transactions/ - Get all transactions")
        logger.info("- GET /api/ledger-transactions/{id} - Get specific transaction")
        logger.info("- PUT /api/ledger-transactions/{id} - Update transaction")
        logger.info("- DELETE /api/ledger-transactions/{id} - Delete transaction")
        logger.info("- POST /api/ledger-transactions/bulk - Create bulk transactions")
        logger.info("- GET /api/ledger-transactions/reports/account-balance - Account balance report")
        logger.info("- GET /api/ledger-transactions/batches/ - Transaction batches")
        logger.info("- GET /api/ledger-transactions/templates/ - Transaction templates")
        
    except Exception as e:
        logger.error(f"❌ Error creating ledger transaction tables: {e}")
        raise

if __name__ == "__main__":
    create_ledger_transaction_tables()
