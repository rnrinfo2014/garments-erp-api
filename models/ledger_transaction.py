from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from decimal import Decimal


class LedgerTransaction(Base):
    """
    Ledger Transaction Model for Double Entry Bookkeeping
    Each transaction affects at least two accounts (debit and credit)
    """
    __tablename__ = "ledger_transactions"

    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_number = Column(String(50), unique=True, nullable=False, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    
    # Account Reference - Foreign Key to AccountsMaster
    account_code = Column(String(20), ForeignKey("accounts_master.account_code"), nullable=False, index=True)
    
    # Transaction Details
    description = Column(String(500), nullable=False)
    reference_type = Column(String(50), nullable=True, index=True)  # 'PURCHASE_ORDER', 'SALE', 'PAYMENT', 'RECEIPT', 'JOURNAL'
    reference_id = Column(String(50), nullable=True, index=True)  # Reference to source document ID
    
    # Financial Fields
    debit_amount = Column(DECIMAL(15, 2), default=0.00, nullable=False)
    credit_amount = Column(DECIMAL(15, 2), default=0.00, nullable=False)
    
    # Additional Information
    voucher_type = Column(String(20), nullable=False)  # 'JV' (Journal), 'PV' (Payment), 'RV' (Receipt), 'SV' (Sales), 'PurchaseV' (Purchase)
    voucher_number = Column(String(50), nullable=True)
    
    # Party Details (optional)
    party_type = Column(String(20), nullable=True)  # 'CUSTOMER', 'SUPPLIER', 'VENDOR', 'EMPLOYEE'
    party_id = Column(String(50), nullable=True)
    party_name = Column(String(200), nullable=True)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False, nullable=False)
    reconciled_date = Column(DateTime, nullable=True)
    
    # Status and Control
    is_active = Column(Boolean, default=True, nullable=False)
    is_posted = Column(Boolean, default=True, nullable=False)  # False for draft transactions
    
    # Audit Fields
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Additional Notes
    notes = Column(Text, nullable=True)
    
    # Relationship with AccountsMaster (explicit query recommended to avoid circular imports)
    # account = relationship("AccountsMaster", back_populates="ledger_transactions")
    
    # Calculated Properties
    @property
    def transaction_amount(self):
        """Return the transaction amount (debit or credit, whichever is non-zero)"""
        try:
            debit = Decimal(str(self.debit_amount or '0.00'))
            credit = Decimal(str(self.credit_amount or '0.00'))
            return debit if debit > Decimal('0.00') else credit
        except (TypeError, ValueError):
            return Decimal('0.00')
    
    @property
    def transaction_type(self):
        """Return whether this is a debit or credit transaction"""
        try:
            debit = Decimal(str(self.debit_amount or '0.00'))
            return "DEBIT" if debit > Decimal('0.00') else "CREDIT"
        except (TypeError, ValueError):
            return "CREDIT"
    
    @property
    def balance_effect(self):
        """Return the net effect on account balance (debit - credit)"""
        try:
            debit = Decimal(str(self.debit_amount or '0.00'))
            credit = Decimal(str(self.credit_amount or '0.00'))
            return debit - credit
        except (TypeError, ValueError):
            return Decimal('0.00')

    def __repr__(self):
        return f"<LedgerTransaction(id={self.id}, transaction_number='{self.transaction_number}', account_code='{self.account_code}', amount={self.transaction_amount})>"


class TransactionBatch(Base):
    """
    Transaction Batch Model for grouping related transactions
    Useful for ensuring double-entry balance and batch operations
    """
    __tablename__ = "transaction_batches"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    batch_date = Column(DateTime, nullable=False, index=True)
    
    # Batch Details
    description = Column(String(500), nullable=False)
    reference_type = Column(String(50), nullable=True, index=True)  # Source of batch
    reference_id = Column(String(50), nullable=True, index=True)
    
    # Financial Summary
    total_debit = Column(DECIMAL(15, 2), default=0.00, nullable=False)
    total_credit = Column(DECIMAL(15, 2), default=0.00, nullable=False)
    
    # Status
    is_balanced = Column(Boolean, default=False, nullable=False)  # True when total_debit = total_credit
    is_posted = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit Fields
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Calculated Properties
    @property
    def is_valid_double_entry(self):
        """Check if batch maintains double-entry balance"""
        try:
            total_debit = Decimal(str(self.total_debit or '0.00'))
            total_credit = Decimal(str(self.total_credit or '0.00'))
            return total_debit == total_credit
        except (TypeError, ValueError):
            return False
    
    @property
    def balance_difference(self):
        """Return the difference between debit and credit (should be 0 for valid double-entry)"""
        try:
            total_debit = Decimal(str(self.total_debit or '0.00'))
            total_credit = Decimal(str(self.total_credit or '0.00'))
            return total_debit - total_credit
        except (TypeError, ValueError):
            return Decimal('0.00')

    def __repr__(self):
        return f"<TransactionBatch(id={self.id}, batch_number='{self.batch_number}', total_debit={self.total_debit}, total_credit={self.total_credit})>"


# Additional helper model for transaction templates (optional)
class TransactionTemplate(Base):
    """
    Transaction Templates for common recurring transactions
    """
    __tablename__ = "transaction_templates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    template_name = Column(String(100), unique=True, nullable=False)
    template_code = Column(String(20), unique=True, nullable=False)
    description = Column(String(500), nullable=False)
    
    # Template Categories
    category = Column(String(50), nullable=False)  # 'SALES', 'PURCHASE', 'PAYMENT', 'RECEIPT', 'ADJUSTMENT'
    transaction_type = Column(String(20), nullable=False)  # Same as voucher_type in LedgerTransaction
    
    # Default Accounts (can be overridden)
    default_debit_account = Column(String(20), ForeignKey("accounts_master.account_code"), nullable=True)
    default_credit_account = Column(String(20), ForeignKey("accounts_master.account_code"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit Fields
    created_by = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<TransactionTemplate(template_code='{self.template_code}', template_name='{self.template_name}')>"
