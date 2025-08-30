from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional
from datetime import date
from decimal import Decimal

from dependencies import get_db, get_current_user
from models.purchase_order import PurchaseOrder, PurchaseOrderItem
from models.suppliers import Supplier
from models.raw_material_master import RawMaterialMaster
from models.unit_master import UnitMaster
from schemas.purchase_order import (
    PurchaseOrderCreate, 
    PurchaseOrderUpdate, 
    PurchaseOrderResponse, 
    PurchaseOrderSummary,
    PurchaseOrderStatusUpdate
)
from models.user import User

router = APIRouter()

# Helper function to build response with related data
def build_purchase_order_response(po_entry, db: Session):
    """Helper function to build purchase order response with related data"""
    
    # Load supplier
    supplier = db.query(Supplier).filter(Supplier.id == po_entry.supplier_id).first()
    supplier_data = {
        "id": supplier.id,
        "supplier_name": supplier.supplier_name,
        "supplier_type": supplier.supplier_type,
        "contact_person": supplier.contact_person,
        "phone": supplier.phone,
        "email": supplier.email
    } if supplier else None
    
    # Build items with related data
    items_data = []
    for item in po_entry.items:
        # Load material
        material = db.query(RawMaterialMaster).filter(RawMaterialMaster.id == item.material_id).first()
        material_data = {
            "id": material.id,
            "material_name": material.material_name,
            "material_code": material.material_code,
            "description": material.description
        } if material else None
        
        # Load unit
        unit = db.query(UnitMaster).filter(UnitMaster.id == item.unit_id).first()
        unit_data = {
            "id": unit.id,
            "unit_name": unit.unit_name,
            "unit_code": unit.unit_code
        } if unit else None
        
        item_data = {
            "id": item.id,
            "po_id": item.po_id,
            "material_id": item.material_id,
            "supplier_material_name": item.supplier_material_name,
            "description": item.description,
            "quantity": item.quantity,
            "unit_id": item.unit_id,
            "rate": item.rate,
            "total_amount": item.total_amount,
            "received_qty": item.received_qty,
            "pending_qty": item.pending_qty,
            "item_status": item.item_status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "material": material_data,
            "unit": unit_data
        }
        items_data.append(item_data)
    
    # Create response dict
    return {
        "id": po_entry.id,
        "po_number": po_entry.po_number,
        "supplier_id": po_entry.supplier_id,
        "po_date": po_entry.po_date,
        "due_date": po_entry.due_date,
        "status": po_entry.status,
        "transport_details": po_entry.transport_details,
        "sub_total": po_entry.sub_total,
        "tax_amount": po_entry.tax_amount,
        "discount_amount": po_entry.discount_amount,
        "total_amount": po_entry.total_amount,
        "remarks": po_entry.remarks,
        "created_by": po_entry.created_by,
        "is_active": po_entry.is_active,
        "created_at": po_entry.created_at,
        "updated_at": po_entry.updated_at,
        "calculated_sub_total": po_entry.calculated_sub_total,
        "calculated_total": po_entry.calculated_total,
        "supplier": supplier_data,
        "items": items_data
    }

# Purchase Order CRUD Operations

@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new purchase order with items using JWT Token Authentication."""
    
    # Check if PO number already exists
    existing_po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_data.po_number).first()
    if existing_po:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase order number {po_data.po_number} already exists"
        )
    
    # Validate supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == po_data.supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {po_data.supplier_id} not found"
        )
    
    # Create purchase order
    db_po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        po_date=po_data.po_date,
        due_date=po_data.due_date,
        transport_details=po_data.transport_details,
        tax_amount=po_data.tax_amount,
        discount_amount=po_data.discount_amount,
        remarks=po_data.remarks,
        created_by=current_user.username
    )
    
    db.add(db_po)
    db.flush()  # Get the PO ID
    
    # Create purchase order items
    total_amount = Decimal("0.00")
    for item_data in po_data.items:
        # Validate material exists
        material = db.query(RawMaterialMaster).filter(RawMaterialMaster.id == item_data.material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {item_data.material_id} not found"
            )
        
        # Validate unit exists
        unit = db.query(UnitMaster).filter(UnitMaster.id == item_data.unit_id).first()
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unit with ID {item_data.unit_id} not found"
            )
        
        # Calculate item total
        item_total = item_data.quantity * item_data.rate
        total_amount += item_total
        
        # Create PO item
        db_item = PurchaseOrderItem(
            po_id=db_po.id,
            material_id=item_data.material_id,
            supplier_material_name=item_data.supplier_material_name,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_id=item_data.unit_id,
            rate=item_data.rate,
            total_amount=item_total,
            pending_qty=item_data.quantity
        )
        db.add(db_item)
    
    # Update PO totals using setattr to avoid SQLAlchemy column assignment issues
    setattr(db_po, 'sub_total', total_amount)
    setattr(db_po, 'total_amount', total_amount + (po_data.tax_amount or Decimal("0.00")) - (po_data.discount_amount or Decimal("0.00")))
    
    db.commit()
    db.refresh(db_po)
    
    return build_purchase_order_response(db_po, db)

@router.get("/", response_model=List[PurchaseOrderSummary])
async def get_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    po_date_from: Optional[date] = Query(None),
    po_date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get purchase orders with filtering options using JWT Token Authentication."""
    
    query = db.query(
        PurchaseOrder.id,
        PurchaseOrder.po_number,
        PurchaseOrder.supplier_id,
        PurchaseOrder.po_date,
        PurchaseOrder.due_date,
        PurchaseOrder.status,
        PurchaseOrder.total_amount,
        PurchaseOrder.created_at,
        Supplier.supplier_name,
        func.count(PurchaseOrderItem.id).label("items_count")
    ).join(Supplier).outerjoin(PurchaseOrderItem).group_by(
        PurchaseOrder.id, Supplier.supplier_name
    )
    
    # Apply filters
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if po_date_from:
        query = query.filter(PurchaseOrder.po_date >= po_date_from)
    if po_date_to:
        query = query.filter(PurchaseOrder.po_date <= po_date_to)
    
    # Order by PO date descending
    query = query.order_by(desc(PurchaseOrder.po_date), desc(PurchaseOrder.id))
    
    results = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": result.id,
            "po_number": result.po_number,
            "supplier_id": result.supplier_id,
            "supplier_name": result.supplier_name,
            "po_date": result.po_date,
            "due_date": result.due_date,
            "status": result.status,
            "total_amount": result.total_amount,
            "items_count": result.items_count,
            "created_at": result.created_at
        }
        for result in results
    ]

@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific purchase order by ID using JWT Token Authentication."""
    
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.items)
    ).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    return build_purchase_order_response(po, db)

@router.put("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: int,
    po_update: PurchaseOrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a purchase order using JWT Token Authentication."""
    
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    # Check if PO can be updated (only Draft and Pending orders)
    po_status = getattr(po, 'status')
    if po_status not in ["Draft", "Pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update purchase order in {po_status} status"
        )
    
    # Update only provided fields
    update_data = po_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)
    
    db.commit()
    db.refresh(po)
    
    return build_purchase_order_response(po, db)

@router.put("/{po_id}/status", response_model=PurchaseOrderResponse)
async def update_purchase_order_status(
    po_id: int,
    status_update: PurchaseOrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update purchase order status using JWT Token Authentication."""
    
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    # Valid status transitions
    valid_statuses = ["Draft", "Pending", "Approved", "Received", "Cancelled"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}"
        )
    
    setattr(po, 'status', status_update.status)
    if status_update.remarks:
        current_remarks = getattr(po, 'remarks')
        new_remarks = f"{current_remarks}\n{status_update.remarks}" if current_remarks else status_update.remarks
        setattr(po, 'remarks', new_remarks)
    
    db.commit()
    db.refresh(po)
    
    return build_purchase_order_response(po, db)

@router.delete("/{po_id}")
async def delete_purchase_order(
    po_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a purchase order using JWT Token Authentication."""
    
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    # Only allow deletion of Draft orders
    po_status = getattr(po, 'status')
    if po_status != "Draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete purchase order in {po_status} status. Only Draft orders can be deleted."
        )
    
    db.delete(po)
    db.commit()
    return {"message": f"Purchase order {po.po_number} deleted successfully"}

# Purchase Order Statistics

@router.get("/stats")
async def get_purchase_order_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get purchase order statistics using JWT Token Authentication."""
    
    stats = db.query(
        PurchaseOrder.status,
        func.count(PurchaseOrder.id).label("count"),
        func.sum(PurchaseOrder.total_amount).label("total_value")
    ).group_by(PurchaseOrder.status).all()
    
    total_pos = db.query(func.count(PurchaseOrder.id)).scalar()
    total_value = db.query(func.sum(PurchaseOrder.total_amount)).scalar() or Decimal("0.00")
    
    return {
        "total_purchase_orders": total_pos,
        "total_value": total_value,
        "by_status": [
            {
                "status": stat.status,
                "count": stat.count,
                "total_value": stat.total_value or Decimal("0.00")
            }
            for stat in stats
        ]
    }
