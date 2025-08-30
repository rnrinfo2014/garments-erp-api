#!/usr/bin/env python3
"""
Add sample data to bill_books table
"""

from database import engine
from sqlalchemy import text

def add_sample_bill_books():
    """Add sample bill book data with correct syntax"""
    
    try:
        print("📝 Adding sample bill books...")
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Insert sample bill books one by one
                sample_books = [
                    ("Tax Invoice Book", "TAX_INV", "INV", "INCLUDE_TAX", "ACTIVE"),
                    ("B2B Sales Book", "B2B_SLS", "B2B", "EXCLUDE_TAX", "ACTIVE"),
                    ("Export Sales Book", "EXP_SLS", "EXP", "WITHOUT_TAX", "ACTIVE"),
                    ("Retail Sales Book", "RTL_SLS", "RTL", "INCLUDE_TAX", "ACTIVE")
                ]
                
                for book_name, book_code, prefix, tax_type, status in sample_books:
                    conn.execute(text("""
                        INSERT INTO bill_books 
                        (book_name, book_code, prefix, tax_type, starting_number, last_bill_no, status, created_at, updated_at)
                        VALUES 
                        (:book_name, :book_code, :prefix, :tax_type, 1, 0, :status, NOW(), NOW())
                    """), {
                        "book_name": book_name,
                        "book_code": book_code,
                        "prefix": prefix,
                        "tax_type": tax_type,
                        "status": status
                    })
                
                trans.commit()
                print("✅ Sample bill books added successfully!")
                
                # Show the added data
                result = conn.execute(text("""
                    SELECT id, book_name, book_code, prefix, tax_type, status, starting_number, last_bill_no 
                    FROM bill_books 
                    ORDER BY id
                """))
                
                print("\n📚 Bill Books in database:")
                print("-" * 80)
                for row in result:
                    print(f"ID: {row[0]} | {row[1]} ({row[2]}) | Prefix: {row[3]} | Tax: {row[4]} | Status: {row[5]}")
                
                print(f"\n✅ Total bill books: {len(sample_books)}")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error adding sample data: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    add_sample_bill_books()
