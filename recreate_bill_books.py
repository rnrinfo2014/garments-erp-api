#!/usr/bin/env python3
"""
Drop and recreate bill_books table with correct schema
"""

from database import engine
from sqlalchemy import text
from models.bill_book import BillBook
from models import Base

def drop_and_recreate_bill_books():
    """Drop existing bill_books table and recreate with correct schema"""
    
    try:
        print("🗑️  Dropping existing bill_books table...")
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Drop the table if it exists
                conn.execute(text("DROP TABLE IF EXISTS bill_books CASCADE"))
                print("✅ Existing table dropped")
                
                # Drop the enum type if it exists
                conn.execute(text("DROP TYPE IF EXISTS taxtype CASCADE"))
                conn.execute(text("DROP TYPE IF EXISTS billbookstatus CASCADE"))
                print("✅ Existing enum types dropped")
                
                trans.commit()
                print("✅ Cleanup completed")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during cleanup: {e}")
                raise
        
        # Create the new table with correct schema
        print("\n🛠️  Creating new bill_books table...")
        
        # Create just the bill_books table
        BillBook.__table__.create(engine, checkfirst=True)
        
        print("✅ New bill_books table created with correct schema!")
        
        # Verify the new table structure
        print("\n🔍 Verifying new table structure...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'bill_books' 
                ORDER BY ordinal_position
            """))
            
            print("📋 New table structure:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
        
        # Add some sample data
        print("\n📝 Adding sample bill books...")
        add_sample_data()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def add_sample_data():
    """Add sample bill book data"""
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Insert sample bill books
                sample_books = [
                    {
                        'book_name': 'Tax Invoice Book',
                        'book_code': 'TAX_INV',
                        'prefix': 'INV',
                        'tax_type': 'INCLUDE_TAX',
                        'starting_number': 1,
                        'last_bill_no': 0,
                        'status': 'ACTIVE'
                    },
                    {
                        'book_name': 'B2B Sales Book',
                        'book_code': 'B2B_SLS',
                        'prefix': 'B2B',
                        'tax_type': 'EXCLUDE_TAX',
                        'starting_number': 1,
                        'last_bill_no': 0,
                        'status': 'ACTIVE'
                    },
                    {
                        'book_name': 'Export Sales Book',
                        'book_code': 'EXP_SLS',
                        'prefix': 'EXP',
                        'tax_type': 'WITHOUT_TAX',
                        'starting_number': 1,
                        'last_bill_no': 0,
                        'status': 'ACTIVE'
                    }
                ]
                
                for book in sample_books:
                    conn.execute(text("""
                        INSERT INTO bill_books 
                        (book_name, book_code, prefix, tax_type, starting_number, last_bill_no, status, created_at, updated_at)
                        VALUES 
                        (:book_name, :book_code, :prefix, :tax_type::taxtype, :starting_number, :last_bill_no, :status::billbookstatus, NOW(), NOW())
                    """), book)
                
                trans.commit()
                print("✅ Sample bill books added:")
                
                # Show the added data
                result = conn.execute(text("SELECT book_name, book_code, prefix, tax_type, status FROM bill_books"))
                for row in result:
                    print(f"  📚 {row[0]} ({row[1]}) - Prefix: {row[2]}, Tax: {row[3]}, Status: {row[4]}")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error adding sample data: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Error with sample data: {e}")

if __name__ == "__main__":
    print("🚀 Starting bill_books table recreation...")
    print("=" * 60)
    
    success = drop_and_recreate_bill_books()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Bill books table successfully recreated!")
        print("\nNext steps:")
        print("1. Your API should now work without errors")
        print("2. Test the bill books endpoints")
        print("3. The table now has the correct schema with tax_type enum")
    else:
        print("\n❌ Recreation failed. Check the errors above.")
