# 📋 Product Sales Billing System - Implementation Plan

## 📊 Database Schema Design

### 1. **Sales Table**
```sql
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_book_id INTEGER NOT NULL REFERENCES bill_books(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    agent_id INTEGER NULL REFERENCES agents(id),
    bill_number VARCHAR(50) NOT NULL UNIQUE,
    bill_date DATE NOT NULL,
    due_date DATE NULL,
    
    -- Summary fields
    item_count INTEGER DEFAULT 0,
    total_qty DECIMAL(15,3) DEFAULT 0.000,
    gross_amount DECIMAL(15,2) DEFAULT 0.00,
    discount_amount DECIMAL(15,2) DEFAULT 0.00,
    tax_amount DECIMAL(15,2) DEFAULT 0.00,
    additional_charges DECIMAL(15,2) DEFAULT 0.00,
    total_amount DECIMAL(15,2) DEFAULT 0.00,
    
    -- Transport details
    transport_details TEXT NULL,
    llr_no VARCHAR(100) NULL,
    llr_date DATE NULL,
    
    -- Status and audit
    status ENUM('DRAFT', 'CONFIRMED', 'DISPATCHED', 'DELIVERED', 'CANCELLED') DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(50) NOT NULL,
    updated_by VARCHAR(50) NULL,
    
    -- Indexes
    INDEX idx_sales_bill_number (bill_number),
    INDEX idx_sales_customer (customer_id),
    INDEX idx_sales_agent (agent_id),
    INDEX idx_sales_date (bill_date),
    INDEX idx_sales_status (status)
);
```

### 2. **Sales Items Table**
```sql
CREATE TABLE sales_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    
    -- Product details (captured at time of sale)
    product_name VARCHAR(200) NOT NULL,
    hsn_code VARCHAR(20) NULL,
    unit_type VARCHAR(50) NOT NULL,
    
    -- Quantity and pricing
    quantity DECIMAL(15,3) NOT NULL,
    mrp DECIMAL(15,2) NOT NULL,
    sale_rate DECIMAL(15,2) NOT NULL,
    
    -- Tax calculations
    tax_percentage DECIMAL(5,2) DEFAULT 0.00,
    tax_amount DECIMAL(15,2) DEFAULT 0.00,
    
    -- Discount calculations
    discount_percentage DECIMAL(5,2) DEFAULT 0.00,
    discount_amount DECIMAL(15,2) DEFAULT 0.00,
    
    -- Total amount
    total_amount DECIMAL(15,2) NOT NULL,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_sales_items_sales_id (sales_id),
    INDEX idx_sales_items_variant (variant_id)
);
```

## 🎯 API Endpoints Plan

### **Base URL:** `/api/sales/`

### 1. **Sales Management**
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| `POST` | `/api/sales/` | Create new sales invoice | All Users |
| `GET` | `/api/sales/` | List all sales with filtering | All Users |
| `GET` | `/api/sales/{sales_id}` | Get specific sales details | All Users |
| `PUT` | `/api/sales/{sales_id}` | Update sales invoice | All Users |
| `DELETE` | `/api/sales/{sales_id}` | Delete sales invoice | Admin/Creator |
| `PATCH` | `/api/sales/{sales_id}/status` | Update sales status | All Users |

### 2. **Sales Items Management**
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| `POST` | `/api/sales/{sales_id}/items/` | Add item to sales | All Users |
| `PUT` | `/api/sales/{sales_id}/items/{item_id}` | Update sales item | All Users |
| `DELETE` | `/api/sales/{sales_id}/items/{item_id}` | Remove sales item | All Users |
| `GET` | `/api/sales/{sales_id}/items/` | Get all items for sales | All Users |

### 3. **Special Operations**
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| `POST` | `/api/sales/{sales_id}/duplicate` | Duplicate sales invoice | All Users |
| `GET` | `/api/sales/reports/summary` | Sales summary report | All Users |
| `GET` | `/api/sales/customer/{customer_id}` | Get customer sales history | All Users |
| `POST` | `/api/sales/bulk-create` | Bulk create sales | Admin |

## 📝 Request/Response Schemas

### **Create Sales Request**
```json
{
  "bill_book_id": 1,
  "customer_id": 123,
  "agent_id": 45,
  "bill_date": "2025-08-30",
  "due_date": "2025-09-30",
  "transport_details": "Truck transport",
  "llr_no": "LLR12345",
  "llr_date": "2025-08-30",
  "additional_charges": 100.00,
  "created_by": "user123",
  "items": [
    {
      "variant_id": 1,
      "quantity": 5.000,
      "sale_rate": 250.00,
      "discount_percentage": 5.00,
      "tax_percentage": 18.00
    },
    {
      "variant_id": 2,
      "quantity": 3.000,
      "sale_rate": 400.00,
      "discount_percentage": 0.00,
      "tax_percentage": 18.00
    }
  ]
}
```

### **Sales Response**
```json
{
  "id": 1,
  "bill_number": "INV0001",
  "bill_book": {
    "id": 1,
    "book_name": "Tax Invoice Book",
    "tax_type": "INCLUDE_TAX"
  },
  "customer": {
    "id": 123,
    "customer_name": "ABC Company Ltd",
    "contact_person": "John Doe"
  },
  "agent": {
    "id": 45,
    "agent_name": "Sales Agent 1"
  },
  "bill_date": "2025-08-30",
  "due_date": "2025-09-30",
  "item_count": 2,
  "total_qty": 8.000,
  "gross_amount": 2450.00,
  "discount_amount": 62.50,
  "tax_amount": 429.75,
  "additional_charges": 100.00,
  "total_amount": 2917.25,
  "status": "DRAFT",
  "transport_details": "Truck transport",
  "llr_no": "LLR12345",
  "llr_date": "2025-08-30",
  "created_at": "2025-08-30T10:00:00Z",
  "updated_at": "2025-08-30T10:00:00Z",
  "created_by": "user123",
  "items": [
    {
      "id": 1,
      "variant_id": 1,
      "product_name": "Smart Plus Shirt - Size 36 - Full Sleeve",
      "hsn_code": "6205",
      "unit_type": "PCS",
      "quantity": 5.000,
      "mrp": 300.00,
      "sale_rate": 250.00,
      "tax_percentage": 18.00,
      "tax_amount": 225.00,
      "discount_percentage": 5.00,
      "discount_amount": 62.50,
      "total_amount": 1412.50
    }
  ]
}
```

## 🔧 Implementation Steps

### **Phase 1: Database Setup**
1. ✅ Create sales table migration script
2. ✅ Create sales_items table migration script  
3. ✅ Add foreign key constraints
4. ✅ Create necessary indexes
5. ✅ Add sample data for testing

### **Phase 2: Models & Schemas**
1. ✅ Create Sales SQLAlchemy model
2. ✅ Create SalesItem SQLAlchemy model
3. ✅ Create Pydantic schemas for requests/responses
4. ✅ Add validation rules
5. ✅ Create enums for status

### **Phase 3: Business Logic**
1. ✅ Tax calculation logic based on bill_book.tax_type
2. ✅ Discount calculation logic
3. ✅ Bill number generation integration
4. ✅ Inventory integration (stock updates)
5. ✅ Automatic totals calculation

### **Phase 4: API Routes**
1. ✅ Create sales CRUD operations
2. ✅ Create sales items CRUD operations
3. ✅ Add filtering and pagination
4. ✅ Add validation and error handling
5. ✅ Add business rule enforcement

### **Phase 5: Integration**
1. ✅ Bill book integration for numbering
2. ✅ Customer/Agent integration
3. ✅ Product variant integration
4. ✅ Stock ledger updates
5. ✅ Accounting ledger integration

### **Phase 6: Advanced Features**
1. ✅ Sales reports and analytics
2. ✅ Bulk operations
3. ✅ Invoice printing/PDF generation
4. ✅ Sales tracking and status updates
5. ✅ Customer sales history

## 🛡️ Business Rules

### **Tax Calculation Rules**
- **INCLUDE_TAX**: Separate tax from sale_rate
- **EXCLUDE_TAX**: Add tax on top of sale_rate  
- **WITHOUT_TAX**: No tax calculations

### **Validation Rules**
- Bill number must be unique
- Sale rate cannot be negative
- Quantity must be greater than 0
- Total amount must match calculated totals
- Due date cannot be before bill date
- Customer must exist and be active

### **Status Workflow**
```
DRAFT → CONFIRMED → DISPATCHED → DELIVERED
  ↓
CANCELLED (from any status)
```

### **Deletion Rules**
- Only DRAFT invoices can be deleted
- CONFIRMED+ invoices can only be cancelled
- Admin can delete any invoice with proper reason

## 📊 Integration Points

### **With Existing Systems**
1. **Bill Books**: Auto bill number generation
2. **Customers**: Customer validation and details
3. **Agents**: Agent commission tracking
4. **Product Variants**: Stock validation and updates
5. **Accounts**: Automatic ledger entries

### **Stock Management**
- Reduce stock on CONFIRMED status
- Return stock on CANCELLED status
- Track stock movements in product_stock_ledger

## 🧪 Testing Strategy

### **Unit Tests**
- Tax calculation functions
- Discount calculation functions
- Total amount calculations
- Business rule validations

### **Integration Tests**
- Complete sales creation flow
- Bill number generation
- Stock updates
- Customer/agent integrations

### **API Tests**
- All CRUD operations
- Error handling scenarios
- Authentication/authorization
- Performance with large datasets

## 📈 Future Enhancements

1. **Payment Integration**: Link with payment system
2. **Delivery Tracking**: GPS tracking integration
3. **Customer Portal**: Customer can view their invoices
4. **Mobile App**: Sales team mobile application
5. **Analytics Dashboard**: Sales performance metrics
6. **Automated Invoicing**: Recurring invoice generation
7. **Multi-currency**: Support for different currencies
8. **Barcode Integration**: Barcode scanning for items

---

## 🚀 Ready to Start Implementation?

This plan provides a comprehensive roadmap for implementing the Product Sales Billing system. Each phase builds upon the previous one, ensuring a solid foundation before adding advanced features.

**Next Step**: Should I start with Phase 1 (Database Setup) and create the migration scripts for the sales tables?
