from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from database import get_db
from dependencies import get_current_user
from models.purchase_return import PurchaseReturn, PurchaseReturnItem, PurchaseReturnApproval
from models.purchase import Purchase, PurchaseItem
from models.suppliers import Supplier
from models.accounts import AccountsMaster
from models.raw_material_master import RawMaterialMaster
from models.size_master import SizeMaster
from models.unit_master import UnitMaster
from models.stock_ledger import StockLedger
from models.ledger_transaction import LedgerTransaction, TransactionBatch
from schemas.purchase_return import (
    PurchaseReturnCreate, PurchaseReturnUpdate, PurchaseReturnResponse, PurchaseReturnListResponse,
    PurchaseReturnItemResponse, PurchaseReturnPostRequest, PurchaseReturnApprovalRequest,
    QualityCheckRequest, PurchaseReturnSummaryResponse, SupplierReturnSummary,
    CreateReturnFromPurchaseRequest, ProcessRefundRequest, PurchaseItemReturnEligibility,
    PurchaseReturnStatusEnum, ReturnReasonEnum, RefundModeEnum
)
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper functions
def generate_return_number(db: Session) -> str:
    """Generate unique purchase return number"""
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    
    # Find last return number for today
    last_return = db.query(PurchaseReturn).filter(
        PurchaseReturn.return_number.like(f"PR{date_str}%")
    ).order_by(desc(PurchaseReturn.return_number)).first()
    
    if last_return:
        last_num = int(last_return.return_number[-4:])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"PR{date_str}{new_num:04d}"


async def create_reverse_stock_entries(db: Session, purchase_return: PurchaseReturn, user_id: str):
    """Create reverse stock ledger entries for returned items"""
    try:
        for item in purchase_return.items:
            if item.return_quantity > 0:
                # Create stock OUT entry (reducing inventory)
                stock_entry = StockLedger(
                    raw_material_id=item.material_id,
                    size_id=item.size_id,
                    supplier_id=purchase_return.supplier_id,
                    transaction_date=purchase_return.return_date,
                    transaction_type="Purchase Return",
                    reference_table="purchase_returns",
                    reference_id=purchase_return.id,
                    qty_in=Decimal("0.000"),
                    qty_out=item.return_quantity,
                    rate=item.rate,
                    created_by=user_id
                )
                db.add(stock_entry)
                db.flush()
                
                # Update return item with stock ledger reference
                item.stock_ledger_id = stock_entry.ledger_id
                item.is_stock_updated = True
        
        # Mark return as stock updated
        purchase_return.is_stock_updated = True
        db.commit()
        logger.info(f"Reverse stock entries created for return {purchase_return.return_number}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating reverse stock entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating stock ledger: {str(e)}"
        )


async def create_reverse_ledger_entries(db: Session, purchase_return: PurchaseReturn, user_id: str):
    """Create reverse double-entry ledger transactions for purchase return"""
    try:
        # Get supplier account
        supplier = db.query(Supplier).filter(Supplier.id == purchase_return.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Create transaction batch
        batch = TransactionBatch(
            batch_number=f"BATCH-{purchase_return.return_number}",
            batch_date=datetime.combine(purchase_return.return_date, datetime.min.time()),
            batch_description=f"Purchase return - {purchase_return.return_number}",
            total_debit_amount=purchase_return.total_amount,
            total_credit_amount=purchase_return.total_amount,
            created_by=user_id,
            is_posted=True
        )
        db.add(batch)
        db.flush()
        
        transactions = []
        transaction_date = datetime.combine(purchase_return.return_date, datetime.min.time())
        
        # 1. Credit: Purchase/Inventory Account (Asset decrease)
        purchase_credit_transaction = LedgerTransaction(
            transaction_number=f"PRV{purchase_return.return_number}001",
            transaction_date=transaction_date,
            account_code="PURCHASE001",  # Purchase account
            description=f"Purchase return to {supplier.supplier_name} - {purchase_return.return_number}",
            reference_type="PURCHASE_RETURN",
            reference_id=str(purchase_return.id),
            debit_amount=Decimal("0.00"),
            credit_amount=purchase_return.total_amount,
            voucher_type="PRV",  # Purchase Return Voucher
            voucher_number=purchase_return.return_number,
            party_type="SUPPLIER",
            party_id=str(purchase_return.supplier_id),
            party_name=supplier.supplier_name,
            batch_id=batch.id,
            created_by=user_id,
            is_posted=True
        )
        transactions.append(purchase_credit_transaction)
        
        # 2. Debit: Supplier Account or Cash/Bank Account (depending on refund mode)
        if purchase_return.refund_mode and purchase_return.refund_amount > 0:
            if purchase_return.refund_mode.value == "CASH":
                # Cash refund - Debit Cash Account
                refund_account = "CASH001"
            elif purchase_return.refund_mode.value == "BANK":
                # Bank refund - Debit Bank Account  
                refund_account = "BANK001"
            else:
                # Adjust payable - Debit Supplier Account
                refund_account = supplier.supplier_acc_code
            
            debit_transaction = LedgerTransaction(
                transaction_number=f"PRV{purchase_return.return_number}002",
                transaction_date=transaction_date,
                account_code=refund_account,
                description=f"Refund for return to {supplier.supplier_name} - {purchase_return.return_number}",
                reference_type="PURCHASE_RETURN",
                reference_id=str(purchase_return.id),
                debit_amount=purchase_return.refund_amount,
                credit_amount=Decimal("0.00"),
                voucher_type="PRV",
                voucher_number=purchase_return.return_number,
                party_type="SUPPLIER",
                party_id=str(purchase_return.supplier_id),
                party_name=supplier.supplier_name,
                batch_id=batch.id,
                created_by=user_id,
                is_posted=True
            )
            transactions.append(debit_transaction)
            
            # If partial refund, create adjustment entry for remaining amount
            pending_amount = purchase_return.total_amount - purchase_return.refund_amount
            if pending_amount > 0:
                adjustment_transaction = LedgerTransaction(
                    transaction_number=f"PRV{purchase_return.return_number}003",
                    transaction_date=transaction_date,
                    account_code=supplier.supplier_acc_code,
                    description=f"Payable adjustment for return - {purchase_return.return_number}",
                    reference_type="PURCHASE_RETURN",
                    reference_id=str(purchase_return.id),
                    debit_amount=pending_amount,
                    credit_amount=Decimal("0.00"),
                    voucher_type="PRV",
                    voucher_number=purchase_return.return_number,
                    party_type="SUPPLIER",
                    party_id=str(purchase_return.supplier_id),
                    party_name=supplier.supplier_name,
                    batch_id=batch.id,
                    created_by=user_id,
                    is_posted=True
                )
                transactions.append(adjustment_transaction)
        else:
            # No immediate refund - Debit Supplier Account (reduce payable)
            supplier_debit_transaction = LedgerTransaction(
                transaction_number=f"PRV{purchase_return.return_number}002",
                transaction_date=transaction_date,
                account_code=supplier.supplier_acc_code,
                description=f"Return credit from {supplier.supplier_name} - {purchase_return.return_number}",
                reference_type="PURCHASE_RETURN",
                reference_id=str(purchase_return.id),
                debit_amount=purchase_return.total_amount,
                credit_amount=Decimal("0.00"),
                voucher_type="PRV",
                voucher_number=purchase_return.return_number,
                party_type="SUPPLIER",
                party_id=str(purchase_return.supplier_id),
                party_name=supplier.supplier_name,
                batch_id=batch.id,
                created_by=user_id,
                is_posted=True
            )
            transactions.append(supplier_debit_transaction)
        
        # Add all transactions to database
        for transaction in transactions:
            db.add(transaction)
        
        # Update return with batch reference
        purchase_return.ledger_batch_id = batch.id
        purchase_return.is_ledger_posted = True
        
        db.commit()
        logger.info(f"Reverse ledger entries created for return {purchase_return.return_number}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating reverse ledger entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ledger entries: {str(e)}"
        )


# API Endpoints

@router.post("/", response_model=PurchaseReturnResponse)
async def create_purchase_return(
    return_data: PurchaseReturnCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new purchase return"""
    try:
        # Validate original purchase exists
        purchase = db.query(Purchase).filter(Purchase.id == return_data.purchase_id).first()
        if not purchase:
            raise HTTPException(status_code=404, detail="Original purchase not found")
        
        # Validate supplier matches
        if purchase.supplier_id != return_data.supplier_id:
            raise HTTPException(
                status_code=400, 
                detail="Supplier ID does not match original purchase"
            )
        
        # Generate return number
        return_number = generate_return_number(db)
        
        # Create purchase return
        purchase_return = PurchaseReturn(
            return_number=return_number,
            return_date=return_data.return_date,
            supplier_id=return_data.supplier_id,
            purchase_id=return_data.purchase_id,
            purchase_number=purchase.purchase_number,
            return_reason=return_data.return_reason,
            supplier_credit_note_number=return_data.supplier_credit_note_number,
            supplier_credit_note_date=return_data.supplier_credit_note_date,
            tax_amount=return_data.tax_amount,
            discount_amount=return_data.discount_amount,
            transport_charges=return_data.transport_charges,
            other_charges=return_data.other_charges,
            refund_amount=return_data.refund_amount,
            refund_mode=return_data.refund_mode,
            refund_reference=return_data.refund_reference,
            refund_date=return_data.refund_date,
            transport_details=return_data.transport_details,
            remarks=return_data.remarks,
            approval_required=return_data.approval_required,
            created_by=return_data.created_by
        )
        
        db.add(purchase_return)
        db.flush()
        
        # Create return items
        total_amount = Decimal("0.00")
        for item_data in return_data.items:
            # Validate original purchase item exists
            purchase_item = db.query(PurchaseItem).filter(
                PurchaseItem.id == item_data.purchase_item_id
            ).first()
            if not purchase_item:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Purchase item {item_data.purchase_item_id} not found"
                )
            
            # Validate material matches
            if purchase_item.material_id != item_data.material_id:
                raise HTTPException(
                    status_code=400, 
                    detail="Material ID does not match original purchase item"
                )
            
            # Check return quantity doesn't exceed purchased quantity
            if item_data.return_quantity > purchase_item.accepted_qty:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Return quantity {item_data.return_quantity} exceeds purchased quantity {purchase_item.accepted_qty}"
                )
            
            item = PurchaseReturnItem(
                return_id=purchase_return.id,
                purchase_item_id=item_data.purchase_item_id,
                material_id=item_data.material_id,
                size_id=item_data.size_id,
                supplier_material_name=item_data.supplier_material_name,
                description=item_data.description,
                return_quantity=item_data.return_quantity,
                unit_id=item_data.unit_id,
                rate=item_data.rate,
                total_amount=item_data.return_quantity * item_data.rate,
                return_reason=item_data.return_reason,
                condition_on_return=item_data.condition_on_return,
                batch_number=item_data.batch_number,
                expiry_date=item_data.expiry_date,
                quality_notes=item_data.quality_notes
            )
            
            db.add(item)
            total_amount += item.total_amount
        
        # Update return totals
        purchase_return.sub_total = total_amount
        purchase_return.total_amount = total_amount + purchase_return.tax_amount + purchase_return.transport_charges + purchase_return.other_charges - purchase_return.discount_amount
        
        db.commit()
        
        # Refresh to get the complete object with items
        db.refresh(purchase_return)
        
        logger.info(f"Purchase return {return_number} created successfully")
        return purchase_return
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase return: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating purchase return: {str(e)}"
        )


@router.get("/", response_model=List[PurchaseReturnListResponse])
async def get_purchase_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    supplier_id: Optional[int] = Query(None),
    purchase_id: Optional[int] = Query(None),
    status: Optional[PurchaseReturnStatusEnum] = Query(None),
    return_reason: Optional[ReturnReasonEnum] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    is_posted: Optional[bool] = Query(None),
    pending_approval: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get purchase returns with filtering options"""
    query = db.query(PurchaseReturn)
    
    if supplier_id:
        query = query.filter(PurchaseReturn.supplier_id == supplier_id)
    if purchase_id:
        query = query.filter(PurchaseReturn.purchase_id == purchase_id)
    if status:
        query = query.filter(PurchaseReturn.status == status)
    if return_reason:
        query = query.filter(PurchaseReturn.return_reason == return_reason)
    if date_from:
        query = query.filter(PurchaseReturn.return_date >= date_from)
    if date_to:
        query = query.filter(PurchaseReturn.return_date <= date_to)
    if is_posted is not None:
        query = query.filter(PurchaseReturn.is_ledger_posted == is_posted)
    if pending_approval is not None:
        if pending_approval:
            query = query.filter(and_(
                PurchaseReturn.approval_required == True,
                PurchaseReturn.approved_by.is_(None)
            ))
        else:
            query = query.filter(or_(
                PurchaseReturn.approval_required == False,
                PurchaseReturn.approved_by.isnot(None)
            ))
    
    returns = query.order_by(desc(PurchaseReturn.created_at)).offset(skip).limit(limit).all()
    return returns


@router.get("/{return_id}", response_model=PurchaseReturnResponse)
async def get_purchase_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific purchase return by ID"""
    purchase_return = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
    if not purchase_return:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    return purchase_return


@router.put("/{return_id}", response_model=PurchaseReturnResponse)
async def update_purchase_return(
    return_id: int,
    return_data: PurchaseReturnUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a purchase return (only if not posted)"""
    purchase_return = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
    if not purchase_return:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    
    if purchase_return.status == PurchaseReturnStatusEnum.POSTED:
        raise HTTPException(
            status_code=400, 
            detail="Cannot update posted purchase return"
        )
    
    # Update fields
    for field, value in return_data.dict(exclude_unset=True).items():
        if hasattr(purchase_return, field):
            setattr(purchase_return, field, value)
    
    # Recalculate total if charges are updated
    if any(field in return_data.dict(exclude_unset=True) for field in 
           ['tax_amount', 'discount_amount', 'transport_charges', 'other_charges']):
        purchase_return.total_amount = (
            purchase_return.sub_total + purchase_return.tax_amount + 
            purchase_return.transport_charges + purchase_return.other_charges - 
            purchase_return.discount_amount
        )
    
    db.commit()
    db.refresh(purchase_return)
    return purchase_return


@router.delete("/{return_id}")
async def delete_purchase_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a purchase return (only if not posted)"""
    purchase_return = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
    if not purchase_return:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    
    if purchase_return.status == PurchaseReturnStatusEnum.POSTED:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete posted purchase return"
        )
    
    db.delete(purchase_return)
    db.commit()
    return {"message": "Purchase return deleted successfully"}


@router.post("/{return_id}/post")
async def post_purchase_return(
    return_id: int,
    post_data: PurchaseReturnPostRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Post a purchase return to ledger and stock"""
    purchase_return = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
    if not purchase_return:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    
    if purchase_return.status == PurchaseReturnStatusEnum.POSTED:
        raise HTTPException(status_code=400, detail="Purchase return already posted")
    
    # Check approval if required
    if purchase_return.approval_required and not purchase_return.approved_by:
        raise HTTPException(
            status_code=400, 
            detail="Purchase return requires approval before posting"
        )
    
    # Update reverse stock ledger
    if post_data.post_to_stock and not purchase_return.is_stock_updated:
        await create_reverse_stock_entries(db, purchase_return, post_data.posted_by)
    
    # Create reverse ledger entries
    if post_data.post_to_ledger and not purchase_return.is_ledger_posted:
        await create_reverse_ledger_entries(db, purchase_return, post_data.posted_by)
    
    # Update return status
    purchase_return.status = PurchaseReturnStatusEnum.POSTED
    purchase_return.posted_by = post_data.posted_by
    purchase_return.posted_at = datetime.now()
    
    db.commit()
    
    return {"message": "Purchase return posted successfully"}


@router.post("/{return_id}/approve")
async def approve_purchase_return(
    return_id: int,
    approval_data: PurchaseReturnApprovalRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve or reject a purchase return"""
    purchase_return = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
    if not purchase_return:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    
    if not purchase_return.approval_required:
        raise HTTPException(status_code=400, detail="This return does not require approval")
    
    if purchase_return.approved_by:
        raise HTTPException(status_code=400, detail="Return already approved/rejected")
    
    # Create approval record
    approval = PurchaseReturnApproval(
        return_id=return_id,
        approver_id=approval_data.approver_id,
        approver_name=approval_data.approver_name,
        approval_level=1,
        status="Approved" if approval_data.approved else "Rejected",
        approval_date=datetime.now(),
        comments=approval_data.comments
    )
    
    db.add(approval)
    
    # Update return approval status
    if approval_data.approved:
        purchase_return.approved_by = approval_data.approver_id
        purchase_return.approved_at = datetime.now()
    else:
        purchase_return.status = PurchaseReturnStatusEnum.CANCELLED
    
    db.commit()
    
    status_text = "approved" if approval_data.approved else "rejected"
    return {"message": f"Purchase return {status_text} successfully"}


@router.get("/reports/summary", response_model=PurchaseReturnSummaryResponse)
async def get_return_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get purchase return summary report"""
    query = db.query(PurchaseReturn)
    
    if date_from:
        query = query.filter(PurchaseReturn.return_date >= date_from)
    if date_to:
        query = query.filter(PurchaseReturn.return_date <= date_to)
    
    returns = query.all()
    
    total_returns = len(returns)
    total_amount = sum(r.total_amount for r in returns)
    total_refunded = sum(r.refund_amount for r in returns)
    pending_refund = total_amount - total_refunded
    draft_count = len([r for r in returns if r.status == PurchaseReturnStatusEnum.DRAFT])
    posted_count = len([r for r in returns if r.status == PurchaseReturnStatusEnum.POSTED])
    pending_approval_count = len([r for r in returns if r.approval_required and not r.approved_by])
    quality_pending_count = len([r for r in returns if not r.quality_check_done])
    
    return PurchaseReturnSummaryResponse(
        total_returns=total_returns,
        total_amount=total_amount,
        total_refunded=total_refunded,
        pending_refund=pending_refund,
        draft_count=draft_count,
        posted_count=posted_count,
        pending_approval_count=pending_approval_count,
        quality_pending_count=quality_pending_count
    )
