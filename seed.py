from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models.user import User, UserRole, UserStatus
from models.company import CompanyDetails
from models.state import State
from models.accounts import AccountsMaster
from models.agents import Agent  # Import Agent so it gets created
from models.suppliers import Supplier  # Import Supplier so it gets created (needed by StockLedger)
from models.vendors import VendorMaster  # Import VendorMaster so it gets created
from models.customers import Customer  # Import Customer so it gets created
from models.category_master import CategoryMaster  # Import to ensure creation (needed by RawMaterial)
from models.size_master import SizeMaster  # Import to ensure creation (needed by RawMaterial & StockLedger)
from models.unit_master import UnitMaster  # Import to ensure creation (needed by RawMaterial)
from models.raw_material_master import RawMaterialMaster  # Import to ensure creation (needed by StockLedger)
from models.stock_ledger import StockLedger  # Import StockLedger last
from auth import get_password_hash
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_indian_states():
    """Seed Indian states with GST codes."""
    db = SessionLocal()
    try:
        # Check if states already exist
        existing_states = db.query(State).first()
        if existing_states:
            logger.info("States already exist")
            return
        
        # Indian states with GST codes
        indian_states = [
            {"name": "Andhra Pradesh", "code": "AP", "gst_code": "37"},
            {"name": "Arunachal Pradesh", "code": "AR", "gst_code": "12"},
            {"name": "Assam", "code": "AS", "gst_code": "18"},
            {"name": "Bihar", "code": "BR", "gst_code": "10"},
            {"name": "Chhattisgarh", "code": "CG", "gst_code": "22"},
            {"name": "Goa", "code": "GA", "gst_code": "30"},
            {"name": "Gujarat", "code": "GJ", "gst_code": "24"},
            {"name": "Haryana", "code": "HR", "gst_code": "06"},
            {"name": "Himachal Pradesh", "code": "HP", "gst_code": "02"},
            {"name": "Jharkhand", "code": "JH", "gst_code": "20"},
            {"name": "Karnataka", "code": "KA", "gst_code": "29"},
            {"name": "Kerala", "code": "KL", "gst_code": "32"},
            {"name": "Madhya Pradesh", "code": "MP", "gst_code": "23"},
            {"name": "Maharashtra", "code": "MH", "gst_code": "27"},
            {"name": "Manipur", "code": "MN", "gst_code": "14"},
            {"name": "Meghalaya", "code": "ML", "gst_code": "17"},
            {"name": "Mizoram", "code": "MZ", "gst_code": "15"},
            {"name": "Nagaland", "code": "NL", "gst_code": "13"},
            {"name": "Odisha", "code": "OR", "gst_code": "21"},
            {"name": "Punjab", "code": "PB", "gst_code": "03"},
            {"name": "Rajasthan", "code": "RJ", "gst_code": "08"},
            {"name": "Sikkim", "code": "SK", "gst_code": "11"},
            {"name": "Tamil Nadu", "code": "TN", "gst_code": "33"},
            {"name": "Telangana", "code": "TG", "gst_code": "36"},
            {"name": "Tripura", "code": "TR", "gst_code": "16"},
            {"name": "Uttar Pradesh", "code": "UP", "gst_code": "09"},
            {"name": "Uttarakhand", "code": "UK", "gst_code": "05"},
            {"name": "West Bengal", "code": "WB", "gst_code": "19"},
            # Union Territories
            {"name": "Andaman and Nicobar Islands", "code": "AN", "gst_code": "35"},
            {"name": "Chandigarh", "code": "CH", "gst_code": "04"},
            {"name": "Dadra and Nagar Haveli and Daman and Diu", "code": "DH", "gst_code": "26"},
            {"name": "Delhi", "code": "DL", "gst_code": "07"},
            {"name": "Jammu and Kashmir", "code": "JK", "gst_code": "01"},
            {"name": "Ladakh", "code": "LA", "gst_code": "38"},
            {"name": "Lakshadweep", "code": "LD", "gst_code": "31"},
            {"name": "Puducherry", "code": "PY", "gst_code": "34"},
        ]
        
        # Create state records
        for state_data in indian_states:
            state = State(**state_data)
            db.add(state)
        
        db.commit()
        logger.info(f"Successfully seeded {len(indian_states)} Indian states")
        
    except Exception as e:
        logger.error(f"Error seeding states: {e}")
        db.rollback()
    finally:
        db.close()

def create_default_company():
    """Create default company details if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if any company exists
        existing_company = db.query(CompanyDetails).first()
        
        if existing_company:
            logger.info("Company details already exist")
            return existing_company
        
        # Create default company with Maharashtra as default state
        maharashtra = db.query(State).filter(State.code == "MH").first()
        default_company = CompanyDetails(
            name="Garments ERP Company",
            address="123 Business Street, Mumbai",
            contact="+91 9876543210",
            email="info@garmenterp.com",
            gst="27ABCDE1234F1Z5",
            website="https://www.garmenterp.com",
            logo="",
            state_id=maharashtra.id if maharashtra else None
        )
        
        db.add(default_company)
        db.commit()
        db.refresh(default_company)
        
        logger.info("Default company details created successfully")
        return default_company
        
    except Exception as e:
        logger.error(f"Error creating default company: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def create_superadmin():
    """Create superadmin user if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if superadmin already exists
        existing_superadmin = db.query(User).filter(
            User.role == UserRole.SUPERADMIN
        ).first()
        
        if existing_superadmin:
            logger.info("Superadmin already exists")
            return existing_superadmin
        
        # Create superadmin user
        superadmin = User(
            username="superadmin",
            password=get_password_hash("admin123"),  # Change this password!
            role=UserRole.SUPERADMIN,
            status=UserStatus.ACTIVE
        )
        
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        
        logger.info("Superadmin user created successfully")
        logger.info("Username: superadmin, Password: admin123 (CHANGE THIS!)")
        return superadmin
        
    except Exception as e:
        logger.error(f"Error creating superadmin: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def create_default_accounts():
    """Create default chart of accounts for garments ERP."""
    db = SessionLocal()
    try:
        # Check if accounts already exist
        existing_accounts = db.query(AccountsMaster).first()
        if existing_accounts:
            logger.info("Accounts already exist")
            return

        # Default Chart of Accounts for Garments ERP
        default_accounts = [
            # Assets
            {"account_code": "1000", "account_name": "Assets", "account_type": "Asset", "parent_account_code": None},
            {"account_code": "1100", "account_name": "Current Assets", "account_type": "Asset", "parent_account_code": "1000"},
            {"account_code": "1101", "account_name": "Cash in Hand", "account_type": "Asset", "parent_account_code": "1100"},
            {"account_code": "1102", "account_name": "Bank Account", "account_type": "Asset", "parent_account_code": "1100"},
            {"account_code": "1103", "account_name": "Accounts Receivable", "account_type": "Asset", "parent_account_code": "1100"},
            {"account_code": "1300", "account_name": "Agent Receivables", "account_type": "Asset", "parent_account_code": "1103"},
            {"account_code": "1301", "account_name": "Customer Receivables", "account_type": "Asset", "parent_account_code": "1103"},
            {"account_code": "1104", "account_name": "Raw Materials Inventory", "account_type": "Asset", "parent_account_code": "1100"},
            {"account_code": "1105", "account_name": "Work in Progress", "account_type": "Asset", "parent_account_code": "1100"},
            {"account_code": "1106", "account_name": "Finished Goods Inventory", "account_type": "Asset", "parent_account_code": "1100"},
            {"account_code": "1200", "account_name": "Fixed Assets", "account_type": "Asset", "parent_account_code": "1000"},
            {"account_code": "1201", "account_name": "Machinery & Equipment", "account_type": "Asset", "parent_account_code": "1200"},
            {"account_code": "1202", "account_name": "Furniture & Fixtures", "account_type": "Asset", "parent_account_code": "1200"},
            {"account_code": "1203", "account_name": "Building", "account_type": "Asset", "parent_account_code": "1200"},
            
            # Liabilities
            {"account_code": "2000", "account_name": "Liabilities", "account_type": "Liability", "parent_account_code": None},
            {"account_code": "2100", "account_name": "Current Liabilities", "account_type": "Liability", "parent_account_code": "2000"},
            {"account_code": "2101", "account_name": "Accounts Payable", "account_type": "Liability", "parent_account_code": "2100"},
            {"account_code": "2102", "account_name": "GST Output Tax", "account_type": "Liability", "parent_account_code": "2100"},
            {"account_code": "2103", "account_name": "TDS Payable", "account_type": "Liability", "parent_account_code": "2100"},
            {"account_code": "2104", "account_name": "Salary Payable", "account_type": "Liability", "parent_account_code": "2100"},
            {"account_code": "2105", "account_name": "Agent Commissions Payable", "account_type": "Liability", "parent_account_code": "2100"},
            {"account_code": "2106", "account_name": "Supplier Payables", "account_type": "Liability", "parent_account_code": "2100"},
            {"account_code": "2107", "account_name": "Vendor Payables", "account_type": "Liability", "parent_account_code": "2100"},
            {"account_code": "2108", "account_name": "Employee Payables", "account_type": "Liability", "parent_account_code": "2100"},
            {"account_code": "2200", "account_name": "Long Term Liabilities", "account_type": "Liability", "parent_account_code": "2000"},
            {"account_code": "2201", "account_name": "Bank Loan", "account_type": "Liability", "parent_account_code": "2200"},
            
            # Equity
            {"account_code": "3000", "account_name": "Owner's Equity", "account_type": "Equity", "parent_account_code": None},
            {"account_code": "3001", "account_name": "Capital", "account_type": "Equity", "parent_account_code": "3000"},
            {"account_code": "3002", "account_name": "Retained Earnings", "account_type": "Equity", "parent_account_code": "3000"},
            
            # Income
            {"account_code": "4000", "account_name": "Revenue", "account_type": "Income", "parent_account_code": None},
            {"account_code": "4001", "account_name": "Sales Revenue", "account_type": "Income", "parent_account_code": "4000"},
            {"account_code": "4002", "account_name": "Other Income", "account_type": "Income", "parent_account_code": "4000"},
            
            # Expenses
            {"account_code": "5000", "account_name": "Expenses", "account_type": "Expense", "parent_account_code": None},
            {"account_code": "5100", "account_name": "Cost of Goods Sold", "account_type": "Expense", "parent_account_code": "5000"},
            {"account_code": "5101", "account_name": "Raw Material Cost", "account_type": "Expense", "parent_account_code": "5100"},
            {"account_code": "5102", "account_name": "Labor Cost", "account_type": "Expense", "parent_account_code": "5100"},
            {"account_code": "5103", "account_name": "Manufacturing Overhead", "account_type": "Expense", "parent_account_code": "5100"},
            {"account_code": "5200", "account_name": "Operating Expenses", "account_type": "Expense", "parent_account_code": "5000"},
            {"account_code": "5201", "account_name": "Salary Expense", "account_type": "Expense", "parent_account_code": "5200"},
            {"account_code": "5202", "account_name": "Rent Expense", "account_type": "Expense", "parent_account_code": "5200"},
            {"account_code": "5203", "account_name": "Utilities Expense", "account_type": "Expense", "parent_account_code": "5200"},
            {"account_code": "5204", "account_name": "Transportation Expense", "account_type": "Expense", "parent_account_code": "5200"},
            {"account_code": "5205", "account_name": "GST Input Tax", "account_type": "Expense", "parent_account_code": "5200"},
        ]

        for account_data in default_accounts:
            account = AccountsMaster(
                account_code=account_data["account_code"],
                account_name=account_data["account_name"],
                account_type=account_data["account_type"],
                parent_account_code=account_data["parent_account_code"],
                is_active=True,
                opening_balance=Decimal('0.00'),
                current_balance=Decimal('0.00'),
                description=f"Default {account_data['account_type']} account"
            )
            db.add(account)

        db.commit()
        logger.info(f"Successfully created {len(default_accounts)} default accounts")

    except Exception as e:
        logger.error(f"Error creating default accounts: {e}")
    finally:
        db.close()


def init_database():
    """Initialize database with tables and seed data."""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        # Seed Indian states first
        seed_indian_states()
        
        # Create superadmin
        create_superadmin()
        
        # Create default company
        create_default_company()
        
        # Create default accounts
        create_default_accounts()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_database()
