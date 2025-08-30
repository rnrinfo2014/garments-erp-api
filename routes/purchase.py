from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from database import get_db
from dependencies import get_current_user
from models.purchase import Purchase, PurchaseItem
from models.suppliers import Supplier
from models.accounts import AccountsMaster
from models.raw_material_master import RawMaterialMaster
from models.size_master import SizeMaster
from models.unit_master import UnitMaster
from models.purchase_order import PurchaseOrder, PurchaseOrderItem
from models.stock_ledger import StockLedger
from models.ledger_transaction import LedgerTransaction, TransactionBatch
from schemas.purchase import (
    PurchaseCreate, PurchaseUpdate, PurchaseResponse, PurchaseListResponse,
    PurchaseItemResponse, PurchasePostRequest, PurchaseSummaryResponse,
    SupplierPurchaseSummary, PurchaseFromPORequest, BulkPurchaseCreate,
    PurchaseStatusEnum, PurchaseTypeEnum
)
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper functions
def generate_purchase_number(db: Session) -> str:
    """Generate unique purchase number"""
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    
    # Find last purchase number for today
    last_purchase = db.query(Purchase).filter(
        Purchase.purchase_number.like(f"PUR{date_str}%")
    ).order_by(desc(Purchase.purchase_number)).first()
    
    if last_purchase:
        last_num = int(last_purchase.purchase_number[-4:])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"PUR{date_str}{new_num:04d}"


async def create_stock_ledger_entries(db: Session, purchase: Purchase, user_id: str):
    """Create stock ledger entries for purchase items"""
    try:
        for item in purchase.items:
            if item.accepted_qty > 0:
                # Create stock IN entry
                stock_entry = StockLedger(
                    raw_material_id=item.material_id,
                    size_id=item.size_id,
                    supplier_id=purchase.supplier_id,
                    transaction_date=purchase.purchase_date,
                    transaction_type="Purchase",
                    reference_table="purchases",
                    reference_id=purchase.id,
                    qty_in=item.accepted_qty,
                    qty_out=Decimal("0.000"),
                    rate=item.rate,
                    created_by=user_id
                )
                db.add(stock_entry)
                db.flush()
                
                # Update purchase item with stock ledger reference
                item.stock_ledger_id = stock_entry.ledger_id
                item.is_stock_updated = True
        
        # Mark purchase as stock updated
        purchase.is_stock_updated = True
        db.commit()
        logger.info(f"Stock ledger entries created for purchase {purchase.purchase_number}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating stock ledger entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating stock ledger: {str(e)}"
        )


async def create_ledger_entries(db: Session, purchase: Purchase, user_id: str):
    """Create double-entry ledger transactions for purchase"""
    try:
        # Get supplier account
        supplier = db.query(Supplier).filter(Supplier.id == purchase.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Create transaction batch
        batch = TransactionBatch(
            batch_number=f"BATCH-{purchase.purchase_number}",
            batch_date=datetime.combine(purchase.purchase_date, datetime.min.time()),
            batch_description=f"Purchase entry - {purchase.purchase_number}",
            total_debit_amount=purchase.total_amount,
            total_credit_amount=purchase.total_amount,
            created_by=user_id,
            is_posted=True
        )
        db.add(batch)
        db.flush()
        
        transactions = []
        transaction_date = datetime.combine(purchase.purchase_date, datetime.min.time())
        
        # 1. Debit: Purchase/Inventory Account (Asset increase)
        purchase_transaction = LedgerTransaction(
            transaction_number=f"PV{purchase.purchase_number}001",
            transaction_date=transaction_date,
            account_code="PURCHASE001",  # Purchase account
            description=f"Purchase from {supplier.supplier_name} - {purchase.purchase_number}",
            reference_type="PURCHASE",
            reference_id=str(purchase.id),
            debit_amount=purchase.total_amount,
            credit_amount=Decimal("0.00"),
            voucher_type="PurchaseV",
            voucher_number=purchase.purchase_number,
            party_type="SUPPLIER",
            party_id=str(purchase.supplier_id),
            party_name=supplier.supplier_name,
            batch_id=batch.id,
            created_by=user_id,
            is_posted=True
        )
        transactions.append(purchase_transaction)
        
        # 2. Credit: Supplier Account or Cash/Bank Account
        if purchase.purchase_type.value == "CASH":
            # Cash purchase - Credit Cash Account
            payment_account = "CASH001" if purchase.payment_mode == "CASH" else "BANK001"
            credit_transaction = LedgerTransaction(
                transaction_number=f"PV{purchase.purchase_number}002",
                transaction_date=transaction_date,
                account_code=payment_account,
                description=f"Cash payment for purchase - {purchase.purchase_number}",
                reference_type="PURCHASE",
                reference_id=str(purchase.id),
                debit_amount=Decimal("0.00"),
                credit_amount=purchase.total_amount,
                voucher_type="PurchaseV",
                voucher_number=purchase.purchase_number,
                party_type="SUPPLIER",
                party_id=str(purchase.supplier_id),
                party_name=supplier.supplier_name,
                batch_id=batch.id,
                created_by=user_id,
                is_posted=True
            )
        else:
            # Credit purchase - Credit Supplier Account (Accounts Payable)
            credit_transaction = LedgerTransaction(
                transaction_number=f"PV{purchase.purchase_number}002",
                transaction_date=transaction_date,
                account_code=supplier.supplier_acc_code,
                description=f"Credit purchase from {supplier.supplier_name} - {purchase.purchase_number}",
                reference_type="PURCHASE",
                reference_id=str(purchase.id),
                debit_amount=Decimal("0.00"),
                credit_amount=purchase.total_amount,
                voucher_type="PurchaseV",
                voucher_number=purchase.purchase_number,
                party_type="SUPPLIER",
                party_id=str(purchase.supplier_id),
                party_name=supplier.supplier_name,
                batch_id=batch.id,
                created_by=user_id,
                is_posted=True
            )
        
        transactions.append(credit_transaction)
        
        # Add partial payment entry if applicable
        if purchase.amount_paid > 0 and purchase.purchase_type.value == "CREDIT":
            # Debit Supplier Account (reduce liability)
            payment_debit = LedgerTransaction(
                transaction_number=f"PV{purchase.purchase_number}003",
                transaction_date=transaction_date,
                account_code=supplier.supplier_acc_code,
                description=f"Partial payment to {supplier.supplier_name} - {purchase.purchase_number}",
                reference_type="PURCHASE",
                reference_id=str(purchase.id),
                debit_amount=purchase.amount_paid,
                credit_amount=Decimal("0.00"),
                voucher_type="PV",
                voucher_number=purchase.purchase_number,
                party_type="SUPPLIER",
                party_id=str(purchase.supplier_id),
                party_name=supplier.supplier_name,
                batch_id=batch.id,
                created_by=user_id,
                is_posted=True
            )
            transactions.append(payment_debit)
            
            # Credit Cash/Bank Account
            payment_account = "CASH001" if purchase.payment_mode == "CASH" else "BANK001"
            payment_credit = LedgerTransaction(
                transaction_number=f"PV{purchase.purchase_number}004",
                transaction_date=transaction_date,
                account_code=payment_account,
                description=f"Payment made to {supplier.supplier_name} - {purchase.purchase_number}",
                reference_type="PURCHASE",
                reference_id=str(purchase.id),
                debit_amount=Decimal("0.00"),
                credit_amount=purchase.amount_paid,
                voucher_type="PV",
                voucher_number=purchase.purchase_number,
                party_type="SUPPLIER",
                party_id=str(purchase.supplier_id),
                party_name=supplier.supplier_name,
                batch_id=batch.id,
                created_by=user_id,
                is_posted=True
            )
            transactions.append(payment_credit)
        
        # Add all transactions to database
        for transaction in transactions:
            db.add(transaction)
        
        # Update purchase with batch reference
        purchase.ledger_batch_id = batch.id
        purchase.is_ledger_posted = True
        
        db.commit()
        logger.info(f"Ledger entries created for purchase {purchase.purchase_number}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ledger entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ledger entries: {str(e)}"
        )


# API Endpoints

@router.post("/", response_model=PurchaseResponse)
async def create_purchase(
    purchase_data: PurchaseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new purchase entry"""
    try:
        # Validate supplier exists
        supplier = db.query(Supplier).filter(Supplier.id == purchase_data.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Generate purchase number
        purchase_number = generate_purchase_number(db)
        
        # Create purchase
        purchase = Purchase(
            purchase_number=purchase_number,
            purchase_date=purchase_data.purchase_date,
            supplier_id=purchase_data.supplier_id,
            supplier_invoice_number=purchase_data.supplier_invoice_number,
            supplier_invoice_date=purchase_data.supplier_invoice_date,
            po_id=purchase_data.po_id,
            po_number=purchase_data.po_number,
            purchase_type=purchase_data.purchase_type,
            tax_amount=purchase_data.tax_amount,
            discount_amount=purchase_data.discount_amount,
            transport_charges=purchase_data.transport_charges,
            other_charges=purchase_data.other_charges,
            amount_paid=purchase_data.amount_paid,
            payment_mode=purchase_data.payment_mode,
            payment_reference=purchase_data.payment_reference,
            transport_details=purchase_data.transport_details,
            remarks=purchase_data.remarks,
            created_by=purchase_data.created_by
        )
        
        db.add(purchase)
        db.flush()
        
        # Create purchase items
        total_amount = Decimal("0.00")
        for item_data in purchase_data.items:
            # Validate material exists
            material = db.query(RawMaterialMaster).filter(
                RawMaterialMaster.id == item_data.material_id
            ).first()
            if not material:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Material {item_data.material_id} not found"
                )
            
            # Calculate accepted quantity
            accepted_qty = item_data.quantity - item_data.rejected_qty
            
            item = PurchaseItem(
                purchase_id=purchase.id,
                material_id=item_data.material_id,
                size_id=item_data.size_id,
                supplier_material_name=item_data.supplier_material_name,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_id=item_data.unit_id,
                rate=item_data.rate,
                total_amount=item_data.quantity * item_data.rate,
                po_item_id=item_data.po_item_id,
                quality_status=item_data.quality_status.value,
                rejected_qty=item_data.rejected_qty,
                accepted_qty=accepted_qty,
                batch_number=item_data.batch_number,
                expiry_date=item_data.expiry_date
            )
            
            db.add(item)
            total_amount += item.total_amount
        
        # Update purchase totals
        purchase.sub_total = total_amount
        purchase.total_amount = total_amount + purchase.tax_amount + purchase.transport_charges + purchase.other_charges - purchase.discount_amount
        
        db.commit()
        
        # Refresh to get the complete object with items
        db.refresh(purchase)
        
        logger.info(f"Purchase {purchase_number} created successfully")
        return purchase
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating purchase: {str(e)}"
        )


@router.get("/", response_model=List[PurchaseListResponse])
async def get_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    supplier_id: Optional[int] = Query(None),
    status: Optional[PurchaseStatusEnum] = Query(None),
    purchase_type: Optional[PurchaseTypeEnum] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    is_posted: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get purchases with filtering options"""
    query = db.query(Purchase)
    
    if supplier_id:
        query = query.filter(Purchase.supplier_id == supplier_id)
    if status:
        query = query.filter(Purchase.status == status)
    if purchase_type:
        query = query.filter(Purchase.purchase_type == purchase_type)
    if date_from:
        query = query.filter(Purchase.purchase_date >= date_from)
    if date_to:
        query = query.filter(Purchase.purchase_date <= date_to)
    if is_posted is not None:
        query = query.filter(Purchase.is_ledger_posted == is_posted)
    
    purchases = query.order_by(desc(Purchase.created_at)).offset(skip).limit(limit).all()
    return purchases


@router.get("/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific purchase by ID"""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.put("/{purchase_id}", response_model=PurchaseResponse)
async def update_purchase(
    purchase_id: int,
    purchase_data: PurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a purchase (only if not posted)"""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    if purchase.status == PurchaseStatusEnum.POSTED:
        raise HTTPException(
            status_code=400, 
            detail="Cannot update posted purchase"
        )
    
    # Update fields
    for field, value in purchase_data.dict(exclude_unset=True).items():
        if hasattr(purchase, field):
            setattr(purchase, field, value)
    
    # Recalculate total if charges are updated
    if any(field in purchase_data.dict(exclude_unset=True) for field in 
           ['tax_amount', 'discount_amount', 'transport_charges', 'other_charges']):
        purchase.total_amount = (
            purchase.sub_total + purchase.tax_amount + 
            purchase.transport_charges + purchase.other_charges - 
            purchase.discount_amount
        )
    
    db.commit()
    db.refresh(purchase)
    return purchase


@router.delete("/{purchase_id}")
async def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a purchase (only if not posted)"""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    if purchase.status == PurchaseStatusEnum.POSTED:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete posted purchase"
        )
    
    db.delete(purchase)
    db.commit()
    return {"message": "Purchase deleted successfully"}


@router.post("/{purchase_id}/post")
async def post_purchase(
    purchase_id: int,
    post_data: PurchasePostRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Post a purchase to ledger and stock"""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    if purchase.status == PurchaseStatusEnum.POSTED:
        raise HTTPException(status_code=400, detail="Purchase already posted")
    
    # Update stock ledger
    if post_data.post_to_stock and not purchase.is_stock_updated:
        await create_stock_ledger_entries(db, purchase, post_data.posted_by)
    
    # Create ledger entries
    if post_data.post_to_ledger and not purchase.is_ledger_posted:
        await create_ledger_entries(db, purchase, post_data.posted_by)
    
    # Update purchase status
    purchase.status = PurchaseStatusEnum.POSTED
    purchase.posted_by = post_data.posted_by
    purchase.posted_at = datetime.now()
    
    db.commit()
    
    return {"message": "Purchase posted successfully"}


@router.post("/from-po", response_model=PurchaseResponse)
async def create_purchase_from_po(
    po_data: PurchaseFromPORequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create purchase entry from purchase order"""
    # Get purchase order
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_data.po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # Generate purchase number
    purchase_number = generate_purchase_number(db)
    
    # Create purchase
    purchase = Purchase(
        purchase_number=purchase_number,
        purchase_date=po_data.purchase_date,
        supplier_id=po.supplier_id,
        supplier_invoice_number=po_data.supplier_invoice_number,
        supplier_invoice_date=po_data.supplier_invoice_date,
        po_id=po.id,
        po_number=po.po_number,
        purchase_type=PurchaseTypeEnum.CREDIT,
        created_by=po_data.created_by
    )
    
    db.add(purchase)
    db.flush()
    
    # Create items from received items
    total_amount = Decimal("0.00")
    for received_item in po_data.received_items:
        po_item_id = received_item.get("po_item_id")
        po_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.id == po_item_id
        ).first()
        
        if not po_item:
            continue
            
        received_qty = Decimal(str(received_item.get("received_quantity", 0)))
        rate = Decimal(str(received_item.get("rate", po_item.rate)))
        
        item = PurchaseItem(
            purchase_id=purchase.id,
            material_id=po_item.material_id,
            size_id="DEFAULT",  # Get from material if needed
            quantity=received_qty,
            unit_id=po_item.unit_id,
            rate=rate,
            total_amount=received_qty * rate,
            po_item_id=po_item.id,
            quality_status=received_item.get("quality_status", "Accepted"),
            accepted_qty=received_qty,
            batch_number=received_item.get("batch_number")
        )
        
        db.add(item)
        total_amount += item.total_amount
        
        # Update PO item received quantity
        po_item.received_qty += received_qty
        po_item.pending_qty = po_item.quantity - po_item.received_qty
        
        if po_item.pending_qty <= 0:
            po_item.item_status = "Received"
        elif po_item.received_qty > 0:
            po_item.item_status = "Partial"
    
    # Update purchase totals
    purchase.sub_total = total_amount
    purchase.total_amount = total_amount
    
    db.commit()
    db.refresh(purchase)
    
    return purchase


@router.get("/reports/summary", response_model=PurchaseSummaryResponse)
async def get_purchase_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get purchase summary report"""
    query = db.query(Purchase)
    
    if date_from:
        query = query.filter(Purchase.purchase_date >= date_from)
    if date_to:
        query = query.filter(Purchase.purchase_date <= date_to)
    
    purchases = query.all()
    
    total_purchases = len(purchases)
    total_amount = sum(p.total_amount for p in purchases)
    total_paid = sum(p.amount_paid for p in purchases)
    total_pending = total_amount - total_paid
    draft_count = len([p for p in purchases if p.status == PurchaseStatusEnum.DRAFT])
    posted_count = len([p for p in purchases if p.status == PurchaseStatusEnum.POSTED])
    
    return PurchaseSummaryResponse(
        total_purchases=total_purchases,
        total_amount=total_amount,
        total_paid=total_paid,
        total_pending=total_pending,
        draft_count=draft_count,
        posted_count=posted_count
    )
