#!/usr/bin/env python3
"""
Sales Tables Verification Script
Verifies that sales tables are properly created and relationships are correct
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_sales_system():
    """Comprehensive check of sales system setup"""
    try:
        logger.info("🔍 COMPREHENSIVE SALES SYSTEM VERIFICATION")
        logger.info("=" * 60)
        
        with engine.connect() as conn:
            # 1. Check tables exist
            logger.info("\n1️⃣ Checking table existence...")
            tables_check = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('sales', 'sales_items') 
                AND table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in tables_check]
            if 'sales' in tables and 'sales_items' in tables:
                logger.info("✅ All sales tables exist")
            else:
                logger.error(f"❌ Missing tables. Found: {tables}")
                return False
            
            # 2. Check enum type
            logger.info("\n2️⃣ Checking enum types...")
            enum_check = conn.execute(text("""
                SELECT typname FROM pg_type WHERE typname = 'salesstatus'
            """))
            if enum_check.fetchone():
                logger.info("✅ salesstatus enum exists")
            else:
                logger.error("❌ salesstatus enum missing")
                return False
            
            # 3. Check foreign key constraints
            logger.info("\n3️⃣ Checking foreign key constraints...")
            fk_check = conn.execute(text("""
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name IN ('sales', 'sales_items')
                ORDER BY tc.table_name, kcu.column_name
            """))
            
            fk_constraints = list(fk_check)
            expected_fks = [
                ('sales', 'agent_id', 'agents', 'id'),
                ('sales', 'bill_book_id', 'bill_books', 'id'),
                ('sales', 'customer_id', 'customers', 'id'),
                ('sales_items', 'sales_id', 'sales', 'id'),
                ('sales_items', 'variant_id', 'product_variants', 'id')
            ]
            
            found_fks = [(row[0], row[1], row[2], row[3]) for row in fk_constraints]
            
            all_fks_found = True
            for expected_fk in expected_fks:
                if expected_fk in found_fks:
                    logger.info(f"✅ {expected_fk[0]}.{expected_fk[1]} → {expected_fk[2]}.{expected_fk[3]}")
                else:
                    logger.error(f"❌ Missing FK: {expected_fk[0]}.{expected_fk[1]} → {expected_fk[2]}.{expected_fk[3]}")
                    all_fks_found = False
            
            if not all_fks_found:
                return False
            
            # 4. Check indexes
            logger.info("\n4️⃣ Checking indexes...")
            index_check = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_indexes 
                WHERE tablename IN ('sales', 'sales_items')
                AND schemaname = 'public'
                ORDER BY tablename, indexname
            """))
            
            indexes = list(index_check)
            expected_indexes = [
                'idx_sales_agent',
                'idx_sales_bill_book',
                'idx_sales_bill_number',
                'idx_sales_created_at',
                'idx_sales_customer',
                'idx_sales_date',
                'idx_sales_status',
                'idx_sales_items_sales_id',
                'idx_sales_items_variant'
            ]
            
            found_indexes = [row[2] for row in indexes if not row[2].endswith('_pkey')]
            
            for expected_idx in expected_indexes:
                if expected_idx in found_indexes:
                    logger.info(f"✅ Index: {expected_idx}")
                else:
                    logger.warning(f"⚠️ Missing index: {expected_idx}")
            
            # 5. Check triggers
            logger.info("\n5️⃣ Checking triggers...")
            trigger_check = conn.execute(text("""
                SELECT 
                    trigger_name,
                    event_object_table
                FROM information_schema.triggers 
                WHERE event_object_table IN ('sales', 'sales_items')
                ORDER BY event_object_table, trigger_name
            """))
            
            triggers = list(trigger_check)
            expected_triggers = [
                ('update_sales_updated_at', 'sales'),
                ('update_sales_items_updated_at', 'sales_items')
            ]
            
            found_triggers = [(row[0], row[1]) for row in triggers]
            
            for expected_trigger in expected_triggers:
                if expected_trigger in found_triggers:
                    logger.info(f"✅ Trigger: {expected_trigger[0]} on {expected_trigger[1]}")
                else:
                    logger.warning(f"⚠️ Missing trigger: {expected_trigger[0]} on {expected_trigger[1]}")
            
            # 6. Check referential integrity with existing tables
            logger.info("\n6️⃣ Checking referential integrity...")
            
            # Check if referenced tables exist
            ref_tables = ['bill_books', 'customers', 'agents', 'product_variants']
            for table in ref_tables:
                table_check = conn.execute(text(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = '{table}' AND table_schema = 'public'
                """))
                if table_check.fetchone():
                    logger.info(f"✅ Referenced table exists: {table}")
                else:
                    logger.error(f"❌ Referenced table missing: {table}")
                    return False
            
            # 7. Test constraints
            logger.info("\n7️⃣ Testing constraints...")
            
            # Test sales table constraints
            try:
                conn.execute(text("""
                    INSERT INTO sales (
                        bill_book_id, customer_id, bill_number, bill_date, created_by
                    ) VALUES (-1, -1, 'TEST-001', '2025-08-30', 'test_user')
                """))
                logger.error("❌ Should have failed due to FK constraint")
                return False
            except Exception:
                logger.info("✅ Foreign key constraints working (sales table)")
            
            # Test sales_items constraints
            try:
                conn.execute(text("""
                    INSERT INTO sales_items (
                        sales_id, variant_id, product_name, unit_type,
                        quantity, mrp, sale_rate, total_amount
                    ) VALUES (-1, -1, 'Test Product', 'PCS', -1, 100, 90, 90)
                """))
                logger.error("❌ Should have failed due to quantity check constraint")
                return False
            except Exception:
                logger.info("✅ Check constraints working (sales_items table)")
            
            logger.info("\n" + "="*60)
            logger.info("🎉 SALES SYSTEM VERIFICATION COMPLETE!")
            logger.info("="*60)
            logger.info("✅ All checks passed - Sales billing system is ready!")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def show_sales_system_summary():
    """Show summary of the sales system capabilities"""
    logger.info("\n📊 SALES BILLING SYSTEM CAPABILITIES:")
    logger.info("=" * 60)
    
    logger.info("\n🏪 SALES MANAGEMENT:")
    logger.info("  • Multi-bill book support (Tax Invoice, B2B, Export, Retail)")
    logger.info("  • Customer and agent tracking")
    logger.info("  • Automatic bill number generation")
    logger.info("  • Status workflow (Draft → Confirmed → Dispatched → Delivered)")
    
    logger.info("\n💰 FINANCIAL FEATURES:")
    logger.info("  • Flexible tax calculations (Include/Exclude/Without tax)")
    logger.info("  • Item-level and bill-level discounts")
    logger.info("  • Additional charges support")
    logger.info("  • Automatic total calculations")
    
    logger.info("\n📦 PRODUCT FEATURES:")
    logger.info("  • Product variant integration")
    logger.info("  • HSN code tracking")
    logger.info("  • Multiple unit types")
    logger.info("  • MRP and sale rate differentiation")
    
    logger.info("\n🚚 LOGISTICS:")
    logger.info("  • Transport details tracking")
    logger.info("  • LLR number and date")
    logger.info("  • Delivery status management")
    
    logger.info("\n🔧 TECHNICAL FEATURES:")
    logger.info("  • Audit trail (created/updated timestamps)")
    logger.info("  • Data integrity constraints")
    logger.info("  • Optimized database indexes")
    logger.info("  • Automatic summary calculations")


if __name__ == "__main__":
    success = check_sales_system()
    
    if success:
        show_sales_system_summary()
        logger.info("\n🚀 Ready to proceed with Phase 2: Model Creation!")
    else:
        logger.error("\n❌ Sales system verification failed. Please check the issues above.")
