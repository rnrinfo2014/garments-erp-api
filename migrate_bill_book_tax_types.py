#!/usr/bin/env python3
"""
Migration script to update bill_book table structure:
1. Add tax_type column to replace with_tax/without_tax boolean columns
2. Add starting_number column for bill sequence
3. Add bill_book_id to sales table
4. Update existing data
"""

import logging
from sqlalchemy import create_engine, text, Column, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import sessionmaker
from database import DATABASE_URL, Base
from models.bill_book import BillBook, TaxType


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the bill book migration"""
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        logger.info("Starting bill book tax type migration...")
        
        # Step 1: Add new columns to bill_books table
        logger.info("Step 1: Adding new columns to bill_books table...")
        
        # Add tax_type column
        try:
            session.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name='bill_books' AND column_name='tax_type') THEN
                        -- Create enum type if it doesn't exist
                        CREATE TYPE taxtype AS ENUM ('INCLUDE_TAX', 'EXCLUDE_TAX', 'WITHOUT_TAX');
                        
                        -- Add the column
                        ALTER TABLE bill_books ADD COLUMN tax_type taxtype DEFAULT 'INCLUDE_TAX';
                    END IF;
                END $$;
            """))
            logger.info("✓ Added tax_type column")
        except Exception as e:
            logger.warning(f"Tax type column might already exist: {e}")
        
        # Add starting_number column
        try:
            session.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name='bill_books' AND column_name='starting_number') THEN
                        ALTER TABLE bill_books ADD COLUMN starting_number INTEGER DEFAULT 1;
                    END IF;
                END $$;
            """))
            logger.info("✓ Added starting_number column")
        except Exception as e:
            logger.warning(f"Starting number column might already exist: {e}")
        
        # Step 2: Migrate existing data
        logger.info("Step 2: Migrating existing bill book data...")
        
        # Update tax_type based on existing with_tax/without_tax columns
        session.execute(text("""
            UPDATE bill_books 
            SET tax_type = CASE 
                WHEN with_tax = true AND without_tax = false THEN 'INCLUDE_TAX'::taxtype
                WHEN with_tax = false AND without_tax = true THEN 'WITHOUT_TAX'::taxtype
                ELSE 'INCLUDE_TAX'::taxtype
            END
            WHERE tax_type IS NULL OR tax_type = 'INCLUDE_TAX'::taxtype;
        """))
        
        # Update starting_number for existing records
        session.execute(text("""
            UPDATE bill_books 
            SET starting_number = 1 
            WHERE starting_number IS NULL;
        """))
        
        session.commit()
        logger.info("✓ Migrated existing bill book data")
        
        # Step 3: Add bill_book_id to sales table if it doesn't exist
        logger.info("Step 3: Adding bill_book_id to sales table...")
        
        try:
            session.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name='sales' AND column_name='bill_book_id') THEN
                        ALTER TABLE sales ADD COLUMN bill_book_id INTEGER;
                        ALTER TABLE sales ADD CONSTRAINT fk_sales_bill_book 
                            FOREIGN KEY (bill_book_id) REFERENCES bill_books(id);
                    END IF;
                END $$;
            """))
            logger.info("✓ Added bill_book_id to sales table")
        except Exception as e:
            logger.warning(f"Bill book ID column might already exist: {e}")
        
        session.commit()
        
        # Step 4: Show migration results
        logger.info("Step 4: Checking migration results...")
        
        result = session.execute(text("""
            SELECT 
                book_name, 
                book_code, 
                prefix, 
                tax_type, 
                starting_number, 
                last_bill_no,
                COALESCE(with_tax, false) as old_with_tax,
                COALESCE(without_tax, false) as old_without_tax
            FROM bill_books 
            ORDER BY id;
        """))
        
        logger.info("\nMigration Results:")
        logger.info("=" * 80)
        for row in result:
            logger.info(f"Book: {row.book_name}")
            logger.info(f"  Code: {row.book_code}")
            logger.info(f"  Prefix: {row.prefix}")
            logger.info(f"  Tax Type: {row.tax_type}")
            logger.info(f"  Starting Number: {row.starting_number}")
            logger.info(f"  Last Bill No: {row.last_bill_no}")
            logger.info(f"  Old flags: with_tax={row.old_with_tax}, without_tax={row.old_without_tax}")
            logger.info("-" * 40)
        
        # Step 5: Optional - Remove old columns (commented out for safety)
        logger.info("\nStep 5: Old columns (with_tax, without_tax) are kept for safety")
        logger.info("You can manually drop them later if migration is successful:")
        logger.info("  ALTER TABLE bill_books DROP COLUMN with_tax;")
        logger.info("  ALTER TABLE bill_books DROP COLUMN without_tax;")
        
        logger.info("\n✅ Bill book migration completed successfully!")
        
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Migration failed: {str(e)}")
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the new bill book functionality")
        print("2. Update your frontend to use the new tax_type field")
        print("3. Use the new bill number generation endpoints")
    else:
        print("\n❌ Migration failed. Check the logs above.")
