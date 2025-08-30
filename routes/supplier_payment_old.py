from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from ..database import get_db
from ..dependencies import get_current_user
from ..models.supplier_payment import (
    SupplierPayment, SupplierPaymentBill, SupplierLedger, 
    TDSEntry, PaymentStatus, PaymentMode, PaymentType
)
from ..models.suppliers import Supplier
from ..models.purchase import Purchase
from ..models.accounts import AccountsMaster
from ..models.stock_ledger import StockLedger
from ..models.ledger_transaction import TransactionBatch
from ..schemas.supplier_payment import (
    SupplierPaymentCreate, SupplierPaymentUpdate, SupplierPaymentResponse,
    SupplierPaymentListResponse, SupplierPaymentBillResponse, SupplierPaymentBillCreate,
    PaymentPostRequest, PaymentReconciliationRequest,
    OutstandingBillResponse, GetOutstandingBillsRequest,
    PayAgainstBillsRequest, SupplierPaymentSummaryResponse,
    SupplierOutstandingResponse, TDSSummaryResponse,
    TDSEntryResponse, SupplierLedgerResponse, PaymentModeEnum, PaymentTypeEnum
)

router = APIRouter(prefix="/supplier-payments", tags=["supplier-payments"])


# Helper function to generate payment number
def generate_payment_number(db: Session) -> str:
    """Generate unique payment number"""
    last_payment = db.query(SupplierPayment).order_by(desc(SupplierPayment.id)).first()
    if last_payment:
        last_num = int(last_payment.payment_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"SPAY-{new_num:06d}"


# Helper function to create ledger entries
async def create_ledger_entries(payment: SupplierPayment, db: Session):
    """Create automatic ledger entries for supplier payment"""
    try:
        # Create transaction batch
        batch = TransactionBatch(
            batch_date=payment.payment_date,
            batch_type="Supplier Payment",
            reference_number=payment.payment_number,
            total_amount=payment.net_amount,
            created_by=payment.created_by,
            status="Posted"
        )
        db.add(batch)
        db.flush()
        
        # Get supplier account
        supplier_account = db.query(AccountsMaster).filter(
            AccountsMaster.account_type == "Creditors",
            AccountsMaster.reference_id == payment.supplier_id,
            AccountsMaster.reference_type == "Supplier"
        ).first()
        
        if not supplier_account:
            raise HTTPException(status_code=404, detail="Supplier account not found")
        
        # Get payment account based on payment mode
        payment_account_code = get_payment_account_code(payment.payment_mode)
        payment_account = db.query(AccountsMaster).filter(
            AccountsMaster.account_code == payment_account_code
        ).first()
        
        if not payment_account:
            raise HTTPException(status_code=404, detail=f"Payment account {payment_account_code} not found")
        
        entries = []
        
        # Credit supplier account (decrease liability)
        entries.append({
            'account_code': supplier_account.account_code,
            'debit_amount': payment.gross_amount,
            'credit_amount': Decimal('0.00'),
            'particulars': f"Payment against supplier bills - {payment.payment_number}"
        })
        
        # Debit payment account (cash/bank)
        entries.append({
            'account_code': payment_account.account_code,
            'debit_amount': Decimal('0.00'),
            'credit_amount': payment.net_amount,
            'particulars': f"Payment to {supplier_account.account_name} - {payment.payment_number}"
        })
        
        # Handle TDS if any
        if payment.tds_amount > 0:
            tds_account = db.query(AccountsMaster).filter(
                AccountsMaster.account_code == "TDS_PAYABLE"
            ).first()
            
            if tds_account:
                entries.append({
                    'account_code': tds_account.account_code,
                    'debit_amount': Decimal('0.00'),
                    'credit_amount': payment.tds_amount,
                    'particulars': f"TDS deducted - {payment.payment_number}"
                })
        
        # Handle other deductions
        if payment.other_deductions > 0:
            deduction_account = db.query(AccountsMaster).filter(
                AccountsMaster.account_code == "OTHER_DEDUCTIONS"
            ).first()
            
            if deduction_account:
                entries.append({
                    'account_code': deduction_account.account_code,
                    'debit_amount': Decimal('0.00'),
                    'credit_amount': payment.other_deductions,
                    'particulars': f"Other deductions - {payment.payment_number}"
                })
        
        # Create ledger entries
        from ..models.accounts import AccountsLedger
        for entry in entries:
            ledger_entry = AccountsLedger(
                transaction_date=payment.payment_date,
                account_code=entry['account_code'],
                debit_amount=entry['debit_amount'],
                credit_amount=entry['credit_amount'],
                particulars=entry['particulars'],
                reference_type="Supplier Payment",
                reference_id=payment.id,
                reference_number=payment.payment_number,
                batch_id=batch.id,
                created_by=payment.created_by,
                is_reconciled=False
            )
            db.add(ledger_entry)
        
        # Update payment with batch ID
        payment.ledger_batch_id = batch.id
        payment.is_ledger_posted = True
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create ledger entries: {str(e)}")


def get_payment_account_code(payment_mode: PaymentMode) -> str:
    """Get account code based on payment mode"""
    mode_mapping = {
        PaymentMode.CASH: "CASH_IN_HAND",
        PaymentMode.BANK_TRANSFER: "BANK_ACCOUNT",
        PaymentMode.CHEQUE: "BANK_ACCOUNT",
        PaymentMode.DEMAND_DRAFT: "BANK_ACCOUNT",
        PaymentMode.ONLINE_TRANSFER: "BANK_ACCOUNT",
        PaymentMode.UPI: "UPI_ACCOUNT",
        PaymentMode.RTGS: "BANK_ACCOUNT",
        PaymentMode.NEFT: "BANK_ACCOUNT",
        PaymentMode.CREDIT_CARD: "CREDIT_CARD_ACCOUNT"
    }
    return mode_mapping.get(payment_mode, "BANK_ACCOUNT")


# Helper function to update supplier ledger
def update_supplier_ledger(payment: SupplierPayment, db: Session):
    """Update supplier ledger with payment entry"""
    try:
        supplier_ledger = SupplierLedger(
            supplier_id=payment.supplier_id,
            transaction_date=payment.payment_date,
            transaction_type="Payment",
            reference_type="Supplier Payment",
            reference_id=payment.id,
            reference_number=payment.payment_number,
            debit_amount=Decimal('0.00'),
            credit_amount=payment.gross_amount,
            description=f"Payment - {payment.payment_number}",
            created_by=payment.created_by
        )
        
        # Calculate running balance
        last_balance = db.query(SupplierLedger).filter(
            SupplierLedger.supplier_id == payment.supplier_id
        ).order_by(desc(SupplierLedger.id)).first()
        
        if last_balance:
            if last_balance.balance_type == "Debit":
                new_balance = last_balance.running_balance - payment.gross_amount
                supplier_ledger.running_balance = abs(new_balance)
                supplier_ledger.balance_type = "Debit" if new_balance >= 0 else "Credit"
            else:
                new_balance = last_balance.running_balance + payment.gross_amount
                supplier_ledger.running_balance = new_balance
                supplier_ledger.balance_type = "Credit"
        else:
            supplier_ledger.running_balance = payment.gross_amount
            supplier_ledger.balance_type = "Credit"
        
        db.add(supplier_ledger)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update supplier ledger: {str(e)}")


@router.get("/outstanding-bills/{supplier_id}", response_model=List[OutstandingBillResponse])
async def get_outstanding_bills(
    supplier_id: int,
    as_of_date: Optional[date] = Query(None, description="As of date for outstanding calculation"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get outstanding bills for a supplier"""
    
    # Validate supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    if not as_of_date:
        as_of_date = date.today()
    
    # Query purchases with outstanding amounts
    purchases = db.query(
        Purchase.id,
        Purchase.purchase_number,
        Purchase.purchase_date,
        Purchase.grand_total,
        Purchase.supplier_invoice_number,
        func.coalesce(func.sum(SupplierPaymentBill.paid_amount), Decimal('0.00')).label('payments_made')
    ).outerjoin(
        SupplierPaymentBill, Purchase.id == SupplierPaymentBill.purchase_id
    ).filter(
        Purchase.supplier_id == supplier_id,
        Purchase.status == "Posted",
        Purchase.purchase_date <= as_of_date
    ).group_by(
        Purchase.id, Purchase.purchase_number, Purchase.purchase_date,
        Purchase.grand_total, Purchase.supplier_invoice_number
    ).having(
        Purchase.grand_total > func.coalesce(func.sum(SupplierPaymentBill.paid_amount), Decimal('0.00'))
    ).all()
    
    outstanding_bills = []
    for purchase in purchases:
        outstanding_amount = purchase.grand_total - purchase.payments_made
        days_outstanding = (as_of_date - purchase.purchase_date).days
        
        outstanding_bills.append(OutstandingBillResponse(
            purchase_id=purchase.id,
            purchase_number=purchase.purchase_number,
            purchase_date=purchase.purchase_date,
            bill_amount=purchase.grand_total,
            payments_made=purchase.payments_made,
            outstanding_amount=outstanding_amount,
            days_outstanding=days_outstanding,
            supplier_invoice_number=purchase.supplier_invoice_number,
            is_overdue=days_outstanding > 30  # Consider 30+ days as overdue
        ))
    
    return outstanding_bills


@router.post("/", response_model=SupplierPaymentResponse)
async def create_supplier_payment(
    payment_data: SupplierPaymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new supplier payment"""
    
    # Validate supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == payment_data.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Validate bills exist and have sufficient outstanding amount
    if payment_data.payment_type == PaymentType.AGAINST_BILL:
        for bill in payment_data.bills:
            purchase = db.query(Purchase).filter(
                Purchase.id == bill.purchase_id,
                Purchase.supplier_id == payment_data.supplier_id,
                Purchase.status == "Posted"
            ).first()
            
            if not purchase:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Purchase {bill.purchase_id} not found or not posted"
                )
            
            # Check outstanding amount
            paid_amount = db.query(func.sum(SupplierPaymentBill.paid_amount)).filter(
                SupplierPaymentBill.purchase_id == bill.purchase_id
            ).scalar() or Decimal('0.00')
            
            outstanding = purchase.grand_total - paid_amount
            if bill.paid_amount > outstanding:
                raise HTTPException(
                    status_code=400,
                    detail=f"Payment amount {bill.paid_amount} exceeds outstanding amount {outstanding} for purchase {purchase.purchase_number}"
                )
    
    try:
        # Create payment record
        payment = SupplierPayment(
            payment_number=generate_payment_number(db),
            payment_date=payment_data.payment_date,
            supplier_id=payment_data.supplier_id,
            payment_type=payment_data.payment_type,
            payment_mode=payment_data.payment_mode,
            gross_amount=payment_data.gross_amount,
            discount_amount=payment_data.discount_amount,
            tds_amount=payment_data.tds_amount,
            other_deductions=payment_data.other_deductions,
            bank_account_id=payment_data.bank_account_id,
            cheque_number=payment_data.cheque_number,
            cheque_date=payment_data.cheque_date,
            bank_name=payment_data.bank_name,
            bank_branch=payment_data.bank_branch,
            transaction_reference=payment_data.transaction_reference,
            tds_rate=payment_data.tds_rate,
            tds_section=payment_data.tds_section,
            narration=payment_data.narration,
            remarks=payment_data.remarks,
            created_by=payment_data.created_by,
            status=PaymentStatus.DRAFT
        )
        
        db.add(payment)
        db.flush()
        
        # Create payment bill entries
        for bill_data in payment_data.bills:
            payment_bill = SupplierPaymentBill(
                payment_id=payment.id,
                purchase_id=bill_data.purchase_id,
                bill_amount=bill_data.bill_amount,
                outstanding_amount=bill_data.outstanding_amount,
                paid_amount=bill_data.paid_amount,
                discount_allowed=bill_data.discount_allowed,
                adjustment_amount=bill_data.adjustment_amount,
                remarks=bill_data.remarks
            )
            db.add(payment_bill)
        
        # Create TDS entry if applicable
        if payment.tds_amount > 0:
            tds_entry = TDSEntry(
                payment_id=payment.id,
                supplier_id=payment.supplier_id,
                tds_section=payment.tds_section,
                tds_rate=payment.tds_rate,
                gross_amount=payment.gross_amount,
                tds_amount=payment.tds_amount,
                financial_year=f"{payment.payment_date.year}-{payment.payment_date.year + 1}",
                quarter=f"Q{((payment.payment_date.month - 1) // 3) + 1}",
                created_by=payment.created_by
            )
            db.add(tds_entry)
        
        db.commit()
        
        # Queue background tasks for ledger and supplier ledger updates
        background_tasks.add_task(update_supplier_ledger, payment, db)
        
        return payment
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


@router.get("/", response_model=List[SupplierPaymentListResponse])
async def get_supplier_payments(
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_date_from: Optional[date] = Query(None, description="Filter payments from date"),
    payment_date_to: Optional[date] = Query(None, description="Filter payments to date"),
    payment_mode: Optional[str] = Query(None, description="Filter by payment mode"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get supplier payments with filters"""
    
    query = db.query(SupplierPayment)
    
    # Apply filters
    if supplier_id:
        query = query.filter(SupplierPayment.supplier_id == supplier_id)
    
    if status:
        query = query.filter(SupplierPayment.status == status)
    
    if payment_date_from:
        query = query.filter(SupplierPayment.payment_date >= payment_date_from)
    
    if payment_date_to:
        query = query.filter(SupplierPayment.payment_date <= payment_date_to)
    
    if payment_mode:
        query = query.filter(SupplierPayment.payment_mode == payment_mode)
    
    # Order by payment date descending
    query = query.order_by(desc(SupplierPayment.payment_date), desc(SupplierPayment.id))
    
    # Apply pagination
    payments = query.offset(offset).limit(limit).all()
    
    return payments


@router.get("/{payment_id}", response_model=SupplierPaymentResponse)
async def get_supplier_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get supplier payment by ID"""
    
    payment = db.query(SupplierPayment).filter(SupplierPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment


@router.put("/{payment_id}", response_model=SupplierPaymentResponse)
async def update_supplier_payment(
    payment_id: int,
    payment_data: SupplierPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update supplier payment (only draft payments can be updated)"""
    
    payment = db.query(SupplierPayment).filter(SupplierPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft payments can be updated")
    
    # Update payment fields
    for field, value in payment_data.dict(exclude_unset=True).items():
        if field != "updated_by":
            setattr(payment, field, value)
    
    payment.updated_by = payment_data.updated_by
    payment.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        return payment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update payment: {str(e)}")


@router.post("/{payment_id}/post")
async def post_supplier_payment(
    payment_id: int,
    post_request: PaymentPostRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Post supplier payment to ledger"""
    
    payment = db.query(SupplierPayment).filter(SupplierPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft payments can be posted")
    
    try:
        payment.status = PaymentStatus.POSTED
        payment.posted_by = post_request.posted_by
        payment.posted_at = datetime.utcnow()
        
        db.commit()
        
        # Create ledger entries in background if requested
        if post_request.post_to_ledger:
            background_tasks.add_task(create_ledger_entries, payment, db)
        
        return {"message": "Payment posted successfully", "payment_id": payment_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to post payment: {str(e)}")


@router.post("/{payment_id}/reconcile")
async def reconcile_supplier_payment(
    payment_id: int,
    reconcile_request: PaymentReconciliationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark supplier payment as reconciled/unreconciled"""
    
    payment = db.query(SupplierPayment).filter(SupplierPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.POSTED:
        raise HTTPException(status_code=400, detail="Only posted payments can be reconciled")
    
    try:
        payment.is_reconciled = reconcile_request.reconciled
        payment.reconciled_by = reconcile_request.reconciled_by if reconcile_request.reconciled else None
        payment.reconciled_date = reconcile_request.reconciliation_date if reconcile_request.reconciled else None
        
        db.commit()
        
        return {"message": f"Payment {'reconciled' if reconcile_request.reconciled else 'unreconciled'} successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reconcile payment: {str(e)}")


@router.delete("/{payment_id}")
async def cancel_supplier_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel supplier payment (only draft payments can be cancelled)"""
    
    payment = db.query(SupplierPayment).filter(SupplierPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft payments can be cancelled")
    
    try:
        payment.status = PaymentStatus.CANCELLED
        db.commit()
        
        return {"message": "Payment cancelled successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cancel payment: {str(e)}")


# Reporting endpoints
@router.get("/reports/summary", response_model=SupplierPaymentSummaryResponse)
async def get_payment_summary(
    date_from: Optional[date] = Query(None, description="From date"),
    date_to: Optional[date] = Query(None, description="To date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get supplier payment summary"""
    
    query = db.query(SupplierPayment)
    
    if date_from:
        query = query.filter(SupplierPayment.payment_date >= date_from)
    if date_to:
        query = query.filter(SupplierPayment.payment_date <= date_to)
    
    payments = query.all()
    
    total_amount = sum(p.net_amount for p in payments)
    total_tds = sum(p.tds_amount for p in payments)
    cash_payments = sum(p.net_amount for p in payments if p.payment_mode == PaymentMode.CASH)
    bank_payments = total_amount - cash_payments
    
    pending_reconciliation = len([p for p in payments if p.status == PaymentStatus.POSTED and not p.is_reconciled])
    draft_payments = len([p for p in payments if p.status == PaymentStatus.DRAFT])
    posted_payments = len([p for p in payments if p.status == PaymentStatus.POSTED])
    
    return SupplierPaymentSummaryResponse(
        total_payments=len(payments),
        total_amount=total_amount,
        total_tds=total_tds,
        cash_payments=cash_payments,
        bank_payments=bank_payments,
        pending_reconciliation=pending_reconciliation,
        draft_payments=draft_payments,
        posted_payments=posted_payments
    )


@router.get("/reports/supplier-outstanding", response_model=List[SupplierOutstandingResponse])
async def get_supplier_outstanding_report(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get supplier-wise outstanding report"""
    
    if not as_of_date:
        as_of_date = date.today()
    
    # Complex query to get supplier outstanding amounts
    suppliers = db.query(
        Supplier.id,
        Supplier.supplier_name,
        func.coalesce(func.sum(Purchase.grand_total), Decimal('0.00')).label('total_purchases'),
        func.coalesce(func.sum(SupplierPaymentBill.paid_amount), Decimal('0.00')).label('total_payments')
    ).outerjoin(
        Purchase, Supplier.id == Purchase.supplier_id
    ).outerjoin(
        SupplierPaymentBill, Purchase.id == SupplierPaymentBill.purchase_id
    ).filter(
        or_(Purchase.purchase_date.is_(None), Purchase.purchase_date <= as_of_date),
        or_(Purchase.status.is_(None), Purchase.status == "Posted")
    ).group_by(
        Supplier.id, Supplier.supplier_name
    ).having(
        func.coalesce(func.sum(Purchase.grand_total), Decimal('0.00')) > 
        func.coalesce(func.sum(SupplierPaymentBill.paid_amount), Decimal('0.00'))
    ).all()
    
    outstanding_report = []
    for supplier in suppliers:
        outstanding_amount = supplier.total_purchases - supplier.total_payments
        
        # Calculate overdue amount (>30 days)
        overdue_purchases = db.query(func.sum(Purchase.grand_total)).filter(
            Purchase.supplier_id == supplier.id,
            Purchase.status == "Posted",
            Purchase.purchase_date <= as_of_date - datetime.timedelta(days=30)
        ).scalar() or Decimal('0.00')
        
        overdue_payments = db.query(func.sum(SupplierPaymentBill.paid_amount)).join(
            Purchase, SupplierPaymentBill.purchase_id == Purchase.id
        ).filter(
            Purchase.supplier_id == supplier.id,
            Purchase.purchase_date <= as_of_date - datetime.timedelta(days=30)
        ).scalar() or Decimal('0.00')
        
        overdue_amount = overdue_purchases - overdue_payments
        
        # Get last payment date
        last_payment = db.query(SupplierPayment.payment_date).filter(
            SupplierPayment.supplier_id == supplier.id,
            SupplierPayment.status == PaymentStatus.POSTED
        ).order_by(desc(SupplierPayment.payment_date)).first()
        
        # Calculate average outstanding days
        avg_days = db.query(func.avg(func.extract('days', as_of_date - Purchase.purchase_date))).filter(
            Purchase.supplier_id == supplier.id,
            Purchase.status == "Posted"
        ).scalar() or 0
        
        outstanding_report.append(SupplierOutstandingResponse(
            supplier_id=supplier.id,
            supplier_name=supplier.supplier_name,
            total_purchases=supplier.total_purchases,
            total_payments=supplier.total_payments,
            outstanding_amount=outstanding_amount,
            overdue_amount=max(overdue_amount, Decimal('0.00')),
            days_outstanding=int(avg_days),
            last_payment_date=last_payment.payment_date if last_payment else None
        ))
    
    return outstanding_report


@router.get("/supplier-ledger/{supplier_id}", response_model=List[SupplierLedgerResponse])
async def get_supplier_ledger(
    supplier_id: int,
    date_from: Optional[date] = Query(None, description="From date"),
    date_to: Optional[date] = Query(None, description="To date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get supplier ledger entries"""
    
    # Validate supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    query = db.query(SupplierLedger).filter(SupplierLedger.supplier_id == supplier_id)
    
    if date_from:
        query = query.filter(SupplierLedger.transaction_date >= date_from)
    if date_to:
        query = query.filter(SupplierLedger.transaction_date <= date_to)
    
    ledger_entries = query.order_by(SupplierLedger.transaction_date, SupplierLedger.id).all()
    
    return ledger_entries


@router.get("/tds/summary", response_model=List[TDSSummaryResponse])
async def get_tds_summary(
    financial_year: Optional[str] = Query(None, description="Financial year (e.g., 2023-24)"),
    quarter: Optional[str] = Query(None, description="Quarter (Q1, Q2, Q3, Q4)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get TDS summary report"""
    
    query = db.query(
        TDSEntry.financial_year,
        TDSEntry.quarter,
        func.sum(TDSEntry.tds_amount).label('total_tds'),
        func.count(func.distinct(TDSEntry.supplier_id)).label('total_suppliers'),
        func.count(func.case([(TDSEntry.is_certificate_issued == True, 1)])).label('certificates_issued'),
        func.count(func.case([(TDSEntry.is_certificate_issued == False, 1)])).label('certificates_pending'),
        func.sum(func.case([(TDSEntry.is_deposited == True, TDSEntry.tds_amount)], else_=Decimal('0.00'))).label('deposited_amount'),
        func.sum(func.case([(TDSEntry.is_deposited == False, TDSEntry.tds_amount)], else_=Decimal('0.00'))).label('pending_deposit')
    )
    
    if financial_year:
        query = query.filter(TDSEntry.financial_year == financial_year)
    if quarter:
        query = query.filter(TDSEntry.quarter == quarter)
    
    tds_summary = query.group_by(TDSEntry.financial_year, TDSEntry.quarter).all()
    
    result = []
    for summary in tds_summary:
        result.append(TDSSummaryResponse(
            financial_year=summary.financial_year,
            quarter=summary.quarter,
            total_tds=summary.total_tds or Decimal('0.00'),
            total_suppliers=summary.total_suppliers or 0,
            certificates_issued=summary.certificates_issued or 0,
            certificates_pending=summary.certificates_pending or 0,
            deposited_amount=summary.deposited_amount or Decimal('0.00'),
            pending_deposit=summary.pending_deposit or Decimal('0.00')
        ))
    
    return result


@router.post("/pay-against-bills", response_model=SupplierPaymentResponse)
async def pay_against_selected_bills(
    request: PayAgainstBillsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create payment against selected bills with automatic calculation"""
    
    # Validate supplier
    supplier = db.query(Supplier).filter(Supplier.id == request.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Calculate totals from selected bills
    gross_amount = Decimal('0.00')
    bills_data = []
    
    for bill in request.selected_bills:
        purchase = db.query(Purchase).filter(
            Purchase.id == bill['purchase_id'],
            Purchase.supplier_id == request.supplier_id,
            Purchase.status == "Posted"
        ).first()
        
        if not purchase:
            raise HTTPException(
                status_code=404,
                detail=f"Purchase {bill['purchase_id']} not found"
            )
        
        # Validate amounts
        paying_amount = Decimal(str(bill['paying_amount']))
        discount_allowed = Decimal(str(bill.get('discount_allowed', '0.00')))
        outstanding_amount = Decimal(str(bill['outstanding_amount']))
        
        if paying_amount + discount_allowed > outstanding_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Payment + discount cannot exceed outstanding amount for bill {purchase.purchase_number}"
            )
        
        gross_amount += paying_amount + discount_allowed
        
        bills_data.append({
            'purchase_id': bill['purchase_id'],
            'bill_amount': purchase.grand_total,
            'outstanding_amount': outstanding_amount,
            'paid_amount': paying_amount,
            'discount_allowed': discount_allowed,
            'adjustment_amount': Decimal('0.00'),
            'remarks': f"Payment against {purchase.purchase_number}"
        })
    
    # Calculate TDS
    tds_amount = (gross_amount * request.tds_rate / 100).quantize(Decimal('0.01'))
    
    # Create payment data
    payment_create = SupplierPaymentCreate(
        payment_date=request.payment_date,
        supplier_id=request.supplier_id,
        payment_type=PaymentType.AGAINST_BILL,
        payment_mode=PaymentMode(request.payment_mode),
        gross_amount=gross_amount,
        discount_amount=sum(Decimal(str(bill.get('discount_allowed', '0.00'))) for bill in request.selected_bills),
        tds_amount=tds_amount,
        other_deductions=Decimal('0.00'),
        bank_account_id=request.bank_account_id,
        cheque_number=request.cheque_number,
        cheque_date=request.cheque_date,
        transaction_reference=request.transaction_reference,
        tds_rate=request.tds_rate,
        tds_section=request.tds_section,
        narration=f"Payment against {len(bills_data)} bills",
        bills=[SupplierPaymentBillCreate(**bill) for bill in bills_data],
        created_by=request.created_by
    )
    
    # Use the existing create payment function
    return await create_supplier_payment(payment_create, background_tasks, db, current_user)
