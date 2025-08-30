"""
Sales Calculator Utilities
Business logic for sales calculations, validations, and operations
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from models.sales import Sales, SalesItem, SalesStatus
from models.bill_book import BillBook, TaxType
from models.product_management import ProductVariant
from schemas.sales import SalesItemCreate, SalesCreate
import logging

logger = logging.getLogger(__name__)


class SalesCalculator:
    """
    Sales calculation engine
    Handles all financial calculations for sales transactions
    """
    
    @staticmethod
    def calculate_item_amounts(
        quantity: Decimal,
        sale_rate: Decimal,
        discount_percentage: Decimal = Decimal('0'),
        tax_percentage: Decimal = Decimal('0'),
        tax_type: TaxType = TaxType.EXCLUDE_TAX
    ) -> Dict[str, Decimal]:
        """
        Calculate all amounts for a sales item
        
        Args:
            quantity: Item quantity
            sale_rate: Rate per unit
            discount_percentage: Discount percentage
            tax_percentage: Tax percentage
            tax_type: How tax is applied (INCLUDE_TAX, EXCLUDE_TAX, WITHOUT_TAX)
            
        Returns:
            Dictionary with calculated amounts
        """
        # Round to 2 decimal places for currency
        def round_currency(amount: Decimal) -> Decimal:
            return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Calculate base amount
        base_amount = quantity * sale_rate
        
        if tax_type == TaxType.INCLUDE_TAX:
            # Tax is included in the sale rate
            # Need to extract tax from the sale rate
            tax_factor = Decimal('1') + (tax_percentage / Decimal('100'))
            amount_before_tax = base_amount / tax_factor
            
            # Calculate discount on amount before tax
            discount_amount = round_currency(amount_before_tax * discount_percentage / Decimal('100'))
            amount_after_discount = amount_before_tax - discount_amount
            
            # Tax is calculated on discounted amount
            tax_amount = round_currency(amount_after_discount * tax_percentage / Decimal('100'))
            total_amount = amount_after_discount + tax_amount
            
        elif tax_type == TaxType.EXCLUDE_TAX:
            # Tax is added on top of sale rate
            # Calculate discount first
            discount_amount = round_currency(base_amount * discount_percentage / Decimal('100'))
            amount_after_discount = base_amount - discount_amount
            
            # Calculate tax on discounted amount
            tax_amount = round_currency(amount_after_discount * tax_percentage / Decimal('100'))
            total_amount = amount_after_discount + tax_amount
            
        else:  # WITHOUT_TAX
            # No tax calculation
            discount_amount = round_currency(base_amount * discount_percentage / Decimal('100'))
            tax_amount = Decimal('0')
            total_amount = base_amount - discount_amount
        
        return {
            'base_amount': round_currency(base_amount),
            'discount_amount': round_currency(discount_amount),
            'tax_amount': round_currency(tax_amount),
            'total_amount': round_currency(total_amount),
            'amount_after_discount': round_currency(base_amount - discount_amount) if tax_type != TaxType.INCLUDE_TAX else round_currency(amount_after_discount)
        }
    
    @staticmethod
    def calculate_sales_totals(items: List[SalesItem], additional_charges: Decimal = Decimal('0')) -> Dict[str, Decimal]:
        """
        Calculate total amounts for entire sales transaction
        
        Args:
            items: List of sales items
            additional_charges: Additional charges to add
            
        Returns:
            Dictionary with calculated totals
        """
        def round_currency(amount: Decimal) -> Decimal:
            return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        item_count = len(items)
        total_qty = sum(item.quantity for item in items)
        gross_amount = sum(item.quantity * item.sale_rate for item in items)
        discount_amount = sum(item.discount_amount for item in items)
        tax_amount = sum(item.tax_amount for item in items)
        
        total_amount = gross_amount - discount_amount + tax_amount + additional_charges
        
        return {
            'item_count': item_count,
            'total_qty': total_qty,
            'gross_amount': round_currency(gross_amount),
            'discount_amount': round_currency(discount_amount),
            'tax_amount': round_currency(tax_amount),
            'total_amount': round_currency(total_amount)
        }


class SalesValidator:
    """
    Sales validation utilities
    Handles business rule validations
    """
    
    @staticmethod
    def validate_status_transition(current_status: SalesStatus, new_status: SalesStatus) -> Tuple[bool, str]:
        """
        Validate if status transition is allowed
        
        Args:
            current_status: Current sales status
            new_status: Desired new status
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_transitions = {
            SalesStatus.DRAFT: [SalesStatus.CONFIRMED, SalesStatus.CANCELLED],
            SalesStatus.CONFIRMED: [SalesStatus.DISPATCHED, SalesStatus.CANCELLED],
            SalesStatus.DISPATCHED: [SalesStatus.DELIVERED, SalesStatus.CANCELLED],
            SalesStatus.DELIVERED: [],  # Final state
            SalesStatus.CANCELLED: []   # Final state
        }
        
        if new_status in valid_transitions.get(current_status, []):
            return True, ""
        
        return False, f"Cannot change status from {current_status.value} to {new_status.value}"
    
    @staticmethod
    def validate_item_data(db: Session, item_data: SalesItemCreate) -> Tuple[bool, str, Optional[ProductVariant]]:
        """
        Validate sales item data
        
        Args:
            db: Database session
            item_data: Sales item create data
            
        Returns:
            Tuple of (is_valid, error_message, product_variant)
        """
        # Check if product variant exists
        variant = db.query(ProductVariant).filter(ProductVariant.id == item_data.variant_id).first()
        if not variant:
            return False, f"Product variant {item_data.variant_id} not found", None
        
        # Check if variant is active
        if not variant.is_active:
            return False, f"Product variant {variant.variant_name} is not active", None
        
        # Validate quantity
        if item_data.quantity <= 0:
            return False, "Quantity must be greater than 0", None
        
        # Validate sale rate
        if item_data.sale_rate < 0:
            return False, "Sale rate cannot be negative", None
        
        # Validate percentages
        if item_data.discount_percentage and (item_data.discount_percentage < 0 or item_data.discount_percentage > 100):
            return False, "Discount percentage must be between 0 and 100", None
        
        if item_data.tax_percentage and (item_data.tax_percentage < 0 or item_data.tax_percentage > 100):
            return False, "Tax percentage must be between 0 and 100", None
        
        return True, "", variant
    
    @staticmethod
    def validate_sales_data(db: Session, sales_data: SalesCreate) -> Tuple[bool, str, Optional[BillBook]]:
        """
        Validate sales data
        
        Args:
            db: Database session
            sales_data: Sales create data
            
        Returns:
            Tuple of (is_valid, error_message, bill_book)
        """
        # Check if bill book exists
        bill_book = db.query(BillBook).filter(BillBook.id == sales_data.bill_book_id).first()
        if not bill_book:
            return False, f"Bill book {sales_data.bill_book_id} not found", None
        
        # Check if bill book is active
        if bill_book.status != "ACTIVE":
            return False, f"Bill book {bill_book.book_name} is not active", None
        
        # Validate dates
        if sales_data.due_date and sales_data.due_date < sales_data.bill_date:
            return False, "Due date cannot be before bill date", None
        
        # Validate additional charges
        if sales_data.additional_charges and sales_data.additional_charges < 0:
            return False, "Additional charges cannot be negative", None
        
        # Validate items
        if not sales_data.items:
            return False, "Sales must have at least one item", None
        
        # Validate each item
        for i, item in enumerate(sales_data.items):
            is_valid, error, _ = SalesValidator.validate_item_data(db, item)
            if not is_valid:
                return False, f"Item {i+1}: {error}", None
        
        return True, "", bill_book


class SalesBusinessLogic:
    """
    Sales business logic utilities
    Handles complex business operations
    """
    
    @staticmethod
    def prepare_sales_item(
        db: Session,
        item_data: SalesItemCreate,
        variant: ProductVariant,
        tax_type: TaxType
    ) -> SalesItem:
        """
        Prepare a sales item with calculated amounts
        
        Args:
            db: Database session
            item_data: Sales item create data
            variant: Product variant
            tax_type: Bill book tax type
            
        Returns:
            Prepared SalesItem instance
        """
        # Calculate amounts
        amounts = SalesCalculator.calculate_item_amounts(
            quantity=item_data.quantity,
            sale_rate=item_data.sale_rate,
            discount_percentage=item_data.discount_percentage or Decimal('0'),
            tax_percentage=item_data.tax_percentage or Decimal('0'),
            tax_type=tax_type
        )
        
        # Create sales item
        sales_item = SalesItem(
            variant_id=variant.id,
            product_name=variant.variant_name or f"Product Variant {variant.id}",
            hsn_code=variant.hsn_code,
            unit_type=variant.unit_type,
            quantity=item_data.quantity,
            mrp=variant.mrp,
            sale_rate=item_data.sale_rate,
            discount_percentage=item_data.discount_percentage or Decimal('0'),
            discount_amount=amounts['discount_amount'],
            tax_percentage=item_data.tax_percentage or Decimal('0'),
            tax_amount=amounts['tax_amount'],
            total_amount=amounts['total_amount']
        )
        
        return sales_item
    
    @staticmethod
    def generate_bill_number(db: Session, bill_book: BillBook) -> str:
        """
        Generate next bill number for the bill book
        
        Args:
            db: Database session
            bill_book: Bill book instance
            
        Returns:
            Generated bill number
        """
        # Get next sequence number
        bill_book.last_bill_no += 1
        
        # Generate bill number using prefix and sequence
        bill_number = f"{bill_book.prefix}{str(bill_book.last_bill_no).zfill(3)}"
        
        # Save updated bill book
        db.commit()
        
        return bill_number
    
    @staticmethod
    def create_sales_transaction(
        db: Session,
        sales_data: SalesCreate,
        created_by: str
    ) -> Tuple[bool, str, Optional[Sales]]:
        """
        Create complete sales transaction with all validations
        
        Args:
            db: Database session
            sales_data: Sales create data
            created_by: User creating the sales
            
        Returns:
            Tuple of (success, message, sales_instance)
        """
        try:
            # Validate sales data
            is_valid, error, bill_book = SalesValidator.validate_sales_data(db, sales_data)
            if not is_valid:
                return False, error, None
            
            # Generate bill number
            bill_number = SalesBusinessLogic.generate_bill_number(db, bill_book)
            
            # Create sales record
            sales = Sales(
                bill_book_id=bill_book.id,
                customer_id=sales_data.customer_id,
                agent_id=sales_data.agent_id,
                bill_number=bill_number,
                bill_date=sales_data.bill_date,
                due_date=sales_data.due_date,
                additional_charges=sales_data.additional_charges or Decimal('0'),
                transport_details=sales_data.transport_details,
                llr_no=sales_data.llr_no,
                llr_date=sales_data.llr_date,
                created_by=created_by
            )
            
            # Add to session to get ID
            db.add(sales)
            db.flush()
            
            # Create sales items
            sales_items = []
            for item_data in sales_data.items:
                # Validate and get variant
                is_valid, error, variant = SalesValidator.validate_item_data(db, item_data)
                if not is_valid:
                    db.rollback()
                    return False, error, None
                
                # Create sales item
                sales_item = SalesBusinessLogic.prepare_sales_item(
                    db, item_data, variant, bill_book.tax_type
                )
                sales_item.sales_id = sales.id
                sales_items.append(sales_item)
                db.add(sales_item)
            
            # Update sales totals
            totals = SalesCalculator.calculate_sales_totals(
                sales_items, 
                sales.additional_charges
            )
            
            sales.item_count = totals['item_count']
            sales.total_qty = totals['total_qty']
            sales.gross_amount = totals['gross_amount']
            sales.discount_amount = totals['discount_amount']
            sales.tax_amount = totals['tax_amount']
            sales.total_amount = totals['total_amount']
            
            # Commit transaction
            db.commit()
            
            # Refresh to get relationships
            db.refresh(sales)
            
            logger.info(f"Sales created successfully: ID={sales.id}, Bill Number={sales.bill_number}")
            return True, "Sales created successfully", sales
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating sales: {str(e)}")
            return False, f"Error creating sales: {str(e)}", None


class SalesReportGenerator:
    """
    Sales reporting utilities
    """
    
    @staticmethod
    def generate_sales_summary(
        db: Session,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        customer_id: Optional[int] = None,
        agent_id: Optional[int] = None
    ) -> Dict:
        """
        Generate sales summary report
        
        Args:
            db: Database session
            from_date: Start date filter
            to_date: End date filter
            customer_id: Customer filter
            agent_id: Agent filter
            
        Returns:
            Summary report dictionary
        """
        query = db.query(Sales)
        
        # Apply filters
        if from_date:
            query = query.filter(Sales.bill_date >= from_date)
        if to_date:
            query = query.filter(Sales.bill_date <= to_date)
        if customer_id:
            query = query.filter(Sales.customer_id == customer_id)
        if agent_id:
            query = query.filter(Sales.agent_id == agent_id)
        
        sales_list = query.all()
        
        # Calculate summary
        total_sales = len(sales_list)
        total_amount = sum(sale.total_amount for sale in sales_list)
        
        # Status breakdown
        status_breakdown = {}
        for status in SalesStatus:
            count = len([s for s in sales_list if s.status == status])
            if count > 0:
                status_breakdown[status.value] = count
        
        return {
            'total_sales': total_sales,
            'total_amount': float(total_amount),
            'status_breakdown': status_breakdown,
            'average_sale_amount': float(total_amount / total_sales) if total_sales > 0 else 0
        }
