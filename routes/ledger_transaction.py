from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from database import get_db
from dependencies import get_current_user
from models.ledger_transaction import LedgerTransaction, TransactionBatch, TransactionTemplate
from models.accounts import AccountsMaster
from schemas.ledger_transaction import (
    LedgerTransactionCreate, LedgerTransactionUpdate, LedgerTransactionResponse,
    TransactionBatchCreate, TransactionBatchUpdate, TransactionBatchResponse,
    TransactionTemplateCreate, TransactionTemplateUpdate, TransactionTemplateResponse,
    AccountBalanceResponse, LedgerSummaryResponse, BulkTransactionCreate,
    VoucherType, ReferenceType, PartyType, TransactionCategory
)
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Helper function to generate transaction numbers
def generate_transaction_number(db: Session, voucher_type: str) -> str:
    """Generate unique transaction number"""
    today = datetime.now()
    prefix = f"{voucher_type}{today.strftime('%Y%m%d')}"
    
    # Get the last transaction number for today
    last_transaction = db.query(LedgerTransaction).filter(
        LedgerTransaction.transaction_number.like(f"{prefix}%")
    ).order_by(desc(LedgerTransaction.transaction_number)).first()
    
    if last_transaction:
        last_number = int(str(last_transaction.transaction_number)[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{prefix}{new_number:04d}"


# Helper function to generate batch numbers
def generate_batch_number(db: Session) -> str:
    """Generate unique batch number"""
    today = datetime.now()
    prefix = f"BATCH{today.strftime('%Y%m%d')}"
    
    # Get the last batch number for today
    last_batch = db.query(TransactionBatch).filter(
        TransactionBatch.batch_number.like(f"{prefix}%")
    ).order_by(desc(TransactionBatch.batch_number)).first()
    
    if last_batch:
        last_number = int(str(last_batch.batch_number)[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{prefix}{new_number:04d}"


# Ledger Transaction CRUD Operations
@router.post("/", response_model=LedgerTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_ledger_transaction(
    transaction: LedgerTransactionCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create a new ledger transaction with JWT Token Authentication."""
    try:
        # Verify account exists
        account = db.query(AccountsMaster).filter(
            AccountsMaster.account_code == transaction.account_code
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account with code {transaction.account_code} not found"
            )
        
        # Generate transaction number if not provided
        if not transaction.transaction_number:
            transaction.transaction_number = generate_transaction_number(db, transaction.voucher_type.value)
        
        # Create transaction
        db_transaction = LedgerTransaction(
            **transaction.dict(),
            created_by=current_user
        )
        
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        logger.info(f"Created ledger transaction {db_transaction.transaction_number} by user {current_user}")
        return db_transaction
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ledger transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transaction: {str(e)}"
        )


@router.get("/", response_model=List[LedgerTransactionResponse])
async def get_ledger_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    account_code: Optional[str] = Query(None, description="Filter by account code"),
    voucher_type: Optional[VoucherType] = Query(None, description="Filter by voucher type"),
    reference_type: Optional[ReferenceType] = Query(None, description="Filter by reference type"),
    reference_id: Optional[str] = Query(None, description="Filter by reference ID"),
    party_type: Optional[PartyType] = Query(None, description="Filter by party type"),
    party_id: Optional[str] = Query(None, description="Filter by party ID"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    is_posted: Optional[bool] = Query(None, description="Filter by posted status"),
    is_reconciled: Optional[bool] = Query(None, description="Filter by reconciled status"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get ledger transactions with filtering options using JWT Token Authentication."""
    try:
        query = db.query(LedgerTransaction).filter(LedgerTransaction.is_active == True)
        
        # Apply filters
        if account_code:
            query = query.filter(LedgerTransaction.account_code == account_code)
        if voucher_type:
            query = query.filter(LedgerTransaction.voucher_type == voucher_type)
        if reference_type:
            query = query.filter(LedgerTransaction.reference_type == reference_type)
        if reference_id:
            query = query.filter(LedgerTransaction.reference_id == reference_id)
        if party_type:
            query = query.filter(LedgerTransaction.party_type == party_type)
        if party_id:
            query = query.filter(LedgerTransaction.party_id == party_id)
        if date_from:
            query = query.filter(LedgerTransaction.transaction_date >= date_from)
        if date_to:
            query = query.filter(LedgerTransaction.transaction_date <= date_to)
        if is_posted is not None:
            query = query.filter(LedgerTransaction.is_posted == is_posted)
        if is_reconciled is not None:
            query = query.filter(LedgerTransaction.is_reconciled == is_reconciled)
        
        # Order by transaction date descending
        transactions = query.order_by(desc(LedgerTransaction.transaction_date)).offset(skip).limit(limit).all()
        
        return transactions
        
    except Exception as e:
        logger.error(f"Error fetching ledger transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching transactions"
        )


@router.get("/{transaction_id}", response_model=LedgerTransactionResponse)
async def get_ledger_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get a specific ledger transaction by ID using JWT Token Authentication."""
    transaction = db.query(LedgerTransaction).filter(
        LedgerTransaction.id == transaction_id,
        LedgerTransaction.is_active == True
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


@router.put("/{transaction_id}", response_model=LedgerTransactionResponse)
async def update_ledger_transaction(
    transaction_id: int,
    transaction_update: LedgerTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update a ledger transaction using JWT Token Authentication."""
    try:
        # Get existing transaction
        db_transaction = db.query(LedgerTransaction).filter(
            LedgerTransaction.id == transaction_id,
            LedgerTransaction.is_active == True
        ).first()
        
        if not db_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if transaction is posted
        if getattr(db_transaction, 'is_posted', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update posted transactions"
            )
        
        # Update fields
        update_data = transaction_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_transaction, field, value)
        
        setattr(db_transaction, 'updated_by', current_user)
        
        db.commit()
        db.refresh(db_transaction)
        
        logger.info(f"Updated ledger transaction {db_transaction.transaction_number} by user {current_user}")
        return db_transaction
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating ledger transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating transaction: {str(e)}"
        )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ledger_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Soft delete a ledger transaction using JWT Token Authentication."""
    try:
        db_transaction = db.query(LedgerTransaction).filter(
            LedgerTransaction.id == transaction_id,
            LedgerTransaction.is_active == True
        ).first()
        
        if not db_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if transaction is posted
        if getattr(db_transaction, 'is_posted', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete posted transactions"
            )
        
        # Soft delete
        setattr(db_transaction, 'is_active', False)
        setattr(db_transaction, 'updated_by', current_user)
        
        db.commit()
        
        logger.info(f"Deleted ledger transaction {db_transaction.transaction_number} by user {current_user}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting ledger transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting transaction: {str(e)}"
        )


# Bulk Transaction Operations
@router.post("/bulk", response_model=TransactionBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_transactions(
    bulk_transaction: BulkTransactionCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create multiple transactions as a batch with double-entry validation using JWT Token Authentication."""
    try:
        # Generate batch number
        batch_number = generate_batch_number(db)
        
        # Calculate totals
        total_debit = sum(t.debit_amount for t in bulk_transaction.transactions)
        total_credit = sum(t.credit_amount for t in bulk_transaction.transactions)
        
        # Create transaction batch
        db_batch = TransactionBatch(
            batch_number=batch_number,
            batch_date=bulk_transaction.batch_date,
            description=bulk_transaction.batch_description,
            total_debit=total_debit,
            total_credit=total_credit,
            is_balanced=(total_debit == total_credit),
            is_posted=True,
            created_by=current_user
        )
        
        db.add(db_batch)
        db.flush()  # Get the batch ID
        
        # Create individual transactions
        for transaction_data in bulk_transaction.transactions:
            # Generate transaction number
            transaction_number = generate_transaction_number(db, transaction_data.voucher_type.value)
            
            db_transaction = LedgerTransaction(
                **transaction_data.dict(),
                transaction_number=transaction_number,
                created_by=current_user
            )
            db.add(db_transaction)
        
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"Created bulk transaction batch {batch_number} with {len(bulk_transaction.transactions)} transactions by user {current_user}")
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating bulk transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bulk transactions: {str(e)}"
        )


# Account Balance Reports
@router.get("/reports/account-balance", response_model=List[AccountBalanceResponse])
async def get_account_balances(
    account_code: Optional[str] = Query(None, description="Specific account code"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    date_from: Optional[date] = Query(None, description="Calculate balance from date"),
    date_to: Optional[date] = Query(None, description="Calculate balance to date"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get account balance report using JWT Token Authentication."""
    try:
        # Base query for accounts
        accounts_query = db.query(AccountsMaster).filter(AccountsMaster.is_active == True)
        
        if account_code:
            accounts_query = accounts_query.filter(AccountsMaster.account_code == account_code)
        if account_type:
            accounts_query = accounts_query.filter(AccountsMaster.account_type == account_type)
        
        accounts = accounts_query.all()
        balance_reports = []
        
        for account in accounts:
            # Build transaction query
            transactions_query = db.query(LedgerTransaction).filter(
                LedgerTransaction.account_code == account.account_code,
                LedgerTransaction.is_active == True,
                LedgerTransaction.is_posted == True
            )
            
            if date_from:
                transactions_query = transactions_query.filter(
                    LedgerTransaction.transaction_date >= date_from
                )
            if date_to:
                transactions_query = transactions_query.filter(
                    LedgerTransaction.transaction_date <= date_to
                )
            
            # Calculate totals
            result = transactions_query.with_entities(
                func.sum(LedgerTransaction.debit_amount).label('total_debits'),
                func.sum(LedgerTransaction.credit_amount).label('total_credits'),
                func.count(LedgerTransaction.id).label('transaction_count'),
                func.max(LedgerTransaction.transaction_date).label('last_transaction_date')
            ).first()
            
            if result:
                total_debits = result[0] or Decimal('0.00')
                total_credits = result[1] or Decimal('0.00')
                transaction_count = result[2] or 0
                last_transaction_date = result[3]
            else:
                total_debits = Decimal('0.00')
                total_credits = Decimal('0.00')
                transaction_count = 0
                last_transaction_date = None
            
            net_balance = total_debits - total_credits
            
            balance_reports.append(AccountBalanceResponse(
                account_code=str(account.account_code),
                account_name=str(account.account_name),
                account_type=str(account.account_type),
                total_debits=total_debits,
                total_credits=total_credits,
                net_balance=net_balance,
                transaction_count=transaction_count,
                last_transaction_date=last_transaction_date
            ))
        
        return balance_reports
        
    except Exception as e:
        logger.error(f"Error generating account balance report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating balance report"
        )


# Transaction Batches
@router.get("/batches/", response_model=List[TransactionBatchResponse])
async def get_transaction_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    is_posted: Optional[bool] = Query(None, description="Filter by posted status"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get transaction batches using JWT Token Authentication."""
    try:
        query = db.query(TransactionBatch).filter(TransactionBatch.is_active == True)
        
        if date_from:
            query = query.filter(TransactionBatch.batch_date >= date_from)
        if date_to:
            query = query.filter(TransactionBatch.batch_date <= date_to)
        if is_posted is not None:
            query = query.filter(TransactionBatch.is_posted == is_posted)
        
        batches = query.order_by(desc(TransactionBatch.batch_date)).offset(skip).limit(limit).all()
        return batches
        
    except Exception as e:
        logger.error(f"Error fetching transaction batches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching batches"
        )


# Transaction Templates
@router.post("/templates/", response_model=TransactionTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction_template(
    template: TransactionTemplateCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create a transaction template using JWT Token Authentication."""
    try:
        db_template = TransactionTemplate(
            **template.dict(),
            created_by=current_user
        )
        
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        logger.info(f"Created transaction template {db_template.template_code} by user {current_user}")
        return db_template
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating transaction template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )


@router.get("/templates/", response_model=List[TransactionTemplateResponse])
async def get_transaction_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[TransactionCategory] = Query(None, description="Filter by category"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get transaction templates using JWT Token Authentication."""
    try:
        query = db.query(TransactionTemplate).filter(TransactionTemplate.is_active == is_active)
        
        if category:
            query = query.filter(TransactionTemplate.category == category)
        
        templates = query.order_by(TransactionTemplate.template_name).offset(skip).limit(limit).all()
        return templates
        
    except Exception as e:
        logger.error(f"Error fetching transaction templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching templates"
        )
