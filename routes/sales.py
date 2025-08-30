"""
Sales Management API Routes
Complete CRUD operations for sales billing system
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal

from database import get_db
from models.sales import Sales, SalesItem, SalesStatus
from models.bill_book import BillBook
from models.customers import Customer
from models.agents import Agent
from models.product_management import ProductVariant
from schemas.sales import (
    SalesCreate, SalesUpdate, SalesResponse, SalesListResponse,
    SalesItemCreate, SalesItemUpdate, SalesItemResponse,
    SalesStatusUpdate, SalesFilter, PaginationParams, PaginatedSalesResponse,
    SalesSummary, BulkStatusUpdate, BulkOperationResponse
)
from utils.sales_calculator import SalesCalculator, SalesValidator, SalesBusinessLogic, SalesReportGenerator
from dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sales Management"])


# ================================
# SALES CRUD OPERATIONS
# ================================

@router.post("/", response_model=SalesResponse, status_code=status.HTTP_201_CREATED)
async def create_sales(
    sales_data: SalesCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new sales transaction
    
    - **bill_book_id**: ID of the bill book for bill number generation
    - **customer_id**: Customer ID
    - **agent_id**: Sales agent ID (optional)
    - **items**: List of sales items (minimum 1 required)
    - **bill_date**: Date of the bill
    - **due_date**: Payment due date (optional)
    - **additional_charges**: Additional charges (optional)
    - **transport_details**: Transport information (optional)
    """
    try:
        logger.info(f"Creating new sales for customer {sales_data.customer_id}")
        
        # Create sales transaction using business logic
        success, message, sales = SalesBusinessLogic.create_sales_transaction(
            db=db,
            sales_data=sales_data,
            created_by=current_user.get("username", "unknown")
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Load relationships for response
        db.refresh(sales)
        sales_with_items = db.query(Sales).options(
            joinedload(Sales.items),
            joinedload(Sales.bill_book),
            joinedload(Sales.customer),
            joinedload(Sales.agent)
        ).filter(Sales.id == sales.id).first()
        
        logger.info(f"Sales created successfully: ID={sales.id}, Bill={sales.bill_number}")
        return sales_with_items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sales: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sales: {str(e)}"
        )


@router.get("/", response_model=PaginatedSalesResponse)
async def list_sales(
    pagination: PaginationParams = Depends(),
    filters: SalesFilter = Depends(),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List sales with filtering, pagination, and sorting
    
    **Filters:**
    - **customer_id**: Filter by customer
    - **agent_id**: Filter by agent
    - **bill_book_id**: Filter by bill book
    - **status**: Filter by status
    - **from_date**: Filter from date
    - **to_date**: Filter to date
    - **min_amount**: Minimum amount
    - **max_amount**: Maximum amount
    - **bill_number**: Search by bill number
    
    **Pagination:**
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 10, max: 100)
    
    **Sorting:**
    - **sort_by**: Field to sort by (default: created_at)
    - **sort_order**: asc or desc (default: desc)
    """
    try:
        query = db.query(Sales)
        
        # Apply filters
        if filters.customer_id:
            query = query.filter(Sales.customer_id == filters.customer_id)
        
        if filters.agent_id:
            query = query.filter(Sales.agent_id == filters.agent_id)
        
        if filters.bill_book_id:
            query = query.filter(Sales.bill_book_id == filters.bill_book_id)
        
        if filters.status:
            query = query.filter(Sales.status == filters.status)
        
        if filters.from_date:
            query = query.filter(Sales.bill_date >= filters.from_date)
        
        if filters.to_date:
            query = query.filter(Sales.bill_date <= filters.to_date)
        
        if filters.min_amount:
            query = query.filter(Sales.total_amount >= filters.min_amount)
        
        if filters.max_amount:
            query = query.filter(Sales.total_amount <= filters.max_amount)
        
        if filters.bill_number:
            query = query.filter(Sales.bill_number.ilike(f"%{filters.bill_number}%"))
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        if hasattr(Sales, sort_by):
            order_column = getattr(Sales, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(Sales.created_at))
        
        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)
        
        sales_list = query.all()
        
        # Calculate total pages
        pages = (total + pagination.limit - 1) // pagination.limit
        
        return PaginatedSalesResponse(
            items=sales_list,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error listing sales: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing sales: {str(e)}"
        )


@router.get("/{sales_id}", response_model=SalesResponse)
async def get_sales(
    sales_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get sales details by ID with all related information
    
    Returns complete sales information including:
    - Sales header details
    - All line items
    - Customer information
    - Agent information (if applicable)
    - Bill book information
    """
    try:
        sales = db.query(Sales).options(
            joinedload(Sales.items).joinedload(SalesItem.variant),
            joinedload(Sales.bill_book),
            joinedload(Sales.customer),
            joinedload(Sales.agent)
        ).filter(Sales.id == sales_id).first()
        
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales with ID {sales_id} not found"
            )
        
        return sales
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sales {sales_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sales: {str(e)}"
        )


@router.put("/{sales_id}", response_model=SalesResponse)
async def update_sales(
    sales_id: int,
    sales_update: SalesUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update sales header information
    
    **Note:** This only updates header fields. Use separate endpoints for items.
    
    **Editable only when status is DRAFT or CONFIRMED**
    """
    try:
        sales = db.query(Sales).filter(Sales.id == sales_id).first()
        
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales with ID {sales_id} not found"
            )
        
        # Check if sales can be edited
        if not sales.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sales with status {sales.status.value} cannot be edited"
            )
        
        # Update fields that are provided
        update_data = sales_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(sales, field, value)
        
        sales.updated_by = current_user.get("username", "unknown")
        
        db.commit()
        db.refresh(sales)
        
        logger.info(f"Sales {sales_id} updated successfully")
        return sales
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sales {sales_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating sales: {str(e)}"
        )


@router.delete("/{sales_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sales(
    sales_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete sales transaction
    
    **Note:** Only DRAFT sales can be deleted
    """
    try:
        sales = db.query(Sales).filter(Sales.id == sales_id).first()
        
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales with ID {sales_id} not found"
            )
        
        # Only allow deletion of DRAFT sales
        if sales.status != SalesStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete sales with status {sales.status.value}. Only DRAFT sales can be deleted."
            )
        
        db.delete(sales)
        db.commit()
        
        logger.info(f"Sales {sales_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sales {sales_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting sales: {str(e)}"
        )


# ================================
# SALES STATUS MANAGEMENT
# ================================

@router.patch("/{sales_id}/status", response_model=SalesResponse)
async def update_sales_status(
    sales_id: int,
    status_update: SalesStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update sales status
    
    **Valid status transitions:**
    - DRAFT → CONFIRMED, CANCELLED
    - CONFIRMED → DISPATCHED, CANCELLED  
    - DISPATCHED → DELIVERED, CANCELLED
    - DELIVERED → (final state)
    - CANCELLED → (final state)
    """
    try:
        sales = db.query(Sales).filter(Sales.id == sales_id).first()
        
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales with ID {sales_id} not found"
            )
        
        # Validate status transition
        is_valid, error_message = SalesValidator.validate_status_transition(
            sales.status, status_update.status
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Update status
        sales.status = status_update.status
        sales.updated_by = status_update.updated_by
        
        db.commit()
        db.refresh(sales)
        
        logger.info(f"Sales {sales_id} status updated to {status_update.status.value}")
        return sales
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sales status {sales_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating sales status: {str(e)}"
        )


@router.post("/bulk-status-update", response_model=BulkOperationResponse)
async def bulk_update_status(
    bulk_update: BulkStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update status for multiple sales transactions
    
    **Returns:**
    - **success_count**: Number of successfully updated sales
    - **failed_count**: Number of failed updates
    - **failed_ids**: List of sales IDs that failed to update
    - **errors**: List of error messages
    """
    try:
        success_count = 0
        failed_count = 0
        failed_ids = []
        errors = []
        
        for sales_id in bulk_update.sales_ids:
            try:
                sales = db.query(Sales).filter(Sales.id == sales_id).first()
                
                if not sales:
                    failed_count += 1
                    failed_ids.append(sales_id)
                    errors.append(f"Sales ID {sales_id}: Not found")
                    continue
                
                # Validate status transition
                is_valid, error_message = SalesValidator.validate_status_transition(
                    sales.status, bulk_update.status
                )
                
                if not is_valid:
                    failed_count += 1
                    failed_ids.append(sales_id)
                    errors.append(f"Sales ID {sales_id}: {error_message}")
                    continue
                
                # Update status
                sales.status = bulk_update.status
                sales.updated_by = bulk_update.updated_by
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_ids.append(sales_id)
                errors.append(f"Sales ID {sales_id}: {str(e)}")
        
        db.commit()
        
        logger.info(f"Bulk status update completed: {success_count} success, {failed_count} failed")
        
        return BulkOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            failed_ids=failed_ids,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error in bulk status update: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk status update: {str(e)}"
        )


# ================================
# SALES ITEMS MANAGEMENT
# ================================

@router.get("/{sales_id}/items", response_model=List[SalesItemResponse])
async def get_sales_items(
    sales_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all items for a sales transaction"""
    try:
        # Verify sales exists
        sales = db.query(Sales).filter(Sales.id == sales_id).first()
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales with ID {sales_id} not found"
            )
        
        items = db.query(SalesItem).options(
            joinedload(SalesItem.variant)
        ).filter(SalesItem.sales_id == sales_id).all()
        
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sales items for {sales_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sales items: {str(e)}"
        )


@router.post("/{sales_id}/items", response_model=SalesItemResponse, status_code=status.HTTP_201_CREATED)
async def add_sales_item(
    sales_id: int,
    item_data: SalesItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add new item to sales transaction
    
    **Note:** Sales must be in DRAFT or CONFIRMED status
    """
    try:
        # Get sales and validate
        sales = db.query(Sales).filter(Sales.id == sales_id).first()
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales with ID {sales_id} not found"
            )
        
        if not sales.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add items to sales with status {sales.status.value}"
            )
        
        # Validate item data
        is_valid, error, variant = SalesValidator.validate_item_data(db, item_data)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Get bill book for tax type
        bill_book = db.query(BillBook).filter(BillBook.id == sales.bill_book_id).first()
        
        # Create sales item
        sales_item = SalesBusinessLogic.prepare_sales_item(
            db, item_data, variant, bill_book.tax_type
        )
        sales_item.sales_id = sales_id
        
        db.add(sales_item)
        db.flush()
        
        # Recalculate sales totals
        sales.calculate_totals()
        
        db.commit()
        db.refresh(sales_item)
        
        logger.info(f"Item added to sales {sales_id}: Item ID {sales_item.id}")
        return sales_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding item to sales {sales_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding item: {str(e)}"
        )


@router.put("/{sales_id}/items/{item_id}", response_model=SalesItemResponse)
async def update_sales_item(
    sales_id: int,
    item_id: int,
    item_update: SalesItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update sales item
    
    **Note:** Sales must be in DRAFT or CONFIRMED status
    """
    try:
        # Get sales and validate
        sales = db.query(Sales).filter(Sales.id == sales_id).first()
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales with ID {sales_id} not found"
            )
        
        if not sales.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update items in sales with status {sales.status.value}"
            )
        
        # Get item
        item = db.query(SalesItem).filter(
            SalesItem.id == item_id,
            SalesItem.sales_id == sales_id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales item with ID {item_id} not found in sales {sales_id}"
            )
        
        # Update fields
        update_data = item_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(item, field, value)
        
        # Recalculate amounts
        item.calculate_amounts()
        
        # Recalculate sales totals
        sales.calculate_totals()
        
        db.commit()
        db.refresh(item)
        
        logger.info(f"Item {item_id} updated in sales {sales_id}")
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id} in sales {sales_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating item: {str(e)}"
        )


@router.delete("/{sales_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sales_item(
    sales_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete sales item
    
    **Note:** Sales must be in DRAFT or CONFIRMED status
    """
    try:
        # Get sales and validate
        sales = db.query(Sales).filter(Sales.id == sales_id).first()
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales with ID {sales_id} not found"
            )
        
        if not sales.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete items from sales with status {sales.status.value}"
            )
        
        # Get item
        item = db.query(SalesItem).filter(
            SalesItem.id == item_id,
            SalesItem.sales_id == sales_id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales item with ID {item_id} not found in sales {sales_id}"
            )
        
        # Check if this is the last item
        item_count = db.query(SalesItem).filter(SalesItem.sales_id == sales_id).count()
        if item_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last item. Sales must have at least one item."
            )
        
        db.delete(item)
        
        # Recalculate sales totals
        sales.calculate_totals()
        
        db.commit()
        
        logger.info(f"Item {item_id} deleted from sales {sales_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id} from sales {sales_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting item: {str(e)}"
        )


# ================================
# SALES ANALYTICS & REPORTS
# ================================

@router.get("/analytics/summary", response_model=SalesSummary)
async def get_sales_summary(
    from_date: Optional[date] = Query(None, description="Start date for summary"),
    to_date: Optional[date] = Query(None, description="End date for summary"),
    customer_id: Optional[int] = Query(None, description="Filter by customer"),
    agent_id: Optional[int] = Query(None, description="Filter by agent"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get sales summary and analytics
    
    **Returns:**
    - Total sales count and amount
    - Status breakdown
    - Average sale amount
    - Date range information
    """
    try:
        summary = SalesReportGenerator.generate_sales_summary(
            db=db,
            from_date=from_date.isoformat() if from_date else None,
            to_date=to_date.isoformat() if to_date else None,
            customer_id=customer_id,
            agent_id=agent_id
        )
        
        # Add date range info
        summary['date_range'] = {
            'from_date': from_date or date.min,
            'to_date': to_date or date.today()
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating sales summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sales summary: {str(e)}"
        )


# ================================
# UTILITY ENDPOINTS
# ================================

@router.get("/bill-books/active", response_model=List[Dict[str, Any]])
async def get_active_bill_books(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of active bill books for sales creation"""
    try:
        bill_books = db.query(BillBook).filter(BillBook.status == "ACTIVE").all()
        
        return [
            {
                "id": bb.id,
                "book_name": bb.book_name,
                "book_code": bb.book_code,
                "prefix": bb.prefix,
                "tax_type": bb.tax_type.value,
                "last_bill_no": bb.last_bill_no
            }
            for bb in bill_books
        ]
        
    except Exception as e:
        logger.error(f"Error getting active bill books: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting bill books: {str(e)}"
        )


@router.get("/customers/active", response_model=List[Dict[str, Any]])
async def get_active_customers(
    search: Optional[str] = Query(None, description="Search customers by name"),
    limit: int = Query(50, le=100, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of active customers for sales creation"""
    try:
        query = db.query(Customer).filter(Customer.status == "Active")
        
        if search:
            query = query.filter(Customer.customer_name.ilike(f"%{search}%"))
        
        customers = query.limit(limit).all()
        
        return [
            {
                "id": c.id,
                "customer_name": c.customer_name,
                "customer_type": c.customer_type.value,
                "gst_number": c.gst_number,
                "city": c.city,
                "phone": c.phone
            }
            for c in customers
        ]
        
    except Exception as e:
        logger.error(f"Error getting active customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting customers: {str(e)}"
        )


@router.get("/agents/active", response_model=List[Dict[str, Any]])
async def get_active_agents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of active agents for sales creation"""
    try:
        agents = db.query(Agent).filter(Agent.status == "Active").all()
        
        return [
            {
                "id": a.id,
                "agent_name": a.agent_name,
                "agent_acc_code": a.agent_acc_code,
                "city": a.city,
                "phone": a.phone
            }
            for a in agents
        ]
        
    except Exception as e:
        logger.error(f"Error getting active agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting agents: {str(e)}"
        )


@router.get("/product-variants/active", response_model=List[Dict[str, Any]])
async def get_active_product_variants(
    search: Optional[str] = Query(None, description="Search variants by name"),
    limit: int = Query(50, le=100, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of active product variants for sales items"""
    try:
        query = db.query(ProductVariant).options(
            joinedload(ProductVariant.product)
        ).filter(ProductVariant.is_active == True)
        
        if search:
            query = query.filter(ProductVariant.variant_name.ilike(f"%{search}%"))
        
        variants = query.limit(limit).all()
        
        return [
            {
                "id": v.id,
                "variant_name": v.variant_name,
                "variant_code": v.variant_code,
                "sku": v.sku,
                "hsn_code": v.hsn_code,
                "unit_type": v.unit_type,
                "price": float(v.price) if v.price else 0,
                "mrp": float(v.mrp) if v.mrp else 0,
                "stock_balance": float(v.stock_balance),
                "product_name": v.product.product_name if v.product else None
            }
            for v in variants
        ]
        
    except Exception as e:
        logger.error(f"Error getting active product variants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting product variants: {str(e)}"
        )
