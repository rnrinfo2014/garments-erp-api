#!/usr/bin/env python3
"""
Script to insert a test vendor into the database
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from models.vendors import VendorMaster
from models.accounts import AccountsMaster
from decimal import Decimal


def generate_vendor_account_code(db, vendor_name: str) -> str:
    """Generate a unique account code for vendor payable account."""
    base_code = "2107"  # Vendor payables base code
    
    # Find the next available account code
    counter = 1
    while True:
        acc_code = f"{base_code}{counter:03d}"
        existing = db.query(AccountsMaster).filter(AccountsMaster.account_code == acc_code).first()
        if not existing:
            return acc_code
        counter += 1


def create_vendor_account(db, vendor_name: str, company_name: str) -> str:
    """Create a payable account for the vendor."""
    acc_code = generate_vendor_account_code(db, vendor_name)
    
    # Create the account record
    account = AccountsMaster(
        account_code=acc_code,
        account_name=f"Vendor - {vendor_name}",
        account_type="Liability",
        parent_account_code="2107",  # Vendor Payables parent
        is_active=True,
        opening_balance=Decimal('0.00'),
        current_balance=Decimal('0.00'),
        description=f"Payable account for vendor {company_name}"
    )
    
    db.add(account)
    db.flush()  # Ensure the account is created
    return acc_code


def insert_test_vendor():
    """Insert a test vendor into the database."""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if vendor already exists
        existing_vendor = db.query(VendorMaster).filter(VendorMaster.id == "VENDOR001").first()
        if existing_vendor:
            print("Test vendor already exists!")
            print(f"Vendor ID: {existing_vendor.id}")
            print(f"Name: {existing_vendor.name}")
            print(f"Company: {existing_vendor.company_name}")
            return
        
        # Create vendor data
        vendor_data = {
            "id": "VENDOR001",
            "name": "John Smith",
            "company_name": "Smith Trading Co.",
            "address": "123 Business Street, Mumbai, Maharashtra 400001",
            "phone": "9876543210",
            "gst": "27ABCDE1234F1Z5",
            "services": "Raw materials supply, Fabric trading, Logistics support",
            "status": "Active"
        }
        
        # Create vendor record
        db_vendor = VendorMaster(**vendor_data)
        db.add(db_vendor)
        db.flush()  # Ensure vendor is created before creating account
        
        # Create associated payable account
        acc_code = create_vendor_account(db, vendor_data["name"], vendor_data["company_name"])
        
        # Update vendor with account code
        setattr(db_vendor, 'acc_code', acc_code)
        
        db.commit()
        
        print("✅ Test vendor created successfully!")
        print(f"Vendor ID: {db_vendor.id}")
        print(f"Name: {db_vendor.name}")
        print(f"Company: {db_vendor.company_name}")
        print(f"Account Code: {db_vendor.acc_code}")
        print(f"Phone: {db_vendor.phone}")
        print(f"GST: {db_vendor.gst}")
        print(f"Services: {db_vendor.services}")
        print(f"Status: {db_vendor.status}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test vendor: {str(e)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    insert_test_vendor()
