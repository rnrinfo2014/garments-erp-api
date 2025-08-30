#!/usr/bin/env python3
"""
Script to remove stock_ledger table from the database
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def remove_stock_ledger_table():
    """Remove the stock_ledger table from the database"""
    
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL environment variable is not set")
        return False
    
    # Extract connection parameters from SQLAlchemy URL
    # Format: postgresql://username:password@host:port/database
    url_parts = DATABASE_URL.replace("postgresql://", "").split("/")
    database = url_parts[1]
    auth_host = url_parts[0]
    
    if "@" in auth_host:
        auth, host_port = auth_host.split("@")
        username, password = auth.split(":")
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host = host_port
            port = "5432"
    else:
        # Handle case without credentials
        host_port = auth_host
        username = "postgres"
        password = ""
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host = host_port
            port = "5432"
    
    print(f"Connecting to database: {database} at {host}:{port}")
    
    try:
        # Create connection using psycopg2 directly
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'stock_ledger'
            );
        """)
        
        result = cursor.fetchone()
        table_exists = result[0] if result else False
        
        if table_exists:
            print("stock_ledger table found. Dropping table...")
            
            # Drop the table
            cursor.execute("DROP TABLE IF EXISTS stock_ledger CASCADE;")
            print("✅ stock_ledger table has been dropped successfully!")
            
            # Also drop the enum if it exists
            cursor.execute("DROP TYPE IF EXISTS transactiontype CASCADE;")
            print("✅ TransactionType enum has been dropped successfully!")
            
        else:
            print("stock_ledger table does not exist. Nothing to drop.")
        
        # Show remaining tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("\nRemaining tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🔧 Removing stock_ledger table from database...")
    print("=" * 50)
    
    success = remove_stock_ledger_table()
    
    print("=" * 50)
    if success:
        print("✅ Stock ledger table removal completed successfully!")
        print("\nNext steps:")
        print("1. Stock ledger API endpoints have been removed from routes")
        print("2. Opening stock API endpoints have been removed from routes")
        print("3. stock_ledger table has been dropped from database")
        print("4. You can now restart the server without stock ledger functionality")
    else:
        print("❌ Stock ledger table removal failed!")
