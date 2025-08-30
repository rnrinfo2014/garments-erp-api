from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from decimal import Decimal
from database import Base
import enum


class PaymentStatus(enum.Enum):
    DRAFT = "Draft"
    POSTED = "Posted"
    CANCELLED = "Cancelled"


class PaymentMode(enum.Enum):
    CASH = "Cash"
    BANK_TRANSFER = "Bank Transfer"
    CHEQUE = "Cheque"
    DEMAND_DRAFT = "Demand Draft"
    ONLINE_TRANSFER = "Online Transfer"
    UPI = "UPI"
    RTGS = "RTGS"
    NEFT = "NEFT"
    CREDIT_CARD = "Credit Card"


class PaymentType(enum.Enum):
    ADVANCE = "Advance"  # Payment before purchase
    AGAINST_BILL = "Against Bill"  # Payment against specific purchase
    ON_ACCOUNT = "On Account"  # General payment to supplier


class SupplierPayment(Base):
    """
    Supplier Payment Model - Payments made to suppliers
    Automatically creates ledger transactions and links with purchase bills
    """
    __tablename__ = "supplier_payments"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_number = Column(String(50), nullable=False, unique=True, index=True)
    payment_date = Column(Date, nullable=False, index=True)
    
    # Supplier Information
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Payment Details
    payment_type = Column(SQLEnum(PaymentType), nullable=False, default=PaymentType.AGAINST_BILL)
    payment_mode = Column(SQLEnum(PaymentMode), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.DRAFT)
    
    # Amount Details
    gross_amount = Column(Numeric(15, 2), default=0.00, nullable=False)  # Total bills amount
    discount_amount = Column(Numeric(15, 2), default=0.00, nullable=False)  # Discount given
    tds_amount = Column(Numeric(15, 2), default=0.00, nullable=False)  # Tax deducted at source
    other_deductions = Column(Numeric(15, 2), default=0.00, nullable=False)  # Other deductions
    net_amount = Column(Numeric(15, 2), default=0.00, nullable=False)  # Actual payment amount
    
    # Payment Mode Specific Details
    bank_account_id = Column(String(50), ForeignKey("accounts_master.account_code"), nullable=True)  # Our bank account
    cheque_number = Column(String(50), nullable=True)
    cheque_date = Column(Date, nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_branch = Column(String(100), nullable=True)
    transaction_reference = Column(String(100), nullable=True)  # UTR, Transaction ID, etc.
    
    # TDS Details
    tds_rate = Column(Numeric(5, 2), default=0.00, nullable=False)  # TDS percentage
    tds_section = Column(String(20), nullable=True)  # Like 194C, 194J, etc.
    
    # Additional Information
    narration = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    
    # Ledger Integration
    ledger_batch_id = Column(Integer, ForeignKey("transaction_batches.id"), nullable=True)
    is_ledger_posted = Column(Boolean, default=False, nullable=False)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False, nullable=False)
    reconciled_date = Column(Date, nullable=True)
    reconciled_by = Column(String(50), nullable=True)
    
    # Audit Fields
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=True)
    posted_by = Column(String(50), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier")
    bank_account = relationship("AccountsMaster", foreign_keys=[bank_account_id])
    bills = relationship("SupplierPaymentBill", back_populates="payment", cascade="all, delete-orphan")
    ledger_batch = relationship("TransactionBatch")
    
    @property
    def calculated_net_amount(self):
        """Calculate net amount: gross - discount - tds - other_deductions"""
        gross = self.gross_amount or Decimal('0.00')
        discount = self.discount_amount or Decimal('0.00')
        tds = self.tds_amount or Decimal('0.00')
        other = self.other_deductions or Decimal('0.00')
        return gross - discount - tds - other
    
    @property
    def total_bill_amount(self):
        """Calculate total amount from linked bills"""
        return sum(bill.paid_amount for bill in self.bills) if self.bills else Decimal('0.00')
    
    @property
    def payment_method_display(self):
        """Display payment method with details"""
        # Note: Column comparisons moved to application layer
        return f"{self.payment_mode} Payment"
    
    def __repr__(self):
        return f"<SupplierPayment(id={self.id}, payment_number='{self.payment_number}', status='{self.status}')>"


class SupplierPaymentBill(Base):
    """
    Supplier Payment Bill Model - Links payments to specific purchase bills
    Tracks partial payments and outstanding amounts
    """
    __tablename__ = "supplier_payment_bills"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(Integer, ForeignKey("supplier_payments.id"), nullable=False, index=True)
    
    # Purchase Bill Reference
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False, index=True)
    purchase_number = Column(String(50), nullable=True)
    
    # Bill Details
    bill_date = Column(Date, nullable=True)
    bill_amount = Column(Numeric(15, 2), nullable=False)  # Original bill amount
    previous_payments = Column(Numeric(15, 2), default=0.00, nullable=False)  # Already paid amount
    outstanding_amount = Column(Numeric(15, 2), nullable=False)  # Outstanding before this payment
    paid_amount = Column(Numeric(15, 2), nullable=False)  # Amount paid in this transaction
    balance_amount = Column(Numeric(15, 2), nullable=False)  # Remaining balance after payment
    
    # Discount and Adjustments
    discount_allowed = Column(Numeric(15, 2), default=0.00, nullable=False)
    adjustment_amount = Column(Numeric(15, 2), default=0.00, nullable=False)  # +ve or -ve adjustments
    
    # Additional Details
    remarks = Column(Text, nullable=True)
    
    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    payment = relationship("SupplierPayment", back_populates="bills")
    purchase = relationship("Purchase")
    
    @property
    def is_fully_paid(self):
        """Check if bill is fully paid"""
        return self.balance_amount <= Decimal('0.00')
    
    @property
    def payment_percentage(self):
        """Calculate payment percentage"""
        # Note: Column comparison moved to application layer
        return 0.00  # Will be calculated in the API layer
    
    def __repr__(self):
        return f"<SupplierPaymentBill(id={self.id}, payment_id={self.payment_id}, purchase_id={self.purchase_id})>"


class SupplierLedger(Base):
    """
    Supplier Ledger Model - Running balance for each supplier
    Tracks all transactions (purchases, payments, returns, adjustments)
    """
    __tablename__ = "supplier_ledger"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Transaction Details
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # 'Purchase', 'Payment', 'Return', 'Adjustment'
    reference_type = Column(String(50), nullable=True)  # 'PURCHASE', 'PAYMENT', 'RETURN'
    reference_id = Column(Integer, nullable=True)
    reference_number = Column(String(50), nullable=True)
    
    # Amount Details
    debit_amount = Column(Numeric(15, 2), default=0.00, nullable=False)  # Payments, Returns
    credit_amount = Column(Numeric(15, 2), default=0.00, nullable=False)  # Purchases, Charges
    running_balance = Column(Numeric(15, 2), default=0.00, nullable=False)  # Running balance
    
    # Description
    description = Column(String(500), nullable=False)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False, nullable=False)
    reconciled_date = Column(Date, nullable=True)
    
    # Audit Fields
    created_by = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier")
    
    @property
    def balance_type(self):
        """Determine if balance is payable or receivable"""
        # Note: Column comparisons moved to application layer
        return "Payable"  # Default, will be calculated in API layer
    
    def __repr__(self):
        return f"<SupplierLedger(id={self.id}, supplier_id={self.supplier_id}, balance={self.running_balance})>"


class TDSEntry(Base):
    """
    TDS Entry Model - Tax Deducted at Source tracking
    Links with supplier payments and generates TDS reports
    """
    __tablename__ = "tds_entries"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    financial_year = Column(String(10), nullable=False, index=True)  # '2025-26'
    quarter = Column(String(10), nullable=False)  # 'Q1', 'Q2', 'Q3', 'Q4'
    
    # Payment Reference
    payment_id = Column(Integer, ForeignKey("supplier_payments.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # TDS Details
    tds_section = Column(String(20), nullable=False)  # '194C', '194J', etc.
    tds_rate = Column(Numeric(5, 2), nullable=False)
    gross_amount = Column(Numeric(15, 2), nullable=False)  # Amount on which TDS calculated
    tds_amount = Column(Numeric(15, 2), nullable=False)  # TDS deducted
    
    # Certificate Details
    certificate_number = Column(String(50), nullable=True)
    certificate_date = Column(Date, nullable=True)
    is_certificate_issued = Column(Boolean, default=False, nullable=False)
    
    # Government Filing
    challan_number = Column(String(50), nullable=True)
    challan_date = Column(Date, nullable=True)
    is_deposited = Column(Boolean, default=False, nullable=False)
    
    # Audit Fields
    created_by = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    payment = relationship("SupplierPayment")
    supplier = relationship("Supplier")
    
    def __repr__(self):
        return f"<TDSEntry(id={self.id}, section='{self.tds_section}', amount={self.tds_amount})>"
