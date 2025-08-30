from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional
import logging

from dependencies import get_db, require_admin, get_current_user
from models.bill_book import BillBook, BillBookStatus, TaxType
from schemas.bill_book import (
    BillBookCreate,
    BillBookUpdate,
    BillBook as BillBookSchema,
    BillBookListResponse,
    TaxType as TaxTypeSchema
)
from models.user import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=BillBookSchema)
async def create_bill_book(
    bill_book_data: BillBookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_admin)  # Only admins can create bill books
):
    """Create a new bill book for sales billing."""
    try:
        # Check if book code already exists
        existing = db.query(BillBook).filter(
            BillBook.book_code == bill_book_data.book_code
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bill book with code '{bill_book_data.book_code}' already exists"
            )
        
        # Create new bill book
        db_bill_book = BillBook(**bill_book_data.model_dump())
        db.add(db_bill_book)
        db.commit()
        db.refresh(db_bill_book)
        
        logger.info(f"Created bill book: {db_bill_book.book_name}")
        return db_bill_book
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating bill book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bill book: {str(e)}"
        )


@router.get("/", response_model=BillBookListResponse)
async def list_bill_books(
    search: Optional[str] = Query(None, description="Search in book name or code"),
    status: Optional[BillBookStatus] = Query(None, description="Filter by status"),
    tax_type: Optional[TaxType] = Query(None, description="Filter by tax type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all bill books with filtering and pagination."""
    try:
        query = db.query(BillBook)
        
        # Apply filters
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    BillBook.book_name.ilike(search_filter),
                    BillBook.book_code.ilike(search_filter)
                )
            )
        
        if status:
            query = query.filter(BillBook.status == status)
        
        if tax_type:
            query = query.filter(BillBook.tax_type == tax_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        bill_books = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return BillBookListResponse(
            bill_books=bill_books,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing bill books: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list bill books: {str(e)}"
        )


@router.get("/{bill_book_id}", response_model=BillBookSchema)
async def get_bill_book(
    bill_book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific bill book by ID."""
    try:
        bill_book = db.query(BillBook).filter(BillBook.id == bill_book_id).first()
        if not bill_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill book not found"
            )
        return bill_book
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving bill book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve bill book: {str(e)}"
        )


@router.put("/{bill_book_id}", response_model=BillBookSchema)
async def update_bill_book(
    bill_book_id: int,
    bill_book_data: BillBookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_admin)  # Only admins can update bill books
):
    """Update a bill book."""
    try:
        # Get existing bill book
        db_bill_book = db.query(BillBook).filter(BillBook.id == bill_book_id).first()
        if not db_bill_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill book not found"
            )
        
        # Check if updating book_code and if it already exists
        if bill_book_data.book_code and bill_book_data.book_code != db_bill_book.book_code:
            existing = db.query(BillBook).filter(
                BillBook.book_code == bill_book_data.book_code
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Bill book with code '{bill_book_data.book_code}' already exists"
                )
        
        # Update fields
        update_data = bill_book_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_bill_book, field, value)
        
        db.commit()
        db.refresh(db_bill_book)
        
        logger.info(f"Updated bill book: {db_bill_book.book_name}")
        return db_bill_book
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating bill book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bill book: {str(e)}"
        )


@router.patch("/{bill_book_id}/increment", response_model=BillBookSchema)
async def increment_bill_number(
    bill_book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Increment the last bill number for a bill book."""
    try:
        # Get existing bill book
        db_bill_book = db.query(BillBook).filter(BillBook.id == bill_book_id).first()
        if not db_bill_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill book not found"
            )
        
        # Check if bill book is active
        if db_bill_book.status != BillBookStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot increment bill number for {db_bill_book.status.lower()} bill book"
            )
        
        # Increment last bill number
        db_bill_book.last_bill_no += 1
        db.commit()
        db.refresh(db_bill_book)
        
        logger.info(f"Incremented bill number for {db_bill_book.book_name} to {db_bill_book.last_bill_no}")
        return db_bill_book
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error incrementing bill number: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to increment bill number: {str(e)}"
        )


@router.get("/{bill_book_id}/next-bill-number")
async def get_next_bill_number(
    bill_book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the next bill number for a bill book without incrementing it."""
    try:
        # Get existing bill book
        db_bill_book = db.query(BillBook).filter(BillBook.id == bill_book_id).first()
        if not db_bill_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill book not found"
            )
        
        # Check if bill book is active
        if db_bill_book.status != BillBookStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot generate bill number for {db_bill_book.status.lower()} bill book"
            )
        
        # Calculate next bill number
        next_number = max(db_bill_book.last_bill_no + 1, db_bill_book.starting_number)
        next_bill_number = f"{db_bill_book.prefix}{next_number:04d}"
        
        return {
            "bill_book_id": bill_book_id,
            "bill_book_name": db_bill_book.book_name,
            "prefix": db_bill_book.prefix,
            "next_number": next_number,
            "next_bill_number": next_bill_number,
            "tax_type": db_bill_book.tax_type,
            "current_last_bill_no": db_bill_book.last_bill_no
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next bill number: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get next bill number: {str(e)}"
        )


@router.post("/{bill_book_id}/generate-bill-number")
async def generate_and_reserve_bill_number(
    bill_book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and reserve the next bill number for a bill book (increments the counter)."""
    try:
        # Get existing bill book
        db_bill_book = db.query(BillBook).filter(BillBook.id == bill_book_id).first()
        if not db_bill_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill book not found"
            )
        
        # Check if bill book is active
        if db_bill_book.status != BillBookStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot generate bill number for {db_bill_book.status.lower()} bill book"
            )
        
        # Calculate next bill number
        next_number = max(db_bill_book.last_bill_no + 1, db_bill_book.starting_number)
        next_bill_number = f"{db_bill_book.prefix}{next_number:04d}"
        
        # Update last bill number
        db_bill_book.last_bill_no = next_number
        db.commit()
        db.refresh(db_bill_book)
        
        logger.info(f"Generated bill number {next_bill_number} for {db_bill_book.book_name}")
        
        return {
            "bill_book_id": bill_book_id,
            "bill_book_name": db_bill_book.book_name,
            "prefix": db_bill_book.prefix,
            "bill_number": next_number,
            "full_bill_number": next_bill_number,
            "tax_type": db_bill_book.tax_type,
            "tax_type_description": {
                "INCLUDE_TAX": "Tax is included in item rates - will be separated during calculation",
                "EXCLUDE_TAX": "Tax will be added on top of item rates",
                "WITHOUT_TAX": "No tax calculations needed"
            }.get(db_bill_book.tax_type.value, "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating bill number: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bill number: {str(e)}"
        )
