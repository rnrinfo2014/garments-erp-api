from database import SessionLocal
from sqlalchemy import text

def check_database():
    db = SessionLocal()
    try:
        # Check database version
        result = db.execute(text('SELECT version()'))
        version = result.fetchone()[0]
        print(f"✅ Database connected successfully")
        print(f"📊 PostgreSQL version: {version}")

        # List all tables
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        tables = result.fetchall()

        print(f"\n📋 Database Tables ({len(tables)} total):")
        for table in tables:
            print(f"  • {table[0]}")

        # Check if income receipt tables exist
        income_tables = ['income_receipts', 'receipt_bill_allocations', 'receipt_templates']
        print(f"\n💰 Income Receipt System Status:")
        for table in income_tables:
            exists = db.execute(text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table}')")).fetchone()[0]
            status = "✅ Exists" if exists else "❌ Missing"
            print(f"  • {table}: {status}")

    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
