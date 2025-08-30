from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, DateTime, func
from sqlalchemy.orm import relationship
from models.user import Base


class AccountsMaster(Base):
    __tablename__ = "accounts_master"

    account_code = Column(String(20), primary_key=True, index=True)  # Primary key should be account_code
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(50), nullable=False)  # Asset, Liability, Equity, Income, Expense
    parent_account_code = Column(String(20), nullable=True)  # For hierarchical accounts
    is_active = Column(Boolean, default=True, nullable=False)
    opening_balance = Column(DECIMAL(15, 2), default=0.00, nullable=False)
    current_balance = Column(DECIMAL(15, 2), default=0.00, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # Note: All relationships removed to avoid circular import issues
    # Use explicit queries for related models

    def __repr__(self):
        return f"<AccountsMaster(account_code='{self.account_code}', account_name='{self.account_name}', account_type='{self.account_type}')>"


# Create alias for compatibility
Account = AccountsMaster
