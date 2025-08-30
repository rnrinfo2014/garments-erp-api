"""
Script to drop the enum from stock_ledger table and recreate it with string type
"""
from sqlalchemy import create_engine, text
from database import DATABASE_URL
import os

def drop_and_recreate_stock_ledger_table():
    """Drop the stock_ledger table and recreate it without enum"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        
        try:
            # Drop the table (this will also drop the enum if it's only used by this table)
            print("Dropping stock_ledger table...")
            conn.execute(text("DROP TABLE IF EXISTS stock_ledger CASCADE"))
            
            # Drop the enum type if it exists
            print("Dropping transactiontype enum...")
            conn.execute(text("DROP TYPE IF EXISTS transactiontype CASCADE"))
            
            # Commit the transaction
            trans.commit()
            print("Successfully dropped stock_ledger table and enum")
            
        except Exception as e:
            trans.rollback()
            print(f"Error dropping table/enum: {e}")
            raise

if __name__ == "__main__":
    drop_and_recreate_stock_ledger_table()
    print("Now you can restart the server to recreate the table with string type")
