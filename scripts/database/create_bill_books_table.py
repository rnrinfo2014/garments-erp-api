#!/usr/bin/env python3
"""
Create bill_books table for managing different types of bills
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_bill_books_table():
    """Create the bill_books table."""
    try:
        with engine.connect() as connection:
            # Create BillBookStatus enum type
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'billbookstatus') THEN
                        CREATE TYPE billbookstatus AS ENUM ('ACTIVE', 'INACTIVE', 'CLOSED');
                    END IF;
                END $$;
            """))
            
            # Create bill_books table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS bill_books (
                    id SERIAL PRIMARY KEY,
                    book_name VARCHAR(100) NOT NULL,
                    book_code VARCHAR(20) NOT NULL UNIQUE,
                    prefix VARCHAR(20) NOT NULL,
                    with_tax BOOLEAN DEFAULT TRUE,
                    without_tax BOOLEAN DEFAULT FALSE,
                    last_bill_no INTEGER DEFAULT 0,
                    status billbookstatus DEFAULT 'ACTIVE',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create index on book_code for faster lookups
                CREATE INDEX IF NOT EXISTS idx_bill_books_book_code ON bill_books(book_code);
                
                -- Create trigger for updated_at
                CREATE OR REPLACE FUNCTION update_bill_books_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                DROP TRIGGER IF EXISTS update_bill_books_updated_at ON bill_books;
                CREATE TRIGGER update_bill_books_updated_at
                    BEFORE UPDATE ON bill_books
                    FOR EACH ROW
                    EXECUTE FUNCTION update_bill_books_updated_at();
            """))
            
            connection.commit()
            logger.info("✅ Successfully created bill_books table and related objects")
            
    except Exception as e:
        logger.error(f"❌ Error creating bill_books table: {str(e)}")
        raise e

def check_table():
    """Verify the bill_books table was created correctly."""
    try:
        with engine.connect() as connection:
            # Check if table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'bill_books'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                # Get column information
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'bill_books'
                    ORDER BY ordinal_position;
                """))
                
                logger.info("Bill books table structure:")
                for column in result:
                    logger.info(f"  {column[0]}: {column[1]} (Nullable: {column[2]})")
                
                # Check if indexes exist
                result = connection.execute(text("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = 'bill_books';
                """))
                
                logger.info("\nIndexes:")
                for index in result:
                    logger.info(f"  {index[0]}: {index[1]}")
                
                return True
            else:
                logger.error("❌ bill_books table does not exist!")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error checking bill_books table: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting bill_books table creation...")
    
    try:
        # Create the table and related objects
        create_bill_books_table()
        
        # Verify the creation
        if check_table():
            logger.info("🎉 Bill books table creation completed successfully!")
        else:
            logger.error("❌ Bill books table verification failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Setup failed: {str(e)}")
        sys.exit(1)
