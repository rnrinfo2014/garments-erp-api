from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional
from datetime import date
from decimal import Decimal

from dependencies import get_db, get_current_user
from models.stock_ledger import StockLedger
from schemas.stock_ledger import StockLedgerCreate
from schemas.stock_ledger import StockLedgerUpdate
from schemas.stock_ledger import StockLedgerResponse
from schemas.stock_ledger import StockLedgerSummary
from schemas.stock_ledger import StockMovementFilter
from models.user import User

router = APIRouter()

# Helper function to build response with related data
def build_stock_ledger_response(db_entry, db: Session):
    """Helper function to build stock ledger response with related data"""
    from models.raw_material_master import RawMaterialMaster
    from models.size_master import SizeMaster
    from models.suppliers import Supplier
    
    # Load raw material
    raw_material = db.query(RawMaterialMaster).filter(RawMaterialMaster.id == db_entry.raw_material_id).first()
    raw_material_data = {
        "id": raw_material.id,
        "material_name": raw_material.material_name,
        "description": raw_material.description
    } if raw_material else None
    
    # Load size
    size = db.query(SizeMaster).filter(SizeMaster.id == db_entry.size_id).first()
    size_data = {
        "id": size.id,
        "size_name": size.size_name,
        "description": size.description
    } if size else None
    
    # Load supplier (if provided)
    supplier_data = None
    if db_entry.supplier_id is not None:
        supplier = db.query(Supplier).filter(Supplier.id == db_entry.supplier_id).first()
        supplier_data = {
            "id": supplier.id,
            "supplier_name": supplier.supplier_name,
            "supplier_type": supplier.supplier_type
        } if supplier else None
    
    # Create response dict
    return {
        "ledger_id": db_entry.ledger_id,
        "raw_material_id": db_entry.raw_material_id,
        "size_id": db_entry.size_id,
        "supplier_id": db_entry.supplier_id,
        "transaction_date": db_entry.transaction_date,
        "transaction_type": db_entry.transaction_type,
        "reference_table": db_entry.reference_table,
        "reference_id": db_entry.reference_id,
        "qty_in": db_entry.qty_in,
        "qty_out": db_entry.qty_out,
        "rate": db_entry.rate,
        "created_by": db_entry.created_by,
        "created_at": db_entry.created_at,
        "amount": db_entry.amount,
        "net_quantity": db_entry.net_quantity,
        "raw_material": raw_material_data,
        "size": size_data,
        "supplier": supplier_data
    }

# Stock Ledger CRUD Operations

@router.post("/stock-ledger", response_model=StockLedgerResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_ledger_entry(
    stock_entry: StockLedgerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new stock ledger entry using JWT Token Authentication."""
    
    # Validate that either qty_in or qty_out is provided (not both zero)
    if stock_entry.qty_in == Decimal("0.00") and stock_entry.qty_out == Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either qty_in or qty_out must be greater than zero"
        )
    
    # Create the stock ledger entry
    db_entry = StockLedger(
        raw_material_id=stock_entry.raw_material_id,
        size_id=stock_entry.size_id,
        supplier_id=stock_entry.supplier_id,
        transaction_date=stock_entry.transaction_date,
        transaction_type=stock_entry.transaction_type,
        reference_table=stock_entry.reference_table,
        reference_id=stock_entry.reference_id,
        qty_in=stock_entry.qty_in,
        qty_out=stock_entry.qty_out,
        rate=stock_entry.rate,
        created_by=current_user.username
    )
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    return build_stock_ledger_response(db_entry, db)


@router.get("/stock-ledger", response_model=List[StockLedgerResponse])
async def get_stock_ledger_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    raw_material_id: Optional[str] = Query(None),
    size_id: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get stock ledger entries with filtering options using JWT Token Authentication."""
    
    query = db.query(StockLedger).options(
        joinedload(StockLedger.raw_material),
        joinedload(StockLedger.size)
        # joinedload(StockLedger.supplier)  # Temporarily commented due to circular import
    )
    
    # Apply filters
    if raw_material_id:
        query = query.filter(StockLedger.raw_material_id == raw_material_id)
    if size_id:
        query = query.filter(StockLedger.size_id == size_id)
    if supplier_id:
        query = query.filter(StockLedger.supplier_id == supplier_id)
    if transaction_type:
        query = query.filter(StockLedger.transaction_type == transaction_type)
    if from_date:
        query = query.filter(StockLedger.transaction_date >= from_date)
    if to_date:
        query = query.filter(StockLedger.transaction_date <= to_date)
    
    # Order by transaction_date descending and then by ledger_id descending
    query = query.order_by(desc(StockLedger.transaction_date), desc(StockLedger.ledger_id))
    
    entries = query.offset(skip).limit(limit).all()
    
    # Build response list using helper function
    return [build_stock_ledger_response(entry, db) for entry in entries]


@router.get("/stock-ledger/{ledger_id}", response_model=StockLedgerResponse)
async def get_stock_ledger_entry(
    ledger_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific stock ledger entry by ID using JWT Token Authentication."""
    
    entry = db.query(StockLedger).options(
        joinedload(StockLedger.raw_material),
        joinedload(StockLedger.size)
        # joinedload(StockLedger.supplier)  # Temporarily commented due to circular import
    ).filter(StockLedger.ledger_id == ledger_id).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock ledger entry with ID {ledger_id} not found"
        )
    
    return build_stock_ledger_response(entry, db)


@router.put("/stock-ledger/{ledger_id}", response_model=StockLedgerResponse)
async def update_stock_ledger_entry(
    ledger_id: int,
    stock_update: StockLedgerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a stock ledger entry (Admin only) using JWT Token Authentication."""
    
    entry = db.query(StockLedger).filter(StockLedger.ledger_id == ledger_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock ledger entry with ID {ledger_id} not found"
        )
    
    # Update only provided fields
    update_data = stock_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    # Validate quantities - convert to Decimal for comparison
    qty_in_value = Decimal(str(entry.qty_in)) if entry.qty_in is not None else Decimal("0.00")
    qty_out_value = Decimal(str(entry.qty_out)) if entry.qty_out is not None else Decimal("0.00")
    
    if (qty_in_value == Decimal("0.00") and qty_out_value == Decimal("0.00")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either qty_in or qty_out must be greater than zero"
        )
    
    db.commit()
    db.refresh(entry)
    
    return build_stock_ledger_response(entry, db)


@router.delete("/stock-ledger/{ledger_id}")
async def delete_stock_ledger_entry(
    ledger_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a stock ledger entry (Admin only) using JWT Token Authentication."""
    
    entry = db.query(StockLedger).filter(StockLedger.ledger_id == ledger_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock ledger entry with ID {ledger_id} not found"
        )
    
    db.delete(entry)
    db.commit()
    return {"message": f"Stock ledger entry {ledger_id} deleted successfully"}


# Stock Summary and Reporting

@router.get("/stock-summary", response_model=List[StockLedgerSummary])
async def get_stock_summary(
    raw_material_id: Optional[str] = Query(None),
    size_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current stock summary by raw material and size using JWT Token Authentication."""
    
    # Build the query to get stock summary
    query = db.query(
        StockLedger.raw_material_id,
        StockLedger.size_id,
        func.sum(StockLedger.qty_in).label("total_qty_in"),
        func.sum(StockLedger.qty_out).label("total_qty_out"),
        func.max(StockLedger.transaction_date).label("last_transaction_date"),
        func.avg(StockLedger.rate).label("avg_rate")
    ).group_by(StockLedger.raw_material_id, StockLedger.size_id)
    
    # Apply filters
    if raw_material_id:
        query = query.filter(StockLedger.raw_material_id == raw_material_id)
    if size_id:
        query = query.filter(StockLedger.size_id == size_id)
    
    results = query.all()
    
    # Convert to response format
    summaries = []
    for result in results:
        current_stock = (result.total_qty_in or Decimal("0.00")) - (result.total_qty_out or Decimal("0.00"))
        
        summary = StockLedgerSummary(
            raw_material_id=result.raw_material_id,
            size_id=result.size_id,
            total_qty_in=result.total_qty_in or Decimal("0.00"),
            total_qty_out=result.total_qty_out or Decimal("0.00"),
            current_stock=current_stock,
            last_transaction_date=result.last_transaction_date,
            avg_rate=result.avg_rate
        )
        summaries.append(summary)
    
    return summaries


@router.get("/stock-movement", response_model=List[StockLedgerResponse])
async def get_stock_movements(
    raw_material_id: str = Query(..., description="Raw Material ID is required"),
    size_id: str = Query(..., description="Size ID is required"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed stock movements for a specific raw material and size using JWT Token Authentication."""
    
    query = db.query(StockLedger).options(
        joinedload(StockLedger.raw_material),
        joinedload(StockLedger.size)
        # joinedload(StockLedger.supplier)  # Temporarily commented due to circular import
    ).filter(
        and_(
            StockLedger.raw_material_id == raw_material_id,
            StockLedger.size_id == size_id
        )
    )
    
    # Apply date filters
    if from_date:
        query = query.filter(StockLedger.transaction_date >= from_date)
    if to_date:
        query = query.filter(StockLedger.transaction_date <= to_date)
    
    # Order by transaction_date and then by ledger_id
    query = query.order_by(StockLedger.transaction_date, StockLedger.ledger_id)
    
    movements = query.all()
    return movements


@router.get("/current-stock/{raw_material_id}/{size_id}")
async def get_current_stock(
    raw_material_id: str,
    size_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current stock balance for a specific raw material and size using JWT Token Authentication."""
    
    result = db.query(
        func.sum(StockLedger.qty_in).label("total_in"),
        func.sum(StockLedger.qty_out).label("total_out")
    ).filter(
        and_(
            StockLedger.raw_material_id == raw_material_id,
            StockLedger.size_id == size_id
        )
    ).first()
    
    if result and (result.total_in or result.total_out):
        total_in = result.total_in or Decimal("0.00")
        total_out = result.total_out or Decimal("0.00")
        current_stock = total_in - total_out
        
        return {
            "raw_material_id": raw_material_id,
            "size_id": size_id,
            "total_qty_in": total_in,
            "total_qty_out": total_out,
            "current_stock": current_stock
        }
    else:
        return {
            "raw_material_id": raw_material_id,
            "size_id": size_id,
            "total_qty_in": Decimal("0.00"),
            "total_qty_out": Decimal("0.00"),
            "current_stock": Decimal("0.00")
        }
