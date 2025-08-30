from .user import router as user_router
from .company import router as company_router
from .state import router as state_router
from .accounts import router as accounts_router
from .agents import router as agents_router
from .bill_book import router as bill_book_router
from .customers import router as customers_router
from .suppliers import router as suppliers_router
from .vendors import router as vendors_router  # Temporarily disabled
from .employee_category import router as employee_category_router
from .employees import router as employees_router
from .category_master import router as category_master_router
from .size_master import router as size_master_router
from .unit_master import router as unit_master_router
from .raw_material_master import router as raw_material_master_router
from .stock_ledger import router as stock_ledger_router
from .purchase_order import router as purchase_order_router
from .purchase import router as purchase_router
from .purchase_return import router as purchase_return_router
from .supplier_payment import router as supplier_payment_router
from .ledger_transaction import router as ledger_transaction_router
from .product_management import router as product_management_router
from .sales import router as sales_router
from fastapi import APIRouter

# Create main router
router = APIRouter()

# Include auth and user routes
router.include_router(user_router, tags=["Authentication & Users"])

# Include company routes
router.include_router(company_router, tags=["Company Details"])

# Include state routes
router.include_router(state_router, tags=["States"])

# Include accounts routes
router.include_router(accounts_router, prefix="/accounts", tags=["Accounts Master"])

# Include agents routes
router.include_router(agents_router, prefix="/agents", tags=["Agents"])

# Include customers routes
router.include_router(customers_router, prefix="/customers", tags=["Customers"])

# Include suppliers routes
router.include_router(suppliers_router, prefix="/suppliers", tags=["Suppliers"])

# Include bill book routes
router.include_router(bill_book_router, prefix="/bill-books", tags=["Bill Books"])

# Include vendors routes
router.include_router(vendors_router, prefix="/vendors", tags=["Vendors"])  # Temporarily disabled

# Include employee category routes
router.include_router(employee_category_router, prefix="/employee-categories", tags=["Employee Categories"])

# Include employees routes
router.include_router(employees_router, prefix="/employees", tags=["Employees"])

# Include material master routes
router.include_router(category_master_router, prefix="/category-master", tags=["Category Master"])
router.include_router(size_master_router, prefix="/size-master", tags=["Size Master"])
router.include_router(unit_master_router, prefix="/unit-master", tags=["Unit Master"])
router.include_router(raw_material_master_router, prefix="/raw-material-master", tags=["Raw Material Master"])

# Include stock ledger routes
router.include_router(stock_ledger_router, prefix="/stock-ledger", tags=["Stock Ledger"])

# Include purchase order routes
router.include_router(purchase_order_router, prefix="/purchase-orders", tags=["Purchase Orders"])

# Include purchase routes
router.include_router(purchase_router, prefix="/purchases", tags=["Purchases"])

# Include purchase return routes
router.include_router(purchase_return_router, prefix="/purchase-returns", tags=["Purchase Returns"])

# Include supplier payment routes
router.include_router(supplier_payment_router, prefix="/supplier-payments", tags=["Supplier Payments"])

# Include ledger transaction routes
router.include_router(ledger_transaction_router, prefix="/ledger-transactions", tags=["Ledger Transactions"])

# Include product management routes
router.include_router(product_management_router, prefix="/products", tags=["Product Management"])

# Include sales routes
router.include_router(sales_router, prefix="/sales", tags=["Sales Management"])

__all__ = ["router"]
