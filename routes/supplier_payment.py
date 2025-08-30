from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from database import get_db
from dependencies import get_current_user
from models.supplier_payment import (
    SupplierPayment, SupplierPaymentBill, SupplierLedger, 
    TDSEntry, PaymentStatus, PaymentMode, PaymentType
)
from models.suppliers import Supplier
from models.purchase import Purchase
from models.accounts import AccountsMaster
from models.ledger_transaction import TransactionBatch
from schemas.supplier_payment import (
    SupplierPaymentCreate, SupplierPaymentUpdate, SupplierPaymentResponse,
    SupplierPaymentListResponse, SupplierPaymentBillResponse, SupplierPaymentBillCreate,
    PaymentPostRequest, PaymentReconciliationRequest,
    OutstandingBillResponse, PayAgainstBillsRequest, SupplierPaymentSummaryResponse,
    PaymentModeEnum, PaymentTypeEnum
)

router = APIRouter()


def generate_payment_number(db: Session) -> str:
    """Generate unique payment number"""
    last_payment = db.query(SupplierPayment).order_by(desc(SupplierPayment.id)).first()
    if last_payment:
        last_num = int(last_payment.payment_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"SPAY-{new_num:06d}"


@router.get("/outstanding-bills/{supplier_id}", response_model=List[OutstandingBillResponse])
async def get_outstanding_bills(
    supplier_id: int,
    as_of_date: Optional[date] = Query(None, description="As of date for outstanding calculation"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get outstanding bills for a supplier"""
    
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    if not as_of_date:
        as_of_date = date.today()
    
    # Get purchases with outstanding amounts
    purchases = db.query(Purchase).filter(
        Purchase.supplier_id == supplier_id,
        Purchase.purchase_date <= as_of_date
    ).all()
    
    outstanding_bills = []
    for purchase in purchases:
        # Calculate total payments made for this purchase
        payments = db.query(SupplierPaymentBill).filter(
            SupplierPaymentBill.purchase_id == purchase.id
        ).all()
        
        total_paid = sum([p.paid_amount for p in payments]) if payments else Decimal('0.00')
        outstanding_amount = purchase.grand_total - total_paid
        
        if outstanding_amount > Decimal('0.01'):  # Only include bills with significant outstanding amount
            days_outstanding = (as_of_date - purchase.purchase_date).days
            
            outstanding_bills.append(OutstandingBillResponse(
                purchase_id=purchase.id,
                purchase_number=purchase.purchase_number,
                purchase_date=purchase.purchase_date,
                bill_amount=purchase.grand_total,
                payments_made=total_paid,
                outstanding_amount=outstanding_amount,
                days_outstanding=days_outstanding,
                supplier_invoice_number=purchase.supplier_invoice_number,
                is_overdue=days_outstanding > 30
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
    
    try:
        # Create payment record
        payment = SupplierPayment()
        payment.payment_number = generate_payment_number(db)
        payment.payment_date = payment_data.payment_date
        payment.supplier_id = payment_data.supplier_id
        payment.payment_type = PaymentType(payment_data.payment_type.value)
        payment.payment_mode = PaymentMode(payment_data.payment_mode.value)
        payment.gross_amount = payment_data.gross_amount
        payment.discount_amount = payment_data.discount_amount
        payment.tds_amount = payment_data.tds_amount
        payment.other_deductions = payment_data.other_deductions
        payment.bank_account_id = payment_data.bank_account_id
        payment.cheque_number = payment_data.cheque_number
        payment.cheque_date = payment_data.cheque_date
        payment.bank_name = payment_data.bank_name
        payment.bank_branch = payment_data.bank_branch
        payment.transaction_reference = payment_data.transaction_reference
        payment.tds_rate = payment_data.tds_rate
        if payment_data.tds_section:
            payment.tds_section = payment_data.tds_section.value
        payment.narration = payment_data.narration
        payment.remarks = payment_data.remarks
        payment.created_by = payment_data.created_by
        payment.status = PaymentStatus.DRAFT
        
        db.add(payment)
        db.flush()
        
        # Create payment bill entries
        for bill_data in payment_data.bills:
            payment_bill = SupplierPaymentBill()
            payment_bill.payment_id = payment.id
            payment_bill.purchase_id = bill_data.purchase_id
            payment_bill.bill_amount = bill_data.bill_amount
            payment_bill.outstanding_amount = bill_data.outstanding_amount
            payment_bill.paid_amount = bill_data.paid_amount
            payment_bill.discount_allowed = bill_data.discount_allowed
            payment_bill.adjustment_amount = bill_data.adjustment_amount
            payment_bill.remarks = bill_data.remarks
            
            db.add(payment_bill)
        
        # Create TDS entry if applicable
        if payment_data.tds_amount and payment_data.tds_amount > 0:
            tds_entry = TDSEntry()
            tds_entry.payment_id = payment.id
            tds_entry.supplier_id = payment.supplier_id
            if payment_data.tds_section:
                tds_entry.tds_section = payment_data.tds_section.value
            tds_entry.tds_rate = payment_data.tds_rate
            tds_entry.gross_amount = payment_data.gross_amount
            tds_entry.tds_amount = payment_data.tds_amount
            tds_entry.financial_year = f"{payment.payment_date.year}-{payment.payment_date.year + 1}"
            tds_entry.quarter = f"Q{((payment.payment_date.month - 1) // 3) + 1}"
            tds_entry.created_by = payment.created_by
            
            db.add(tds_entry)
        
        db.commit()
        
        return payment
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


@router.get("/", response_model=List[SupplierPaymentListResponse])
async def get_supplier_payments(
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get supplier payments with filters"""
    
    query = db.query(SupplierPayment)
    
    if supplier_id:
        query = query.filter(SupplierPayment.supplier_id == supplier_id)
    
    query = query.order_by(desc(SupplierPayment.payment_date), desc(SupplierPayment.id))
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


@router.post("/{payment_id}/post")
async def post_supplier_payment(
    payment_id: int,
    post_request: PaymentPostRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Post supplier payment to ledger"""
    
    payment = db.query(SupplierPayment).filter(SupplierPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if str(payment.status) != "Draft":
        raise HTTPException(status_code=400, detail="Only draft payments can be posted")
    
    try:
        # Update payment status - use SQL update for type safety
        db.execute(
            "UPDATE supplier_payments SET status = :status, posted_by = :posted_by, posted_at = :posted_at WHERE id = :id",
            {
                "status": "Posted",
                "posted_by": post_request.posted_by,
                "posted_at": datetime.now(),
                "id": payment_id
            }
        )
        
        db.commit()
        
        return {"message": "Payment posted successfully", "payment_id": payment_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to post payment: {str(e)}")


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
    total_discount = Decimal('0.00')
    bills_data = []
    
    for bill in request.selected_bills:
        purchase = db.query(Purchase).filter(
            Purchase.id == bill['purchase_id'],
            Purchase.supplier_id == request.supplier_id
        ).first()
        
        if not purchase:
            raise HTTPException(
                status_code=404,
                detail=f"Purchase {bill['purchase_id']} not found"
            )
        
        paying_amount = Decimal(str(bill['paying_amount']))
        discount_allowed = Decimal(str(bill.get('discount_allowed', '0.00')))
        
        gross_amount += paying_amount + discount_allowed
        total_discount += discount_allowed
        
        bills_data.append(SupplierPaymentBillCreate(
            purchase_id=bill['purchase_id'],
            bill_amount=purchase.grand_total,
            outstanding_amount=Decimal(str(bill['outstanding_amount'])),
            paid_amount=paying_amount,
            discount_allowed=discount_allowed,
            adjustment_amount=Decimal('0.00'),
            remarks=f"Payment against {purchase.purchase_number}"
        ))
    
    # Calculate TDS
    tds_amount = (gross_amount * request.tds_rate / 100).quantize(Decimal('0.01'))
    
    # Create payment data
    payment_create = SupplierPaymentCreate(
        payment_date=request.payment_date,
        supplier_id=request.supplier_id,
        payment_type=PaymentTypeEnum.AGAINST_BILL,
        payment_mode=PaymentModeEnum(request.payment_mode),
        gross_amount=gross_amount,
        discount_amount=total_discount,
        tds_amount=tds_amount,
        other_deductions=Decimal('0.00'),
        bank_account_id=request.bank_account_id,
        cheque_number=request.cheque_number,
        cheque_date=request.cheque_date,
        transaction_reference=request.transaction_reference,
        tds_rate=request.tds_rate,
        tds_section=request.tds_section,
        narration=f"Payment against {len(bills_data)} bills",
        bills=bills_data,
        created_by=request.created_by
    )
    
    # Use the existing create payment function
    return await create_supplier_payment(payment_create, background_tasks, db, current_user)


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
    
    # Calculate summary using Python instead of complex SQL
    total_amount = sum([p.net_amount for p in payments])
    total_tds = sum([p.tds_amount for p in payments])
    cash_payments = sum([p.net_amount for p in payments if str(p.payment_mode) == "Cash"])
    bank_payments = total_amount - cash_payments
    
    pending_reconciliation = len([p for p in payments if str(p.status) == "Posted" and not p.is_reconciled])
    draft_payments = len([p for p in payments if str(p.status) == "Draft"])
    posted_payments = len([p for p in payments if str(p.status) == "Posted"])
    
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


@router.get("/test")
async def test_payment_system():
    """Test endpoint to verify payment system is working"""
    return {
        "message": "Supplier Payment System is operational!",
        "features": [
            "Outstanding bills lookup",
            "Payment creation",
            "Multi-bill payments", 
            "TDS handling",
            "Payment posting",
            "Summary reports"
        ],
        "status": "active"
    }
